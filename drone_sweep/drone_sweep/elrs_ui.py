"""Подбор binding phrase для веб-интерфейса (CIRCL elrs + ExpressLRS)."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Mapping

from .assemble import Inputs, assemble
from .dump_elrs import public_extraction_summary
from .elrs_assemble import search_binding_sources
from .elrs_binding import binding_phrase_to_uid, parse_uid_field, uid_bytes_to_hex
from .elrs_rainbow import build_memory_table, save_memory_table
from .menu import write_report
from .report import render_html
from .strela_bootstrap import default_binding_paths
from .webapp_forms import Uploaded, resolve_upload_path


def _bundled_wordlist() -> Path | None:
    return default_binding_paths().get("wordlist")


def _bundled_memory_table() -> Path | None:
    return default_binding_paths().get("memory_table")


def _resolve_wordlist(form: dict[str, str], uploads: Mapping[str, Uploaded]) -> Path | None:
    path = resolve_upload_path(form, uploads, "binding_wordlist_file", "binding_wordlist")
    return path if path is not None else _bundled_wordlist()


def _resolve_memory_table(form: dict[str, str], uploads: Mapping[str, Uploaded]) -> Path | None:
    path = resolve_upload_path(form, uploads, "memory_table_file", "memory_table")
    return path if path is not None else _bundled_memory_table()


def _path_field(form: dict[str, str], key: str) -> Path | None:
    text = form.get(key, "").strip()
    return Path(text) if text else None


def _flash_bytes(form: Mapping[str, str], files: Mapping[str, Uploaded]) -> bytes | None:
    upload = files.get("flash_file")
    if upload is not None and upload.data:
        return upload.data
    path = _path_field(dict(form), "flash_path")
    if path is not None and path.is_file():
        return path.read_bytes()
    upload = files.get("radio_image_file")
    if upload is not None and upload.data:
        return upload.data
    path = _path_field(dict(form), "radio_image_path")
    if path is not None and path.is_file():
        return path.read_bytes()
    return None


def _binding_phrase_in_summary(summary: dict) -> str | None:
    for item in summary.get("extracted") or []:
        phrase = item.get("binding_phrase")
        if isinstance(phrase, str) and phrase.strip():
            return phrase.strip()
    return None


def _first_uid_from_summary(summary: dict) -> str | None:
    for item in summary.get("extracted") or []:
        uid = item.get("uid")
        if isinstance(uid, str) and uid.strip():
            return uid.strip()
    return None


def _phrase_panel(phrase: str, *, extra: str = "") -> str:
    return (
        "<article class='panel'><h2>Binding phrase</h2>"
        f"<p class='value-big'><code>{html.escape(phrase)}</code></p>"
        f"{extra}"
        "<p class='help'>Пароль Wi‑Fi для этого не нужен. В отчёт Стрелы текст фразы "
        "по умолчанию не пишется — только статус <code>radio_binding_phrase_crack</code>.</p>"
        "</article>"
    )


def handle_elrs_form(
    form: dict[str, str],
    files: Mapping[str, Uploaded] | None = None,
) -> tuple[bool, str, str]:
    """Возвращает (успех, HTML-фрагмент, UID для подстановки в форму)."""
    uploads = files or {}
    action = form.get("action", "uid").strip()
    if action == "uid":
        phrase = form.get("phrase", "").strip()
        if not phrase:
            return False, "<p class='hole'>Введите binding phrase.</p>", ""
        uid = binding_phrase_to_uid(phrase)
        dec = ",".join(str(byte) for byte in uid)
        hexc = uid_bytes_to_hex(uid)
        return True, (
            "<article class='panel'><h2>UID</h2>"
            f"<p>Десятичный: <code>{html.escape(dec)}</code></p>"
            f"<p>Hex: <code>{html.escape(hexc)}</code></p>"
            "<p class='help'>Та же формула, что в "
            '<a href="https://github.com/CIRCL/Drone-Forensic/tree/main/elrs">CIRCL Drone-Forensic</a> '
            "и ExpressLRS. Этот hex можно вставить в подбор ниже.</p></article>"
        ), dec
    if action in {"dump", "phrase_from_flash"}:
        raw = _flash_bytes(form, uploads)
        if raw is None:
            return False, "<p class='hole'>Выберите файл .bin или Intel HEX с компьютера (или укажите путь).</p>", ""
        summary = public_extraction_summary(raw)
        uid_text = _first_uid_from_summary(summary)
        text = html.escape(json.dumps(summary, ensure_ascii=False, indent=2))
        dump_block = (
            "<article class='panel'><h2>Из flash (dump_elrs)</h2>"
            f"<pre>{text}</pre>"
            "<p class='help'>Пароль Wi‑Fi в карточку не попадает — только флаг wifi_password_present.</p>"
            "</article>"
        )
        inline_phrase = _binding_phrase_in_summary(summary)
        uid_line = ""
        if uid_text:
            uid_line = f"<p>UID из образа: <code>{html.escape(uid_text)}</code> — подставлен в форму ниже.</p>"
        if inline_phrase:
            note = "<p class='help'>Фраза в открытом виде в JSON flash — словарь и Wi‑Fi не нужны.</p>"
            body = dump_block + uid_line + _phrase_panel(inline_phrase, extra=note)
            return True, body, uid_text or ""
        if action == "dump":
            return bool(summary.get("extracted")), dump_block + uid_line, uid_text or ""
        if uid_text is None:
            return False, dump_block + "<p class='hole'>В образе не найден UID из шести байт.</p>", ""
        wordlist = _resolve_wordlist(form, uploads)
        memory = _resolve_memory_table(form, uploads)
        if wordlist is None and memory is None:
            return (
                False,
                dump_block
                + "<p class='hole'>Нет словаря. Запустите <code>strela setup</code> или укажите файл словаря.</p>",
                uid_text,
            )
        try:
            uid = parse_uid_field(uid_text)
        except ValueError as exc:
            return False, dump_block + f"<p class='hole'>{html.escape(str(exc))}</p>", uid_text
        phrase, _source, problem = search_binding_sources(uid, wordlist, memory)
        if phrase is None:
            detail = problem or "Фраза для этого UID не найдена."
            return False, dump_block + f"<p class='hole'>{html.escape(detail)}</p>", uid_text
        return True, dump_block + _phrase_panel(phrase), uid_text
    if action == "crack":
        uid_text = form.get("uid", "").strip()
        if not uid_text:
            return False, "<p class='hole'>Введите UID: шесть байт через запятую или 12 символов hex.</p>", ""
        try:
            uid = parse_uid_field(uid_text)
        except ValueError as exc:
            return False, f"<p class='hole'>{html.escape(str(exc))}</p>", uid_text
        memory = _resolve_memory_table(form, uploads)
        wordlist = _resolve_wordlist(form, uploads)
        if memory is None and wordlist is None:
            return (
                False,
                "<p class='hole'>Нет словаря. Запустите <code>strela setup</code> или загрузите файл словаря.</p>",
                uid_text,
            )
        phrase, _source, problem = search_binding_sources(uid, wordlist, memory)
        if phrase is None:
            detail = problem or "Фраза для этого UID не найдена."
            return False, f"<p class='hole'>{html.escape(detail)}</p>", uid_text
        return True, _phrase_panel(phrase), uid_text
    if action == "build_memory":
        wordlist = resolve_upload_path(form, uploads, "memory_wordlist_file", "memory_wordlist")
        out = _path_field(form, "memory_out")
        if wordlist is None:
            return False, "<p class='hole'>Выберите словарь с компьютера или укажите путь.</p>", ""
        if out is None:
            return False, "<p class='hole'>Куда сохранить JSON таблицу (путь на диске).</p>", ""
        store = build_memory_table(wordlist)
        out.parent.mkdir(parents=True, exist_ok=True)
        save_memory_table(store, out)
        return True, (
            "<article class='panel'><h2>RAM-таблица</h2>"
            f"<p>Записано UID: {len(store.table)}</p>"
            f"<p>Файл: <code>{html.escape(str(out))}</code></p></article>"
        ), ""
    if action == "assemble":
        out = _path_field(form, "out")
        if out is None:
            return False, "<p class='hole'>Папка отчёта обязательна.</p>", ""
        radio_json = None
        radio_json_path = resolve_upload_path(form, uploads, "radio_json_file", "radio_json_path")
        if radio_json_path is not None:
            try:
                radio_json = json.loads(radio_json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                return False, f"<p class='hole'>JSON приёмника не читается: {html.escape(str(exc))}</p>", ""
        radio_image = None
        radio_image_path = resolve_upload_path(form, uploads, "radio_image_file", "radio_image_path")
        if radio_image_path is not None:
            radio_image = radio_image_path.read_bytes()
        if radio_json is None and radio_image is None:
            return False, "<p class='hole'>Нужен JSON страницы или образ flash (файл с ПК или путь).</p>", ""
        card = assemble(
            Inputs(
                radio_json=radio_json,
                radio_image=radio_image,
                binding_wordlist=resolve_upload_path(form, uploads, "assemble_wordlist_file", "assemble_wordlist")
                or _bundled_wordlist(),
                binding_memory_table=resolve_upload_path(form, uploads, "assemble_memory_file", "assemble_memory")
                or _bundled_memory_table(),
            )
        )
        saved = write_report(card, out)
        return True, render_html(card, saved_path=str(saved)), ""
    return False, "<p class='hole'>Неизвестное действие.</p>", ""