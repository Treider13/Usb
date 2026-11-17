"""Подбор binding phrase при сборке карточки (CIRCL rainbow, протоколы LRS)."""

from __future__ import annotations

import json
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
        card.put("radio_binding_phrase_crack", not_applicable(_refusal(protocol), "binding crack"))
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

    phrase, source, problem = search_binding_sources(uid, binding_wordlist, binding_memory_table)
    if problem and phrase is None and not source:
        card.put("radio_binding_phrase_crack", missing(problem, "binding crack"))
        return

    if phrase:
        card.put(
            "radio_binding_phrase_crack",
            confirmed(
                "найдена",
                "binding crack",
                f"{protocol}, источник {source}; текст фразы в карточку не сохраняется",
            ),
        )
        return
    card.put(
        "radio_binding_phrase_crack",
        missing(f"в {source} нет фразы для UID ({protocol})", "binding crack"),
    )


def _refusal(protocol: str | None) -> str:
    if protocol in {"SPEKTRUM2048", "SPEKTRUM1024"}:
        return (
            "подбор UID по фразе только для ExpressLRS и MILELRS. "
            f"{protocol} — класс DSM2/DSMX, приёмники OrangeRX входят в него. Формула ELRS к ним не применяется."
        )
    if protocol:
        return (
            "подбор UID по фразе только для ExpressLRS и MILELRS. "
            f"Протокол {protocol} этой формулой не считается."
        )
    return "протокол приёмника не подтверждён. Подбор UID не запускался."


def search_binding_sources(
    uid: list[int],
    binding_wordlist: Path | None,
    binding_memory_table: Path | None,
) -> tuple[str | None, str, str]:
    """Memory table first. A miss falls through to the wordlist when both were given."""
    problems: list[str] = []
    if binding_memory_table is not None:
        if not binding_memory_table.is_file():
            problems.append(f"таблица не найдена: {binding_memory_table}")
        else:
            try:
                store = load_memory_table(binding_memory_table)
                phrase = crack_binding_phrase_from_store(uid, store)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                problems.append(f"таблица не читается: {exc}")
            except Exception as exc:
                problems.append(f"таблица не читается: {exc}")
            else:
                if phrase:
                    return phrase, binding_memory_table.name, ""
                problems.append(f"в {binding_memory_table.name} нет фразы для UID")
    if binding_wordlist is not None:
        if not binding_wordlist.is_file():
            problems.append(f"словарь не найден: {binding_wordlist}")
        else:
            try:
                phrase = crack_binding_phrase(uid, binding_wordlist)
            except (OSError, ValueError) as exc:
                problems.append(f"словарь не читается: {exc}")
                return None, binding_wordlist.name, "; ".join(problems)
            if phrase:
                return phrase, binding_wordlist.name, ""
            problems.append(f"в {binding_wordlist.name} нет фразы для UID")
            return None, binding_wordlist.name, "; ".join(problems)
    return None, "", "; ".join(problems)