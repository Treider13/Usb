from pathlib import Path

from drone_sweep.elrs_binding import binding_phrase_to_uid, uid_bytes_to_hex
from drone_sweep.elrs_rainbow import (
    build_and_save_table,
    build_memory_table_sqlite,
    crack_binding_phrase_from_store,
    load_memory_table,
)


def test_sqlite_table_lookup(tmp_path: Path):
    words = tmp_path / "w.txt"
    words.write_text("alpha\nbeta\ntest\n", encoding="utf-8")
    db = tmp_path / "t.sqlite"
    build_memory_table_sqlite(words, db)
    store = load_memory_table(db)
    uid = binding_phrase_to_uid("test")
    phrase = crack_binding_phrase_from_store(uid, store)
    assert phrase == "test"
    target = uid_bytes_to_hex(uid)
    assert store.get(target) == "test"


def test_build_and_save_uses_sqlite_for_large_file(tmp_path: Path, monkeypatch):
    words = tmp_path / "big.txt"
    words.write_text("x\n" * 50, encoding="utf-8")
    monkeypatch.setattr("drone_sweep.elrs_rainbow.ROCKYOU_SQLITE_MIN_BYTES", 10)
    table_json = tmp_path / "big-memory.json"
    actual = build_and_save_table(words, table_json)
    assert actual.suffix == ".sqlite"
    store = load_memory_table(actual)
    assert store.get("00" * 6) is None or isinstance(store.get("00" * 6), (str, type(None)))