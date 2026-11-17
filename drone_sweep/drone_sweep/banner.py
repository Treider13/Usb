"""ArduPilot boot lines, the ones GCS_Common::send_banner and Copter send.

The board prints them itself. A line that does not match is left as text.
Words for the frame come from AP_Motors_Class.h and the strings
AP_MotorsMatrix writes into the banner, for example QUAD and X.
"""

from __future__ import annotations

import re


_FIRMWARE = re.compile(
    r"^(ArduCopter|ArduPlane|ArduRover|ArduSub|AntennaTracker|Blimp)"
    r"\s+V\d+\.\d+\.\d+(?:[-.][A-Za-z0-9]+)*(?:\s+\([0-9a-fA-F]+\))?$"
)
_OS = re.compile(
    r"^(?:[A-Za-z0-9]+:\s*[0-9a-fA-F]+\s+)?(?:ChibiOS|Linux|NuttX|FreeRTOS):\s*[0-9a-fA-F]+$"
)
_BOARD = re.compile(
    r"^([A-Za-z][A-Za-z0-9_.-]{1,22}) ((?:[0-9A-Fa-f]{8} ){2}[0-9A-Fa-f]{8})$"
)
_FRAME = re.compile(r"^Frame:\s*(\S+)$")
_RCOUT = re.compile(r"^RCOut:\s*(.+)$")
_IMU = re.compile(r"^IMU(\d+):\s*(normal|fast) sampling (\S+)$")
_IOMCU = re.compile(r"^IOMCU:\s*(.+)$")

# motor_frame_class in AP_Motors_Class.h. The token is what the banner prints.
_CLASS_BY_NUMBER = {
    1: "QUAD",
    2: "HEXA",
    3: "OCTA",
    4: "OCTAQUAD",
    5: "Y6",
    6: "HELI",
    7: "TRI",
    8: "SINGLE",
    9: "COAX",
    10: "TAILSITTER",
    11: "HELI_DUAL",
    12: "DODECAHEXA",
    13: "HELI_QUAD",
    14: "DECA",
    15: "SCRIPTING",
    16: "6DOF",
    17: "DYNAMIC",
}
# motor_frame_type. 18 prints X_REV, the string in AP_MotorsMatrix, not the enum name.
_TYPE_BY_NUMBER = {
    0: "PLUS",
    1: "X",
    2: "V",
    3: "H",
    4: "VTAIL",
    5: "ATAIL",
    6: "PLUSREV",
    10: "Y6B",
    11: "Y6F",
    12: "BF_X",
    13: "DJI_X",
    14: "CW_X",
    15: "I",
    16: "NYT_PLUS",
    17: "NYT_X",
    18: "X_REV",
    19: "Y4",
    20: "X_COR",
    21: "CW_X_COR",
}

_CLASS_WORD = {
    "QUAD": "квадрокоптер",
    "HEXA": "гексакоптер",
    "OCTA": "октокоптер",
    "OCTAQUAD": "октоквад",
    "Y6": "Y6",
    "HELI": "вертолёт",
    "TRI": "трикоптер",
    "SINGLE": "одномоторный",
    "COAX": "соосный",
    "TAILSITTER": "тейлситтер",
    "HELI_DUAL": "вертолёт, два ротора",
    "DODECAHEXA": "12 моторов",
    "HELI_QUAD": "вертолёт на квадросхеме",
    "DECA": "декакоптер",
    "SCRIPTING": "схема из скрипта",
    "6DOF": "6 степеней",
    "DYNAMIC": "динамическая схема",
}
_TYPE_WORD = {
    "PLUS": "схема плюс",
    "X": "схема X",
    "+": "схема плюс",
    "V": "схема V",
    "H": "схема H",
    "VTAIL": "V-хвост",
    "ATAIL": "A-хвост",
    "PLUSREV": "схема плюс, моторы наоборот",
    "Y6B": "Y6B",
    "Y6F": "Y6F",
    "BF_X": "схема X, порядок Betaflight",
    "DJI_X": "схема X, порядок DJI",
    "CW_X": "схема X, по часовой",
    "I": "схема I",
    "NYT_PLUS": "схема плюс без дифференциала",
    "NYT_X": "схема X без дифференциала",
    "X_REV": "схема X, моторы наоборот",
    "Y4": "Y4",
    "X_COR": "схема X, соосные",
    "CW_X_COR": "схема X, соосные, по часовой",
    "X/CW_X": "схема X, по часовой",
}

# MAV_TYPE from HEARTBEAT when the board did not send Frame.
_MAV_TYPE_WORD = {
    1: "самолёт",
    2: "квадрокоптер",
    3: "соосный",
    4: "вертолёт",
    10: "машина",
    11: "лодка",
    12: "подлодка",
    13: "гексакоптер",
    14: "октокоптер",
    15: "трикоптер",
    19: "СВВП",
    20: "квадрокоптер, два мотора вперёд",
    21: "октокоптер, четыре мотора вперёд",
    22: "гексакоптер, два мотора вперёд",
}


def mav_type_word(number: int) -> str | None:
    return _MAV_TYPE_WORD.get(number)


def frame_from_params(frame_class: int, frame_type: int | None) -> tuple[str, str] | None:
    """Return (plain words, raw token) from FRAME_CLASS and FRAME_TYPE."""
    klass = _CLASS_BY_NUMBER.get(frame_class)
    if klass is None:
        return None
    if frame_type is None:
        word = _CLASS_WORD.get(klass)
        if word is None:
            return None
        return word, klass
    token = _TYPE_BY_NUMBER.get(frame_type)
    if token is None:
        return None
    raw = f"{klass}/{token}"
    return _words(klass, token, raw), raw


def describe_frame(raw: str) -> str:
    """Plain words for a Frame line. Unknown tokens stay as the board wrote them."""
    text = raw.strip()
    if "/" not in text:
        word = _CLASS_WORD.get(text)
        return word or text
    klass, token = text.split("/", 1)
    return _words(klass, token, text)


def _words(klass: str, token: str, raw: str) -> str:
    left = _CLASS_WORD.get(klass)
    right = _TYPE_WORD.get(token)
    if left and right:
        return f"{left}, {right}"
    if left:
        return f"{left}, {token}"
    if right:
        return f"{klass}, {right}"
    return raw


def parse_banner_lines(lines: list[str]) -> dict:
    """Split boot lines. Unmatched lines stay in rest, nothing is invented."""
    found: dict = {
        "firmware": None,
        "board_name": None,
        "mcu_id": None,
        "frame_raw": None,
        "frame": None,
        "os": None,
        "outputs": None,
        "imu": [],
        "iomcu": None,
        "rest": [],
    }
    for raw in lines:
        line = " ".join(str(raw).split())
        if not line:
            continue
        if _FIRMWARE.match(line):
            found["firmware"] = line
            continue
        if _OS.match(line):
            found["os"] = line
            continue
        if line.startswith("Frame:"):
            match = _FRAME.match(line)
            if match is None:
                found["rest"].append(line)
                continue
            token = match.group(1)
            found["frame_raw"] = token
            found["frame"] = describe_frame(token)
            continue
        match = _RCOUT.match(line)
        if match:
            found["outputs"] = match.group(1).strip()
            continue
        match = _IMU.match(line)
        if match:
            speed = "обычная выборка" if match.group(2) == "normal" else "быстрая выборка"
            found["imu"].append(f"IMU{match.group(1)}: {speed} {match.group(3)}")
            continue
        match = _IOMCU.match(line)
        if match:
            found["iomcu"] = match.group(1).strip()
            continue
        match = _BOARD.match(line)
        if match:
            found["board_name"] = match.group(1)
            found["mcu_id"] = match.group(2)
            continue
        found["rest"].append(line)
    return found
