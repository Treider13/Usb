"""Read an ExpressLRS Web UI without writing to it.

The routes are the ones registered in ExpressLRS src/lib/WIFI/devWIFI.cpp:
GET /config, GET /options.json, GET /hardware.json.
/update, /reboot, /reset, /cw and /sethome change the device and are not called.
"""

from __future__ import annotations

import json
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen


READ_PATHS = ("/config", "/options.json", "/hardware.json")
FORBIDDEN_PATHS = ("/update", "/reboot", "/reset", "/cw", "/sethome", "/connect", "/forceupdate")


class RadioAuthRequired(Exception):
    """The page asked for a password. One prompt, no retries."""


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
    model = cfg.get("model")
    if isinstance(model, dict):
        for slot in model.values():
            if isinstance(slot, dict) and "packet-rate" in slot:
                out["tx_packet_rate"] = slot["packet-rate"]
                break
    return out
