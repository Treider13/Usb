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


def inav_saved_frequency(settings: dict[str, str]) -> tuple[int | None, str]:
    """Frequency from INAV's compiled tables in src/main/io/vtx_string.c.

    vtx_tramp.c looks up 5.8 GHz unless frequencyGroup is FREQUENCYGROUP_1G3.
    FREQUENCYGROUP_2G4 has no MHz table on that path. Band and channel are 1-based.
    Power stays an index: milliwatts come from the VTX reply, which a dump does not contain.
    """
    def integer(name: str) -> int | None:
        raw = settings.get(name)
        if raw is None or str(raw).strip() == "":
            return None
        text = str(raw).strip()
        if text.upper() == "FREQUENCYGROUP_5G8":
            return 0
        if text.upper() == "FREQUENCYGROUP_2G4":
            return 1
        if text.upper() == "FREQUENCYGROUP_1G3":
            return 2
        return int(text)

    freq = integer("vtx_freq")
    if freq not in (None, 0):
        return freq, "dump vtx_freq"
    band = integer("vtx_band")
    channel = integer("vtx_channel")
    if band is None or channel is None:
        return None, "в дампе INAV нет vtx_band и vtx_channel"
    group = integer("vtx_frequency_group")
    if group is None:
        group = 0
    table = _INAV_1G3 if group == 2 else None if group == 1 else _INAV_58
    if table is None:
        return None, "vtx_frequency_group = FREQUENCYGROUP_2G4. В vtx_tramp.c для этой группы нет таблицы МГц. Таблица FFPV относится к другому протоколу и сюда не подставляется."
    if band < 1 or channel < 1 or band > len(table) or channel > len(table[band - 1]):
        return None, "vtx_band/vtx_channel вне таблицы INAV для этой группы"
    source = "inav vtx_string.c vtx1G3frequencyTable" if group == 2 else "inav vtx_string.c vtx58frequencyTable"
    if integer("vtx_frequency_group") is None:
        source += ", группа в дампе не задана, у прошивки значение по умолчанию 5.8"
    return table[band - 1][channel - 1], source


def inav_grid(group: int) -> dict | None:
    table = _INAV_1G3 if group == 2 else _INAV_58 if group in (0, None) else None
    if table is None:
        return None
    names = ("A", "B") if group == 2 else ("A", "B", "E", "F", "R")
    return {
        str(index + 1): {"name": names[index], "frequencies_mhz": list(row)}
        for index, row in enumerate(table)
    }


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


# vtx58frequencyTable and vtx1G3frequencyTable from INAV src/main/io/vtx_string.c.
# Indexes here are 0-based; the settings vtx_band and vtx_channel are 1-based.
_INAV_58 = (
    (5865, 5845, 5825, 5805, 5785, 5765, 5745, 5725),
    (5733, 5752, 5771, 5790, 5809, 5828, 5847, 5866),
    (5705, 5685, 5665, 5645, 5885, 5905, 5925, 5945),
    (5740, 5760, 5780, 5800, 5820, 5840, 5860, 5880),
    (5658, 5695, 5732, 5769, 5806, 5843, 5880, 5917),
)
_INAV_1G3 = (
    (1080, 1120, 1160, 1200, 1240, 1280, 1320, 1360),
    (1080, 1120, 1160, 1200, 1258, 1280, 1320, 1360),
)
