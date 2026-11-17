"""USB session.

Only read commands are written to the port. `save`, `set`, `defaults`
and MSP codes that write configuration are rejected before they reach
the wire. A MAVLink board is identified by HEARTBEAT and read with
PARAM_REQUEST_LIST. No parameter is written back. A dataflash log is
requested with LOG_REQUEST_LIST and LOG_REQUEST_DATA, then closed with
LOG_REQUEST_END. LOG_ERASE is not sent.
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
    if head == "exit" and text.lower() != "exit noreboot":
        raise ReadOnlyError("exit без noreboot перезагружает плату")
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


def read_cli(port: ScriptedPort, commands: list[str], leave: str | None = "exit noreboot") -> str:
    port.write(b"#")
    parts = [port.read().decode("latin1", errors="replace")]
    for command in commands:
        safe = assert_readonly_cli(command)
        port.write(safe.encode("ascii") + b"\n")
        parts.append(port.read().decode("latin1", errors="replace"))
    if leave is not None:
        # Betaflight cli.c: bare `exit` reboots. `exit noreboot` returns to MSP.
        safe = assert_readonly_cli(leave)
        port.write(safe.encode("ascii") + b"\n")
    return "".join(parts)


def read_boxnames(port: ScriptedPort) -> str:
    port.write(msp_request(MSP_BOXNAMES))
    frame = port.read()
    try:
        payload = _msp_payload(frame, MSP_BOXNAMES)
    except ValueError:
        return ""
    return payload.decode("latin1", errors="replace")


def collect_flight_controller(port, leave_cli: str | None = "exit noreboot", wants: dict | None = None) -> tuple[str, str, dict]:
    """Read MSP identity and box names, then the CLI dump.

    Names and identity are requested first: after `#` the port is a text
    console and an MSP frame is no longer a request. Nothing is saved.
    """
    chosen = wants or {"msp": True, "dump": True}
    raw_identity: dict[int, bytes | None] = {}
    if chosen.get("msp", True):
        raw_identity = _read_msp_identity(port)
    boxes = read_boxnames(port) if chosen.get("dump", True) or chosen.get("msp", True) else ""
    dump_text = ""
    if chosen.get("dump", True):
        dump_text = read_cli(port, ["version", "status", "dump all"], leave=leave_cli)
    from .msp_identity import describe_identity

    identity = describe_identity(raw_identity, family_in_text(dump_text))
    return dump_text, boxes, identity


def _read_msp_identity(port) -> dict[int, bytes | None]:
    from .msp_identity import MSP_BOARD_INFO, MSP_BUILD_INFO, MSP_FC_VERSION, MSP_NAME

    found: dict[int, bytes | None] = {}
    for code in (MSP_FC_VERSION, MSP_BOARD_INFO, MSP_BUILD_INFO, MSP_NAME):
        port.write(msp_request(code))
        frame = port.read()
        try:
            found[code] = _msp_payload(frame, code)
        except ValueError:
            found[code] = None
    return found


def cli_leave(kind: str) -> tuple[str | None, str]:
    """How to leave the CLI without a reboot, for the firmware we identified."""
    if kind == "betaflight":
        return "exit noreboot", ""
    if kind == "inav":
        return (
            None,
            "INAV оставлен в CLI. В src/main/fc/cli.c команда exit вызывает cliReboot(), поэтому она не отправлена.",
        )
    return (
        None,
        "Плата оставлена в CLI. exit noreboot есть в Betaflight cli.c и не перезагружает плату. Для этой прошивки команда не отправлялась.",
    )


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

    def listen(self, seconds: float) -> bytes:
        """Keep the port open for `seconds` even when it is quiet.

        ArduPilot sends HEARTBEAT once a second. The short idle used for a
        CLI line would return before that frame arrives.
        """
        saved = (self.idle_s, self.overall_s)
        self.idle_s = seconds
        self.overall_s = seconds
        try:
            return self.read()
        finally:
            self.idle_s, self.overall_s = saved


def open_betaflight_port(path: str, overall_s: float = 90.0) -> QuietPort:
    import serial

    raw = serial.Serial()
    raw.port = path
    raw.baudrate = 115200
    raw.timeout = 0.05
    raw.dtr = False
    raw.rts = False
    raw.open()
    raw.dtr = False
    raw.rts = False
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
                "src_system": message.get_srcSystem(),
                "src_component": message.get_srcComponent(),
            }
    return None


class SerialMavlink:
    """MAVLink on a port that is already open. The port is not reopened.

    A USB read can hold many PARAM_VALUE or LOG_DATA frames. Every frame in
    the chunk is queued. Returning the first match and discarding the rest
    left the card with one parameter.
    """

    def __init__(self, raw, beat: dict | None):
        from pymavlink.dialects.v20 import ardupilotmega as dialect

        self.raw = raw
        self.mav = dialect.MAVLink(self, srcSystem=255, srcComponent=190)
        # Boot text and a torn frame share the USB stream. Without this flag
        # parse_buffer raises MAVError on a byte that is not 0xFD or 0xFE
        # and the whole read dies. pymavlink then reports BAD_DATA instead.
        self.mav.robust_parsing = True
        self.target_system = int((beat or {}).get("src_system") or 1)
        self.target_component = int((beat or {}).get("src_component") or 1)
        self._queue: list = []

    def write(self, data: bytes) -> None:
        self.raw.write(data)
        flush = getattr(self.raw, "flush", None)
        if flush is not None:
            flush()

    def recv_match(self, type=None, blocking=False, timeout=None):
        import time

        wanted = None if type is None else {type} if isinstance(type, str) else set(type)
        deadline = time.monotonic() + (timeout or 0)
        while True:
            found = self._take(wanted)
            if found is not None:
                return found
            if time.monotonic() >= deadline:
                return None
            self._pull()

    def _take(self, wanted: set[str] | None):
        if len(self._queue) > 200:
            self._queue = [message for message in self._queue if message.get_type() != "HEARTBEAT"]
        for index, message in enumerate(self._queue):
            if wanted is None or message.get_type() in wanted:
                return self._queue.pop(index)
        return None

    def _pull(self) -> None:
        chunk = self.raw.read(8192)
        if not chunk:
            return
        try:
            parsed = self.mav.parse_buffer(chunk) or []
        except Exception as exc:
            if exc.__class__.__name__ != "MAVError":
                raise
            self.mav.robust_parsing = True
            self.mav.buf = bytearray()
            self.mav.buf_index = 0
            try:
                parsed = self.mav.parse_buffer(chunk) or []
            except Exception as again:
                if again.__class__.__name__ != "MAVError":
                    raise
                return
        for message in parsed:
            if message.get_type() != "BAD_DATA":
                self._queue.append(message)

    def close(self) -> None:
        return None


def read_mavlink_parameters(connection) -> tuple[list[dict], str]:
    """PARAM_REQUEST_LIST only. No parameter is written back."""
    from .ardupilot_read import gcs_heartbeat

    gcs_heartbeat(connection)
    rows, expected, silent = _collect_param_rows(connection)
    if silent and not rows:
        gcs_heartbeat(connection)
        rows, expected, silent = _collect_param_rows(connection)
    _fill_missing_parameters(connection, rows, expected)
    got = {
        int(row["param_index"])
        for row in rows
        if row.get("name") == "PARAM_VALUE" and int(row.get("param_index", -1)) >= 0
    }
    if not rows or (expected is not None and len(got) < expected):
        return rows, "список PARAM_VALUE оборвался: тишина 3 секунды"
    return rows, ""


def _collect_param_rows(connection) -> tuple[list[dict], int | None, bool]:
    connection.mav.param_request_list_send(connection.target_system, connection.target_component)
    rows: list[dict] = []
    expected: int | None = None
    while True:
        message = connection.recv_match(type="PARAM_VALUE", blocking=True, timeout=3)
        if message is None:
            return rows, expected, True
        rows.append(_param_row(message))
        expected = int(message.param_count)
        if int(message.param_index) >= 0 and int(message.param_index) + 1 >= int(message.param_count):
            return rows, expected, False


def _param_row(message) -> dict:
    return {
        "name": "PARAM_VALUE",
        "param_id": message.param_id,
        "param_value": message.param_value,
        "param_index": int(message.param_index),
        "param_count": int(message.param_count),
    }


def _fill_missing_parameters(connection, rows: list[dict], expected: int | None) -> None:
    """PARAM_REQUEST_READ for indexes the list skipped. This does not write a value."""
    send = getattr(getattr(connection, "mav", None), "param_request_read_send", None)
    if send is None or not expected:
        return
    have = {
        int(row["param_index"])
        for row in rows
        if row.get("name") == "PARAM_VALUE" and int(row.get("param_index", -1)) >= 0
    }
    for index in range(int(expected)):
        if index in have:
            continue
        send(connection.target_system, connection.target_component, b"\x00" * 16, index)
        message = connection.recv_match(type="PARAM_VALUE", blocking=True, timeout=1)
        if message is None:
            return
        rows.append(_param_row(message))
        have.add(int(message.param_index))


def read_usb(path: str, port_opener=None, mavlink_opener=None, log_dir=None, wants: dict | None = None) -> "Inputs":
    """Identify the board the way the Configurator opens a port, then read it.

    Betaflight Configurator sends MSP_API_VERSION and then MSP_FC_VARIANT and
    stops unless the answer is BTFL. Strela keeps INAV and Cleanflight. An
    ArduPilot board is read with AUTOPILOT_VERSION, PARAM_REQUEST_LIST and,
    when a folder is given, the newest dataflash log. Nothing is written back.
    """
    from pathlib import Path

    from .ardupilot_read import drain, read_dataflash, request_autopilot_version, version_row
    from .assemble import Inputs

    if port_opener is not None:
        port = port_opener(path)
        dump_text, boxes, identity = collect_flight_controller(port, wants=wants)
        return Inputs(dump_text=dump_text, boxnames=boxes, msp_identity=identity)
    port = open_betaflight_port(path)
    try:
        kind, beat = _classify(port)
        if kind == "mavlink":
            link = SerialMavlink(port.raw, beat) if mavlink_opener is None else mavlink_opener(path)
            chosen = wants or {"params": True, "bin": True}
            try:
                rows: list[dict] = []
                note = ""
                log_rows: list[dict] = []
                log_path = None
                log_note = ""
                if chosen.get("params", True) or chosen.get("msp", True):
                    request_autopilot_version(link)
                    rows, note = read_mavlink_parameters(link)
                    for message in drain(link, ("AUTOPILOT_VERSION", "STATUSTEXT")):
                        if message.get_type() == "AUTOPILOT_VERSION":
                            rows.append(version_row(message))
                        else:
                            text = message.text
                            if isinstance(text, bytes):
                                text = text.decode("latin1", errors="replace")
                            rows.append({"name": "STATUSTEXT", "text": str(text).rstrip("\x00").strip()})
                if chosen.get("bin", True):
                    folder = Path(log_dir) if log_dir else None
                    log_rows, log_path, log_note = read_dataflash(link, folder)
            finally:
                close = getattr(link, "close", None)
                if close is not None:
                    close()
            rows.extend(log_rows)
            if beat:
                rows.insert(0, {"name": "HEARTBEAT", **beat})
            notes = " ".join(part for part in (note, log_note) if part)
            return Inputs(mavlink_rows=rows, read_note=notes, bin_path=log_path)
        if kind in {"betaflight", "inav", "cleanflight"}:
            leave, note = cli_leave(kind)
            dump_text, boxes, identity = collect_flight_controller(port, leave_cli=leave, wants=wants)
            return Inputs(dump_text=dump_text, boxnames=boxes, read_note=note, msp_identity=identity)
    finally:
        port.raw.close()
    raise ValueError("порт не назвал Betaflight, INAV, Cleanflight и не прислал HEARTBEAT")


def _classify(port: QuietPort) -> tuple[str, dict | None]:
    import time

    heard = port.listen(2.5)
    beat = mavlink_heartbeat(heard)
    if beat is not None:
        return "mavlink", beat
    deadline = time.monotonic() + 4.0
    while time.monotonic() < deadline:
        port.write(msp_request(MSP_API_VERSION))
        api = port.read()
        beat = mavlink_heartbeat(api)
        if beat is not None:
            return "mavlink", beat
        port.write(msp_request(MSP_FC_VARIANT))
        reply = port.read()
        beat = mavlink_heartbeat(reply)
        if beat is not None:
            return "mavlink", beat
        variant = msp_variant_name(reply)
        if variant is not None:
            return variant, None
    # A board left in the CLI stays silent for MSP. `version` is a read.
    port.write(b"version\n")
    kind = family_in_text(port.read().decode("latin1", errors="replace"))
    if kind is not None:
        return kind, None
    return "unknown", None


def family_in_text(text: str) -> str | None:
    lowered = text.lower()
    if "betaflight" in lowered:
        return "betaflight"
    if "cleanflight" in lowered:
        return "cleanflight"
    if "inav" in lowered:
        return "inav"
    return None


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
    start = 0
    while True:
        index = frame.find(b"$M>", start)
        if index < 0 or index + 6 > len(frame):
            raise ValueError("порт не вернул MSP-ответ")
        size = frame[index + 3]
        if frame[index + 4] != code or index + 6 + size > len(frame):
            start = index + 1
            continue
        payload = frame[index + 5:index + 5 + size]
        checksum = size ^ code
        for byte in payload:
            checksum ^= byte
        if frame[index + 5 + size] != checksum:
            start = index + 1
            continue
        return payload
