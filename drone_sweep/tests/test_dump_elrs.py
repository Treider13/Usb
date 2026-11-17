import json
from pathlib import Path

from drone_sweep.assemble import Inputs, assemble
from drone_sweep.dump_elrs import build_json_payload, compute_hashes, extract_json_objects, public_extraction_summary
from drone_sweep.elrs_rainbow import build_memory_table, load_memory_table, lookup_binding_phrase, save_memory_table
from drone_sweep.radio import parse_radio_image


def test_extract_json_from_binary_flash():
    inner = {
        "uid": [79, 4, 253, 130, 33, 85],
        "wifi-ssid": "ELRS_TX",
        "wifi-password": "secret-pass",
        "binding-phrase": "test",
    }
    blob = b"\xff\xff" + json.dumps(inner).encode() + b"\x00"
    entries = extract_json_objects(blob)
    assert len(entries) == 1
    assert entries[0]["uid"] == inner["uid"]
    md5, sha256 = compute_hashes(blob)
    payload = build_json_payload(md5, sha256, entries)
    assert payload["extracted"][0]["wifi-password"] == "secret-pass"


def test_parse_radio_image_merges_elrs_json():
    inner = {"uid": [1, 2, 3, 4, 5, 6], "wifi-password": "x"}
    blob = b"ExpressLRS 3.0\x00" + json.dumps(inner).encode()
    reading = parse_radio_image(blob)
    assert reading.fields["uid"] == "1,2,3,4,5,6"
    assert "wifi-password" in reading.removed_secrets


def test_assemble_binding_crack_without_storing_phrase(tmp_path: Path):
    wordlist = tmp_path / "w.txt"
    wordlist.write_text("nope\ntest\n", encoding="utf-8")
    card = assemble(
        Inputs(
            radio_json={"version": "ExpressLRS 3.0", "uid": "79,4,253,130,33,85"},
            binding_wordlist=wordlist,
        )
    )
    crack = card.fields["radio_binding_phrase_crack"]
    assert crack.value == "найдена"
    dumped = json.dumps(card.to_dict(), ensure_ascii=False)
    assert "test" not in dumped


def test_orange_does_not_use_elrs_binding_crack(tmp_path: Path):
    wordlist = tmp_path / "w.txt"
    wordlist.write_text("test\n", encoding="utf-8")
    card = assemble(
        Inputs(
            banner="Betaflight 4.5.0",
            dump_text="serialrx_provider = SPEKTRUM2048",
            nameplates={"radio": "OrangeRX"},
            binding_wordlist=wordlist,
        )
    )
    crack = card.fields["radio_binding_phrase_crack"]
    assert crack.status == "not_applicable"
    assert "SPEKTRUM2048" in crack.reason
    assert "OrangeRX" in crack.reason
    assert "test" not in json.dumps(card.to_dict())


def test_milelrs_binding_crack_with_uid(tmp_path: Path):
    wordlist = tmp_path / "w.txt"
    wordlist.write_text("nope\ntest\n", encoding="utf-8")
    card = assemble(
        Inputs(
            radio_json={"version": "MILELRS_v437", "uid": "79,4,253,130,33,85"},
            binding_wordlist=wordlist,
        )
    )
    assert card.fields["radio_protocol"].value == "MILELRS"
    assert card.fields["radio_binding_phrase_crack"].value == "найдена"


def test_public_extraction_includes_binding_phrase_from_flash():
    blob = json.dumps({"uid": [1, 2, 3, 4, 5, 6], "binding-phrase": "from_flash", "wifi-password": "x"}).encode()
    summary = public_extraction_summary(b"\xff" + blob)
    assert summary["extracted"][0]["binding_phrase"] == "from_flash"
    assert "x" not in json.dumps(summary)


def test_public_extraction_skips_wifi_password_value():
    blob = json.dumps({"uid": [1, 2, 3, 4, 5, 6], "wifi-password": "secret"}).encode()
    summary = public_extraction_summary(b"\xff" + blob)
    assert summary["extracted"][0]["wifi_password_present"] is True
    assert "secret" not in json.dumps(summary)


def test_memory_table_roundtrip(tmp_path: Path):
    words = tmp_path / "w.txt"
    words.write_text("test\n", encoding="utf-8")
    store = build_memory_table(words)
    table_path = tmp_path / "t.json"
    save_memory_table(store, table_path)
    loaded = load_memory_table(table_path)
    assert lookup_binding_phrase([79, 4, 253, 130, 33, 85], loaded) == "test"