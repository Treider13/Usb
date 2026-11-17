from drone_sweep.assemble import Inputs, assemble


def test_ardupilot_dsm_from_rc_protocols_mask():
    card = assemble(
        Inputs(
            banner="ArduCopter V4.5.0",
            mavlink_rows=[
                {"name": "HEARTBEAT", "autopilot": 3, "type": 2},
                {"name": "PARAM_VALUE", "param_id": "RC_PROTOCOLS", "param_value": 1 << 5},
            ],
        )
    )
    assert "DSM" in card.fields["rc_protocols"].value["bits"]
    assert card.fields["serial_link_class"].value == "DSM2/DSMX"
    assert card.fields["ardupilot_radio_summary"].value["rc_protocols"]["bits"]


def test_inav_spektrum_matches_betaflight():
    dump = "set serialrx_provider = SPEKTRUM2048\n"
    card_bf = assemble(Inputs(dump_text=dump, banner="Betaflight 4.5.0"))
    card_inav = assemble(Inputs(dump_text=dump, banner="INAV 7.1.0"))
    assert card_bf.fields["spektrum_channel_count"].value == card_inav.fields["spektrum_channel_count"].value
    assert card_bf.fields["orange_rx_profile"].value["protocol"] == "SPEKTRUM2048"