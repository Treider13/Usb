"""Which UART carries the receiver, taken from the firmware's own printout.

Betaflight 4.5 prints `serial <identifier> <functionMask> <msp> <gps> <telemetry> <blackbox>`.
The identifier values and the function bits are `serialPortIdentifier_e` and
`serialPortFunction_e` in src/main/io/serial.h on the 4.5-maintenance branch.
Baud 0 is `BAUD_AUTO`: `baudRates[0]` is 0.

ArduPilot Copter 4.5 stores `SERIALn_PROTOCOL` as `AP_SerialManager::SerialProtocol`
in libraries/AP_SerialManager/AP_SerialManager.h. `SERIALn_BAUD` is mapped by
`AP_SerialManager::map_baudrate`.
"""

from __future__ import annotations

import re


# identifier -> name printed by the 4.5 enum, not a later rename.
BF_PORT_NAMES = {
    0: "USART1",
    1: "USART2",
    2: "USART3",
    3: "UART4",
    4: "UART5",
    5: "USART6",
    6: "USART7",
    7: "USART8",
    8: "UART9",
    9: "USART10",
    20: "USB_VCP",
    30: "SOFTSERIAL1",
    31: "SOFTSERIAL2",
    40: "LPUART1",
}

# bit -> name. Bit 8 is unused in the 4.5 enum, so it is not named here.
BF_FUNCTION_BITS = (
    (0, "MSP"),
    (1, "GPS"),
    (2, "TELEMETRY_FRSKY_HUB"),
    (3, "TELEMETRY_HOTT"),
    (4, "TELEMETRY_LTM"),
    (5, "TELEMETRY_SMARTPORT"),
    (6, "RX_SERIAL"),
    (7, "BLACKBOX"),
    (9, "TELEMETRY_MAVLINK"),
    (10, "ESC_SENSOR"),
    (11, "VTX_SMARTAUDIO"),
    (12, "TELEMETRY_IBUS"),
    (13, "VTX_TRAMP"),
    (14, "RCDEVICE"),
    (15, "LIDAR_TF"),
    (16, "FRSKY_OSD"),
    (17, "VTX_MSP"),
)

_SERIAL = re.compile(r"^serial\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$", re.IGNORECASE)


def function_names(mask: int, bits: tuple[tuple[int, str], ...] = BF_FUNCTION_BITS) -> list[str]:
    names = []
    known = set()
    for bit, name in bits:
        known.add(bit)
        if mask & (1 << bit):
            names.append(name)
    for bit in range(32):
        if bit in known:
            continue
        if mask & (1 << bit):
            names.append(f"bit{bit}")
    return names


# src/main/io/serial.h on INAV master. Bit 6 is still RX_SERIAL.
# From bit 8 the names differ from Betaflight 4.5.
INAV_PORT_NAMES = {
    0: "USART1",
    1: "USART2",
    2: "USART3",
    3: "USART4",
    4: "USART5",
    5: "USART6",
    6: "USART7",
    7: "USART8",
    20: "USB_VCP",
    30: "SOFTSERIAL1",
    31: "SOFTSERIAL2",
}

INAV_FUNCTION_BITS = (
    (0, "MSP"),
    (1, "GPS"),
    (2, "UNUSED_3"),
    (3, "TELEMETRY_HOTT"),
    (4, "TELEMETRY_LTM"),
    (5, "TELEMETRY_SMARTPORT"),
    (6, "RX_SERIAL"),
    (7, "BLACKBOX"),
    (8, "TELEMETRY_MAVLINK"),
    (9, "TELEMETRY_IBUS"),
    (10, "RCDEVICE"),
    (11, "VTX_SMARTAUDIO"),
    (12, "VTX_TRAMP"),
    (13, "UNUSED_1"),
    (14, "OPTICAL_FLOW"),
    (15, "LOG"),
    (16, "RANGEFINDER"),
    (17, "VTX_FFPV"),
    (18, "ESCSERIAL"),
    (19, "TELEMETRY_SIM"),
    (20, "FRSKY_OSD"),
    (21, "DJI_HD_OSD"),
    (22, "SERVO_SERIAL"),
    (23, "TELEMETRY_SMARTPORT_MASTER"),
    (25, "MSP_OSD"),
    (26, "GIMBAL"),
    (27, "GIMBAL_HEADTRACKER"),
)


def parse_betaflight_serial(lines: list[str], family: str = "betaflight") -> list[dict]:
    inav = family == "inav"
    names = INAV_PORT_NAMES if inav else BF_PORT_NAMES
    bits = INAV_FUNCTION_BITS if inav else BF_FUNCTION_BITS
    ports = []
    for raw in lines:
        match = _SERIAL.match(raw.strip())
        if not match:
            continue
        identifier, mask, msp, gps, telemetry, blackbox = (int(part) for part in match.groups())
        ports.append(
            {
                "identifier": identifier,
                "port": names.get(identifier, f"identifier {identifier}"),
                "function_mask": mask,
                "functions": function_names(mask, bits),
                "msp_baud": msp,
                "gps_baud": gps,
                "telemetry_baud": telemetry,
                "blackbox_baud": blackbox,
                "msp_baud_auto": msp == 0,
                "gps_baud_auto": gps == 0,
                "telemetry_baud_auto": telemetry == 0,
                "blackbox_baud_auto": blackbox == 0,
            }
        )
    return ports


def decode_osd_position(value: int, family: str = "betaflight") -> dict:
    """Position bits from the firmware header.

    Betaflight 4.5 osd.h: OSD_X uses bits 0-4 and bit 10, OSD_Y uses bits 5-9.
    INAV osd.h: OSD_X is bits 0-5, OSD_Y is bits 6-11, visible is bit 13.
    """
    if family == "inav":
        return {
            "x": value & 0x3F,
            "y": (value >> 6) & 0x3F,
            "visible": bool(value & 0x2000),
            "type": None,
            "raw": value,
        }
    x = (value & 0x1F) | ((value & 0x400) >> 5)
    y = (value >> 5) & 0x1F
    return {
        "x": x,
        "y": y,
        "visible": bool(value & 0x3800),
        "type": (value & 0xC000) >> 14,
        "raw": value,
    }


# Copter 4.5 SerialProtocol. Value 47 is reserved in the header and has no name.
AP_SERIAL_PROTOCOL_45 = {
    -1: "None",
    0: "Console",
    1: "MAVLink",
    2: "MAVLink2",
    3: "FrSky_D",
    4: "FrSky_SPort",
    5: "GPS",
    6: "GPS2",
    7: "AlexMos",
    8: "Gimbal",
    9: "Rangefinder",
    10: "FrSky_SPort_Passthrough",
    11: "Lidar360",
    12: "Aerotenna_USD1",
    13: "Beacon",
    14: "Volz",
    15: "Sbus1",
    16: "ESCTelemetry",
    17: "Devo_Telem",
    18: "OpticalFlow",
    19: "Robotis",
    20: "NMEAOutput",
    21: "WindVane",
    22: "SLCAN",
    23: "RCIN",
    24: "EFI",
    25: "LTM_Telem",
    26: "RunCam",
    27: "Hott",
    28: "Scripting",
    29: "CRSF",
    30: "Generator",
    31: "Winch",
    32: "MSP",
    33: "DJI_FPV",
    34: "AirSpeed",
    35: "ADSB",
    36: "AHRS",
    37: "SmartAudio",
    38: "FETtecOneWire",
    39: "Torqeedo",
    40: "AIS",
    41: "CoDevESC",
    42: "MSP_DisplayPort",
    43: "MAVLinkHL",
    44: "Tramp",
    45: "DDS_XRCE",
    46: "IMUOUT",
    48: "PPP",
}

# Protocols whose header comment is a receiver or an RC input.
AP_RECEIVER_PROTOCOLS = {3, 4, 10, 15, 23, 29}

_AP_BAUD = {
    1: 1200,
    2: 2400,
    4: 4800,
    9: 9600,
    19: 19200,
    38: 38400,
    57: 57600,
    100: 100000,
    111: 111100,
    115: 115200,
    230: 230400,
    256: 256000,
    460: 460800,
    500: 500000,
    921: 921600,
    1500: 1500000,
    2000: 2000000,
}

_AP_PORT = re.compile(r"^SERIAL(\d+)_(PROTOCOL|BAUD)$")


def map_baudrate(rate: int) -> int:
    """AP_SerialManager::map_baudrate from Copter 4.5."""
    if rate <= 0:
        rate = 57
    if rate in _AP_BAUD:
        return _AP_BAUD[rate]
    if rate > 2000:
        return rate
    return rate * 1000


def ardupilot_ports(params: dict) -> list[dict]:
    grouped: dict[int, dict] = {}
    for name, value in params.items():
        match = _AP_PORT.match(str(name))
        if not match or value is None:
            continue
        index = int(match.group(1))
        slot = grouped.setdefault(index, {"port": f"SERIAL{index}"})
        number = int(value)
        if match.group(2) == "PROTOCOL":
            slot["protocol"] = number
            slot["protocol_name"] = AP_SERIAL_PROTOCOL_45.get(number, "unknown")
            slot["receiver"] = number in AP_RECEIVER_PROTOCOLS
        else:
            slot["baud_param"] = number
            slot["baud"] = map_baudrate(number)
    return [grouped[index] for index in sorted(grouped)]
