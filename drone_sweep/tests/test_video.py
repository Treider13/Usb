"""Video grid and the separate packet-rate facts.

Frequencies are taken from the firmware tables, not from a guessed
5.8 GHz list. Packet-rate numbers stay on the field that produced them.
"""

from pathlib import Path

from drone_sweep.ardupilot_vtx import table_frequency
from drone_sweep.assemble import Inputs, assemble
from drone_sweep.vtx import parse_video_grid, parse_vtx_rules, selected_channel
from tests.bin_builder import write_bin


FACTORY_A = "5865 5845 5825 5805 5785 5765 5745 5725"


def _parm(time_us: int, name: str, value: float) -> tuple:
    return ("PARM", "QNf", "TimeUS,Name,Value", (time_us, name.encode("ascii"), value))


def _rcin(time_us: int) -> tuple:
    return (
        "RCIN",
        "Q" + "h" * 14,
        "TimeUS," + ",".join(f"C{i}" for i in range(1, 15)),
        (time_us, *([1500] * 14)),
    )


def _dump(**settings: str) -> str:
    lines = [
        "# Betaflight / STM32F405 (S405) 4.5.0 Jan 01 2025 / GIT",
        "vtxtable bands 1",
        "vtxtable channels 8",
        f"vtxtable band 1 BOSCAM_A A FACTORY {FACTORY_A}",
        "vtxtable powerlevels 3",
        "vtxtable powervalues 25 100 200",
        "vtxtable powerlabels 25 100 200",
        "vtx 0 0 1 3 1 900 2100",
    ]
    for key, value in settings.items():
        lines.append(f"set {key} = {value}")
    return "\n".join(lines) + "\n"


def test_betaflight_table_is_one_based_and_vtx_line_is_an_aux_rule():
    grid = parse_video_grid(_dump().splitlines())
    assert grid.frequency(1, 1) == 5865
    assert grid.frequency(1, 8) == 5725
    assert grid.frequency(1, 9) is None
    assert grid.power(2) == {"index": 2, "mw": 100, "label": "100"}
    rules = parse_vtx_rules(["vtx 0 0 1 3 1 900 2100"], grid)
    assert rules[0]["frequency_mhz"] == 5825
    assert rules[0]["aux_channel"] == 0
    selected = selected_channel({"vtx_band": "1", "vtx_channel": "1", "vtx_power": "2", "vtx_freq": "0"}, grid)
    assert selected["frequency_mhz"] == 5865
    assert selected["frequency_source"] == "vtxtable"


def test_betaflight_card_uses_vtx_freq_when_it_is_set():
    card = assemble(Inputs(dump_text=_dump(vtx_band="1", vtx_channel="1", vtx_power="2", vtx_freq="5900")))
    assert card.fields["video_frequency_mhz"].value == 5900
    assert card.fields["video_frequency_mhz"].source == "dump vtx_freq"
    assert card.fields["video_power"].value["mw"] == 100
    assert card.fields["vtx_switch_rules"].value[0]["frequency_mhz"] == 5825
    assert card.fields["vtx_device_responded"].status == "missing"
    assert "ответ" in card.fields["video_frequency_mhz"].reason


def test_betaflight_missing_cell_is_not_filled_from_a_stock_table():
    card = assemble(Inputs(dump_text=_dump(vtx_band="1", vtx_channel="9", vtx_freq="0")))
    assert card.fields["video_frequency_mhz"].status == "missing"
    assert card.fields["video_grid"].value["bands"][1]["frequencies_mhz"][0] == 5865


def test_ardupilot_table_matches_ap_videotx_band_a_channel_zero():
    assert table_frequency(0, 0) == 5865
    assert table_frequency(4, 0) == 5658
    assert table_frequency(8, 7) == 5200
    assert table_frequency(10, 7) == 3310
    assert table_frequency(11, 0) is None


def test_ardupilot_vtx_freq_wins_and_a_mismatch_is_kept(tmp_path: Path):
    path = tmp_path / "vtx.bin"
    write_bin(
        path,
        [
            _parm(1, "VTX_ENABLE", 0),
            _parm(1, "VTX_BAND", 0),
            _parm(1, "VTX_CHANNEL", 0),
            _parm(1, "VTX_FREQ", 5000),
            _parm(1, "VTX_POWER", 25),
            _parm(1, "VTX_OPTIONS", 1),
            _rcin(1_000_000),
            _rcin(1_020_000),
            _rcin(1_040_000),
        ],
    )
    card = assemble(Inputs(bin_path=path))
    assert card.fields["video_frequency_mhz"].value == 5000
    assert card.fields["video_frequency_mhz"].source == "bin PARM VTX_FREQ"
    assert card.fields["video_grid_lookup"].value["table_frequency_mhz"] == 5865
    assert card.fields["video_power_mw"].value == 25
    assert card.fields["vtx_pitmode_configured"].value is True
    assert card.fields["vtx_device_responded"].status == "missing"
    assert any("не совпали" in hole for hole in card.holes)
    assert card.fields["rcin_interval_us"].value == 20_000
    assert "не пакетрейт" in card.fields["rcin_interval_us"].reason
    assert "packet_rate_log_hz" not in card.fields


def test_ardupilot_uses_the_table_when_vtx_freq_is_zero(tmp_path: Path):
    path = tmp_path / "table.bin"
    write_bin(
        path,
        [
            _parm(1, "VTX_BAND", 0),
            _parm(1, "VTX_CHANNEL", 1),
            _parm(1, "VTX_FREQ", 0),
        ],
    )
    card = assemble(Inputs(bin_path=path))
    assert card.fields["video_frequency_mhz"].value == 5845
    assert card.fields["video_frequency_mhz"].source == "AP_VideoTX VIDEO_CHANNELS"
    assert not any("не совпали" in hole for hole in card.holes)


def test_packet_rate_fields_are_not_copied_onto_each_other(tmp_path: Path):
    blackbox = tmp_path / "flight.bbl"
    blackbox.write_text("H rc_smoothing_rx_smoothed:250\n", encoding="ascii")
    card = assemble(
        Inputs(
            dump_text=_dump(),
            blackbox_path=blackbox,
            radio_json={
                "version": "MILELRS_v437",
                "BINDING_RATE": "44",
                "rateInitialIdx": "3",
            },
        )
    )
    assert card.fields["packet_rate_log_hz"].value == "250"
    assert card.fields["radio_binding_rate"].value == "44"
    assert card.fields["radio_rateinitialidx"].value == "3"
    assert "не измеренный пакетрейт" in card.fields["radio_binding_rate"].reason
    assert "не частота этого вылета" in card.fields["radio_rateinitialidx"].reason
    assert card.fields["packet_rate_log_hz"].value != card.fields["radio_binding_rate"].value
    tx = assemble(
        Inputs(
            radio_json={"firmware": "ExpressLRS", "tx_packet_rate": "6"},
        )
    )
    assert tx.fields["radio_tx_packet_rate"].value == "6"
    assert "не частота из лога" in tx.fields["radio_tx_packet_rate"].reason
    assert "packet_rate_log_hz" not in tx.fields
