"""Подбор binding phrase для веб-интерфейса (CIRCL elrs + ExpressLRS)."""

from __future__ import annotations

import html
import json
from pathlib import Path

from .assemble import Inputs, assemble
from .dump_elrs import public_extraction_summary
from .elrs_assemble import BINDING_UID_PROTOCOLS
from .elrs_binding import binding_phrase_to_uid, parse_uid_bytes, uid_bytes_to_hex
from .elrs_rainbow import (
    build_memory_table,
    crack_binding_phrase,
    crack_binding_phrase_from_store,
    load_memory_table,
    lookup_binding_phrase,
    save_memory_table,
)
from .menu import write_report
from .report import render_html


def _path_field(form: dict[str, str], key: str) -> Path | None:
    text = form.get(key, "").strip()
    return Path(text) if text else None


def handle_elrs_form(form: dict[str, str]) -> tuple[bool, str]:
    """Возвращает (успех, HTML-фрагмент результата)."""
    action = form.get("action", "uid").strip()
    if action == "uid":
        phrase = form.get("phrase", "").strip()
        if not phrase:
            return False, "<p class='hole'>Введите binding phrase.</p>"
        uid = binding_phrase_to_uid(phrase)
        dec = ",".join(str(byte) for byte in uid)
        hexc = uid_bytes_to_hex(uid)
        return True, (
            "<article class='panel'><h2>UID</h2>"
            f"<p>Десятичный: <code>{html.escape(dec)}</code></p>"
            f"<p>Hex: <code>{html.escape(hexc)}</code></p>"
            "<p class='help'>Та же формула, что в "
            '<a href="https://github.com/CIRCL/Drone-Forensic/tree/main/elrs">CIRCL Drone-Forensic</a> '
            "и ExpressLRS.</p></article>"
        )
    if action == "dump":
        path = _path_field(form, "flash_path")
        if path is None or not path.is_file():
            return False, "<p class='hole'>Укажите существующий файл .bin или Intel HEX.</p>"
        raw = path.read_bytes()
        summary = public_extraction_summary(raw)
        text = html.escape(json.dumps(summary, ensure_ascii=False, indent=2))
        ok = bool(summary.get("extracted"))
        return ok, (
            "<article class='panel'><h2>Из flash (dump_elrs)</h2>"
            f"<pre>{text}</pre>"
            "<p class='help'>Пароль Wi‑Fi в карточку не попадает — только флаг wifi_password_present.</p></article>"
        )
    if action == "crack":
        uid_text = form.get("uid", "").strip()
        if not uid_text:
            return False, "<p class='hole'>Введите шесть байт UID через запятую.</p>"
        try:
            uid = parse_uid_bytes(uid_text)
        except ValueError as exc:
            return False, f"<p class='hole'>{html.escape(str(exc))}</p>"
        phrase: str | None = None
        memory = _path_field(form, "memory_table")
        wordlist = _path_field(form, "binding_wordlist")
        if memory is not None:
            if not memory.is_file():
                return False, "<p class='hole'>Файл RAM-таблицы не найден.</p>"
            phrase = lookup_binding_phrase(uid, load_memory_table(memory))
        elif wordlist is not None:
            if not wordlist.is_file():
                return False, "<p class='hole'>Словарь не найден.</p>"
            phrase = crack_binding_phrase(uid, wordlist)
        else:
            return False, "<p class='hole'>Укажите словарь или JSON таблицу (build-memory --out).</p>"
        if phrase is None:
            return False, "<p class='hole'>Фраза для этого UID не найдена.</p>"
        return True, (
            "<article class='panel'><h2>Найдена binding phrase</h2>"
            f"<p><code>{html.escape(phrase)}</code></p>"
            "<p class='help'>В отчёт Стрелы по умолчанию текст не пишется — только статус "
            "<code>radio_binding_phrase_crack</code>.</p></article>"
        )
    if action == "build_memory":
        wordlist = _path_field(form, "memory_wordlist")
        out = _path_field(form, "memory_out")
        if wordlist is None or not wordlist.is_file():
            return False, "<p class='hole'>Укажите словарь.</p>"
        if out is None:
            return False, "<p class='hole'>Куда сохранить JSON таблицу.</p>"
        store = build_memory_table(wordlist)
        out.parent.mkdir(parents=True, exist_ok=True)
        save_memory_table(store, out)
        return True, (
            "<article class='panel'><h2>RAM-таблица</h2>"
            f"<p>Записано UID: {len(store.table)}</p>"
            f"<p>Файл: <code>{html.escape(str(out))}</code></p></article>"
        )
    if action == "assemble":
        out = _path_field(form, "out")
        if out is None:
            return False, "<p class='hole'>Папка отчёта обязательна.</p>"
        radio_json = None
        radio_json_path = _path_field(form, "radio_json_path")
        if radio_json_path is not None:
            if not radio_json_path.is_file():
                return False, "<p class='hole'>JSON приёмника не найден.</p>"
            radio_json = json.loads(radio_json_path.read_text(encoding="utf-8"))
        radio_image = None
        radio_image_path = _path_field(form, "radio_image_path")
        if radio_image_path is not None:
            if not radio_image_path.is_file():
                return False, "<p class='hole'>Образ приёмника не найден.</p>"
            radio_image = radio_image_path.read_bytes()
        if radio_json is None and radio_image is None:
            return False, "<p class='hole'>Нужен JSON страницы или образ flash.</p>"
        card = assemble(
            Inputs(
                radio_json=radio_json,
                radio_image=radio_image,
                binding_wordlist=_path_field(form, "assemble_wordlist"),
                binding_memory_table=_path_field(form, "assemble_memory"),
            )
        )
        protocol = card.fields.get("radio_protocol")
        proto = str(protocol.value) if protocol and protocol.status == "confirmed" else None
        if form.get("assemble_wordlist") or form.get("assemble_memory"):
            if proto and proto not in BINDING_UID_PROTOCOLS:
                note = (
                    f"<p class='help'>Протокол {html.escape(proto)}: подбор UID как у CIRCL "
                    f"только для ExpressLRS/MILELRS. OrangeRX — DSM, не ELRS.</p>"
                )
            else:
                note = ""
        else:
            note = ""
        saved = write_report(card, out)
        return True, note + render_html(card, saved_path=str(saved))
    return False, "<p class='hole'>Неизвестное действие.</p>"