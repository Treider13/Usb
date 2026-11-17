"""Подбор binding phrase при сборке карточки (CIRCL rainbow, протоколы LRS)."""

from __future__ import annotations

from pathlib import Path

from .elrs_binding import parse_uid_field
from .elrs_rainbow import crack_binding_phrase, crack_binding_phrase_from_store, load_memory_table
from .model import Card, confirmed, missing, not_applicable

# CIRCL elrs/ — тот же MD5 UID; в проекте ещё текстовый дамп MILELRS.
BINDING_UID_PROTOCOLS = frozenset({"ExpressLRS", "MILELRS"})


def binding_crack_supported(card: Card) -> str | None:
    protocol = card.fields.get("radio_protocol")
    if protocol is None or protocol.status != "confirmed":
        return None
    value = str(protocol.value)
    if value in BINDING_UID_PROTOCOLS:
        return value
    if value == "mLRS":
        return "mLRS"
    return value


def try_binding_phrase_crack(
    card: Card,
    *,
    binding_wordlist: Path | None,
    binding_memory_table: Path | None,
) -> None:
    if binding_wordlist is None and binding_memory_table is None:
        return

    protocol = binding_crack_supported(card)
    if protocol not in BINDING_UID_PROTOCOLS:
        card.put(
            "radio_binding_phrase_crack",
            not_applicable(
                f"подбор UID по фразе только для ExpressLRS/MILELRS; "
                f"у OrangeRX — DSM (SPEKTRUM), у {protocol or 'неизвестного приёмника'} — свой механизм",
                "binding crack",
            ),
        )
        return

    uid_field = card.fields.get("radio_uid")
    if uid_field is None or uid_field.status != "confirmed":
        card.put(
            "radio_binding_phrase_crack",
            missing(
                f"в карточке нет UID для {protocol}; снимите dump/страницу приёмника или strela elrs dump",
                "binding crack",
            ),
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
                f"{protocol}, словарь {source}; текст фразы в карточку не сохраняется",
            ),
        )
        return
    card.put(
        "radio_binding_phrase_crack",
        missing(f"в {source} нет фразы для UID ({protocol})", "binding crack"),
    )