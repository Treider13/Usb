import json
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from drone_sweep.elrs_ui import handle_elrs_form
from drone_sweep.webapp import StrelaHandler, crack_page, home_page
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


def test_multipart_file_and_blank_field():
    boundary = "----bound"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="action"\r\n\r\n'
        "dump\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="note"\r\n\r\n'
        "\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="flash_file"; filename="rx.bin"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
        "abc\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    fields, files = parse_post_body(f'multipart/form-data; boundary="{boundary}"', body)
    assert fields["action"] == "dump"
    assert fields["note"] == ""
    assert files["flash_file"].filename == "rx.bin"
    assert files["flash_file"].data == b"abc"


def test_urlencoded_post():
    fields, files = parse_post_body(
        "application/x-www-form-urlencoded",
        b"action=uid&phrase=test",
    )
    assert fields["action"] == "uid"
    assert fields["phrase"] == "test"
    assert files == {}


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


def test_post_crash_returns_html_instead_of_dropping_the_socket(monkeypatch):
    def boom(content_type, body):
        raise RuntimeError("boom")

    monkeypatch.setattr("drone_sweep.webapp_forms.parse_post_body", boom)
    server = ThreadingHTTPServer(("127.0.0.1", 0), StrelaHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        urlopen(Request(f"http://127.0.0.1:{port}/crack", data=b"action=uid&phrase=test"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        assert exc.code == 500
        assert "RuntimeError: boom" in body
    else:
        raise AssertionError("сервер должен ответить 500, а не закрыть сокет")
    finally:
        server.shutdown()


def test_crack_multipart_post_answers():
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="action"\r\n\r\n'
        "uid\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="phrase"\r\n\r\n'
        "test\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    server = ThreadingHTTPServer(("127.0.0.1", 0), StrelaHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        request = Request(
            f"http://127.0.0.1:{port}/crack",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        page = urlopen(request).read().decode("utf-8")
    finally:
        server.shutdown()
    assert "Десятичный" in page


def test_stash_upload_writes_temp_file():
    path = stash_upload(Uploaded("x.txt", b"hello"))
    assert path is not None
    assert path.read_text(encoding="utf-8") == "hello"
    path.unlink(missing_ok=True)