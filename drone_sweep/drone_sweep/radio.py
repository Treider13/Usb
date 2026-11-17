"""Receiver page or flash image. The dictionary follows the firmware string."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .redact import redact_json, redact_text_blob


_FIRMWARES = ("MILELRS", "ExpressLRS", "mLRS")

# Printed by the MILELRS / ExpressLRS pages we accept into the card.
PUBLIC_KEYS = {
    "version",
    "firmware",
    "model",
    "chip",
    "domain",
    "uid",
    "serial_protocol",
    "uart_baud",
    "rate_index",
    "rateinitialidx",
    "model_id",
    "custom_freq",
    "binding_rate",
    "swarm_id",
    "vx_table",
    "vx_bands",
    "modulation_mode",
}


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
                found[name.lower()] = str(value)
                found[child.lower()] = str(value)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.update(_flatten(value, f"{prefix}[{index}]"))
    return found


def parse_radio_json(payload: Any) -> RadioReading:
    clean, removed = redact_json(payload)
    flat = _flatten(clean)
    blob = json.dumps(clean, ensure_ascii=False).encode("utf-8")
    firmware = _firmware_of(json.dumps(payload, ensure_ascii=False))
    kept = {key: value for key, value in flat.items() if key.split(".")[-1] in PUBLIC_KEYS}
    return RadioReading(firmware, kept, removed, blob)


def parse_radio_image(blob: bytes) -> RadioReading:
    redacted, removed = redact_text_blob(blob)
    text = redacted.decode("latin1", errors="replace")
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
        if key in PUBLIC_KEYS:
            fields[key] = match.group(2).strip()
    version = re.search(r"MILELRS_v\d+|ExpressLRS[^\s\"]{0,40}|\bmLRS[^\s\"]{0,20}", text)
    if version and "version" not in fields:
        fields["version"] = version.group(0)
    return RadioReading(firmware, fields, removed, redacted)
