"""Card fields. Exactly four statuses. A guess has no status to hide in."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


STATUSES = ("confirmed", "document", "missing", "not_applicable")


@dataclass
class Item:
    """One card cell.

    ``confirmed`` and ``document`` hold a value. ``missing`` and
    ``not_applicable`` hold nothing: the reason says why.
    """

    status: str
    value: Any = None
    reason: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"unknown status {self.status!r}")
        if self.status in ("missing", "not_applicable"):
            self.value = None
        elif self.value is None:
            raise ValueError(f"{self.status} field has no value")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.status in ("missing", "not_applicable"):
            data["value"] = None
        return data


def confirmed(value: Any, source: str, reason: str = "") -> Item:
    return Item("confirmed", value, reason, source)


def document(value: Any, source: str, reason: str = "") -> Item:
    return Item("document", value, reason, source)


def missing(reason: str, source: str = "") -> Item:
    return Item("missing", None, reason, source)


def not_applicable(reason: str, source: str = "") -> Item:
    return Item("not_applicable", None, reason, source)


@dataclass
class Card:
    family: str
    fields: dict[str, Item] = field(default_factory=dict)
    flights: list[dict[str, Any]] = field(default_factory=list)
    journal: list[dict[str, str]] = field(default_factory=list)
    holes: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    files: list[dict[str, str]] = field(default_factory=list)
    raw_banner: str = ""

    def put(self, name: str, item: Item) -> None:
        self.fields[name] = item

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "raw_banner": self.raw_banner,
            "fields": {key: item.to_dict() for key, item in self.fields.items()},
            "flights": self.flights,
            "journal": self.journal,
            "holes": self.holes,
            "hints": self.hints,
            "files": self.files,
        }
