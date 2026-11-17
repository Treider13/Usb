"""Чтение ELRS/MILELRS с борта: USB полётник + Wi‑Fi модуля при питании."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from typing import Any

from .elrs_binding import parse_uid_field
from .dump_elrs import public_extraction_summary
from .elrs_http import RadioAuthRequired, DEFAULT_RX_WIFI_PASSWORDS, fetch_pages_with_passwords, normalize_pages
from .strela_bootstrap import search_binding_installed
from .usb_read import ReadOnlyError, read_usb

def _password_candidates(form: dict[str, str]) -> tuple[str, ...]:
    entered = form.get("wifi_password", "").strip()
    if entered:
        return (entered, *DEFAULT_RX_WIFI_PASSWORDS)
    return DEFAULT_RX_WIFI_PASSWORDS


def _wants_radio_read(form: dict[str, str]) -> bool:
    if form.get("radio_base", "").strip():
        return True
    if form.get("drone_port", "").strip():
        return True
    if form.get("flash_source", "").strip() == "drone":
        return True
    return form.get("action", "").strip() == "read_drone"


def _effective_radio_base(form: dict[str, str]) -> str:
    """Только адрес, который вписали. 10.0.0.1 сами не открываем: фразу CIRCL берёт из байтов."""
    return form.get("radio_base", "").strip()


def synthesize_flash_bytes(radio_json: dict) -> bytes:
    """JSON с модуля как бинарник для CIRCL dump_elrs (ищет «{» в потоке)."""
    payload = dict(radio_json)
    if isinstance(payload.get("uid"), str) and "," in str(payload["uid"]):
        payload["uid"] = [int(part) for part in str(payload["uid"]).split(",")]
    return b"\xff\xff" + json.dumps(payload, ensure_ascii=False).encode("utf-8")


def synthesize_flash_bytes_from_pages(pages: dict[str, Any]) -> bytes:
    """Полный config приёмника (uid, wifi-password, binding-phrase) для dump_elrs."""
    body = pages.get("/config") or {}
    if not isinstance(body, dict):
        body = {}
    payload: dict[str, Any] = dict(body.get("config") or {})
    normalized = normalize_pages(pages)
    uid = normalized.get("uid")
    if uid and "uid" not in payload:
        if isinstance(uid, str) and "," in uid:
            payload["uid"] = [int(part) for part in uid.split(",")]
        else:
            payload["uid"] = uid
    for key in ("wifi-ssid", "wifi-password", "binding-phrase", "binding_phrase"):
        if key in body and key not in payload:
            payload[key] = body[key]
    cfg = body.get("config")
    if isinstance(cfg, dict):
        for key in ("wifi-ssid", "wifi-password", "binding-phrase"):
            if key in cfg and key not in payload:
                payload[key] = cfg[key]
    return b"\xff\xff" + json.dumps(payload, ensure_ascii=False).encode("utf-8")


@dataclass
class DroneCapture:
    flash_bytes: bytes | None = None
    dump_text: str | None = None
    radio_json: dict | None = None
    notes: str = ""
    error: str = ""


def capture_drone(form: dict[str, str]) -> DroneCapture:
    port = form.get("drone_port", "").strip()
    base = _effective_radio_base(form)
    notes: list[str] = []
    dump_text: str | None = None
    radio_json: dict | None = None
    flash_bytes: bytes | None = None

    if port:
        try:
            captured = read_usb(
                port,
                wants={"dump": True, "msp": True, "params": False, "bin": False},
            )
            dump_text = captured.dump_text
            notes.append("Полётник по USB: дамп снят.")
        except (OSError, ReadOnlyError, ValueError) as exc:
            return DroneCapture(error=str(exc))

    if base:
        try:
            pages, auth_note = fetch_pages_with_passwords(base, passwords=_password_candidates(form))
            radio_json = normalize_pages(pages)
            flash_bytes = synthesize_flash_bytes_from_pages(pages)
            notes.append(f"Модуль по Wi‑Fi ({auth_note}): конфиг прочитан.")
        except RadioAuthRequired:
            return DroneCapture(
                notes=" ".join(notes),
                error="WebUI сменил пароль — укажите его в поле ниже или снимите .bin с приёмника",
            )
        except OSError:
            return DroneCapture(
                notes=" ".join(notes),
                error=(
                    f"Нет ответа от {base}/config. Компьютер должен быть в Wi‑Fi точке приёмника "
                    "(сеть ELRS, адрес обычно http://10.0.0.1). Откройте этот адрес в браузере: "
                    "если там пусто, приёмник не в режиме Wi‑Fi."
                ),
            )

    if dump_text is None and radio_json is None:
        if not port and not base:
            return DroneCapture(error="выберите USB-порт или подключите приёмник (Wi‑Fi точка ELRS RX)")
        return DroneCapture(error="чтение не дало данных")

    return DroneCapture(
        flash_bytes=flash_bytes,
        dump_text=dump_text,
        radio_json=radio_json,
        notes=" ".join(notes),
    )


def capture_drone_flash_bytes(form: dict[str, str]) -> tuple[bytes | None, str, str]:
    cap = capture_drone(form)
    if cap.error and cap.flash_bytes is None:
        return None, cap.notes, cap.error
    if cap.flash_bytes is None:
        return None, cap.notes, "UID на приёмнике — включите Wi‑Fi точку RX (ELRS) при питании с USB или загрузите .bin"
    return cap.flash_bytes, cap.notes, cap.error


def _blobs_from_capture(cap: DroneCapture) -> list[bytes]:
    blobs: list[bytes] = []
    if cap.flash_bytes:
        blobs.append(cap.flash_bytes)
    if cap.dump_text:
        blobs.append(cap.dump_text.encode("utf-8", "replace"))
    return blobs


def _first_extracted(blobs: list[bytes]) -> tuple[str | None, str | None, str | None]:
    """CIRCL dump_elrs по снятым байтам: uid, фраза если она в JSON, wifi-password."""
    uid_text = None
    phrase = None
    wifi = None
    for blob in blobs:
        summary = public_extraction_summary(blob, reveal_wifi_password=True)
        for item in summary.get("extracted") or []:
            if uid_text is None and isinstance(item.get("uid"), str) and item["uid"].strip():
                uid_text = item["uid"].strip()
            if phrase is None and isinstance(item.get("binding_phrase"), str) and item["binding_phrase"].strip():
                phrase = item["binding_phrase"].strip()
            if wifi is None and isinstance(item.get("wifi_password"), str) and item["wifi_password"].strip():
                wifi = item["wifi_password"].strip()
    return uid_text, phrase, wifi


def read_drone_elrs_html(
    form: dict[str, str],
    *,
    source_id: str = "all",
) -> tuple[bool, str, str]:
    """USB-дамп полётника → dump_elrs → словарь по UID. http://10.0.0.1 не открываем."""
    cap = capture_drone(form)
    blocks: list[str] = []
    if cap.notes:
        blocks.append(f"<p>{html.escape(cap.notes)}</p>")
    if cap.error and not cap.dump_text and not cap.flash_bytes:
        return False, "".join(blocks) + f"<p class='hole'>{html.escape(cap.error)}</p>", ""

    uid_text, inline_phrase, wifi = _first_extracted(_blobs_from_capture(cap))
    if wifi:
        blocks.append(
            "<p class='help'>Пароль WebUI из файла, как CIRCL <code>wifi-password</code>: "
            f"<code>{html.escape(wifi)}</code>. Им открывают http://10.0.0.1 уже после фразы.</p>"
        )
    if inline_phrase:
        blocks.append(
            "<article class='panel'><h2>Binding phrase</h2>"
            f"<p class='value-big'><code>{html.escape(inline_phrase)}</code></p>"
            "<p class='help'>Фраза была в JSON с борта. Словарь не понадобился.</p></article>"
        )
        return True, "".join(blocks), uid_text or ""
    if not uid_text:
        blocks.append(
            "<p class='hole'>В данных с USB нет JSON <code>uid</code>. "
            "CIRCL достаёт его из образа приёмника (.bin), а не из текста dump all полётника. "
            "Положите файл приёмника в форму выше.</p>"
        )
        return False, "".join(blocks), ""
    try:
        uid = parse_uid_field(uid_text)
    except ValueError as exc:
        return False, "".join(blocks) + f"<p class='hole'>{html.escape(str(exc))}</p>", uid_text
    phrase, used, problem = search_binding_installed(uid, source_id)
    blocks.append(f"<p>UID из dump_elrs: <code>{html.escape(uid_text)}</code></p>")
    if phrase:
        blocks.append(
            "<article class='panel'><h2>Binding phrase</h2>"
            f"<p class='value-big'><code>{html.escape(phrase)}</code></p>"
            f"<p class='help'>Словарь CIRCL: {html.escape(used)}.</p></article>"
        )
        return True, "".join(blocks), uid_text
    detail = problem or "фраза не найдена — выполните strela setup"
    blocks.append(f"<p class='hole'>{html.escape(detail)}</p>")
    return False, "".join(blocks), uid_text