"""JSON из бинарного дампа ExpressLRS (CIRCL dump_elrs.py).

Источник: CIRCL/Drone-Forensic (AGPL-3.0).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def find_json_end(data: bytes, start: int) -> int | None:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(data)):
        byte = data[index]
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte == 0x7B:
            depth += 1
        elif byte == 0x7D:
            depth -= 1
            if depth == 0:
                return index
            if depth < 0:
                return None
    return None


def decode_candidate(candidate: bytes) -> dict[str, Any] | None:
    try:
        text = candidate.decode("utf-8")
        parsed = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(parsed, dict):
        return None
    uid = parsed.get("uid")
    valid_uid = uid if isinstance(uid, list) else None
    wifi_ssid = parsed.get("wifi-ssid") if isinstance(parsed.get("wifi-ssid"), str) else None
    wifi_password = parsed.get("wifi-password") if isinstance(parsed.get("wifi-password"), str) else None
    rendered = json.dumps(parsed, ensure_ascii=False)
    fragment = rendered[1:-1] if rendered.startswith("{") and rendered.endswith("}") else rendered
    return {
        "fragment": fragment,
        "config": parsed,
        "uid": valid_uid,
        "wifi_ssid": wifi_ssid,
        "wifi_password": wifi_password,
    }


def extract_json_objects(data: bytes) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    index = 0
    while index < len(data):
        if data[index] != 0x7B:
            index += 1
            continue
        end = find_json_end(data, index)
        if end is None:
            index += 1
            continue
        decoded = decode_candidate(data[index : end + 1])
        if decoded is not None:
            results.append(decoded)
            index = end + 1
            continue
        index += 1
    return results


def compute_hashes(data: bytes) -> tuple[str, str]:
    return hashlib.md5(data).hexdigest(), hashlib.sha256(data).hexdigest()


def build_json_payload(
    md5_hash: str,
    sha256_hash: str,
    entries: list[dict[str, Any]],
    *,
    debug: bool = False,
) -> dict[str, Any]:
    extracted: list[dict[str, Any]] = []
    for entry in entries:
        item: dict[str, Any] = {}
        if entry["uid"] is not None:
            item["uid"] = entry["uid"]
        if entry["wifi_ssid"] is not None:
            item["wifi-ssid"] = entry["wifi_ssid"]
        if entry["wifi_password"] is not None:
            item["wifi-password"] = entry["wifi_password"]
        if debug:
            item["config"] = entry["config"]
        if item:
            extracted.append(item)
    return {"md5": md5_hash, "sha256": sha256_hash, "extracted": extracted}


def uid_list_to_field(uid: list) -> str | None:
    if not isinstance(uid, list) or len(uid) != 6:
        return None
    try:
        values = [int(part) for part in uid]
    except (TypeError, ValueError):
        return None
    if not all(0 <= value <= 255 for value in values):
        return None
    return ",".join(str(value) for value in values)