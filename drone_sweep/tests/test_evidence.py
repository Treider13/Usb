"""Hashes, diff all, INAV wp, a chosen ArduPilot log, and a card diff."""

import json
from pathlib import Path

from drone_sweep.assemble import Inputs, assemble
from drone_sweep.compare import diff_cards, render_diff
from drone_sweep.logs import flight_timeline
from drone_sweep.menu import main
from drone_sweep.mission_files import parse_inav_wp
from drone_sweep.report import render_html
from tests.bin_builder import write_bin
from tests.test_card import _msg
from tests.test_ports import _Board, _Entry, _LogData


WP = """\
#wp 1 valid
wp 0 1 545454545 245454545 5000 0 0 0 165
wp 1 0 0 0 0 0 0 0 0
"""

DIFF = """\
# diff all
# Betaflight / STM32F405 4.5.0
set serialrx_provider = CRSF
"""


def test_inav_wp_uses_the_cli_line_and_skips_empty_slots():
    points, note = parse_inav_wp(WP)
    assert len(points) == 1
    assert points[0]["action_name"] == "WAYPOINT"
    assert points[0]["lat"] == 54.5454545
    assert points[0]["lon"] == 24.5454545
    assert points[0]["alt_cm"] == 5000
    assert points[0]["flag_name"] == "LAST"
    assert "valid" in note
    card = assemble(Inputs(banner="INAV 7.1.0", wp_text=WP))
    assert card.fields["inav_waypoints"].value[0]["action_name"] == "WAYPOINT"
    assert card.fields["mission_file_source"].value == "inav wp"
    assert card.fields["mission_waypoints"].value[0]["lat"] == 54.5454545


def test_diff_all_keeps_only_the_printed_settings():
    card = assemble(Inputs(dump_text="# Betaflight / STM32F405 4.5.0\nset craft_name = Blink\n", diff_text=DIFF))
    assert card.fields["cli_diff"].value == {"serialrx_provider": "CRSF"}
    assert card.fields["craft_name"].value == "Blink"
    assert any(item["kind"] == "diff_all" and len(item["sha256"]) == 64 for item in card.files)
    page = render_html(card)
    assert "sha256" in page
    assert "serialrx_provider" in page


def test_empty_diff_is_a_confirmed_absence():
    card = assemble(Inputs(banner="Betaflight 4.5.0", diff_text="# diff all\n"))
    assert card.fields["cli_diff"].value == "нет отличий"


def test_blackbox_ends_are_the_csv_points(tmp_path: Path):
    csv_path = tmp_path / "gps.csv"
    csv_path.write_text(
        "GPS_coord[0],GPS_coord[1],GPS_numSat,time\n"
        "10.0,20.0,7,100\n"
        "11.0,21.0,4,200\n"
        "12.0,22.0,8,300\n",
        encoding="utf-8",
    )
    card = assemble(Inputs(gps_csv_path=csv_path))
    assert card.fields["blackbox_arm"].value["lat"] == 10.0
    assert card.fields["blackbox_disarm"].value["lat"] == 12.0
    assert card.fields["blackbox_disarm"].value["time_us"] == 300


def test_timeline_names_the_logger_events(tmp_path: Path):
    named = flight_timeline(
        [
            {"name": "EV", "TimeUS": 10, "Id": 10},
            {"name": "EV", "TimeUS": 20, "Id": 11},
            {"name": "ERR", "TimeUS": 15, "Subsys": 5, "ECode": 1},
            {"name": "MSG", "TimeUS": 16, "Message": "Failsafe throttle"},
            {"name": "MSG", "TimeUS": 17, "Message": "Armed"},
        ]
    )
    assert [item["name"] for item in named] == ["ARMED", "DISARMED", "FAILSAFE_RADIO", "Failsafe throttle"]
    path = tmp_path / "flight.BIN"
    write_bin(
        path,
        [
            ("EV", "QB", "TimeUS,Id", (10, 10)),
            ("EV", "QB", "TimeUS,Id", (30, 18)),
            _msg(20, "Failsafe GCS"),
            ("ERR", "QBB", "TimeUS,Subsys,ECode", (25, 12, 1)),
        ],
    )
    card = assemble(Inputs(bin_path=path))
    names = [item["name"] for item in card.fields["flight_timeline"].value]
    assert names == ["ARMED", "LAND_COMPLETE", "Failsafe GCS", "CRASH_CHECK"]


def test_named_log_is_downloaded_and_a_missing_id_is_not_replaced(tmp_path: Path):
    from drone_sweep.ardupilot_read import read_dataflash

    source = tmp_path / "source.BIN"
    write_bin(source, [_msg(1, "ArduCopter V4.5.7")])
    blob = source.read_bytes()
    messages = [_Entry(1, 2, 2, 0, len(blob)), _Entry(2, 2, 2, 0, len(blob))]
    offset = 0
    while offset < len(blob):
        piece = blob[offset:offset + 90]
        messages.append(_LogData(1, offset, piece))
        offset += len(piece)
    board = _Board(messages)
    rows, path, note = read_dataflash(board, tmp_path / "out", log_id=1)
    assert path is not None
    assert path.name == "ardupilot-1.BIN"
    assert path.read_bytes() == blob
    assert "скачан журнал 1" in note
    assert rows[0]["id"] == 1
    missing = _Board([_Entry(1, 1, 1, 0, 10)])
    _rows, missed, why = read_dataflash(missing, tmp_path, log_id=9)
    assert missed is None
    assert "нет в списке" in why
    assert "log_request_data" not in [name for name, _args in missing.sent]


def test_two_cards_diff_ignores_holes(tmp_path: Path):
    left = assemble(Inputs(dump_text="# Betaflight / STM32F405 4.5.0\nset craft_name = Blink\n"))
    right = assemble(Inputs(dump_text="# Betaflight / STM32F405 4.5.1\nset craft_name = Other\n"))
    changes = diff_cards(left.to_dict(), right.to_dict())
    fields = {item["field"]: item for item in changes}
    assert fields["craft_name"]["left"] == "Blink"
    assert fields["craft_name"]["right"] == "Other"
    assert "pilot_name" not in fields
    text = render_diff(changes)
    assert "Blink → Other" in text
    left_path = tmp_path / "a.json"
    right_path = tmp_path / "b.json"
    left_path.write_text(json.dumps(left.to_dict()), encoding="utf-8")
    right_path.write_text(json.dumps(right.to_dict()), encoding="utf-8")
    assert main(["diff", str(left_path), str(right_path)]) == 0


def test_evidence_file_lists_the_hash(tmp_path: Path):
    from drone_sweep.menu import write_report

    card = assemble(Inputs(dump_text="# Betaflight / STM32F405 4.5.0\n"))
    write_report(card, tmp_path)
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["files"][0]["kind"] == "dump_all"
    assert len(evidence["files"][0]["sha256"]) == 64
