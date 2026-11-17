"""Mission files. A GPX track is recorded in the journal and does not
become the flight track. Waypoints do.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


# src/main/fc/cli.c prints: wp %u %u %d %d %d %d %d %d %u
# index, action, lat, lon, alt, p1, p2, p3, flag.
# lat and lon are degrees × 1e7. alt is centimetres. action 0 is an empty slot.
_WP_LINE = re.compile(
    r"^wp\s+(\d+)\s+(\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s*$"
)
_WP_HEADER = re.compile(r"^#wp\s+(\d+)\s+(in)?valid\s*$", re.IGNORECASE)

# navigation.h navWaypointActions_e. There is no action 2 in that enum.
_WP_ACTION = {
    1: "WAYPOINT",
    3: "HOLD_TIME",
    4: "RTH",
    5: "SET_POI",
    6: "JUMP",
    7: "SET_HEAD",
    8: "LAND",
}
_WP_FLAG = {
    0x48: "HOME",
    0xA5: "LAST",
}


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def parse_gpx(path: Path) -> dict[str, list[dict[str, float]]]:
    root = ET.parse(path).getroot()
    tracks: list[dict[str, float]] = []
    waypoints: list[dict[str, float]] = []
    for node in root.iter():
        name = _local(node.tag)
        if name not in ("trkpt", "rtept", "wpt"):
            continue
        lat = node.attrib.get("lat")
        lon = node.attrib.get("lon")
        if lat is None or lon is None:
            continue
        point = {"lat": float(lat), "lon": float(lon)}
        for child in list(node):
            if _local(child.tag) == "ele" and child.text:
                point["alt"] = float(child.text)
        if name == "trkpt":
            tracks.append(point)
        else:
            waypoints.append(point)
    return {"track_points_not_used": tracks, "waypoints": waypoints}


def parse_inav_wp(text: str) -> tuple[list[dict], str]:
    """Read the text INAV prints for the bare command `wp`.

    `wp load`, `wp save` and `wp reset` are not accepted here: those words
    change the board, and this function only sees text that was already printed.
    """
    count = None
    valid = None
    points: list[dict] = []
    for raw in text.splitlines():
        line = raw.strip()
        header = _WP_HEADER.match(line)
        if header:
            count = int(header.group(1))
            valid = header.group(2) is None
            continue
        matched = _WP_LINE.match(line)
        if matched is None:
            continue
        index, action, lat, lon, alt, p1, p2, p3, flag = (int(part) for part in matched.groups())
        if action == 0:
            continue
        points.append(
            {
                "index": index,
                "action": action,
                "action_name": _WP_ACTION.get(action, f"action {action}"),
                "lat": lat / 1e7,
                "lon": lon / 1e7,
                "alt_cm": alt,
                "p1": p1,
                "p2": p2,
                "p3": p3,
                "flag": flag,
                "flag_name": _WP_FLAG.get(flag, f"flag {flag}"),
            }
        )
    if valid is False:
        note = "INAV напечатал #wp invalid. Точки ниже разобраны, список на плате сам себя не подтвердил."
    elif count is not None:
        note = f"INAV напечатал #wp {count} valid. Пустые слоты с действием 0 не попали в список."
    elif points:
        note = "Строки wp разобраны. Строки #wp в тексте не было."
    else:
        note = "В тексте wp нет строки с действием. Точки не выдуманы."
    return points, note


def parse_qgc_waypoints(path: Path) -> list[dict[str, float]]:
    """QGroundControl WPL 110. Columns are tab-separated."""
    points: list[dict[str, float]] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("QGC"):
            continue
        parts = line.split()
        if len(parts) < 11:
            continue
        points.append(
            {
                "seq": float(parts[0]),
                "command": float(parts[3]),
                "lat": float(parts[8]),
                "lon": float(parts[9]),
                "alt": float(parts[10]),
            }
        )
    return points


def parse_plan(path: Path) -> list[dict[str, float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("mission", {}).get("items", [])
    points: list[dict[str, float]] = []
    for item in items:
        params = item.get("params") or []
        if len(params) < 7:
            continue
        lat, lon, alt = params[4], params[5], params[6]
        if lat is None or lon is None:
            continue
        points.append(
            {
                "seq": float(item.get("doJumpId") or len(points)),
                "command": float(item.get("command") or 0),
                "lat": float(lat),
                "lon": float(lon),
                "alt": float(alt),
            }
        )
    return points
