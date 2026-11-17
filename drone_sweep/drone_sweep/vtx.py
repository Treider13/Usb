"""Betaflight video table, as printed by `dump all`.

`vtxtable band` is 1-based and lists frequencies in MHz. That is
src/main/cli/cli.c, format `vtxtable band %d %s %c FACTORY|CUSTOM <MHz>...`.

`vtx` lines are aux switch rules, not the channel that is selected now:
`vtx <index> <aux> <band> <channel> <power> <start us> <end us>`.

The selected channel is `vtx_band`, `vtx_channel`, `vtx_power` and, when
it is not zero, `vtx_freq`. Band and channel in those settings are
1-based, the same numbers as in the table lines. Zero means unset.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


_BAND = re.compile(
    r"^vtxtable band (\d+) (\S+) (\S) (FACTORY|CUSTOM)((?:\s+\d+)*)$",
    re.IGNORECASE,
)
_POWER_VALUES = re.compile(r"^vtxtable powervalues((?:\s+\d+)*)$", re.IGNORECASE)
_POWER_LABELS = re.compile(r"^vtxtable powerlabels((?:\s+\S+)*)$", re.IGNORECASE)
_VTX = re.compile(r"^vtx (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)$", re.IGNORECASE)


@dataclass
class VideoGrid:
    bands: dict[int, dict] = field(default_factory=dict)
    power_mw: list[int] = field(default_factory=list)
    power_labels: list[str] = field(default_factory=list)

    def frequency(self, band: int, channel: int) -> int | None:
        if band < 1 or channel < 1:
            return None
        row = self.bands.get(band)
        if row is None:
            return None
        freqs = row["frequencies_mhz"]
        if channel > len(freqs):
            return None
        return freqs[channel - 1]

    def power(self, level: int) -> dict | None:
        if level < 1 or level > len(self.power_mw):
            return None
        label = self.power_labels[level - 1] if level <= len(self.power_labels) else ""
        return {"index": level, "mw": self.power_mw[level - 1], "label": label}


def parse_video_grid(lines: list[str]) -> VideoGrid:
    grid = VideoGrid()
    for raw in lines:
        line = raw.strip()
        band = _BAND.match(line)
        if band:
            freqs = [int(part) for part in band.group(5).split()]
            grid.bands[int(band.group(1))] = {
                "name": band.group(2),
                "letter": band.group(3),
                "factory": band.group(4).upper() == "FACTORY",
                "frequencies_mhz": freqs,
            }
            continue
        powers = _POWER_VALUES.match(line)
        if powers:
            grid.power_mw = [int(part) for part in powers.group(1).split()]
            continue
        labels = _POWER_LABELS.match(line)
        if labels:
            grid.power_labels = labels.group(1).split()
    return grid


def parse_vtx_rules(lines: list[str], grid: VideoGrid) -> list[dict]:
    rules = []
    for raw in lines:
        match = _VTX.match(raw.strip())
        if not match:
            continue
        index, aux, band, channel, power, start, end = (int(part) for part in match.groups())
        rules.append(
            {
                "index": index,
                "aux_channel": aux,
                "band": band,
                "channel": channel,
                "power_index": power,
                "range_start_us": start,
                "range_end_us": end,
                "frequency_mhz": grid.frequency(band, channel),
                "power": grid.power(power),
            }
        )
    return rules


def selected_channel(settings: dict[str, str], grid: VideoGrid) -> dict:
    """The channel saved in vtx_band / vtx_channel / vtx_freq."""
    def integer(name: str) -> int | None:
        raw = settings.get(name)
        if raw is None or raw == "":
            return None
        return int(raw)

    band = integer("vtx_band")
    channel = integer("vtx_channel")
    power = integer("vtx_power")
    freq = integer("vtx_freq")
    result: dict = {
        "band": band,
        "channel": channel,
        "power_index": power,
        "vtx_freq_mhz": freq,
        "frequency_mhz": None,
        "frequency_source": None,
        "power": grid.power(power) if power is not None else None,
    }
    if freq not in (None, 0):
        result["frequency_mhz"] = freq
        result["frequency_source"] = "vtx_freq"
        return result
    if band is None or channel is None:
        return result
    looked = grid.frequency(band, channel)
    if looked is not None:
        result["frequency_mhz"] = looked
        result["frequency_source"] = "vtxtable"
    return result
