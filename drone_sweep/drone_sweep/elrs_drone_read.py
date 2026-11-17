"""Чтение ELRS/MILELRS с борта: USB полётник + Wi‑Fi модуля при питании."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from typing import Any

from .assemble import Inputs, assemble
from .elrs_assemble import BINDING_UID_PROTOCOLS
from .elrs_binding import parse_uid_field
from .elrs_http import RadioAuthRequired, DEFAULT_RX_WIFI_PASSWORDS, fetch_pages_with_passwords, normalize_pages
from .strela_bootstrap import search_binding_installed
from .usb_read import ReadOnlyError, read_usb

DEFAULT_RADIO_BASE = "http://10.0.0.1"


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
    base = form.get("radio_base", "").strip()
    if base:
        return base
    if _wants_radio_read(form):
        return DEFAULT_RADIO_BASE
    return ""


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
        except OSError as exc:
            return DroneCapture(notes=" ".join(notes), error=str(exc))

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


def read_drone_elrs_html(
    form: dict[str, str],
    *,
    source_id: str = "all",
) -> tuple[bool, str, str]:
    """USB и/или WebUI модуля → UID → binding phrase (без заранее известного пароля Wi‑Fi)."""
    cap = capture_drone(form)
    blocks: list[str] = []
    if cap.notes:
        blocks.append(f"<p>{html.escape(cap.notes)}</p>")
    if cap.error and cap.radio_json is None and not cap.dump_text:
        return False, f"<p class='hole'>{html.escape(cap.error)}</p>", ""

    card = assemble(Inputs(dump_text=cap.dump_text, radio_json=cap.radio_json))
    protocol = card.fields.get("radio_protocol")
    proto = str(protocol.value) if protocol and protocol.status == "confirmed" else None
    if proto and proto not in BINDING_UID_PROTOCOLS:
        return False, f"<p class='hole'>Протокол {html.escape(proto)}: подбор UID только ExpressLRS/MILELRS.</p>", ""

    uid_field = card.fields.get("radio_uid")
    if uid_field is None or uid_field.status != "confirmed":
        blocks.append(
            "<p class='hole'>Нет UID: питайте приёмник от USB, дождитесь Wi‑Fi «ELRS_*» или загрузите .bin.</p>"
        )
        return False, "".join(blocks), ""

    uid_text = str(uid_field.value)
    try:
        uid = parse_uid_field(uid_text)
    except ValueError as exc:
        return False, f"<p class='hole'>{html.escape(str(exc))}</p>", uid_text

    phrase, used, problem = search_binding_installed(uid, source_id)
    body = "".join(blocks)
    body += f"<p>UID: <code>{html.escape(uid_text)}</code></p>"
    if phrase:
        body += (
            "<article class='panel'><h2>Binding phrase</h2>"
            f"<p class='value-big'><code>{html.escape(phrase)}</code></p>"
            f"<p class='help'>Источник: {html.escape(used)}. Пароль Wi‑Fi WebUI для подбора не нужен.</p></article>"
        )
        return True, body, uid_text
    detail = problem or "фраза не найдена — выполните strela setup"
    body += f"<p class='hole'>{html.escape(detail)}</p>"
    return False, body, uid_text