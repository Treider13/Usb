"""Labels taken from ArduPilot Copter 4.5 parameter metadata.

RC_PROTOCOLS bit 0 is All, so the stored value 1 means every protocol is
enabled. That is the bitmask, not "PPM". The bit positions are the ones
published for Copter 4.5 (bit 0 All, bit 1 PPM, bit 3 SBUS, bit 9 CRSF).

MNT1_TYPE 8 is Siyi. MNT1_TYPE 4 is SToRM32 MAVLink. Those stay different
facts from a nameplate that says SToRM32.

CAM1_TYPE 4 is the camera enum value Mount. The official Siyi page tells
the operator to set CAM1_TYPE to 4 to drive the camera through the mount.
The number is not a second copy of the gimbal nameplate.
"""

from __future__ import annotations


RC_PROTOCOL_BITS_45 = (
    "All",
    "PPM",
    "IBUS",
    "SBUS",
    "SBUS_NI",
    "DSM",
    "SUMD",
    "SRXL",
    "SRXL2",
    "CRSF",
    "ST24",
    "FPORT",
    "FPORT2",
    "FastSBUS",
)

# libraries/AP_Mount, values published with Copter 4.5.
MOUNT_TYPE_45 = {
    0: "None",
    1: "Servo",
    2: "Solo",
    3: "Alexmos",
    4: "SToRM32 MAVLink",
    5: "SToRM32 Serial",
    6: "Gremsy",
    7: "BrushlessPWM",
    8: "Siyi",
}

# CAM_TYPE in Copter 4.5. Value 4 is Mount.
CAMERA_TYPE_45 = {
    0: "None",
    1: "Servo",
    2: "Relay",
    3: "Servo and relay",
    4: "Mount",
    5: "MAVLink",
    6: "MAVLinkCamV2",
    7: "Scripting",
}

# AP_GPS fix status. A track requires 3D or better.
GPS_FIX_3D = 3

# AP_Logger LogEvent values used by Copter 4.5.
EV_ARMED = 10
EV_DISARMED = 11

# ORGN.Type in AP_AHRS.
ORGN_EKF = 0
ORGN_HOME = 1


def rc_protocols_45(value: int) -> list[str]:
    """Decode RC_PROTOCOLS the way Copter 4.5 stores the mask."""
    if value < 0:
        raise ValueError(value)
    if value & 1:
        return ["All"]
    names = []
    for bit, name in enumerate(RC_PROTOCOL_BITS_45):
        if bit == 0:
            continue
        if value & (1 << bit):
            names.append(name)
    return names
