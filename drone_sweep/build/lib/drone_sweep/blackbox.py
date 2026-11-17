"""Blackbox header lines and the GPS CSV written by blackbox_decode.

Binary G-frames are not reimplemented here. A track from Blackbox is
accepted only from that decoder's GPS CSV (decimal degrees, or the
firmware's degrees×1e7 when the absolute value exceeds 180). Header
fields such as Craft name and rc_smoothing_rx_smoothed are read from
the ASCII `H ` lines of the .bbl/.txt log itself.
"""

from __future__ import annotations

import csv
from pathlib import Path


def parse_header(text: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("H "):
            # Binary logs keep an ASCII header and then stop being text.
            if headers and not line.startswith("H"):
                break
            continue
        body = line[2:]
        if ":" not in body:
            continue
        key, value = body.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def parse_header_file(path: Path) -> dict[str, str]:
    data = path.read_bytes()
    # The header is ASCII. Cut at the first NUL, which starts the frames.
    zero = data.find(b"\x00")
    chunk = data if zero < 0 else data[:zero]
    return parse_header(chunk.decode("latin1", errors="replace"))


def _coordinate(raw: str) -> float | None:
    text = raw.strip()
    if not text:
        return None
    value = float(text)
    if abs(value) > 180:
        return value / 1e7
    return value


def parse_gps_csv(path: Path) -> list[dict[str, float]]:
    """Read blackbox_decode's GPS CSV.

    Required columns: GPS_coord[0] and GPS_coord[1]. GPS_numSat, when
    present, must be at least 6, the same gate blackbox_decode uses
    before it writes a GPX point.
    """
    points: list[dict[str, float]] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        fields = {name.strip(): name for name in reader.fieldnames}
        lat_key = fields.get("GPS_coord[0]")
        lon_key = fields.get("GPS_coord[1]")
        if lat_key is None or lon_key is None:
            raise ValueError("в GPS CSV нет колонок GPS_coord[0] и GPS_coord[1]")
        alt_key = fields.get("GPS_altitude")
        sat_key = fields.get("GPS_numSat")
        time_key = fields.get("time") or fields.get("time (us)")
        for row in reader:
            if sat_key is not None and row.get(sat_key, "").strip():
                if int(float(row[sat_key])) < 6:
                    continue
            lat = _coordinate(row[lat_key])
            lon = _coordinate(row[lon_key])
            if lat is None or lon is None:
                continue
            point: dict[str, float] = {"lat": lat, "lon": lon}
            if alt_key and row.get(alt_key, "").strip():
                point["alt"] = float(row[alt_key])
            if time_key and row.get(time_key, "").strip():
                point["time_us"] = float(row[time_key])
            points.append(point)
    return points
