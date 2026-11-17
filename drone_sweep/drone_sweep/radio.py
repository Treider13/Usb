"""Receiver page or flash image. The dictionary follows the firmware string."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .dump_elrs import extract_json_objects, uid_list_to_field
from .redact import redact_json, redact_text_blob, _secret_name


_FIRMWARES = ("MILELRS", "ExpressLRS", "mLRS")


@dataclass
class RadioReading:
    firmware: str | None
    fields: dict[str, str] = field(default_factory=dict)
    removed_secrets: list[str] = field(default_factory=list)
    redacted: bytes = b""


def _firmware_of(text: str) -> str | None:
    # MILELRS contains the letters LRS but must win over ExpressLRS and mLRS.
    if re.search(r"MILELRS", text, re.IGNORECASE):
        return "MILELRS"
    if re.search(r"ExpressLRS", text, re.IGNORECASE):
        return "ExpressLRS"
    if re.search(r"\bmLRS\b", text):
        return "mLRS"
    return None


def _flatten(node: Any, prefix: str = "") -> dict[str, str]:
    found: dict[str, str] = {}
    if isinstance(node, dict):
        for key, value in node.items():
            name = str(key).strip()
            child = f"{prefix}.{name}" if prefix else name
            if isinstance(value, (dict, list)):
                found.update(_flatten(value, child))
            elif value is not None:
                text = str(value)
                full = child.lower().replace("-", "_")
                found[full] = text
                found.setdefault(name.lower().replace("-", "_"), text)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.update(_flatten(value, f"{prefix}[{index}]"))
    return found


def parse_radio_json(payload: Any) -> RadioReading:
    clean, removed = redact_json(payload)
    flat = _flatten(clean)
    blob = json.dumps(clean, ensure_ascii=False).encode("utf-8")
    firmware = _firmware_of(json.dumps(payload, ensure_ascii=False))
    kept = {key: value for key, value in flat.items() if not _secret_name(key.split(".")[-1])}
    return RadioReading(firmware, kept, removed, blob)


def parse_radio_image(blob: bytes) -> RadioReading:
    redacted, removed = redact_text_blob(blob)
    text = redacted.decode("latin1", errors="replace")
    if _mlrs_cli(text):
        return _parse_mlrs_cli(text, redacted, removed)
    firmware = None
    for name in _FIRMWARES:
        if name == "mLRS":
            if re.search(r"\bmLRS\b", text):
                firmware = "mLRS"
                break
            continue
        if re.search(name, text, re.IGNORECASE):
            firmware = "MILELRS" if name == "MILELRS" else "ExpressLRS"
            break
    fields: dict[str, str] = {}
    for match in re.finditer(r"(?im)^([A-Za-z0-9_\-]{2,40})\s*[:=]\s*(\S.*?)\s*$", text):
        key = match.group(1).lower().replace("-", "_")
        value = match.group(2).strip()
        if _secret_name(key) or value == "[removed]":
            continue
        fields[key] = value
    version = re.search(r"MILELRS_v\d+|ExpressLRS[^\s\"]{0,40}|\bmLRS[^\s\"]{0,20}", text)
    if version and "version" not in fields:
        fields["version"] = version.group(0)
    _merge_elrs_json_from_blob(blob, fields, removed)
    if firmware is None and fields.get("uid"):
        firmware = "ExpressLRS"
    return RadioReading(firmware, fields, removed, redacted)


def _merge_elrs_json_from_blob(blob: bytes, fields: dict[str, str], removed: list[str]) -> None:
    for entry in extract_json_objects(blob):
        uid_text = uid_list_to_field(entry.get("uid"))
        if uid_text and "uid" not in fields:
            fields["uid"] = uid_text
        if entry.get("wifi_ssid") and "wifi_ssid" not in fields:
            fields["wifi_ssid"] = str(entry["wifi_ssid"])
        if entry.get("wifi_password"):
            removed.append("wifi-password")


_MLRS_PARAM = re.compile(r"^  (.+?) = (.*)$")
_MLRS_TX = re.compile(r"^  Tx: (.+)$")
_MLRS_RX = re.compile(r"^  Rx: (.+)$")


def _mlrs_cli(text: str) -> bool:
    """The print format of tTxCli in olliw42/mLRS CommonTx/cli.h."""
    if re.search(r"MILELRS", text, re.IGNORECASE):
        return False
    if re.search(r"(?m)^ConfigId:\s*$", text):
        return True
    return bool(re.search(r"(?m)^  Tx: ", text) and re.search(r"(?m)^  .+ = ", text))


def _parse_mlrs_cli(text: str, redacted: bytes, removed: list[str]) -> RadioReading:
    fields: dict[str, str] = {}
    for raw in text.splitlines():
        tx = _MLRS_TX.match(raw)
        if tx:
            fields["tx"] = tx.group(1).strip()
            continue
        rx = _MLRS_RX.match(raw)
        if rx:
            fields["rx"] = rx.group(1).strip()
            continue
        param = _MLRS_PARAM.match(raw)
        if not param:
            continue
        name = param.group(1).strip().lower().replace(" ", "_")
        value = param.group(2).strip()
        if _secret_name(name):
            removed.append(name)
            continue
        fields[name] = value
    if "version" not in fields and fields.get("tx"):
        fields["version"] = fields["tx"]
    return RadioReading("mLRS", fields, removed, redacted)
