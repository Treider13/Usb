from drone_sweep.elrs_binding import binding_phrase_to_uid
from drone_sweep.elrs_drone_read import synthesize_flash_bytes, synthesize_flash_bytes_from_pages
from drone_sweep.dump_elrs import public_extraction_summary
from drone_sweep.strela_bootstrap import search_binding_installed


def test_synthesize_flash_exposes_uid_for_dump():
    blob = synthesize_flash_bytes({"uid": "79,4,253,130,33,85", "version": "ExpressLRS"})
    summary = public_extraction_summary(blob)
    assert summary["extracted"][0]["uid"] == "79,4,253,130,33,85"


def test_synthesize_from_pages_keeps_wifi_password_for_operator_dump():
    pages = {
        "/config": {
            "config": {"uid": [79, 4, 253, 130, 33, 85], "wifi-password": "custom-wifi"},
            "settings": {"version": "ExpressLRS 3.5.0"},
        }
    }
    blob = synthesize_flash_bytes_from_pages(pages)
    private = public_extraction_summary(blob, reveal_wifi_password=True)
    public = public_extraction_summary(blob, reveal_wifi_password=False)
    assert private["extracted"][0]["wifi_password"] == "custom-wifi"
    assert public["extracted"][0].get("wifi_password_present") is True
    assert "wifi_password" not in public["extracted"][0]


def test_usb_dump_finds_phrase_without_opening_the_web_ui(monkeypatch):
    from drone_sweep.elrs_drone_read import read_drone_elrs_html

    class Captured:
        dump_text = 'cli {"uid": [79, 4, 253, 130, 33, 85], "version": "ExpressLRS"} end'

    def fail_http(*_args, **_kwargs):
        raise AssertionError("10.0.0.1 не нужен, пока фраза ищется по UID")

    monkeypatch.setattr("drone_sweep.elrs_drone_read.read_usb", lambda *_a, **_k: Captured())
    monkeypatch.setattr("drone_sweep.elrs_drone_read.fetch_pages_with_passwords", fail_http)
    monkeypatch.setattr(
        "drone_sweep.elrs_drone_read.search_binding_installed",
        lambda _uid, _source="all": ("test", "combined-memory", ""),
    )
    ok, fragment, uid = read_drone_elrs_html({"action": "read_drone", "drone_port": "/dev/ttyACM0"})
    assert ok
    assert ">test<" in fragment
    assert uid == "79,4,253,130,33,85"


def test_usb_dump_without_uid_does_not_call_the_receiver(monkeypatch):
    from drone_sweep.elrs_drone_read import read_drone_elrs_html

    class Captured:
        dump_text = "set serialrx_provider = CRSF\n"

    def fail_http(*_args, **_kwargs):
        raise AssertionError("без uid в дампе WebUI не открываем")

    monkeypatch.setattr("drone_sweep.elrs_drone_read.read_usb", lambda *_a, **_k: Captured())
    monkeypatch.setattr("drone_sweep.elrs_drone_read.fetch_pages_with_passwords", fail_http)
    ok, fragment, uid = read_drone_elrs_html({"action": "read_drone", "drone_port": "/dev/ttyACM0"})
    assert not ok
    assert uid == ""
    assert "dump all" in fragment


def test_search_binding_installed_uses_passhelp(tmp_path, monkeypatch):
    tiny = tmp_path / "w.txt"
    tiny.write_text("nope\ntest\n", encoding="utf-8")

    def fake_fetch(preset: str, destination, **kwargs):
        destination.write_text(tiny.read_text(encoding="utf-8"), encoding="utf-8")
        from drone_sweep.elrs_resources import FetchResult

        return FetchResult(path=destination, preset=preset, bytes_written=10)

    monkeypatch.setattr("drone_sweep.strela_bootstrap.fetch_wordlist_preset", fake_fetch)
    from drone_sweep.strela_bootstrap import run_setup

    run_setup(data_dir=tmp_path / "data", quiet=True)
    uid = binding_phrase_to_uid("test")
    phrase, source, problem = search_binding_installed(uid, "all", data_dir=tmp_path / "data")
    assert phrase == "test"
    assert not problem
    assert source