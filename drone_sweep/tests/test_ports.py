"""Ports and the USB read that fills a card from them.

The numbers are the ones in the firmware sources, so a wrong index fails here.
"""

from pathlib import Path

from drone_sweep.assemble import Inputs, assemble
from drone_sweep.menu import run_menu
from drone_sweep.ports import decode_osd_position, map_baudrate
from drone_sweep.usb_read import QuietPort, ScriptedPort, collect_flight_controller, msp_request
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
    assert b"save" not in written.lower()
    assert b"serialpassthrough" not in written.lower()
    assert msp_request(116) in port.written

    out = tmp_path / "usb-out"
    menu = run_menu(["3", "/dev/ttyTEST", str(out), "5"], port_opener=lambda path: _scripted_fc())
    assert "Отчёт:" in menu
    assert "Приёмник назначен на USART1" in menu
    saved = (out / "card.json").read_text(encoding="utf-8")
    assert "USART1" in saved


def test_usb_without_a_banner_does_not_invent_a_card(tmp_path: Path):
    empty = bytes([ord("$"), ord("M"), ord(">"), 0, 116, 116])
    port = ScriptedPort(chunks=[b"\r\n", b"hello\r\n", empty])
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
    return ScriptedPort(chunks=[b"#\r\n", DUMP.encode("ascii"), reply])


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
