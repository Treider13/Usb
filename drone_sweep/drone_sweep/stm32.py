"""Identity lines from a saved STM32 programmer log.

STM32_Programmer_CLI prints them after `--connect` and before any download.
The field names are the ones in that banner: Device ID, Device name, Flash size.
st-info --probe prints `chipid`, `flash`, `sram`, `dev-type` from
stlink src/st-info/info.c.

A log that also contains erase or download is still parsed, and marked.
This module does not run those commands.
"""

from __future__ import annotations

import re

from .usb_read import ReadOnlyError


_CUBE = re.compile(r"^([A-Za-z][A-Za-z0-9 \-]*?)\s*:\s*(.*?)\s*$")
_ST = re.compile(
    r"^\s*(version|serial|flash|sram|chipid|dev-type|descr|voltage)\s*:\s*(.*?)\s*$",
    re.IGNORECASE,
)
_FLASH = re.compile(r"^(\d+)\s+\(pagesize:\s*(\d+)\)$")

CUBE_KEYS = {
    "ST-LINK SN": "stlink_sn",
    "ST-LINK FW": "stlink_fw",
    "Board": "board",
    "Voltage": "voltage",
    "SWD freq": "swd_freq",
    "Connect mode": "connect_mode",
    "Reset mode": "reset_mode",
    "Device ID": "device_id",
    "Revision ID": "revision_id",
    "Device name": "device_name",
    "Flash size": "flash_size",
    "Device type": "device_type",
    "Device CPU": "device_cpu",
    "BL Version": "bl_version",
}

_WRITE = (
    "erasing memory",
    "download in progress",
    "memory programming",
    "programming complete",
    "--erase",
    "--download",
)


def assert_readonly_programmer(command: str) -> str:
    """Allow a connect or an st-info read. Refuse erase, download and start."""
    text = command.strip()
    if not text:
        raise ReadOnlyError("пустая команда программатора")
    lowered = text.lower()
    if any(mark in lowered for mark in ("--erase", "--download", "--write", "--start", "-w ", "-e ", "erase all")):
        raise ReadOnlyError(f"команда меняет память STM32: {text}")
    head = lowered.split()[0]
    if "stm32_programmer_cli" in head:
        if "--connect" not in lowered:
            raise ReadOnlyError("у STM32_Programmer_CLI разрешён только --connect без записи")
        return text
    if head == "st-info":
        flags = {part.split("=", 1)[0] for part in lowered.split() if part.startswith("--")}
        reads = {"--probe", "--chipid", "--descr", "--flash", "--sram", "--serial"}
        modifiers = {"--connect-under-reset", "--hot-plug", "--freq", "--remote"}
        if not flags & reads or flags - reads - modifiers:
            raise ReadOnlyError(f"команда st-info не из списка чтения: {text}")
        return text
    raise ReadOnlyError(f"команда программатора не из списка чтения: {head}")


def parse_stm32_log(text: str) -> dict | None:
    cube: dict[str, str] = {}
    probe: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.rstrip()
        cube_match = _CUBE.match(line.strip())
        if cube_match and cube_match.group(1) in CUBE_KEYS:
            cube[CUBE_KEYS[cube_match.group(1)]] = cube_match.group(2)
            continue
        st_match = _ST.match(line)
        if not st_match:
            continue
        name = st_match.group(1).lower()
        value = st_match.group(2)
        if name == "flash":
            sized = _FLASH.match(value)
            if sized:
                probe["flash_bytes"] = sized.group(1)
                probe["page_size"] = sized.group(2)
            else:
                probe["flash"] = value
        elif name == "sram":
            probe["sram_bytes"] = value.split()[0]
        elif name == "voltage" and value.endswith("mV"):
            probe["voltage_mv"] = value[:-2].strip()
        elif name == "descr":
            probe["dev_type"] = value
        elif name == "dev-type":
            probe["dev_type"] = value
        else:
            probe[name] = value
    if not cube and not probe:
        return None
    found: dict[str, object] = {}
    if cube:
        found["cubeprogrammer"] = cube
    if probe:
        found["st_info"] = probe
    found["log_contains_write"] = any(mark in text.lower() for mark in _WRITE)
    return found
