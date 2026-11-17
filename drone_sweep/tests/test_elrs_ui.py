from drone_sweep.elrs_ui import handle_elrs_form
from drone_sweep.webapp import crack_page, crack_response


def test_crack_page_has_nav_tab():
    body = crack_page().decode("utf-8")
    assert "Подбор" in body
    assert 'href="/crack"' in body
    assert "aria-current" in body
    assert "CIRCL" in body or "circl" in body.lower()
    assert "OrangeRX" in body


def test_handle_uid_action():
    ok, fragment = handle_elrs_form({"action": "uid", "phrase": "test"})
    assert ok
    assert "4F04FD822155" in fragment
    assert "79,4,253,130,33,85" in fragment


def test_handle_crack_missing_wordlist():
    ok, fragment = handle_elrs_form({"action": "crack", "uid": "79,4,253,130,33,85"})
    assert not ok
    assert "словарь" in fragment.lower()


def test_handle_crack_accepts_the_hex_uid_shown_above(tmp_path):
    words = tmp_path / "words.txt"
    words.write_text("nope\ntest\n", encoding="utf-8")
    ok, fragment = handle_elrs_form(
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