from drone_sweep.elrs_binding import binding_phrase_to_uid
from drone_sweep.strela_bootstrap import search_binding_installed


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