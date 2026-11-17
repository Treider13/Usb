"""Read an ExpressLRS Web UI without writing to it.

The routes are the ones registered in ExpressLRS src/lib/WIFI/devWIFI.cpp.
Current firmware: GET /config, GET /options.json, GET /hardware.json.
ExpressLRS 3.0.0 also answers GET /target and GET /mode.json.
/networks.json starts a Wi-Fi scan, so it is not called.
/update, /reboot, /reset, /cw and /sethome change the device and are not called.
"""

from __future__ import annotations

import json
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen


READ_PATHS = ("/config", "/options.json", "/hardware.json", "/target", "/mode.json")
FORBIDDEN_PATHS = ("/update", "/reboot", "/reset", "/cw", "/sethome", "/connect", "/forceupdate", "/networks.json", "/access")


class RadioAuthRequired(Exception):
    """The page asked for a password. One prompt, no retries."""


# Заводской WebUI ExpressLRS RX; при чтении с борта пробуем по очереди.
DEFAULT_RX_WIFI_PASSWORDS: tuple[str, ...] = ("", "expresslrs")


def _join(base: str, path: str) -> str:
    return base.rstrip("/") + path


def fetch_pages(base: str, opener: Callable[..., Any] | None = None, timeout: float = 5.0) -> dict[str, Any]:
    """GET the three read endpoints. A 401 stops the session."""
    fetch = opener or _open
    pages: dict[str, Any] = {}
    for path in READ_PATHS:
        if path in FORBIDDEN_PATHS:
            raise RuntimeError(path)
        url = _join(base, path)
        try:
            payload = fetch(url, timeout=timeout)
        except HTTPError as exc:
            if exc.code == 401:
                raise RadioAuthRequired(url) from exc
            pages[path] = None
            continue
        if isinstance(payload, (bytes, str)):
            text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
            pages[path] = json.loads(text) if text.strip() else None
        else:
            pages[path] = payload
    return pages


def _open(url: str, timeout: float = 5.0) -> bytes:
    request = Request(url, method="GET")
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _opener_for_password(password: str, timeout: float = 8.0) -> Callable[..., Any]:
    from base64 import b64encode

    def opener(url: str, timeout: float = timeout) -> bytes:
        request = Request(url, method="GET")
        if password:
            token = b64encode(f":{password}".encode("ascii", errors="ignore")).decode("ascii")
            request.add_header("Authorization", f"Basic {token}")
        with urlopen(request, timeout=timeout) as response:
            return response.read()

    return opener


def fetch_pages_with_passwords(
    base: str,
  *,
    passwords: tuple[str, ...] | None = None,
    timeout: float = 8.0,
) -> tuple[dict[str, Any], str]:
    """Читает WebUI. Сначала пароль из формы, затем заводские."""
    tried: list[str] = []
    for password in passwords or DEFAULT_RX_WIFI_PASSWORDS:
        if password in tried:
            continue
        tried.append(password)
        try:
            pages = fetch_pages(base, opener=_opener_for_password(password, timeout=timeout), timeout=timeout)
        except RadioAuthRequired:
            continue
        note = "без пароля" if not password else f"пароль «{password}»"
        return pages, note
    raise RadioAuthRequired(base)


def normalize_pages(pages: dict[str, Any]) -> dict[str, Any]:
    """Turn /config into the public radio fields. Packet rate on an RX page is absent."""
    config_body = pages.get("/config") or {}
    options = pages.get("/options.json") or {}
    hardware = pages.get("/hardware.json") or {}
    if not isinstance(config_body, dict):
        config_body = {}
    settings = config_body.get("settings") or {}
    cfg = config_body.get("config") or {}
    if not isinstance(settings, dict):
        settings = {}
    if not isinstance(cfg, dict):
        cfg = {}
    version = str(settings.get("version") or "")
    product = str(settings.get("product_name") or "")
    out: dict[str, Any] = {}
    if "milelrs" in version.lower() or "milelrs" in product.lower():
        out["version"] = version or product
    elif settings or cfg:
        out["version"] = version if "expresslrs" in version.lower() else f"ExpressLRS {version}".strip()
    if product:
        out["model"] = product
    if settings.get("radio-type"):
        out["chip"] = settings["radio-type"]
    if settings.get("target"):
        out["target"] = settings["target"]
    if settings.get("module-type"):
        out["module_type"] = settings["module-type"]
    if settings.get("git-commit"):
        out["git_commit"] = settings["git-commit"]
    uid = cfg.get("uid")
    if isinstance(uid, list) and uid:
        out["uid"] = ",".join(str(part) for part in uid)
    if "serial-protocol" in cfg:
        out["serial_protocol"] = cfg["serial-protocol"]
    if "modelid" in cfg:
        out["model_id"] = cfg["modelid"]
    if isinstance(options, dict):
        for key in ("domain", "custom_freq", "custom-freq", "binding_rate", "binding-rate", "swarm_id", "vx_table", "vx_bands"):
            if key in options and options[key] not in (None, ""):
                out[key.replace("-", "_")] = options[key]
        if "domain" not in out and options.get("reg_domain_low") not in (None, ""):
            out["domain"] = options["reg_domain_low"]
    if isinstance(hardware, dict) and not out.get("model") and hardware.get("product_name"):
        out["model"] = hardware["product_name"]
    target = pages.get("/target") or {}
    mode = pages.get("/mode.json") or {}
    if not isinstance(target, dict):
        target = {}
    if not isinstance(mode, dict):
        mode = {}
    if not out.get("version") and target.get("version"):
        version = str(target["version"])
        product = str(target.get("product_name") or mode.get("product_name") or "")
        if "milelrs" in version.lower() or "milelrs" in product.lower():
            out["version"] = version
        else:
            out["version"] = version if "expresslrs" in version.lower() else f"ExpressLRS {version}".strip()
    if not out.get("model"):
        out["model"] = target.get("product_name") or mode.get("product_name") or ""
        if not out["model"]:
            out.pop("model")
    if target.get("target") and "target" not in out:
        out["target"] = target["target"]
    if "domain" not in out:
        domain = target.get("reg_domain") or mode.get("reg_domain")
        if domain not in (None, ""):
            out["domain"] = domain
    if "uid" not in out and isinstance(mode.get("uid"), list) and mode["uid"]:
        out["uid"] = ",".join(str(part) for part in mode["uid"])
    if mode.get("modelid") not in (None, "") and "model_id" not in out:
        out["model_id"] = mode["modelid"]
    if mode.get("lua_name"):
        out["lua_name"] = mode["lua_name"]
    if mode.get("mode"):
        out["wifi_mode"] = mode["mode"]
    if mode.get("uidtype"):
        out["uid_type"] = mode["uidtype"]
    model = cfg.get("model")
    if isinstance(model, dict):
        for slot in model.values():
            if isinstance(slot, dict) and "packet-rate" in slot:
                out["tx_packet_rate"] = slot["packet-rate"]
                break
    return out
