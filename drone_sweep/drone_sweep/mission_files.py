"""Mission files. A GPX track is recorded in the journal and does not
become the flight track. Waypoints do.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


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
