"""Drop secret radio fields before anything is stored."""

from __future__ import annotations

import json
import re
from typing import Any


# Names, not values. Matching is case-insensitive.
SECRET_KEYS = {
    "binding_phrase",
    "bind_phrase",
    "bindphrase",
    "passphrase",
    "wifi_password",
    "wifi_pass",
    "wifi_ssid_password",
    "password",
    "passwd",
    "rx_key",
    "alt_keys",
    "power_key",
    "phrase_hash",
    "binding_phrase_hash",
    "uid_from_phrase",
}

_ASSIGN = re.compile(
    rb"(?im)^([A-Za-z0-9_\-]{2,40})\s*[:=]\s*(\S.{0,200})$"
)


def _secret_name(name: str) -> bool:
    folded = name.strip().lower().replace("-", "_")
    return folded in SECRET_KEYS


def redact_json(payload: Any) -> tuple[Any, list[str]]:
    """Return a copy with secret keys removed. Lists the removed names."""
    removed: list[str] = []

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            kept = {}
            for key, value in node.items():
                if _secret_name(str(key)):
                    removed.append(str(key))
                    continue
                kept[key] = walk(value)
            return kept
        if isinstance(node, list):
            return [walk(item) for item in node]
        return node

    return walk(payload), removed


def redact_text_blob(blob: bytes) -> tuple[bytes, list[str]]:
    """Blank KEY=value lines whose key is secret. The rest of the image stays."""
    removed: list[str] = []
    pieces: list[bytes] = []
    last = 0
    for match in _ASSIGN.finditer(blob):
        key = match.group(1).decode("ascii", errors="ignore")
        if not _secret_name(key):
            continue
        pieces.append(blob[last:match.start(2)])
        pieces.append(b"[removed]")
        last = match.end(2)
        removed.append(key)
    pieces.append(blob[last:])
    return b"".join(pieces), removed


def dumps_public(payload: Any) -> str:
    clean, _removed = redact_json(payload)
    return json.dumps(clean, ensure_ascii=False, sort_keys=True)
