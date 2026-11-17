"""ExpressLRS UID из binding phrase (логика CIRCL elrs_uid.py).

Формула: md5('-DMY_BINDING_PHRASE="{phrase}"')[:6].
Источник: CIRCL/Drone-Forensic (AGPL-3.0).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterator, Sequence


def binding_phrase_to_uid(bind_phrase: str) -> list[int]:
    define = f'-DMY_BINDING_PHRASE="{bind_phrase}"'
    digest = hashlib.md5(define.encode("utf-8")).digest()
    return list(digest[:6])


def binding_phrase_uid_hex(bind_phrase: str) -> str:
    return uid_bytes_to_hex(binding_phrase_to_uid(bind_phrase))


def uid_bytes_to_hex(uid_bytes: Sequence[int]) -> str:
    return "".join(f"{byte:02X}" for byte in uid_bytes)


def parse_uid_bytes(text: str) -> list[int]:
    """Шесть байт: '79,4,253' или '79, 4, 253, 130, 33, 85'."""
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if len(parts) != 6:
        raise ValueError("нужно ровно шесть байт UID через запятую")
    result: list[int] = []
    for part in parts:
        value = int(part, 10)
        if not 0 <= value <= 255:
            raise ValueError("каждый байт UID — от 0 до 255")
        result.append(value)
    return result


def parse_uid_field(text: str) -> list[int]:
    """UID из карточки или вкладки: десятичные байты, пары hex или 12 символов hex."""
    stripped = text.strip()
    if re.fullmatch(r"[\d,\s]+", stripped) and "," in stripped:
        return parse_uid_bytes(stripped)
    compact = re.sub(r"[\s:]", "", stripped)
    if re.fullmatch(r"[0-9a-fA-F]{12}", compact):
        return [int(compact[index : index + 2], 16) for index in range(0, 12, 2)]
    segments = re.split(r"[\s:,;]+", stripped)
    if len(segments) == 6 and all(re.fullmatch(r"[0-9a-fA-F]{1,2}", segment) for segment in segments):
        return [int(segment, 16) for segment in segments]
    raise ValueError(f"непонятный формат UID: {text!r}")


def hash_binding_phrases(entries: Sequence[str]) -> list[tuple[str, str]]:
    """Пары (uid_hex, phrase) для радужной таблицы."""
    rows: list[tuple[str, str]] = []
    for entry in entries:
        rows.append((binding_phrase_uid_hex(entry), entry))
    return rows


def iter_wordlist_lines(
    path: Path,
    *,
    encoding: str = "utf-8",
    start_offset: int = 0,
) -> Iterator[tuple[str, int]]:
    with path.open("r", encoding=encoding, errors="ignore") as handle:
        if start_offset:
            handle.seek(start_offset)
        while True:
            line = handle.readline()
            if not line:
                break
            phrase = line.rstrip("\r\n")
            if phrase:
                yield phrase, handle.tell()