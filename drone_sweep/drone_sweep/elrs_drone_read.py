"""Чтение ELRS/MILELRS с борта: USB полётник + Wi‑Fi модуль при питании."""

from __future__ import annotations

import html
from pathlib import Path

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


def read_drone_elrs_html(
    form: dict[str, str],
    *,
    source_id: str = "all",
) -> tuple[bool, str, str]:
    """USB и/или WebUI модуля → UID → binding phrase. Возврат как handle_elrs_form."""
    port = form.get("drone_port", "").strip()
    base = form.get("radio_base", "http://10.0.0.1").strip()
    wifi_password = form.get("wifi_password", "").strip()
    blocks: list[str] = []
    dump_text = None
    radio_json = None

    if port:
        try:
            captured = read_usb(
                port,
                wants={"dump": True, "msp": True, "params": False, "bin": False},
            )
            dump_text = captured.dump_text
            blocks.append(
                "<p>Полётник по USB: дамп снят"
                + (f", expresslrs в настройках" if dump_text and "expresslrs" in dump_text.lower() else "")
                + ".</p>"
            )
        except (OSError, ReadOnlyError, ValueError) as exc:
            return False, f"<p class='hole'>USB: {html.escape(str(exc))}</p>", ""

    if base:
        try:
            pages = _fetch_radio(base, wifi_password)
            radio_json = normalize_pages(pages)
            blocks.append("<p>Модуль по Wi‑Fi: страница прочитана.</p>")
        except RadioAuthRequired:
            return (
                False,
                "<p class='hole'>Модуль просит пароль Wi‑Fi (часто <code>expresslrs</code>). Введите в поле ниже.</p>",
                "",
            )
        except OSError as exc:
            return False, f"<p class='hole'>Wi‑Fi: {html.escape(str(exc))}</p>", ""

    if dump_text is None and radio_json is None:
        return False, "<p class='hole'>Укажите USB-порт полётника и/или адрес Wi‑Fi модуля.</p>", ""

    card = assemble(Inputs(dump_text=dump_text, radio_json=radio_json))
    protocol = card.fields.get("radio_protocol")
    proto = str(protocol.value) if protocol and protocol.status == "confirmed" else None
    if proto and proto not in BINDING_UID_PROTOCOLS:
        return False, f"<p class='hole'>Протокол {html.escape(proto)}: подбор UID только ExpressLRS/MILELRS.</p>", ""

    uid_field = card.fields.get("radio_uid")
    if uid_field is None or uid_field.status != "confirmed":
        blocks.append(
            "<p class='hole'>В чтении нет UID. Проверьте питание приёмника, Wi‑Fi сеть ExpressLRS RX "
            "или снимите flash.</p>"
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