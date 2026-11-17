"""Distance on the WGS84 sphere. Used only after a GPS track exists."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt


_EARTH_M = 6378137.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_r, lon1_r = radians(lat1), radians(lon1)
    lat2_r, lon2_r = radians(lat2), radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    return 2 * _EARTH_M * asin(sqrt(a))


def path_length_m(points: list[dict]) -> float:
    total = 0.0
    for left, right in zip(points, points[1:]):
        total += haversine_m(left["lat"], left["lon"], right["lat"], right["lon"])
    return total
