import json
from pathlib import Path

from drone_sweep.strela_bootstrap import (
    default_binding_paths,
    run_setup,
    setup_is_ready,
)


def test_run_setup_builds_manifest_and_table(tmp_path: Path, monkeypatch):
    tiny = tmp_path / "words.txt"
    tiny.write_text("test\nhello\n", encoding="utf-8")

    def fake_fetch(preset: str, destination: Path, *, timeout: float = 120.0):
        destination.write_text(tiny.read_text(encoding="utf-8"), encoding="utf-8")
        from drone_sweep.elrs_resources import FetchResult

        return FetchResult(path=destination, preset=preset, bytes_written=destination.stat().st_size)

    monkeypatch.setattr("drone_sweep.strela_bootstrap.fetch_wordlist_preset", fake_fetch)
    root = tmp_path / "data"
    result = run_setup(data_dir=root, quiet=True)
    assert setup_is_ready(root)
    assert result.manifest["wordlist_passhelp"]
    paths = default_binding_paths(root)
    assert paths["wordlist"].is_file()
    assert paths["memory_table"].is_file()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert "passhelp" in manifest["presets_ready"]