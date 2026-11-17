"""Ports and the USB read that fills a card from them.

The numbers are the ones in the firmware sources, so a wrong index fails here.
"""

from pathlib import Path

from drone_sweep.assemble import Inputs, assemble
from drone_sweep.menu import run_menu
from drone_sweep.ports import decode_osd_position, map_baudrate
from drone_sweep.usb_read import (
    MSP_FC_VARIANT,
    QuietPort,
    ReadOnlyError,
    ScriptedPort,
    assert_readonly_cli,
    cli_leave,
    collect_flight_controller,
    mavlink_heartbeat,
    msp_request,
    msp_variant_name,
    read_mavlink_parameters,
    SerialMavlink,
)
from drone_sweep.webapp import home_page
from tests.bin_builder import write_bin


DUMP = """\
# Betaflight / STM32F405 (S405) 4.5.0 Jan 01 2025 / GIT
board_name TANTOF405_V2
feature -RX_PPM
feature RX_SERIAL
feature OSD
serial 20 1 115200 57600 0 115200
serial 0 64 115200 57600 0 115200
serial 1 2048 115200 57600 0 115200
serial 2 1048576 115200 57600 0 115200
set osd_vbat_pos = 234
set osd_rssi_pos = 2282
set serialrx_provider = CRSF
"""


def test_betaflight_serial_mask_names_the_receiver_and_leaves_unknown_bits():
    card = assemble(Inputs(dump_text=DUMP))
    ports = {item["port"]: item for item in card.fields["serial_ports"].value}
    assert ports["USB_VCP"]["functions"] == ["MSP"]
    assert ports["USB_VCP"]["telemetry_baud_auto"] is True
    assert ports["USART1"]["functions"] == ["RX_SERIAL"]
    assert ports["USART2"]["functions"] == ["VTX_SMARTAUDIO"]
    assert "bit20" in ports["USART3"]["functions"]
    assert "GIMBAL" not in ports["USART3"]["functions"]
    assert card.fields["receiver_port"].value == "USART1"
    assert "не включает" in card.fields["receiver_port"].reason
    assert card.fields["vtx_uart"].value == ["USART2"]
    assert card.fields["features"].value["enabled"] == ["RX_SERIAL", "OSD"]
    assert card.fields["features"].value["disabled"] == ["RX_PPM"]
    layout = {item["name"]: item for item in card.fields["osd_layout"].value}
    assert layout["osd_vbat_pos"] == {"x": 10, "y": 7, "visible": False, "type": 0, "raw": 234, "name": "osd_vbat_pos"}
    assert layout["osd_rssi_pos"]["visible"] is True
    assert layout["osd_rssi_pos"]["x"] == 10
    assert decode_osd_position(234)["y"] == 7


def test_ardupilot_serial_protocol_numbers_match_copter_45(tmp_path: Path):
    assert map_baudrate(115) == 115200
    assert map_baudrate(57) == 57600
    assert map_baudrate(0) == 57600
    assert map_baudrate(2500) == 2500
    assert map_baudrate(12) == 12000
    path = tmp_path / "ports.bin"
    write_bin(
        path,
        [
            _parm(1, "SERIAL1_PROTOCOL", 29),
            _parm(1, "SERIAL1_BAUD", 115),
            _parm(1, "SERIAL2_PROTOCOL", 5),
            _parm(1, "SERIAL3_PROTOCOL", 37),
            _parm(1, "SERIAL4_PROTOCOL", 47),
        ],
    )
    card = assemble(Inputs(bin_path=path))
    ports = {item["port"]: item for item in card.fields["serial_ports"].value}
    assert ports["SERIAL1"]["protocol_name"] == "CRSF"
    assert ports["SERIAL1"]["baud"] == 115200
    assert ports["SERIAL1"]["receiver"] is True
    assert ports["SERIAL2"]["protocol_name"] == "GPS"
    assert ports["SERIAL2"]["receiver"] is False
    assert ports["SERIAL3"]["protocol_name"] == "SmartAudio"
    assert ports["SERIAL4"]["protocol_name"] == "unknown"
    assert card.fields["receiver_port"].value == "SERIAL1"
    assert card.fields["features"].status == "not_applicable"


def test_two_receiver_protocols_are_not_collapsed(tmp_path: Path):
    path = tmp_path / "two.bin"
    write_bin(
        path,
        [
            _parm(1, "SERIAL1_PROTOCOL", 23),
            _parm(1, "SERIAL2_PROTOCOL", 15),
        ],
    )
    card = assemble(Inputs(bin_path=path))
    names = {item["port"]: item["protocol_name"] for item in card.fields["serial_ports"].value}
    assert names == {"SERIAL1": "RCIN", "SERIAL2": "Sbus1"}
    assert card.fields["receiver_port"].status == "missing"


def test_usb_read_sends_dump_all_and_builds_the_card(tmp_path: Path):
    port = _scripted_fc()
    text, boxes, identity = collect_flight_controller(port)
    assert "TANTOF405" in text
    assert boxes == "ARM;ANGLE"
    written = b"".join(port.written)
    assert b"dump all\n" in written
    assert b"version\n" in written
    assert b"status\n" in written
    assert b"save" not in written.lower()
    assert b"serialpassthrough" not in written.lower()
    assert b"exit noreboot\n" in written
    assert b"exit\n" not in written
    assert msp_request(116) in port.written
    assert port.written.index(msp_request(116)) < port.written.index(b"#")

    out = tmp_path / "usb-out"
    menu = run_menu(["3", "/dev/ttyTEST", str(out), "5"], port_opener=lambda path: _scripted_fc())
    assert "Отчёт:" in menu
    assert "Приёмник назначен на USART1" in menu
    saved = (out / "card.json").read_text(encoding="utf-8")
    assert "USART1" in saved


def test_usb_without_a_banner_does_not_invent_a_card(tmp_path: Path):
    empty = bytes([ord("$"), ord("M"), ord(">"), 0, 116, 116])
    port = ScriptedPort(chunks=[b"\r\n", b"hello\r\n", b"no banner\r\n", b"still no\r\n", empty])
    out = tmp_path / "empty"
    menu = run_menu(["3", "/dev/ttyTEST", str(out), "5"], port_opener=lambda path: port)
    assert "не выдуманы" in menu
    assert not out.exists()


def _scripted_fc() -> ScriptedPort:
    payload = b"ARM;ANGLE"
    size = len(payload)
    checksum = size ^ 116
    for byte in payload:
        checksum ^= byte
    reply = bytes([ord("$"), ord("M"), ord(">"), size, 116]) + payload + bytes([checksum])
    return ScriptedPort(
        chunks=[
            b"",
            b"",
            b"",
            b"",
            reply,
            b"#\r\n",
            b"# Betaflight / STM32F405 4.5.0\r\n#\r\n",
            b"System Uptime: 10 seconds\r\n#\r\n",
            DUMP.encode("ascii"),
        ]
    )


def _variant_frame(token: bytes) -> bytes:
    checksum = len(token) ^ MSP_FC_VARIANT
    for byte in token:
        checksum ^= byte
    return bytes([ord("$"), ord("M"), ord(">"), len(token), MSP_FC_VARIANT]) + token + bytes([checksum])


def test_version_text_names_a_board_left_in_the_cli():
    from drone_sweep.usb_read import family_in_text

    assert family_in_text("# Betaflight / STM32F405 4.5.0\r\n#\r\n") == "betaflight"
    assert family_in_text("INAV/MATEKF405 7.0.0\r\n#\r\n") == "inav"
    assert family_in_text("Cleanflight / STM32F303\r\n") == "cleanflight"
    assert family_in_text("Hello\r\n#\r\n") is None


def test_msp_variant_names_the_three_flight_stacks():
    assert msp_variant_name(_variant_frame(b"BTFL")) == "betaflight"
    assert msp_variant_name(_variant_frame(b"INAV")) == "inav"
    assert msp_variant_name(_variant_frame(b"CLFL")) == "cleanflight"
    assert msp_variant_name(_variant_frame(b"XXXX")) is None
    assert msp_variant_name(b"not a frame") is None


def test_mavlink_heartbeat_requires_a_real_frame():
    from io import BytesIO

    from pymavlink.dialects.v20 import ardupilotmega as dialect

    buf = BytesIO()
    link = dialect.MAVLink(buf)
    link.srcSystem = 1
    link.heartbeat_send(2, 3, 0, 0, 4, 3)
    found = mavlink_heartbeat(buf.getvalue())
    assert found is not None
    assert found["autopilot"] == 3
    assert mavlink_heartbeat(b"\xfd" * 40) is None


def test_param_request_list_does_not_write_a_parameter():
    class Link:
        def __init__(self):
            self.sent = []
            self.target_system = 1
            self.target_component = 1
            self.mav = self
            self.left = [
                _Param("SERIAL1_PROTOCOL", 29.0, 0, 2),
                _Param("SERIAL1_BAUD", 115.0, 1, 2),
            ]

        def param_request_list_send(self, system, component):
            self.sent.append((system, component))

        def recv_match(self, type=None, blocking=False, timeout=None):
            return self.left.pop(0) if self.left else None

    link = Link()
    rows, note = read_mavlink_parameters(link)
    assert note == ""
    assert link.sent == [(1, 1)]
    card = assemble(
        Inputs(
            mavlink_rows=[{"name": "HEARTBEAT", "autopilot": 3, "type": 2}, *rows]
        )
    )
    assert card.family == "ardupilot"
    assert card.fields["mavlink_heartbeat"].source == "usb HEARTBEAT"
    assert card.fields["parameters"].source == "usb PARAM_VALUE"
    assert card.fields["serial_ports"].value[0]["protocol_name"] == "CRSF"
    assert "dump all" not in str(link.sent)


class _Param:
    def __init__(self, param_id, param_value, param_index, param_count):
        self.param_id = param_id
        self.param_value = param_value
        self.param_index = param_index
        self.param_count = param_count


def test_bare_exit_is_refused_because_it_reboots():
    import pytest

    with pytest.raises(ReadOnlyError):
        assert_readonly_cli("exit")
    assert assert_readonly_cli("exit noreboot") == "exit noreboot"
    leave, note = cli_leave("betaflight")
    assert leave == "exit noreboot"
    assert note == ""
    leave, note = cli_leave("inav")
    assert leave is None
    assert "cliReboot" in note


def test_msp_identity_uses_betaflight_and_inav_layouts():
    from drone_sweep.msp_identity import MSP_BOARD_INFO, MSP_BUILD_INFO, MSP_FC_VERSION, describe_identity

    beta = describe_identity(
        {
            MSP_FC_VERSION: bytes([25, 3, 0, 5]) + b"4.5.0",
            MSP_BOARD_INFO: (
                b"S405"
                + (0).to_bytes(2, "little")
                + bytes([2, 1, 9])
                + b"STM32F405"
                + bytes([9])
                + b"TANTOF405"
                + bytes([3])
                + b"TBS"
            ),
            MSP_BUILD_INFO: b"Mar 01 2025" + b"12:00:00" + b"abcdef0",
        },
        "betaflight",
    )
    assert beta["fc_version"]["version"] == "4.5.0"
    assert beta["fc_version"]["year_since_2000"] == 25
    assert beta["board"]["board_name"] == "TANTOF405"
    assert beta["board"]["osd_label"] == "MAX7456"
    assert beta["build"]["git"] == "abcdef0"

    inav = describe_identity(
        {
            MSP_FC_VERSION: bytes([7, 0, 0]),
            MSP_BOARD_INFO: b"MF45" + (0).to_bytes(2, "little") + bytes([2, 1, 9]) + b"MATEKF405",
            MSP_BUILD_INFO: b"Mar 01 2025" + b"12:00:00" + b"01234567",
        },
        "inav",
    )
    assert inav["fc_version"]["version"] == "7.0.0"
    assert inav["board"]["target_name"] == "MATEKF405"
    assert "board_name" not in inav["board"]
    assert inav["board"]["osd_label"] == "OSD на плате"
    assert inav["build"]["git"] == "01234567"


def test_a_missing_parameter_index_is_read_again_not_written():
    class Link:
        def __init__(self):
            self.target_system = 1
            self.target_component = 1
            self.mav = self
            self.sent = []
            self.left = [_Param("A", 1.0, 0, 2)]
            self.fill = [_Param("B", 2.0, 1, 2)]

        def param_request_list_send(self, system, component):
            self.sent.append(("list", system, component))

        def param_request_read_send(self, system, component, param_id, index):
            self.sent.append(("read", index, param_id))

        def recv_match(self, type=None, blocking=False, timeout=None):
            if self.left:
                return self.left.pop(0)
            if self.fill and any(item[0] == "read" for item in self.sent):
                return self.fill.pop(0)
            return None

    link = Link()
    rows, note = read_mavlink_parameters(link)
    assert note == ""
    assert [row["param_id"] for row in rows] == ["A", "B"]
    assert ("read", 1, b"\x00" * 16) in link.sent
    assert "set" not in [item[0] for item in link.sent]
    class Link:
        def __init__(self):
            self.target_system = 1
            self.target_component = 1
            self.mav = self
            self.left = [_Param("SERIAL1_PROTOCOL", 29.0, 0, 2)]

        def param_request_list_send(self, system, component):
            return None

        def recv_match(self, type=None, blocking=False, timeout=None):
            return self.left.pop(0) if self.left else None

    rows, note = read_mavlink_parameters(Link())
    card = assemble(Inputs(mavlink_rows=[{"name": "HEARTBEAT", "autopilot": 3}, *rows], read_note=note))
    assert "тишина 3 секунды" in card.holes[-1]
    assert len(card.fields["parameters"].value) == 1


def test_msp_variant_is_found_after_leading_bytes():
    frame = b"garbage" + _variant_frame(b"BTFL") + b"tail"
    assert msp_variant_name(frame) == "betaflight"


def test_home_page_reads_the_selected_usb_port():
    page = home_page([("/dev/ttyACM0", "/dev/ttyACM0 — полётник")]).decode("utf-8")
    assert 'class="topbar"' in page
    assert 'action="/usb"' in page
    assert "Считать" in page
    assert 'name="port"' in page
    assert 'class="baud">115200' in page
    assert "/dev/ttyACM0" in page
    assert "Файл отчёта" not in page
    empty = home_page([]).decode("utf-8")
    assert "Подключите полётник" in empty
    assert "<button" not in empty


def test_quiet_port_keeps_reading_until_the_prompt():
    class Raw:
        def __init__(self):
            self.pieces = [b"# Betaflight 4.5.0\r\n", b"board_name X\r\n#\r\n"]
            self.sent = []

        def write(self, data: bytes) -> None:
            self.sent.append(data)

        def flush(self) -> None:
            return None

        def read(self, size: int) -> bytes:
            if not self.pieces:
                return b""
            return self.pieces.pop(0)

    port = QuietPort(Raw(), idle_s=0.05, overall_s=1.0)
    port.write(b"#")
    text = port.read().decode("ascii")
    assert "Betaflight 4.5.0" in text
    assert "board_name X" in text


def _parm(time_us: int, name: str, value: float) -> tuple:
    return ("PARM", "QNf", "TimeUS,Name,Value", (time_us, name.encode("ascii"), value))


def test_one_usb_read_keeps_every_parameter_frame():
    from io import BytesIO

    from pymavlink.dialects.v20 import ardupilotmega as dialect

    buf = BytesIO()
    encoder = dialect.MAVLink(buf, srcSystem=1, srcComponent=1)
    for index in range(3):
        encoder.param_value_send(f"P{index}".encode("ascii"), float(index), 9, 3, index)
    raw = _Burst([buf.getvalue()])
    link = SerialMavlink(raw, {"src_system": 1, "src_component": 1})
    names = []
    for _ in range(3):
        message = link.recv_match(type="PARAM_VALUE", timeout=0.2)
        assert message is not None
        names.append(str(message.param_id).rstrip("\x00"))
    assert names == ["P0", "P1", "P2"]
    assert link.recv_match(type="PARAM_VALUE", timeout=0) is None


class _Burst:
    def __init__(self, chunks):
        self.chunks = list(chunks)

    def read(self, size: int) -> bytes:
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def write(self, data: bytes) -> None:
        return None

    def flush(self) -> None:
        return None


def test_ardupilot_version_banner_and_log_list_reach_the_card():
    card = assemble(
        Inputs(
            mavlink_rows=[
                {"name": "HEARTBEAT", "autopilot": 3, "type": 2},
                {
                    "name": "AUTOPILOT_VERSION",
                    "major": 4,
                    "minor": 5,
                    "patch": 7,
                    "fw_type": 255,
                    "board_version": 123 << 16,
                    "board_id": 123,
                    "flight_custom_version": "abc",
                    "uid2": "0011",
                    "vendor_id": 0x1209,
                    "product_id": 0x5740,
                    "flight_sw_version": 0,
                },
                {"name": "STATUSTEXT", "text": "ArduCopter V4.5.7 (abc)"},
                {"name": "LOG_ENTRY", "id": 3, "num_logs": 3, "last_log_num": 3, "time_utc": 0, "size": 4096},
            ]
        )
    )
    assert card.family == "ardupilot"
    assert card.raw_banner == "ArduCopter V4.5.7 (abc)"
    assert card.fields["autopilot_version"].value["board_id"] == 123
    assert card.fields["mcu_id"].value == "0011"
    assert card.fields["dataflash_logs"].value[0]["size"] == 4096
    page = __import__("drone_sweep.report", fromlist=["render_html"]).render_html(card)
    assert "Версия прошивки" in page
    assert "Журналы на плате" in page


def test_dataflash_download_saves_the_newest_log_and_never_erases(tmp_path: Path):
    from drone_sweep.ardupilot_read import read_dataflash, request_autopilot_version
    from tests.bin_builder import write_bin
    from tests.test_card import _msg

    source = tmp_path / "source.BIN"
    write_bin(source, [_msg(1, "ArduCopter V4.5.7")])
    blob = source.read_bytes()
    messages = [_Entry(1, 2, 2, 0, 0), _Entry(2, 2, 2, 0, len(blob))]
    offset = 0
    while offset < len(blob):
        piece = blob[offset:offset + 90]
        messages.append(_LogData(2, offset, piece))
        offset += len(piece)
    board = _Board(messages)
    request_autopilot_version(board)
    rows, path, note = read_dataflash(board, tmp_path / "out")
    assert path is not None
    assert path.read_bytes() == blob
    assert "скачан журнал 2" in note
    names = [name for name, _args in board.sent]
    assert "log_erase" not in names
    assert "param_set" not in names
    assert "log_request_list" in names
    assert "log_request_data" in names
    assert "log_request_end" in names
    assert ("command_long", (1, 1, 520, 0, 1, 0, 0, 0, 0, 0, 0)) in board.sent
    assert all(item[1][2] == 0 for item in board.sent if item[0] == "heartbeat")
    card = assemble(Inputs(bin_path=path, mavlink_rows=[{"name": "HEARTBEAT", "autopilot": 3}, *rows]))
    assert any(row.get("text") == "ArduCopter V4.5.7" for row in card.fields["messages"].value)


def test_armed_board_is_not_disarmed_and_the_log_is_not_invented(tmp_path: Path):
    from drone_sweep.ardupilot_read import read_dataflash

    board = _Board([_Status("Disarm for log download")])
    rows, path, note = read_dataflash(board, tmp_path)
    assert path is None
    assert rows == [{"name": "STATUSTEXT", "text": "Disarm for log download"}]
    assert "взведение не снимает" in note
    assert "log_request_data" not in [name for name, _args in board.sent]
    assert "log_erase" not in [name for name, _args in board.sent]


class _Board:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent = []
        self.target_system = 1
        self.target_component = 1
        self.mav = self

    def heartbeat_send(self, *args):
        self.sent.append(("heartbeat", args))

    def command_long_send(self, *args):
        self.sent.append(("command_long", args))

    def log_request_list_send(self, *args):
        self.sent.append(("log_request_list", args))

    def log_request_data_send(self, *args):
        self.sent.append(("log_request_data", args))

    def log_request_end_send(self, *args):
        self.sent.append(("log_request_end", args))

    def recv_match(self, type=None, blocking=False, timeout=None):
        wanted = None if type is None else {type} if isinstance(type, str) else set(type)
        for index, message in enumerate(self.messages):
            if wanted is None or message.get_type() in wanted:
                return self.messages.pop(index)
        return None


class _Entry:
    def __init__(self, ident, num_logs, last_log_num, time_utc, size):
        self.id = ident
        self.num_logs = num_logs
        self.last_log_num = last_log_num
        self.time_utc = time_utc
        self.size = size

    def get_type(self):
        return "LOG_ENTRY"


class _LogData:
    def __init__(self, ident, ofs, data: bytes):
        self.id = ident
        self.ofs = ofs
        self.count = len(data)
        self.data = data

    def get_type(self):
        return "LOG_DATA"


class _Status:
    def __init__(self, text):
        self.text = text

    def get_type(self):
        return "STATUSTEXT"

