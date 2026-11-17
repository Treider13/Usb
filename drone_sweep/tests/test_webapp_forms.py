import json

from drone_sweep.elrs_ui import handle_elrs_form
from drone_sweep.webapp import crack_page, home_page
from drone_sweep.webapp_forms import Uploaded, parse_post_body, stash_upload


def test_crack_and_home_forms_accept_file_upload():
    crack = crack_page().decode("utf-8")
    home = home_page().decode("utf-8")
    assert 'enctype="multipart/form-data"' in crack
    assert 'name="flash_file"' in crack
    assert 'name="binding_wordlist_file"' in crack
    assert 'name="phrase_from_flash"' in crack or 'value="phrase_from_flash"' in crack
    assert 'name="flash_file"' in home


def test_phrase_from_flash_with_uploaded_files(tmp_path):
    inner = {"uid": [79, 4, 253, 130, 33, 85], "wifi-password": "secret", "wifi-ssid": "ELRS"}
    blob = b"\xff" + json.dumps(inner).encode()
    words = tmp_path / "w.txt"
    words.write_text("nope\ntest\n", encoding="utf-8")
    ok, fragment, prefill = handle_elrs_form(
        {"action": "phrase_from_flash"},
        {
            "flash_file": Uploaded("rx.bin", blob),
            "binding_wordlist_file": Uploaded("w.txt", words.read_bytes()),
        },
    )
    assert ok
    assert "test" in fragment
    assert prefill == "79,4,253,130,33,85"
    assert "secret" not in fragment


def test_multipart_roundtrip():
    boundary = "----bound"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="action"\r\n\r\n'
        "crack\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="uid"\r\n\r\n'
        "79,4,253,130,33,85\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    fields, files = parse_post_body(f"multipart/form-data; boundary={boundary}", body)
    assert fields["action"] == "crack"
    assert fields["uid"] == "79,4,253,130,33,85"
    assert files == {}


def test_stash_upload_writes_temp_file():
    path = stash_upload(Uploaded("x.txt", b"hello"))
    assert path is not None
    assert path.read_text(encoding="utf-8") == "hello"
    path.unlink(missing_ok=True)