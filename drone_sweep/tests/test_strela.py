import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from drone_sweep.assemble import Inputs, assemble
from drone_sweep.elrs_http import FORBIDDEN_PATHS, READ_PATHS, RadioAuthRequired, fetch_pages, normalize_pages
from drone_sweep.menu import QUESTIONS, main, run_menu
from drone_sweep.webapp import StrelaHandler
from tests.test_card import BOXES, DUMP


def test_menu_builds_the_b162_card(tmp_path: Path):
    dump = tmp_path / "dump.txt"
    dump.write_text(DUMP, encoding="utf-8")
    boxes = tmp_path / "boxes.txt"
    boxes.write_text(BOXES, encoding="utf-8")
    out = tmp_path / "out"
    # dump and boxnames are filled, out is last, every question in between stays empty.
    blanks = [""] * (len(QUESTIONS) - 3)
    lines = ["1", str(dump), str(boxes), *blanks, str(out), "5"]
    text = run_menu(lines)
    assert "Стрела" in text
    assert "Отчёт:" in text
    page = (out / "report.html").read_text(encoding="utf-8")
    assert "LAZYFLY" in page
    assert "Blink" in page
    assert "Стрела" in page


def test_menu_explain_and_unknown_item():
    text = run_menu(["2", "9", "5"])
    assert "Пароль страницы" in text
    assert "Такого пункта нет" in text
    assert "Выход" in text


def test_check_command_refuses_save():
    assert main(["check-command", "save"]) == 2
    assert main(["check-command", "dump all"]) == 0


def test_serve_never_reads_stdin(monkeypatch):
    seen = {}

    def fake_serve(port):
        seen["port"] = port

    monkeypatch.setattr("drone_sweep.webapp.serve", fake_serve)

    def fail_stdin():
        raise AssertionError("serve прочитал stdin")

    monkeypatch.setattr("drone_sweep.menu._stdin_lines", fail_stdin)
    assert main(["serve", "--port", "8765"]) == 0
    assert seen["port"] == 8765
    assert main(["serve", "--port=9000"]) == 0
    assert seen["port"] == 9000
    assert main(["serve", "--port", "nope"]) == 2


def test_ctrl_c_stops_without_a_traceback(monkeypatch, capsys):
    def interrupt():
        raise KeyboardInterrupt

    monkeypatch.setattr("drone_sweep.menu._stdin_lines", interrupt)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert main([]) == 130
    assert capsys.readouterr().out.strip() == "Стрела остановлена."


def test_web_menu_and_post(tmp_path: Path):
    dump = tmp_path / "dump.txt"
    dump.write_text(DUMP, encoding="utf-8")
    boxes = tmp_path / "boxes.txt"
    boxes.write_text(BOXES, encoding="utf-8")
    out = tmp_path / "web-out"
    server = ThreadingHTTPServer(("127.0.0.1", 0), StrelaHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        home = urlopen(f"http://127.0.0.1:{port}/").read().decode("utf-8")
        assert "Стрела" in home
        assert "Собрать карточку" in home
        explain = urlopen(f"http://127.0.0.1:{port}/explain").read().decode("utf-8")
        assert "парол" in explain.lower()
        payload = urlencode(
            {
                "dump": str(dump),
                "boxnames": str(boxes),
                "out": str(out),
                "nameplate_vtx": "Skyzone VT7550",
            }
        ).encode()
        page = urlopen(Request(f"http://127.0.0.1:{port}/assemble", data=payload)).read().decode("utf-8")
    finally:
        server.shutdown()
    assert "LAZYFLY" in page
    assert "Skyzone VT7550" in page
    card = json.loads((out / "card.json").read_text(encoding="utf-8"))
    assert card["fields"]["craft_name"]["value"] == "Blink"
    assert card["fields"]["nameplate_vtx"]["status"] == "document"


def test_elrs_rx_page_has_no_packet_rate_and_keeps_secrets_out():
    pages = {
        "/config": {
            "settings": {
                "product_name": "LR1824 Dual RX",
                "version": "MILELRS_v437",
                "radio-type": "LR1121",
                "target": "LR1824",
                "module-type": "RX",
            },
            "config": {"uid": [1, 2, 3, 4, 5, 6], "serial-protocol": 1, "modelid": 0},
        },
        "/options.json": {
            "custom-freq": "1900-1920",
            "binding-rate": 44,
            "wifi-password": "do-not-store",
            "binding-phrase": "do-not-store-phrase",
        },
        "/hardware.json": {},
    }
    normalized = normalize_pages(pages)
    assert "packet-rate" not in normalized
    assert "tx_packet_rate" not in normalized
    assert normalized["version"] == "MILELRS_v437"
    assert normalized["custom_freq"] == "1900-1920"
    card = assemble(Inputs(radio_json=normalized))
    dumped = json.dumps(card.to_dict())
    assert "do-not-store" not in dumped
    assert card.fields["radio_protocol"].value == "MILELRS"
    assert card.fields["radio_binding_rate"].value == "44"
    assert card.fields["radio_uid"].value == "1,2,3,4,5,6"
    assert "packet_rate_log_hz" not in card.fields or card.fields.get("packet_rate_log_hz") is None


def test_elrs_tx_export_packet_rate_is_a_separate_field():
    pages = {
        "/config": {
            "settings": {"product_name": "TX", "version": "3.5.3", "module-type": "TX"},
            "config": {"model": {"0": {"packet-rate": 6}}, "uid": [9]},
        }
    }
    normalized = normalize_pages(pages)
    assert normalized["tx_packet_rate"] == 6
    assert normalized["version"].startswith("ExpressLRS")
    card = assemble(Inputs(radio_json=normalized))
    assert card.fields["radio_tx_packet_rate"].value == "6"
    assert card.fields["radio_swarm_id"].status == "not_applicable"


def test_elrs_30_target_and_mode_fill_the_card_without_the_scan():
    assert "/target" in READ_PATHS and "/mode.json" in READ_PATHS
    assert "/networks.json" not in READ_PATHS
    assert "/networks.json" in FORBIDDEN_PATHS
    normalized = normalize_pages(
        {
            "/config": None,
            "/target": {
                "target": "unified_esp8285",
                "version": "3.0.0",
                "product_name": "Generic ESP8285",
                "reg_domain": "ISM2G4",
            },
            "/mode.json": {
                "ssid": "office",
                "mode": "STA",
                "modelid": 1,
                "uid": [4, 5],
                "uidtype": "Traditional",
                "lua_name": "Generic",
            },
        }
    )
    assert normalized["version"] == "ExpressLRS 3.0.0"
    assert normalized["target"] == "unified_esp8285"
    assert normalized["domain"] == "ISM2G4"
    assert normalized["model_id"] == 1
    assert normalized["uid"] == "4,5"
    assert normalized["wifi_mode"] == "STA"
    assert "office" not in json.dumps(normalized)
    card = assemble(Inputs(radio_json=normalized))
    assert card.fields["radio_protocol"].value == "ExpressLRS"
    assert card.fields["radio_wifi_mode"].value == "STA"


def test_fetch_stops_on_401_and_never_calls_write_routes():
    seen = []

    def opener(url, timeout=5.0):
        seen.append(url)
        from urllib.error import HTTPError

        raise HTTPError(url, 401, "auth", hdrs=None, fp=None)

    with pytest.raises(RadioAuthRequired):
        fetch_pages("http://10.0.0.1", opener=opener)
    assert seen == ["http://10.0.0.1/config"]
    assert not any(path in seen[0] for path in FORBIDDEN_PATHS)
    assert READ_PATHS[0] == "/config"


def test_spektrum_has_no_crsf_link_quality():
    card = assemble(Inputs(dump_text="set serialrx_provider = SPEKTRUM2048\n", banner="Betaflight 4.5.0"))
    assert card.fields["serial_link_class"].value == "DSM2/DSMX"
    assert card.fields["radio_protocol"].value == "SPEKTRUM2048"
    assert card.fields["spektrum_channel_count"].value == 12
    assert card.fields["spektrum_baud"].value == 115200
    assert card.fields["uplink_lq"].status == "not_applicable"


def test_orange_spi_protocol_is_the_cyrf_dsm_entry():
    card = assemble(
        Inputs(
            dump_text="set rx_spi_protocol = SPEKTRUM\nset spektrum_sat_bind = 0\n",
            banner="Betaflight 4.5.0",
            nameplates={"radio": "OrangeRX"},
        )
    )
    assert card.fields["nameplate_radio"].status == "document"
    assert card.fields["nameplate_radio"].value == "OrangeRX"
    assert card.fields["radio_protocol"].value == "SPEKTRUM"
    assert card.fields["radio_protocol"].source == "dump rx_spi_protocol"
    assert card.fields["spektrum_sat_bind"].value == "0"
    assert "не отправляется" in card.fields["spektrum_sat_bind"].reason
    assert card.fields["spektrum_channel_count"].value == 12
    assert card.fields["orange_rx_profile"].value["nameplate"] == "OrangeRX"


def test_orange_nameplate_without_a_provider_stays_a_sticker():
    card = assemble(Inputs(banner="Betaflight 4.5.0", nameplates={"radio": "OrangeRX"}))
    assert card.fields["nameplate_radio"].status == "document"
    assert card.fields["radio_protocol"].status == "missing"


def test_crsf_on_the_uart_does_not_name_the_air_protocol():
    card = assemble(Inputs(dump_text="set serialrx_provider = CRSF\n", banner="Betaflight 4.5.0"))
    assert card.fields["uart_protocol"].value == "CRSF"
    assert card.fields["air_protocol"].status == "missing"


def test_orange_nameplate_does_not_replace_the_provider():
    card = assemble(
        Inputs(
            dump_text="set serialrx_provider = SPEKTRUM1024\n",
            banner="Betaflight 4.5.0",
            nameplates={"radio": "OrangeRX"},
        )
    )
    assert card.fields["nameplate_radio"].status == "document"
    assert card.fields["nameplate_radio"].value == "OrangeRX"
    assert card.fields["radio_protocol"].value == "SPEKTRUM1024"
    assert card.fields["spektrum_channel_count"].value == 7
    assert card.fields["radio_protocol"].source == "dump serialrx_provider"
