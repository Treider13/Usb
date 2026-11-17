"""Betaflight and INAV CLI text.

The grammar is the one written by `dump all`: `set name = value`,
`aux <index> <mode> <channel> <start> <end> ...`, `vtxtable ...`,
`vtx ...`, `serial ...`, and bare `board_name`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


_SET = re.compile(r"^(?:set\s+)?([A-Za-z0-9_]+)\s*=\s*(.*)$")
_AUX = re.compile(
    r"^aux\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(\d+))?(?:\s+(\d+))?\s*$",
    re.IGNORECASE,
)
_BOARD = re.compile(r"^board_name\s+(\S+)\s*$", re.IGNORECASE)
_MCU = re.compile(r"^mcu_id\s+(\S+)\s*$", re.IGNORECASE)
_VERSION = re.compile(r"^#\s*(Betaflight|INAV|Cleanflight)\b.*$", re.IGNORECASE)
_FEATURE = re.compile(r"^feature\s+(-?)([A-Za-z0-9_]+)\s*$", re.IGNORECASE)
_SECTION = re.compile(r"^(master|profile|rateprofile|battery_profile|pid_profile)\b", re.IGNORECASE)


@dataclass
class AuxMode:
    index: int
    mode_id: int
    channel: int
    range_start: int
    range_end: int
    name: str | None = None


@dataclass
class Dump:
    family: str
    banner: str
    board_name: str | None
    mcu_id: str | None
    settings: dict[str, str] = field(default_factory=dict)
    sections: list[dict] = field(default_factory=list)
    commands: dict[str, list[str]] = field(default_factory=dict)
    aux: list[AuxMode] = field(default_factory=list)
    vtxtable: list[str] = field(default_factory=list)
    vtx: list[str] = field(default_factory=list)
    serial_lines: list[str] = field(default_factory=list)
    features_enabled: list[str] = field(default_factory=list)
    features_disabled: list[str] = field(default_factory=list)
    osd: dict[str, str] = field(default_factory=dict)
    failsafe: dict[str, str] = field(default_factory=dict)


def master_or_unique(dump: Dump, key: str) -> str | None:
    """Master value wins. A profile value is used only when every copy agrees."""
    if key in dump.settings:
        return dump.settings[key]
    found = [section["settings"][key] for section in dump.sections if key in section["settings"]]
    if found and all(item == found[0] for item in found):
        return found[0]
    return None


def parse_boxnames(text: str | None) -> list[str]:
    """MSP_BOXNAMES is one line of names separated by semicolons."""
    if not text:
        return []
    body = text.strip()
    if not body:
        return []
    return [part.strip() for part in body.split(";")]


def parse_dump(text: str, boxnames: list[str] | None = None) -> Dump:
    family = "unknown"
    banner = ""
    board = None
    mcu = None
    settings: dict[str, str] = {}
    aux: list[AuxMode] = []
    vtxtable: list[str] = []
    vtx: list[str] = []
    serial_lines: list[str] = []
    features_enabled: list[str] = []
    features_disabled: list[str] = []
    names = boxnames or []
    sections: list[dict] = []
    commands: dict[str, list[str]] = {}
    current = {"name": "master", "settings": {}, "lines": []}

    def close_section() -> None:
        if current["settings"] or current["lines"]:
            sections.append({"name": current["name"], "settings": dict(current["settings"]), "lines": list(current["lines"])})

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("###") or line == "#":
            continue
        version = _VERSION.match(line)
        if version:
            family = version.group(1).lower()
            if family == "cleanflight":
                family = "cleanflight"
            banner = line[1:].strip()
            continue
        if line.startswith("#"):
            if not banner and "version" in line.lower():
                banner = line[1:].strip()
            continue
        board_match = _BOARD.match(line)
        if board_match:
            board = board_match.group(1)
            continue
        mcu_match = _MCU.match(line)
        if mcu_match:
            mcu = mcu_match.group(1)
            continue
        if line.lower().startswith("vtxtable "):
            vtxtable.append(line)
            continue
        if line.lower().startswith("vtx "):
            vtx.append(line)
            continue
        if line.lower().startswith("serial "):
            serial_lines.append(line)
            continue
        feature = _FEATURE.match(line)
        if feature:
            if feature.group(1) == "-":
                features_disabled.append(feature.group(2))
            else:
                features_enabled.append(feature.group(2))
            continue
        if _SECTION.match(line):
            close_section()
            current = {"name": line, "settings": {}, "lines": []}
            continue
        aux_match = _AUX.match(line)
        if aux_match:
            mode_id = int(aux_match.group(2))
            name = names[mode_id] if mode_id < len(names) and names[mode_id] else None
            aux.append(
                AuxMode(
                    index=int(aux_match.group(1)),
                    mode_id=mode_id,
                    channel=int(aux_match.group(3)),
                    range_start=int(aux_match.group(4)),
                    range_end=int(aux_match.group(5)),
                    name=name,
                )
            )
            continue
        setting = _SET.match(line)
        if setting:
            key, value = setting.group(1), setting.group(2).strip()
            current["settings"][key] = value
            if current["name"].lower().startswith("master"):
                settings[key] = value
            continue
        verb = line.split()[0].lower()
        commands.setdefault(verb, []).append(line)
        current["lines"].append(line)

    close_section()
    osd: dict[str, str] = {}
    failsafe: dict[str, str] = {}
    for section in sections:
        for key, value in section["settings"].items():
            target = osd if key.startswith("osd_") else failsafe if key.startswith("failsafe_") else None
            if target is None:
                continue
            if key not in target:
                target[key] = value
            elif target[key] != value:
                target[f"{section['name']} {key}"] = value
    if family == "unknown" and any(key.startswith("serialrx_") for key in settings):
        family = "betaflight"
    return Dump(
        family=family,
        banner=banner,
        board_name=board,
        mcu_id=mcu,
        settings=settings,
        aux=aux,
        vtxtable=vtxtable,
        vtx=vtx,
        serial_lines=serial_lines,
        features_enabled=features_enabled,
        features_disabled=features_disabled,
        osd=osd,
        failsafe=failsafe,
        sections=sections,
        commands=commands,
    )
