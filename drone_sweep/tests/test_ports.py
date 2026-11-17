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
    text, boxes = collect_flight_controller(port)
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


def test_permission_denied_names_the_dialout_group():
    from drone_sweep.usb_read import port_open_error

    text = port_open_error("/dev/ttyACM0", PermissionError(13, "Permission denied"))
    assert "dialout" in text
    assert "allow-usb" in text
    assert "0483:5740" in text
    assert "/dev/ttyACM0" in text
    assert "dialout" not in port_open_error("COM3", PermissionError(13, "Permission denied"))


def test_udev_rule_matches_the_serial_ids_and_skips_the_dfu_bootloader(tmp_path: Path):
    from drone_sweep.usb_access import SERIAL_IDS, rules_text, usb_ids

    text = rules_text()
    for vendor, product in SERIAL_IDS:
        assert f'idVendor}}=="{vendor}"' in text
        assert f'idProduct}}=="{product}"' in text
    assert "df11" not in text
    assert 'SUBSYSTEM=="tty"' in text
    device = tmp_path / "1-1:1.0"
    usb = tmp_path
    device.mkdir()
    (usb / "idVendor").write_text("0483\n", encoding="ascii")
    (usb / "idProduct").write_text("5740\n", encoding="ascii")
    assert usb_ids(device) == ("0483", "5740")


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


def test_a_short_parameter_list_is_marked_incomplete():
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
