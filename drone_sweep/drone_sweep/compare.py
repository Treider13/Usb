"""Difference of two cards. Only confirmed and document cells are compared.

A missing cell is not a value, so two holes do not become a difference.
A parameter table is compared key by key. Nothing is written back to a board.
"""

from __future__ import annotations

import json
from typing import Any


_SHOWN = {"confirmed", "document"}


def diff_cards(left: dict[str, Any], right: dict[str, Any]) -> list[dict[str, Any]]:
    left_fields = left.get("fields") or {}
    right_fields = right.get("fields") or {}
    changes: list[dict[str, Any]] = []
    for name in sorted(set(left_fields) | set(right_fields)):
        changes.extend(_field(name, left_fields.get(name), right_fields.get(name)))
    return changes


def _field(name: str, left: dict | None, right: dict | None) -> list[dict[str, Any]]:
    if not _shown(left) and not _shown(right):
        return []
    left_value = None if left is None else left.get("value")
    right_value = None if right is None else right.get("value")
    if _same(left, right):
        return []
    if _leaf_dict(left_value) and _leaf_dict(right_value):
        rows = []
        for key in sorted(set(left_value) | set(right_value), key=str):
            if left_value.get(key) != right_value.get(key):
                rows.append(_row(f"{name}.{key}", left, right, left_value.get(key), right_value.get(key)))
        return rows
    return [_row(name, left, right, left_value, right_value)]


def _shown(item: dict | None) -> bool:
    return bool(item) and item.get("status") in _SHOWN


def _same(left: dict | None, right: dict | None) -> bool:
    if not _shown(left) or not _shown(right):
        return False
    return left.get("status") == right.get("status") and left.get("value") == right.get("value")


def _leaf_dict(value: Any) -> bool:
    return isinstance(value, dict) and all(not isinstance(item, (dict, list)) for item in value.values())


def _row(name: str, left: dict | None, right: dict | None, left_value: Any, right_value: Any) -> dict[str, Any]:
    return {
        "field": name,
        "left_status": None if left is None else left.get("status"),
        "left": left_value if _shown(left) else None,
        "right_status": None if right is None else right.get("status"),
        "right": right_value if _shown(right) else None,
    }


def render_diff(changes: list[dict[str, Any]]) -> str:
    if not changes:
        return "Отличий в подтверждённых полях нет."
    lines = [f"Отличий: {len(changes)}"]
    for change in changes:
        lines.append(
            f"{change['field']}: {_text(change['left'])} → {_text(change['right'])}"
        )
    return "\n".join(lines)


def _text(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and value == int(value) and abs(value) < 1_000_000_000:
            return str(int(value))
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
