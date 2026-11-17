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


# libraries/AP_Logger/AP_Logger.h, enum class LogEvent. Numbers are stable
# so an old .BIN still names the same event.
LOG_EVENT = {
    10: "ARMED",
    11: "DISARMED",
    15: "AUTO_ARMED",
    17: "LAND_COMPLETE_MAYBE",
    18: "LAND_COMPLETE",
    19: "LOST_GPS",
    21: "FLIP_START",
    22: "FLIP_END",
    25: "SET_HOME",
    26: "SET_SIMPLE_ON",
    27: "SET_SIMPLE_OFF",
    28: "NOT_LANDED",
    29: "SET_SUPERSIMPLE_ON",
    30: "AUTOTUNE_INITIALISED",
    31: "AUTOTUNE_OFF",
    32: "AUTOTUNE_RESTART",
    33: "AUTOTUNE_SUCCESS",
    34: "AUTOTUNE_FAILED",
    35: "AUTOTUNE_REACHED_LIMIT",
    36: "AUTOTUNE_PILOT_TESTING",
    37: "AUTOTUNE_SAVEDGAINS",
    38: "SAVE_TRIM",
    39: "SAVEWP_ADD_WP",
    41: "FENCE_ENABLE",
    42: "FENCE_DISABLE",
    43: "ACRO_TRAINER_OFF",
    44: "ACRO_TRAINER_LEVELING",
    45: "ACRO_TRAINER_LIMITED",
    46: "GRIPPER_GRAB",
    47: "GRIPPER_RELEASE",
    49: "PARACHUTE_DISABLED",
    50: "PARACHUTE_ENABLED",
    51: "PARACHUTE_RELEASED",
    52: "LANDING_GEAR_DEPLOYED",
    53: "LANDING_GEAR_RETRACTED",
    54: "MOTORS_EMERGENCY_STOPPED",
    55: "MOTORS_EMERGENCY_STOP_CLEARED",
    56: "MOTORS_INTERLOCK_DISABLED",
    57: "MOTORS_INTERLOCK_ENABLED",
    58: "ROTOR_RUNUP_COMPLETE",
    59: "ROTOR_SPEED_BELOW_CRITICAL",
    60: "EKF_ALT_RESET",
    61: "LAND_CANCELLED_BY_PILOT",
    62: "EKF_YAW_RESET",
    63: "AVOIDANCE_ADSB_ENABLE",
    64: "AVOIDANCE_ADSB_DISABLE",
    65: "AVOIDANCE_PROXIMITY_ENABLE",
    66: "AVOIDANCE_PROXIMITY_DISABLE",
    67: "GPS_PRIMARY_CHANGED",
    71: "ZIGZAG_STORE_A",
    72: "ZIGZAG_STORE_B",
    73: "LAND_REPO_ACTIVE",
    74: "STANDBY_ENABLE",
    75: "STANDBY_DISABLE",
    76: "FENCE_ALT_MAX_ENABLE",
    77: "FENCE_ALT_MAX_DISABLE",
    78: "FENCE_CIRCLE_ENABLE",
    79: "FENCE_CIRCLE_DISABLE",
    80: "FENCE_ALT_MIN_ENABLE",
    81: "FENCE_ALT_MIN_DISABLE",
    82: "FENCE_POLYGON_ENABLE",
    83: "FENCE_POLYGON_DISABLE",
    85: "EK3_SOURCES_SET_TO_PRIMARY",
    86: "EK3_SOURCES_SET_TO_SECONDARY",
    87: "EK3_SOURCES_SET_TO_TERTIARY",
    90: "AIRSPEED_PRIMARY_CHANGED",
    163: "SURFACED",
    164: "NOT_SURFACED",
    165: "BOTTOMED",
    166: "NOT_BOTTOMED",
    167: "EKF_MAG_OFFSETS_SAVED",
}

# libraries/AP_Logger/AP_Logger.h, enum class LogErrorSubsystem.
LOG_ERROR_SUBSYSTEM = {
    1: "MAIN",
    2: "RADIO",
    3: "COMPASS",
    4: "OPTFLOW",
    5: "FAILSAFE_RADIO",
    6: "FAILSAFE_BATT",
    7: "FAILSAFE_GPS",
    8: "FAILSAFE_GCS",
    9: "FAILSAFE_FENCE",
    10: "FLIGHT_MODE",
    11: "GPS",
    12: "CRASH_CHECK",
    13: "FLIP",
    14: "AUTOTUNE",
    15: "PARACHUTES",
    16: "EKFCHECK",
    17: "FAILSAFE_EKFINAV",
    18: "BARO",
    19: "CPU",
    20: "FAILSAFE_ADSB",
    21: "TERRAIN",
    22: "NAVIGATION",
    23: "FAILSAFE_TERRAIN",
    24: "EKF_PRIMARY",
    25: "THRUST_LOSS_CHECK",
    26: "FAILSAFE_SENSORS",
    27: "FAILSAFE_LEAK",
    28: "PILOT_INPUT",
    29: "FAILSAFE_VIBE",
    30: "INTERNAL_ERROR",
    31: "FAILSAFE_DEADRECKON",
}


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
