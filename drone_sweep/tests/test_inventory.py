"""Every printed setting stays on the card. Profiles do not overwrite each other."""

import json

from drone_sweep.assemble import Inputs, assemble, log_inventory
from drone_sweep.dump import parse_dump
from drone_sweep.radio import parse_radio_json
from drone_sweep.report import render_html


DUMP = """# Betaflight / STM32F405 (S405) 4.5.0
board_name MATEKF405
mcu_id 0032001e
set serialrx_provider = CRSF
set craft_name = Blink
profile 0
set p_pitch = 10
profile 1
set p_pitch = 20
resource MOTOR 1 A08
timer A08 AF1
"""


def test_profiles_keep_both_values_and_other_commands_stay():
    parsed = parse_dump(DUMP)
    assert parsed.settings["serialrx_provider"] == "CRSF"
    assert "p_pitch" not in parsed.settings
    by_name = {section["name"]: section["settings"] for section in parsed.sections}
    assert by_name["profile 0"]["p_pitch"] == "10"
    assert by_name["profile 1"]["p_pitch"] == "20"
    assert parsed.commands["resource"] == ["resource MOTOR 1 A08"]
    assert parsed.commands["timer"] == ["timer A08 AF1"]
    card = assemble(Inputs(dump_text=DUMP))
    sections = card.fields["cli_sections"].value
    assert sections[1]["settings"]["p_pitch"] == "10"
    assert sections[2]["settings"]["p_pitch"] == "20"
    assert "resource MOTOR 1 A08" in card.fields["cli_commands"].value["resource"]
    assert card.fields["mcu_id"].value == "0032001e"
    page = render_html(card)
    assert "p_pitch" in page
    assert "A08" in page
    assert ">10<" in page and ">20<" in page


def test_radio_page_keeps_unknown_keys_and_drops_the_password():
    reading = parse_radio_json(
        {
            "version": "ExpressLRS 3.5.3",
            "uid": "01:02",
            "antenna": "omni",
            "binding_phrase": "hidden",
        }
    )
    assert reading.fields["antenna"] == "omni"
    assert "binding_phrase" not in reading.fields
    card = assemble(Inputs(banner="Betaflight 4.5.0", radio_json=reading.fields | {"version": "ExpressLRS 3.5.3"}))
    assert card.fields["radio_page"].value["antenna"] == "omni"
    assert "hidden" not in page_text(card)


def test_mlrs_cli_keeps_printed_values_and_drops_the_bind_phrase():
    blob = "\n".join(
        [
            "mLRS",
            "ConfigId:",
            "1",
            "  Tx: Matek MR900, v1.4.05",
            "  Rx: receiver not connected",
            "  Mode = 50 Hz [0]",
            "  Bind Phrase = secret-phrase",
            "  RF Band = - (unavailable)",
        ]
    ).encode("ascii")
    card = assemble(Inputs(radio_image=blob, banner="Betaflight 4.5.0"))
    assert card.fields["radio_protocol"].value == "mLRS"
    assert card.fields["radio_page"].value["mode"] == "50 Hz [0]"
    assert card.fields["radio_page"].value["rf_band"] == "- (unavailable)"
    assert card.fields["radio_page"].value["tx"] == "Matek MR900, v1.4.05"
    assert card.fields["radio_binding_rate"].status == "not_applicable"
    dumped = json.dumps(card.to_dict(), ensure_ascii=False)
    assert "secret-phrase" not in dumped
    assert "serialpassthrough" not in dumped


def test_log_inventory_lists_every_message_type():
    rows = [{"name": "EV", "TimeUS": 1, "Id": 10}] + [
        {"name": "IMU", "TimeUS": index, "AccX": index} for index in range(31)
    ]
    inventory = log_inventory(rows)
    assert inventory["EV"]["count"] == 1
    assert inventory["EV"]["rows"][0]["Id"] == 10
    assert inventory["IMU"]["count"] == 31
    assert len(inventory["IMU"]["rows"]) == 31
    assert inventory["IMU"]["rows"][0]["TimeUS"] == 0
    assert inventory["IMU"]["rows"][-1]["TimeUS"] == 30


def page_text(card) -> str:
    return json.dumps(card.to_dict(), ensure_ascii=False)
