"""Build a DataFlash file the same way pymavlink packs one, then read it back."""

from __future__ import annotations

import struct
from pathlib import Path

from pymavlink.DFReader import DFFormat


def _fmt_body(type_id: int, name: str, fmt: str, columns: str) -> bytes:
    described = DFFormat(type_id, name, 0, fmt, columns)
    length = struct.calcsize(described.msg_struct) + 3
    payload = struct.pack(
        "<BB4s16s64s",
        type_id,
        length,
        name.encode("ascii").ljust(4, b"\0")[:4],
        fmt.encode("ascii").ljust(16, b"\0")[:16],
        columns.encode("ascii").ljust(64, b"\0")[:64],
    )
    return struct.pack("<BBB", 0xA3, 0x95, 0x80) + payload


def _msg(type_id: int, fmt: str, values: tuple) -> bytes:
    described = DFFormat(type_id, "X", 0, fmt, ",".join("c" for _ in values))
    return struct.pack("<BBB", 0xA3, 0x95, type_id) + struct.pack(described.msg_struct, *values)


def write_bin(path: Path, messages: list[tuple[str, str, str, tuple]]) -> None:
    """messages: (name, fmt, columns, values). Type ids are assigned from 1."""
    blob = bytearray()
    catalog: dict[str, tuple[int, str]] = {}
    next_id = 1
    for name, fmt, columns, values in messages:
        if name not in catalog:
            catalog[name] = (next_id, fmt)
            blob += _fmt_body(next_id, name, fmt, columns)
            next_id += 1
        type_id, known = catalog[name]
        if known != fmt:
            raise ValueError(name)
        blob += _msg(type_id, fmt, values)
    path.write_bytes(blob)
