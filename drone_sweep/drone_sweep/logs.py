"""ArduPilot DataFlash via pymavlink.DFReader.

Message names are the ones inside a .BIN: GPS, GPS2, POS, ORGN, PARM,
MSG, MODE, RCIN, BARO, CTUN, EV, CMD, BAT. GPS_RAW_INT is not a DataFlash
name; that message lives in a .tlog.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .enums_ardupilot import LOG_ERROR_SUBSYSTEM, LOG_EVENT


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


def _whole(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value == int(value):
        return int(value)
    text = str(value).strip()
    if text.lstrip("-").isdigit():
        return int(text)
    return None


def flight_timeline(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Arm, land, failsafe and the other LogEvent / ERR lines already in the .BIN.

    Names come from AP_Logger.h. An id that is not in that enum stays a number.
    A MSG line is kept only when it says Failsafe: the arm itself is the EV row.
    """
    events: list[dict[str, Any]] = []
    for row in rows:
        kind = row.get("name")
        when = row.get("TimeUS")
        if kind == "EV":
            ident = _whole(row.get("Id", row.get("id")))
            if ident is None:
                continue
            events.append(
                {
                    "time_us": when,
                    "kind": "EV",
                    "id": ident,
                    "name": LOG_EVENT.get(ident, f"EV {ident}"),
                }
            )
        elif kind == "ERR":
            subsystem = _whole(row.get("Subsys"))
            code = _whole(row.get("ECode"))
            name = LOG_ERROR_SUBSYSTEM.get(subsystem, f"ERR {subsystem}")
            events.append(
                {
                    "time_us": when,
                    "kind": "ERR",
                    "id": subsystem,
                    "code": code,
                    "name": name,
                }
            )
        elif kind == "MSG" and "failsafe" in str(row.get("Message") or "").lower():
            text = str(row.get("Message")).replace("\x00", "").strip()
            events.append(
                {
                    "time_us": when,
                    "kind": "MSG",
                    "name": text,
                }
            )
    return events
