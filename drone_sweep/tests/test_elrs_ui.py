from drone_sweep.elrs_ui import handle_elrs_form
from drone_sweep.webapp import crack_page, crack_response


def test_uid_table_answers_without_scanning_the_wordlist(tmp_path):
    import json

    from drone_sweep.elrs_assemble import search_binding_sources
    from drone_sweep.elrs_binding import binding_phrase_to_uid, binding_phrase_uid_hex

    table = tmp_path / "mem.json"
    table.write_text(
        json.dumps({binding_phrase_uid_hex("other"): "other"}) + "\n",
        encoding="utf-8",
    )
    words = tmp_path / "w.txt"
    words.write_text("test\n", encoding="utf-8")
    phrase, _used, problem = search_binding_sources(binding_phrase_to_uid("test"), words, table)
    assert phrase is None
    assert "нет фразы" in problem


def test_huge_wordlist_is_not_scanned_in_the_request(tmp_path, monkeypatch):
    from drone_sweep.elrs_assemble import search_binding_sources
    from drone_sweep.elrs_binding import binding_phrase_to_uid

    monkeypatch.setattr("drone_sweep.elrs_assemble._WORDLIST_SCAN_MAX_BYTES", 4)
    words = tmp_path / "rockyou.txt"
    words.write_text("test\n", encoding="utf-8")
    phrase, _used, problem = search_binding_sources(binding_phrase_to_uid("test"), words, None)
    assert phrase is None
    assert "большой" in problem


def test_crack_page_has_nav_tab():
    body = crack_page().decode("utf-8")
    assert "Подбор" in body
    assert 'href="/crack"' in body
    assert "aria-current" in body
    assert "CIRCL" in body or "circl" in body.lower()
    assert "OrangeRX" in body
    assert 'value="read_drone"' not in body
    assert 'value="http://10.0.0.1"' not in body
    assert "10.0.0.1" in body


def test_handle_uid_action():
    ok, fragment, _prefill = handle_elrs_form({"action": "uid", "phrase": "test"})
    assert ok
    assert "4F04FD822155" in fragment
    assert "79,4,253,130,33,85" in fragment


def test_phrase_from_flash_reads_binding_phrase_without_wordlist():
    import json

    from drone_sweep.elrs_ui import handle_elrs_form
    from drone_sweep.webapp_forms import Uploaded

    blob = json.dumps({"uid": [79, 4, 253, 130, 33, 85], "binding-phrase": "test"}).encode()
    ok, fragment, _prefill = handle_elrs_form(
        {"action": "phrase_from_flash"},
        {"flash_file": Uploaded("x.bin", b"\xff" + blob)},
    )
    assert ok
    assert "test" in fragment
    assert "словарь" not in fragment.lower() or "не понадобился" in fragment.lower()


def test_handle_crack_missing_wordlist():
    ok, fragment, _prefill = handle_elrs_form({"action": "crack", "uid": "79,4,253,130,33,85"})
    assert not ok
    assert "словарь" in fragment.lower()


def test_handle_crack_accepts_the_hex_uid_shown_above(tmp_path):
    words = tmp_path / "words.txt"
    words.write_text("nope\ntest\n", encoding="utf-8")
    ok, fragment, _prefill = handle_elrs_form(
        {"action": "crack", "uid": "4F04FD822155", "binding_wordlist": str(words)}
    )
    assert ok
    assert "test" in fragment


def test_other_protocol_is_not_called_orangerx():
    from drone_sweep.elrs_assemble import _refusal

    text = _refusal("CRSF")
    assert "CRSF" in text
    assert "OrangeRX" not in text


def test_assemble_from_the_tab_is_a_whole_report(tmp_path):
    radio = tmp_path / "radio.json"
    radio.write_text('{"version": "ExpressLRS 3.0", "uid": "79,4,253,130,33,85"}', encoding="utf-8")
    words = tmp_path / "words.txt"
    words.write_text("test\n", encoding="utf-8")
    out = tmp_path / "out"
    body = crack_response(
        {
            "action": "assemble",
            "radio_json_path": str(radio),
            "assemble_wordlist": str(words),
            "out": str(out),
        }
    ).decode("utf-8")
    assert body.lstrip().startswith("<!DOCTYPE")
    assert body.count("<!DOCTYPE") == 1
    assert "radio_binding_phrase_crack" in body
    assert "найдена" in body
    assert (out / "card.json").is_file()