from drone_sweep.elrs_resources import WORDLIST_PRESETS, render_elrs_resources_html
from drone_sweep.top2026 import render_top_inner


def test_top2026_lists_elrs_wordlist_sources():
    body = render_top_inner()
    assert "id='elrs-wordlists'" in body
    assert "passhelp" in body
    assert "CIRCL" in body
    assert "expresslrs" in body


def test_resource_html_mentions_presets():
    html = render_elrs_resources_html()
    for key in WORDLIST_PRESETS:
        assert key in html