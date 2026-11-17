"""Чтение ELRS/MILELRS с борта: USB полётник + Wi‑Fi модуль при питании."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass

from .assemble import Inputs, assemble
from .elrs_assemble import BINDING_UID_PROTOCOLS
from .elrs_binding import parse_uid_field
from .elrs_http import RadioAuthRequired, fetch_pages, normalize_pages
from .strela_bootstrap import search_binding_installed
from .usb_read import ReadOnlyError, read_usb


def _fetch_radio(base: str, wifi_password: str) -> dict:
    from base64 import b64encode
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    def opener(url: str, timeout: float = 8.0) -> bytes:
        request = Request(url, method="GET")
        if wifi_password:
            token = b64encode(f":{wifi_password}".encode("ascii", errors="ignore")).decode("ascii")
            request.add_header("Authorization", f"Basic {token}")
        with urlopen(request, timeout=timeout) as response:
            return response.read()

    try:
        return fetch_pages(base, opener=opener)
    except HTTPError as exc:
        if exc.code == 401:
            raise RadioAuthRequired(base) from exc
        raise


def synthesize_flash_bytes(radio_json: dict) -> bytes:
    """JSON с модуля как бинарник для CIRCL dump_elrs (ищет «{» в потоке)."""
    payload = dict(radio_json)
    if isinstance(payload.get("uid"), str) and "," in str(payload["uid"]):
        payload["uid"] = [int(part) for part in str(payload["uid"]).split(",")]
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
    base = (form.get("radio_base") or "").strip()
    wifi_password = form.get("wifi_password", "").strip()
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
            pages = _fetch_radio(base, wifi_password)
            radio_json = normalize_pages(pages)
            flash_bytes = synthesize_flash_bytes(radio_json)
            notes.append("Модуль по Wi‑Fi: конфиг прочитан.")
        except RadioAuthRequired:
            return DroneCapture(notes=" ".join(notes), error="нужен пароль Wi‑Fi WebUI (часто expresslrs)")
        except OSError as exc:
            return DroneCapture(notes=" ".join(notes), error=str(exc))

    if dump_text is None and radio_json is None:
        if not port and not base:
            return DroneCapture(error="выберите USB-порт и/или укажите адрес Wi‑Fi модуля")
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
    if cap.flash_bytes is None and cap.dump_text and "expresslrs" not in (cap.dump_text or "").lower():
        return None, cap.notes, "в USB-дампе нет expresslrs — включите Wi‑Fi на приёмнике или загрузите .bin"
    return cap.flash_bytes, cap.notes, cap.error


def read_drone_elrs_html(
    form: dict[str, str],
    *,
    source_id: str = "all",
) -> tuple[bool, str, str]:
    """USB и/или WebUI модуля → UID → binding phrase."""
    cap = capture_drone(form)
    blocks: list[str] = []
    if cap.notes:
        blocks.append(f"<p>{html.escape(cap.notes)}</p>")
    if cap.error and cap.radio_json is None and not cap.dump_text:
        if "пароль" in cap.error.lower():
            return (
                False,
                "<p class='hole'>Модуль просит пароль Wi‑Fi (часто <code>expresslrs</code>). Введите в поле ниже.</p>",
                "",
            )
        return False, f"<p class='hole'>{html.escape(cap.error)}</p>", ""

    card = assemble(Inputs(dump_text=cap.dump_text, radio_json=cap.radio_json))
    protocol = card.fields.get("radio_protocol")
    proto = str(protocol.value) if protocol and protocol.status == "confirmed" else None
    if proto and proto not in BINDING_UID_PROTOCOLS:
        return False, f"<p class='hole'>Протокол {html.escape(proto)}: подбор UID только ExpressLRS/MILELRS.</p>", ""

    uid_field = card.fields.get("radio_uid")
    if uid_field is None or uid_field.status != "confirmed":
        blocks.append(
            "<p class='hole'>В чтении нет UID. Включите Wi‑Fi ExpressLRS RX, задайте пароль WebUI или загрузите .bin.</p>"
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
            f"<p class='help'>Источник: {html.escape(used)}</p></article>"
        )
        return True, body, uid_text
    detail = problem or "фраза не найдена"
    body += f"<p class='hole'>{html.escape(detail)}</p>"
    return False, body, uid_text