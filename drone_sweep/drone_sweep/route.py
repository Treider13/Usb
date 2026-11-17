"""Flight track rules.

A point enters the track only from GPS/GPS2 with Status >= 3, from a
.tlog GPS_RAW_INT with fix_type >= 3, or from a Blackbox GPS CSV.
POS, ORGN type 0, the first fix before arming, a parameter named HOME,
OSD and a GPX <trk> do not.
"""

from __future__ import annotations

from typing import Any

from .enums_ardupilot import EV_ARMED, EV_DISARMED, GPS_FIX_3D, ORGN_HOME
from .geo import haversine_m, path_length_m


_ARM_WINDOW_US = 1_000_000


def _num(row: dict[str, Any], *names: str) -> float | None:
    for name in names:
        if name in row and row[name] is not None and row[name] != "":
            return float(row[name])
    return None


def bin_gps_points(rows: list[dict[str, Any]]) -> tuple[list[dict], int, int]:
    """Return 3D points, count of GPS rows, count of rows below 3D."""
    points: list[dict] = []
    seen = 0
    weak = 0
    for row in rows:
        if row.get("name") not in ("GPS", "GPS2"):
            continue
        seen += 1
        status = int(_num(row, "Status") or 0)
        lat = _num(row, "Lat")
        lon = _num(row, "Lng")
        if lat is None or lon is None:
            weak += 1
            continue
        if status < GPS_FIX_3D:
            weak += 1
            continue
        points.append(
            {
                "time_us": _num(row, "TimeUS") or 0.0,
                "lat": lat,
                "lon": lon,
                "alt": _num(row, "Alt"),
                "status": status,
                "source": "bin",
            }
        )
    return points, seen, weak


def bin_pos_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("name") == "POS")


def home_from_orgn(rows: list[dict[str, Any]]) -> dict | None:
    for row in rows:
        if row.get("name") != "ORGN":
            continue
        if int(_num(row, "Type") or -1) != ORGN_HOME:
            continue
        lat = _num(row, "Lat")
        lon = _num(row, "Lng")
        if lat is None or lon is None:
            continue
        return {
            "lat": lat,
            "lon": lon,
            "alt": _num(row, "Alt"),
            "time_us": _num(row, "TimeUS"),
            "source": "bin ORGN type 1",
        }
    return None


def arm_pairs(rows: list[dict[str, Any]]) -> list[tuple[float, float | None]]:
    pairs: list[tuple[float, float | None]] = []
    open_arm: float | None = None
    events = [row for row in rows if row.get("name") == "EV"]
    events.sort(key=lambda row: _num(row, "TimeUS") or 0.0)
    for row in events:
        code = int(_num(row, "Id") or -1)
        stamp = _num(row, "TimeUS") or 0.0
        if code == EV_ARMED:
            open_arm = stamp
        elif code == EV_DISARMED and open_arm is not None:
            pairs.append((open_arm, stamp))
            open_arm = None
    if open_arm is not None:
        pairs.append((open_arm, None))
    if pairs:
        return pairs
    # ARM message, used when the log has no EV arm/disarm pair.
    for row in rows:
        if row.get("name") != "ARM":
            continue
        state = int(_num(row, "ArmState") or 0)
        stamp = _num(row, "TimeUS") or 0.0
        if state == 1:
            open_arm = stamp
        elif state == 0 and open_arm is not None:
            pairs.append((open_arm, stamp))
            open_arm = None
    if open_arm is not None:
        pairs.append((open_arm, None))
    return pairs


def tlog_points(rows: list[dict[str, Any]]) -> tuple[list[dict], dict | None, int]:
    points: list[dict] = []
    weak = 0
    home = None
    for row in rows:
        name = row.get("name")
        if name == "GPS_RAW_INT":
            fix = int(_num(row, "fix_type") or 0)
            lat = _num(row, "lat")
            lon = _num(row, "lon")
            if lat is None or lon is None or fix < GPS_FIX_3D:
                weak += 1
                continue
            # MAVLink sends degrees × 1e7 and altitude in millimetres.
            points.append(
                {
                    "time_us": _num(row, "time_usec") or 0.0,
                    "lat": lat / 1e7,
                    "lon": lon / 1e7,
                    "alt": None if _num(row, "alt") is None else _num(row, "alt") / 1000.0,
                    "status": fix,
                    "source": "tlog",
                }
            )
        elif name == "HOME_POSITION" and home is None:
            lat = _num(row, "latitude")
            lon = _num(row, "longitude")
            if lat is not None and lon is not None:
                home = {
                    "lat": lat / 1e7,
                    "lon": lon / 1e7,
                    "alt": None if _num(row, "altitude") is None else _num(row, "altitude") / 1000.0,
                    "source": "tlog HOME_POSITION",
                }
    return points, home, weak


def _in_window(point: dict, start: float, end: float | None) -> bool:
    stamp = point["time_us"]
    if stamp < start:
        return False
    if end is not None and stamp > end:
        return False
    return True


def _nearest_after(points: list[dict], stamp: float) -> dict | None:
    later = [
        point
        for point in points
        if stamp <= point["time_us"] <= stamp + _ARM_WINDOW_US
    ]
    if not later:
        return None
    return min(later, key=lambda point: point["time_us"])


def _nearest_before(points: list[dict], stamp: float) -> dict | None:
    earlier = [
        point
        for point in points
        if stamp - _ARM_WINDOW_US <= point["time_us"] <= stamp
    ]
    if not earlier:
        return None
    return max(earlier, key=lambda point: point["time_us"])


def build_flights(
    bin_points: list[dict],
    pairs: list[tuple[float, float | None]],
    tlog: list[dict],
    blackbox: list[dict],
    home: dict | None,
) -> tuple[list[dict], list[dict[str, str]]]:
    journal: list[dict[str, str]] = []
    if bin_points:
        winner = "bin"
        pool = bin_points
        journal.append({"source": "bin", "result": "found", "detail": f"{len(bin_points)} точек GPS Status>=3"})
        if tlog:
            journal.append({"source": "tlog", "result": "secondary", "detail": "трек есть, в карточку не выбран: старше источник .BIN"})
        if blackbox:
            journal.append({"source": "blackbox", "result": "secondary", "detail": "CSV есть, в карточку не выбран: старше источник .BIN"})
    elif tlog:
        winner = "tlog"
        pool = tlog
        journal.append({"source": "bin", "result": "absent", "detail": "точек GPS Status>=3 нет"})
        journal.append({"source": "tlog", "result": "found", "detail": f"{len(tlog)} точек GPS_RAW_INT fix_type>=3"})
    elif blackbox:
        winner = "blackbox"
        pool = [
            {
                "time_us": point.get("time_us", 0.0),
                "lat": point["lat"],
                "lon": point["lon"],
                "alt": point.get("alt"),
                "status": GPS_FIX_3D,
                "source": "blackbox",
            }
            for point in blackbox
        ]
        journal.append({"source": "bin", "result": "absent", "detail": "точек GPS Status>=3 нет"})
        journal.append({"source": "tlog", "result": "absent", "detail": ".tlog не дал точек"})
        journal.append({"source": "blackbox", "result": "found", "detail": f"{len(pool)} точек GPS CSV"})
    else:
        winner = "none"
        pool = []
        journal.append({"source": "bin", "result": "absent", "detail": "точек GPS Status>=3 нет"})
        journal.append({"source": "tlog", "result": "absent", "detail": ".tlog не дал точек"})
        journal.append({"source": "blackbox", "result": "absent", "detail": "кадров GPS нет"})

    # Arm events share the DataFlash clock. A .tlog or a Blackbox CSV does not,
    # so those tracks stay one flight and are not pinned to the arm timestamp.
    use_pairs = bool(pairs) and winner in ("bin", "none")
    intervals = pairs if use_pairs else []

    flights: list[dict] = []
    if intervals:
        for index, (start, end) in enumerate(intervals):
            track = [point for point in pool if _in_window(point, start, end)]
            if not track and pool:
                journal.append(
                    {
                        "source": "bin",
                        "result": "outside_arm",
                        "detail": f"вылет {index}: GPS есть, но не внутри интервала арминга",
                    }
                )
            flights.append(_flight(index, track, "bin" if track else "none", home, start, end))
    else:
        flight = _flight(0, pool, winner if pool else "none", home, None, None)
        if len(pairs) == 1 and winner != "bin":
            # The arm clock belongs to the .BIN. It is shown as a time and
            # is not used to pick a coordinate out of another file.
            flight["arm_time_us"] = pairs[0][0]
            flight["disarm_time_us"] = pairs[0][1]
            journal.append(
                {
                    "source": "bin_arm",
                    "result": "not_joined",
                    "detail": "время арминга из .BIN не склеивается с координатами другого файла",
                }
            )
        flights.append(flight)
    return flights, journal


def _flight(
    index: int,
    track: list[dict],
    source: str,
    home: dict | None,
    arm: float | None,
    disarm: float | None,
) -> dict:
    takeoff = None
    landing = None
    if arm is not None:
        takeoff = _nearest_after(track, arm)
    if disarm is not None:
        landing = _nearest_before(track, disarm)
    length = path_length_m(track) if len(track) >= 2 else None
    distance = None
    if home is not None and track:
        distance = max(
            haversine_m(home["lat"], home["lon"], point["lat"], point["lon"])
            for point in track
        )
    return {
        "index": index,
        "route_source": source if track else "none",
        "arm_time_us": arm,
        "disarm_time_us": disarm,
        "takeoff": takeoff,
        "landing": landing,
        "track": track,
        "route_length_m": length,
        "max_distance_from_home_m": distance,
        "home": home,
    }
