"""USB session for Betaflight and INAV.

Only read commands are written to the port. `save`, `set`, `defaults`
and MSP codes that write configuration are rejected before they reach
the wire. ArduPilot has no CLI password and no CLI dump; its card is
built from the .BIN file.
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


def open_betaflight_port(path: str) -> QuietPort:
    import serial

    raw = serial.Serial(path, 115200, timeout=0.05)
    return QuietPort(raw)


def _msp_payload(frame: bytes, code: int) -> bytes:
    if len(frame) < 6 or frame[0:3] != b"$M>":
        raise ValueError("порт не вернул MSP-ответ")
    size = frame[3]
    if frame[4] != code:
        raise ValueError(f"ожидался MSP {code}, пришёл {frame[4]}")
    return frame[5:5 + size]
