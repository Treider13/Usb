"""Подбор binding phrase при сборке карточки."""

from __future__ import annotations

from pathlib import Path

from .elrs_binding import parse_uid_field
from .elrs_rainbow import crack_binding_phrase, crack_binding_phrase_from_store, load_memory_table
from .model import Card, confirmed, missing


def try_binding_phrase_crack(
    card: Card,
    *,
    binding_wordlist: Path | None,
    binding_memory_table: Path | None,
) -> None:
    if binding_wordlist is None and binding_memory_table is None:
        return
    uid_field = card.fields.get("radio_uid")
    if uid_field is None or uid_field.status != "confirmed":
        card.put(
            "radio_binding_phrase_crack",
            missing("в карточке нет подтверждённого radio_uid", "binding crack"),
        )
        return
    try:
        uid = parse_uid_field(str(uid_field.value))
    except ValueError as exc:
        card.put("radio_binding_phrase_crack", missing(str(exc), "binding crack"))
        return

    phrase: str | None = None
    source = ""
    if binding_memory_table is not None:
        store = load_memory_table(binding_memory_table)
        phrase = crack_binding_phrase_from_store(uid, store)
        source = binding_memory_table.name
    elif binding_wordlist is not None:
        phrase = crack_binding_phrase(uid, binding_wordlist)
        source = binding_wordlist.name

    if phrase:
        card.put(
            "radio_binding_phrase_crack",
            confirmed(
                "найдена",
                "binding crack",
                f"словарь {source}; текст фразы в карточку не сохраняется",
            ),
        )
        return
    card.put(
        "radio_binding_phrase_crack",
        missing(f"в {source} нет фразы для этого UID", "binding crack"),
    )