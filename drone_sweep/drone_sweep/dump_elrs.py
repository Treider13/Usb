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


_IHEX_DIGITS = frozenset(b"0123456789abcdefABCDEF")


def is_intel_hex(data: bytes) -> bool:
    stripped = data.lstrip()
    if len(stripped) < 11 or stripped[0:1] != b":":
        return False
    return all(byte in _IHEX_DIGITS for byte in stripped[1:9])


def intel_hex_to_bin(data: bytes) -> bytes:
    payload: dict[int, int] = {}
    base = 0
    saw_eof = False
    for line in data.splitlines():
        line = line.strip()
        if not line or line[0:1] != b":":
            if line:
                raise ValueError(f"Intel HEX record does not start with ':': {line[:16]!r}")
            continue
        try:
            raw = bytes.fromhex(line[1:].decode("ascii"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError(f"Malformed Intel HEX record: {line[:16]!r}") from exc
        if len(raw) < 5:
            raise ValueError(f"Intel HEX record too short: {line!r}")
        length, addr_hi, addr_lo, rtype = raw[0], raw[1], raw[2], raw[3]
        record_data = raw[4 : 4 + length]
        checksum = raw[4 + length]
        if len(record_data) != length:
            raise ValueError(f"Intel HEX length mismatch: {line!r}")
        if (sum(raw[: 4 + length]) + checksum) & 0xFF != 0:
            raise ValueError(f"Intel HEX checksum error: {line!r}")
        addr = (addr_hi << 8) | addr_lo
        if rtype == 0x00:
            absolute = base + addr
            for index, byte in enumerate(record_data):
                payload[absolute + index] = byte
        elif rtype == 0x01:
            saw_eof = True
            break
        elif rtype == 0x02:
            if length != 2:
                raise ValueError(f"Intel HEX type 02 length must be 2: {line!r}")
            base = ((record_data[0] << 8) | record_data[1]) << 4
        elif rtype == 0x04:
            if length != 2:
                raise ValueError(f"Intel HEX type 04 length must be 2: {line!r}")
            base = ((record_data[0] << 8) | record_data[1]) << 16
    if not payload:
        return b""
    if not saw_eof:
        raise ValueError("Intel HEX missing EOF record")
    lo, hi = min(payload), max(payload)
    return bytes(payload.get(address, 0xFF) for address in range(lo, hi + 1))


def payload_for_scan(file_bytes: bytes) -> tuple[bytes, str]:
    """Бинарник для extract_json_objects (CIRCL drone_to_misp.extract_elrs)."""
    if is_intel_hex(file_bytes):
        try:
            return intel_hex_to_bin(file_bytes), "intel_hex"
        except ValueError:
            return file_bytes, "raw"
    return file_bytes, "raw"


def public_extraction_summary(file_bytes: bytes) -> dict[str, Any]:
    """Как CIRCL extract_elrs, но без wifi-password в ответе."""
    scan_bytes, fmt = payload_for_scan(file_bytes)
    md5_hash, sha256_hash = compute_hashes(file_bytes)
    entries = extract_json_objects(scan_bytes)
    extracted: list[dict[str, Any]] = []
    for entry in entries:
        item: dict[str, Any] = {}
        uid = uid_list_to_field(entry.get("uid"))
        if uid:
            item["uid"] = uid
        if entry.get("wifi_ssid"):
            item["wifi_ssid"] = entry["wifi_ssid"]
        if entry.get("wifi_password"):
            item["wifi_password_present"] = True
        if item:
            extracted.append(item)
    return {
        "md5": md5_hash,
        "sha256": sha256_hash,
        "format": fmt,
        "fragments": len(entries),
        "extracted": extracted,
    }


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