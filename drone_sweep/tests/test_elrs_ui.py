from drone_sweep.elrs_ui import handle_elrs_form
from drone_sweep.webapp import crack_page


def test_crack_page_has_nav_tab():
    body = crack_page().decode("utf-8")
    assert "Подбор" in body
    assert 'href="/crack"' in body
    assert "aria-current" in body
    assert "circl" not in body.lower()
    assert "github.com" not in body


def test_handle_uid_action():
    ok, fragment = handle_elrs_form({"action": "uid", "phrase": "test"})
    assert ok
    assert "4F04FD822155" in fragment
    assert "79,4,253,130,33,85" in fragment
    assert "circl" not in fragment.lower()


def test_handle_crack_missing_wordlist():
    ok, fragment = handle_elrs_form({"action": "crack", "uid": "79,4,253,130,33,85"})
    assert not ok
    assert "словарь" in fragment.lower()