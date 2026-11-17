"""MSP identity replies from Betaflight and INAV.

Betaflight src/main/msp/msp.c and INAV src/main/fc/fc_msp.c.
Codes are read requests below 200. Nothing here writes a setting.
"""

from __future__ import annotations


MSP_FC_VERSION = 3
MSP_BOARD_INFO = 4
MSP_BUILD_INFO = 5
MSP_NAME = 10


def describe_identity(raw: dict[int, bytes | None], family: str | None) -> dict:
    """Turn payloads into fields. A short or broken payload stays absent."""
    described: dict = {}
    version = _version(raw.get(MSP_FC_VERSION), family)
    if version:
        described["fc_version"] = version
    board = _board(raw.get(MSP_BOARD_INFO), family)
    if board:
        described["board"] = board
    build = _build(raw.get(MSP_BUILD_INFO), family)
    if build:
        described["build"] = build
    name = _name(raw.get(MSP_NAME))
    if name:
        described["craft_name"] = name
    return described


def _version(payload: bytes | None, family: str | None) -> dict | None:
    if not payload or len(payload) < 3:
        return None
    first, second, third = payload[0], payload[1], payload[2]
    if len(payload) == 3:
        return {
            "version": f"{first}.{second}.{third}",
            "major": first,
            "minor": second,
            "patch": third,
            "layout": "три байта major.minor.patch, как MSP_FC_VERSION в INAV",
        }
    text = _pstring(payload[3:])
    if text is None:
        return {
            "version": f"{first}.{second}.{third}",
            "major": first,
            "minor": second,
            "patch": third,
            "layout": "три байта, строка версии не разобрана",
        }
    return {
        "version": text,
        "year_since_2000": first,
        "month": second,
        "patch": third,
        "layout": "строка версии и три байта год-2000, месяц, патч из Betaflight msp.c",
    }


def _board(payload: bytes | None, family: str | None) -> dict | None:
    if not payload or len(payload) < 4:
        return None
    info = {"identifier": payload[:4].decode("latin1", errors="replace").rstrip("\x00")}
    if len(payload) < 8:
        return info
    info["hardware_revision"] = int.from_bytes(payload[4:6], "little")
    osd = payload[6]
    info["osd_type"] = osd
    info["osd_label"] = _osd_label(osd, family)
    info["comm_capabilities"] = payload[7]
    rest = payload[8:]
    target, rest = _take_pstring(rest)
    if target is None:
        return info
    info["target_name"] = target
    if family == "inav":
        # INAV stops after the target name. Later bytes are not a board name.
        return info
    board, rest = _take_pstring(rest)
    maker, _rest = _take_pstring(rest)
    if board is not None:
        info["board_name"] = board
    if maker is not None:
        info["manufacturer_id"] = maker
    return info


def _osd_label(value: int, family: str | None) -> str:
    if family == "inav":
        return {0: "OSD нет", 2: "OSD на плате"}.get(value, f"код {value}")
    if family in {"betaflight", "cleanflight"}:
        return {0: "полётник", 2: "MAX7456"}.get(value, f"код {value}")
    return f"код {value}"


def _build(payload: bytes | None, family: str | None) -> dict | None:
    if not payload or len(payload) < 11 + 8:
        return None
    date = payload[:11].decode("latin1", errors="replace").rstrip("\x00").strip()
    clock = payload[11:19].decode("latin1", errors="replace").rstrip("\x00").strip()
    git_len = 8 if family == "inav" or len(payload) == 27 else 7
    if len(payload) < 19 + git_len:
        return {"date": date, "time": clock}
    git = payload[19:19 + git_len].decode("latin1", errors="replace").rstrip("\x00")
    return {"date": date, "time": clock, "git": git}


def _name(payload: bytes | None) -> str:
    if not payload:
        return ""
    return payload.decode("latin1", errors="replace").rstrip("\x00").strip()


def _take_pstring(payload: bytes) -> tuple[str | None, bytes]:
    if not payload:
        return None, payload
    length = payload[0]
    if length > len(payload) - 1:
        return None, payload
    text = payload[1:1 + length].decode("latin1", errors="replace")
    return text, payload[1 + length:]


def _pstring(payload: bytes) -> str | None:
    text, _rest = _take_pstring(payload)
    return text
