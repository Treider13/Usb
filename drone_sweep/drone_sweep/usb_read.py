"""USB session.

Only read commands are written to the port. `save`, `set`, `defaults`
and MSP codes that write configuration are rejected before they reach
the wire. A MAVLink board is identified by HEARTBEAT and read with
PARAM_REQUEST_LIST. No parameter is written back.
"""

from __future__ import annotations

from dataclasses import dataclass, field


READ_CLI = {"version", "status", "dump", "diff", "tasks", "get", "exit"}
MSP_BOXNAMES = 116
MSP_API_VERSION = 1
MSP_FC_VARIANT = 2
MSP_NAME = 10


class ReadOnlyError(ValueError):
    pass


def assert_readonly_cli(command: str) -> str:
    text = command.strip()
    if not text:
        raise ReadOnlyError("пустая команда")
    if any(token in text.lower() for token in ("save", "defaults", "flash_erase", "bind_rx")):
        raise ReadOnlyError(f"команда меняет полётник: {text}")
    head = text.split()[0].lower()
    if head == "set":
        raise ReadOnlyError("set пишет настройку")
    if head not in READ_CLI:
        raise ReadOnlyError(f"команда не из списка чтения: {head}")
    if head == "dump" and text.lower() != "dump all":
        raise ReadOnlyError("разрешён только dump all")
    if head == "diff" and text.lower() != "diff all":
        raise ReadOnlyError("разрешён только diff all")
    if head == "get" and len(text.split()) != 2:
        raise ReadOnlyError("get читает одно имя")
    return text


def msp_request(code: int, payload: bytes = b"") -> bytes:
    if code >= 200:
        raise ReadOnlyError(f"MSP {code} находится в диапазоне команд записи")
    if payload:
        raise ReadOnlyError("читающий MSP уходит без тела")
    size = 0
    checksum = size ^ code
    return bytes([ord("$"), ord("M"), ord("<"), size, code, checksum])


@dataclass
class ScriptedPort:
    """In-memory port. Tests script the replies; a real port needs read/write."""

    chunks: list[bytes] = field(default_factory=list)
    written: list[bytes] = field(default_factory=list)

    def write(self, data: bytes) -> None:
        self.written.append(data)

    def read(self, size: int = 4096) -> bytes:
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        return chunk[:size]


def read_cli(port: ScriptedPort, commands: list[str]) -> str:
    port.write(b"#")
    parts = [port.read().decode("latin1", errors="replace")]
    for command in commands:
        safe = assert_readonly_cli(command)
        port.write(safe.encode("ascii") + b"\n")
        parts.append(port.read().decode("latin1", errors="replace"))
    port.write(b"exit\n")
    return "".join(parts)


def read_boxnames(port: ScriptedPort) -> str:
    port.write(msp_request(MSP_BOXNAMES))
    frame = port.read()
    return _msp_payload(frame, MSP_BOXNAMES).decode("latin1", errors="replace")


def collect_flight_controller(port) -> tuple[str, str]:
    """Read version, status and dump all, then MSP_BOXNAMES. Nothing is saved."""
    dump_text = read_cli(port, ["version", "status", "dump all"])
    boxes = read_boxnames(port)
    return dump_text, boxes


class QuietPort:
    """Read a real serial port until it stays quiet or the CLI prompt returns.

    `read` is called once per command by `read_cli`. One call keeps pulling
    until the adapter has been idle, so a long `dump all` is not cut at 4096 bytes.
    """

    def __init__(self, raw, idle_s: float = 0.4, overall_s: float = 20.0) -> None:
        self.raw = raw
        self.idle_s = idle_s
        self.overall_s = overall_s

    def write(self, data: bytes) -> None:
        self.raw.write(data)
        flush = getattr(self.raw, "flush", None)
        if flush is not None:
            flush()

    def read(self, size: int = 4096) -> bytes:
        import time

        buf = bytearray()
        deadline = time.monotonic() + self.overall_s
        idle_deadline = time.monotonic() + self.idle_s
        while time.monotonic() < deadline:
            chunk = self.raw.read(size)
            now = time.monotonic()
            if chunk:
                buf += chunk
                idle_deadline = now + self.idle_s
                if buf.rstrip(b"\r\n ").endswith(b"#"):
                    idle_deadline = min(idle_deadline, now + 0.05)
            elif now >= idle_deadline:
                break
        return bytes(buf)


def open_betaflight_port(path: str, overall_s: float = 90.0) -> QuietPort:
    import serial

    raw = serial.Serial(path, 115200, timeout=0.05)
    return QuietPort(raw, overall_s=overall_s)


def msp_variant_name(frame: bytes) -> str | None:
    """MSP_FC_VARIANT payload. Betaflight answers BTFL, INAV answers INAV, Cleanflight answers CLFL."""
    try:
        payload = _msp_payload(frame, MSP_FC_VARIANT)
    except ValueError:
        return None
    token = payload[:4]
    return {b"BTFL": "betaflight", b"INAV": "inav", b"CLFL": "cleanflight"}.get(token)


def mavlink_heartbeat(buf: bytes) -> dict | None:
    """The first HEARTBEAT in a buffer. ArduPilot's autopilot field is 3."""
    try:
        from pymavlink.dialects.v20 import ardupilotmega as dialect
    except ImportError:
        return None
    parser = dialect.MAVLink(None)
    parser.robust_parsing = True
    for index in range(len(buf)):
        message = parser.parse_char(buf[index:index + 1])
        if message is not None and message.get_type() == "HEARTBEAT":
            return {
                "autopilot": message.autopilot,
                "type": message.type,
                "mavlink_version": getattr(message, "mavlink_version", None),
            }
    return None


def read_mavlink_parameters(connection) -> list[dict]:
    """PARAM_REQUEST_LIST only. No parameter is written back."""
    connection.mav.param_request_list_send(connection.target_system, connection.target_component)
    rows: list[dict] = []
    while True:
        message = connection.recv_match(type="PARAM_VALUE", blocking=True, timeout=3)
        if message is None:
            break
        rows.append(
            {
                "name": "PARAM_VALUE",
                "param_id": message.param_id,
                "param_value": message.param_value,
            }
        )
        if message.param_index + 1 >= message.param_count:
            break
    return rows


def read_usb(path: str, port_opener=None, mavlink_opener=None) -> "Inputs":
    """Identify the board the way the Configurator opens a port, then read it.

    Betaflight Configurator sends MSP_API_VERSION and then MSP_FC_VARIANT and
    stops unless the answer is BTFL. Strela keeps INAV and Cleanflight, and a
    MAVLink HEARTBEAT is read with PARAM_REQUEST_LIST.
    """
    from .assemble import Inputs

    if port_opener is not None:
        port = port_opener(path)
        dump_text, boxes = collect_flight_controller(port)
        return Inputs(dump_text=dump_text, boxnames=boxes)
    kind, beat = _probe(path)
    if kind == "mavlink":
        if mavlink_opener is None:
            from pymavlink import mavutil

            link = mavutil.mavlink_connection(path, baud=115200)
            link.wait_heartbeat(timeout=5)
        else:
            link = mavlink_opener(path)
        try:
            rows = read_mavlink_parameters(link)
        finally:
            close = getattr(link, "close", None)
            if close is not None:
                close()
        if beat:
            rows.insert(0, {"name": "HEARTBEAT", **beat})
        return Inputs(mavlink_rows=rows)
    if kind in {"betaflight", "inav", "cleanflight"}:
        port = open_betaflight_port(path)
        try:
            dump_text, boxes = collect_flight_controller(port)
        finally:
            port.raw.close()
        return Inputs(dump_text=dump_text, boxnames=boxes)
    raise ValueError("порт не назвал Betaflight, INAV, Cleanflight и не прислал HEARTBEAT")


def _probe(path: str) -> tuple[str, dict | None]:
    port = open_betaflight_port(path, overall_s=1.5)
    try:
        heard = port.read()
        beat = mavlink_heartbeat(heard)
        if beat is not None:
            return "mavlink", beat
        port.write(msp_request(MSP_API_VERSION))
        port.read()
        port.write(msp_request(MSP_FC_VARIANT))
        variant = msp_variant_name(port.read())
        if variant is not None:
            return variant, None
    finally:
        port.raw.close()
    return "unknown", None


def describe_ports() -> list[tuple[str, str]]:
    """Device path and the label a person sees, same role as the Configurator port list."""
    try:
        from serial.tools import list_ports
    except ImportError:
        return []
    found = []
    for entry in list_ports.comports():
        label = entry.device
        if entry.description and entry.description != "n/a":
            label = f"{entry.device} — {entry.description}"
        found.append((entry.device, label))
    return found


def _msp_payload(frame: bytes, code: int) -> bytes:
    if len(frame) < 6 or frame[0:3] != b"$M>":
        raise ValueError("порт не вернул MSP-ответ")
    size = frame[3]
    if frame[4] != code:
        raise ValueError(f"ожидался MSP {code}, пришёл {frame[4]}")
    return frame[5:5 + size]
