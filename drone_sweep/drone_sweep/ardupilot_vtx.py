"""ArduPilot video-channel table.

Copied from libraries/AP_VideoTX/AP_VideoTX.cpp, array VIDEO_CHANNELS.
Band and channel parameters are zero-based indexes into this array.
VTX_FREQ, when the firmware has written it, is the stored frequency in
MHz and is kept beside the table lookup. VTX_POWER is milliwatts.
VTX_OPTIONS bit 0 is the configured pit-mode bit, not a live reply.
"""

from __future__ import annotations

# Band index matches the parameter metadata:
# 0 A, 1 B, 2 E, 3 Airwave, 4 Race, 5 LO Race,
# 6 1G3 A, 7 1G3 B, 8 X, 9 3G3 A, 10 3G3 B.
VIDEO_CHANNELS_MHZ: tuple[tuple[int, ...], ...] = (
    (5865, 5845, 5825, 5805, 5785, 5765, 5745, 5725),
    (5733, 5752, 5771, 5790, 5809, 5828, 5847, 5866),
    (5705, 5685, 5665, 5645, 5885, 5905, 5925, 5945),
    (5740, 5760, 5780, 5800, 5820, 5840, 5860, 5880),
    (5658, 5695, 5732, 5769, 5806, 5843, 5880, 5917),
    (5362, 5399, 5436, 5473, 5510, 5547, 5584, 5621),
    (1080, 1120, 1160, 1200, 1240, 1280, 1320, 1360),
    (1080, 1120, 1160, 1200, 1258, 1280, 1320, 1360),
    (4990, 5020, 5050, 5080, 5110, 5140, 5170, 5200),
    (3330, 3350, 3370, 3390, 3410, 3430, 3450, 3470),
    (3170, 3190, 3210, 3230, 3250, 3270, 3290, 3310),
)

BAND_NAMES = (
    "A",
    "B",
    "E",
    "Airwave",
    "Race",
    "LO Race",
    "1G3 A",
    "1G3 B",
    "X",
    "3G3 A",
    "3G3 B",
)


def table_frequency(band: int, channel: int) -> int | None:
    if band < 0 or channel < 0:
        return None
    if band >= len(VIDEO_CHANNELS_MHZ) or channel >= len(VIDEO_CHANNELS_MHZ[band]):
        return None
    return VIDEO_CHANNELS_MHZ[band][channel]


def describe(params: dict) -> dict | None:
    """Return the saved VTX parameters. None when the log has no VTX_* keys."""
    names = [name for name in params if name.startswith("VTX_")]
    if not names:
        return None
    band = params.get("VTX_BAND")
    channel = params.get("VTX_CHANNEL")
    freq = params.get("VTX_FREQ")
    power = params.get("VTX_POWER")
    options = params.get("VTX_OPTIONS")
    looked = None
    if band is not None and channel is not None:
        looked = table_frequency(int(band), int(channel))
    stored = int(freq) if freq not in (None, "") else None
    pit = None
    if options is not None:
        pit = bool(int(options) & 1)
    return {
        "band": None if band is None else int(band),
        "band_name": None if band is None or int(band) >= len(BAND_NAMES) else BAND_NAMES[int(band)],
        "channel": None if channel is None else int(channel),
        "table_frequency_mhz": looked,
        "stored_frequency_mhz": stored if stored else None,
        "power_mw": None if power is None else int(power),
        "pitmode_bit": pit,
        "frequencies_agree": stored in (None, 0, looked),
    }
