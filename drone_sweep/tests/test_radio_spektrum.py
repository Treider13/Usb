from drone_sweep.assemble import Inputs, assemble
from drone_sweep.report import render_html


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
    assert card.fields["radio_read_summary"].value["rc_protocols"]["bits"]
    assert card.fields["ardupilot_radio_summary"].value == card.fields["radio_read_summary"].value
    assert "orange_rx_profile" in card.fields["radio_read_summary"].value


def test_ardupilot_rc_protocols_all_note_without_dsm_line():
    card = assemble(
        Inputs(
            banner="ArduCopter V4.5.0",
            mavlink_rows=[
                {"name": "HEARTBEAT", "autopilot": 3, "type": 2},
                {"name": "PARAM_VALUE", "param_id": "RC_PROTOCOLS", "param_value": 1},
            ],
        )
    )
    summary = card.fields["radio_read_summary"].value
    assert summary["rc_protocols"]["bits"] == ["All"]
    assert "rc_protocols_note" in summary
    assert "orange_rx_profile" not in summary


def test_ardupilot_dsm_from_mavlink_msg_only():
    card = assemble(
        Inputs(
            banner="ArduCopter V4.5.0",
            mavlink_rows=[
                {"name": "HEARTBEAT", "autopilot": 3, "type": 2},
                {"name": "STATUSTEXT", "text": "Rc protocol: DSM"},
            ],
        )
    )
    assert card.fields["uart_protocol"].value.lower().startswith("dsm")
    assert card.fields["orange_rx_profile"].value["protocol"] == "DSM"
    assert card.fields["radio_read_summary"].value["flight_os"] == "ardupilot"


def test_inav_spektrum_matches_betaflight():
    serial_line = "serial 1 64 115200 57600 0 115200"
    dump = (
        f"set serialrx_provider = SPEKTRUM2048\n"
        f"{serial_line}\n"
        f"set spektrum_sat_bind = 5\n"
    )
    card_bf = assemble(Inputs(dump_text=dump, banner="Betaflight 4.5.0"))
    card_inav = assemble(Inputs(dump_text=dump, banner="INAV 7.1.0"))
    assert card_bf.fields["spektrum_channel_count"].value == card_inav.fields["spektrum_channel_count"].value
    assert card_bf.fields["orange_rx_profile"].value["protocol"] == "SPEKTRUM2048"
    for card in (card_bf, card_inav):
        orange = card.fields["orange_rx_profile"].value
        assert orange["receiver_port"] == "USART2"
        assert "serial_ports" in orange
        assert card.fields["radio_read_summary"].value["flight_os"] == card.family
        assert card.fields["radio_read_summary"].value["radio_link_kind"] == "uart_serialrx"


def test_betaflight_spi_spektrum_orange_profile():
    dump = (
        "feature RX_SPI\n"
        "set rx_spi_protocol = SPEKTRUM\n"
        "set serialrx_provider = SPEKTRUM2048\n"
    )
    card = assemble(Inputs(dump_text=dump, banner="Betaflight 4.5.0"))
    orange = card.fields["orange_rx_profile"].value
    assert orange["protocol"] == "SPEKTRUM2048"
    assert "features_rx_spi" in orange
    summary = card.fields["radio_read_summary"].value
    assert summary["radio_link_kind"] == "expresslrs_spi" or summary["radio_link_kind"] == "rx_spi"


def test_report_html_includes_radio_read_summary():
    dump = "set serialrx_provider = SPEKTRUM2048\nserial 2 64 115200 57600 0 115200\n"
    card = assemble(Inputs(dump_text=dump, banner="Betaflight 4.5.0"))
    html = render_html(card)
    assert "radio_read_summary" in html or "Радио одним блоком" in html
    assert "orange_rx_profile" in html or "OrangeRX" in html