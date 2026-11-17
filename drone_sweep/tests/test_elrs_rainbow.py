import hashlib
from pathlib import Path

from drone_sweep.elrs_binding import (
    binding_phrase_to_uid,
    binding_phrase_uid_hex,
    hash_binding_phrases,
    parse_uid_bytes,
    parse_uid_field,
    uid_bytes_to_hex,
)
from drone_sweep.elrs_rainbow import MemoryRainbowStore, crack_binding_phrase, lookup_binding_phrase


def test_binding_phrase_uid_matches_circl_formula():
    assert binding_phrase_to_uid("test") == [79, 4, 253, 130, 33, 85]
    assert binding_phrase_uid_hex("test") == "4F04FD822155"


def test_hash_batch_matches_circl_hash_batch():
    entries = ["alpha", "beta", "gamma"]
    ours = dict(hash_binding_phrases(entries))
    for entry in entries:
        define = f'-DMY_BINDING_PHRASE="{entry}"'
        uid_hex = hashlib.md5(define.encode("utf-8")).digest()[:6].hex().upper()
        assert ours[uid_hex] == entry


def test_parse_uid_formats():
    assert parse_uid_bytes("79,4,253,130,33,85") == [79, 4, 253, 130, 33, 85]
    assert parse_uid_field("4F,04,FD,82,21,55") == [0x4F, 0x04, 0xFD, 0x82, 0x21, 0x55]
    assert parse_uid_field("4F04FD822155") == [0x4F, 0x04, 0xFD, 0x82, 0x21, 0x55]


def test_crack_and_memory_rainbow(tmp_path: Path):
    wordlist = tmp_path / "words.txt"
    wordlist.write_text("wrong\nfluff\ntest\n", encoding="utf-8")
    uid = parse_uid_bytes("79,4,253,130,33,85")
    assert crack_binding_phrase(uid, wordlist) == "test"

    store = MemoryRainbowStore({})
    store.set_many([(binding_phrase_uid_hex("test"), "test")])
    assert lookup_binding_phrase(uid, store) == "test"
    assert lookup_binding_phrase([1, 2, 3, 4, 5, 6], store) is None
    assert uid_bytes_to_hex(uid) == "4F04FD822155"