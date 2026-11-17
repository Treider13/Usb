"""ArduPilot DataFlash via pymavlink.DFReader.

Message names are the ones inside a .BIN: GPS, GPS2, POS, ORGN, PARM,
MSG, MODE, RCIN, BARO, CTUN, EV, CMD, BAT. GPS_RAW_INT is not a DataFlash
name; that message lives in a .tlog.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_bin(path: Path) -> list[dict[str, Any]]:
    try:
        from pymavlink import DFReader
    except ImportError as exc:
        raise RuntimeError(
            "pymavlink не установлен. Разбор .BIN без DFReader не запускается."
        ) from exc
    reader = DFReader.DFReader_binary(str(path))
    rows: list[dict[str, Any]] = []
    while True:
        message = reader.recv_msg()
        if message is None:
            break
        if message.get_type() == "FMT":
            continue
        row = message.to_dict()
        row["name"] = message.get_type()
        rows.append(row)
    return rows


def load_tlog(path: Path) -> list[dict[str, Any]]:
    """MAVLink telemetry log. GPS_RAW_INT and HOME_POSITION live here."""
    try:
        from pymavlink import mavutil
    except ImportError as exc:
        raise RuntimeError("pymavlink не установлен, .tlog не прочитан.") from exc
    connection = mavutil.mavlink_connection(str(path))
    rows: list[dict[str, Any]] = []
    while True:
        message = connection.recv_match(blocking=False)
        if message is None:
            break
        kind = message.get_type()
        if kind == "BAD_DATA":
            continue
        row = message.to_dict()
        row["name"] = kind
        rows.append(row)
    return rows
