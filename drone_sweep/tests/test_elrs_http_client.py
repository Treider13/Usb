import socket
import threading

import pytest

from drone_sweep.elrs_http import RadioAuthRequired, fetch_pages


def _serve(sock: socket.socket, handler, stop: threading.Event) -> None:
    sock.settimeout(0.2)
    while not stop.is_set():
        try:
            conn, _addr = sock.accept()
        except TimeoutError:
            continue
        threading.Thread(target=handler, args=(conn,), daemon=True).start()


def test_empty_esp_reply_is_retried_then_config_is_read():
    drops = {"n": 0}

    def handler(conn: socket.socket) -> None:
        try:
            request = conn.recv(4096)
            if drops["n"] < 1:
                drops["n"] += 1
                return
            path = request.split(b" ", 2)[1]
            if path == b"/config":
                body = b'{"config":{"uid":[1,2,3,4,5,6]},"settings":{"version":"ExpressLRS 3.5.0"}}'
            else:
                body = b"{}"
            head = (
                b"HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n"
                b"Connection: close\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n"
            )
            conn.sendall(head + body)
        finally:
            conn.close()

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.listen(8)
    stop = threading.Event()
    threading.Thread(target=_serve, args=(sock, handler, stop), daemon=True).start()
    try:
        pages = fetch_pages(f"http://127.0.0.1:{port}", timeout=1.0)
    finally:
        stop.set()
        sock.close()
    assert pages["/config"]["config"]["uid"] == [1, 2, 3, 4, 5, 6]
    assert drops["n"] == 1


def test_esp_401_stops_like_the_web_ui_password_prompt():
    def handler(conn: socket.socket) -> None:
        try:
            conn.recv(4096)
            conn.sendall(b"HTTP/1.0 401 Unauthorized\r\nConnection: close\r\nContent-Length: 0\r\n\r\n")
        finally:
            conn.close()

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.listen(4)
    stop = threading.Event()
    threading.Thread(target=_serve, args=(sock, handler, stop), daemon=True).start()
    try:
        with pytest.raises(RadioAuthRequired):
            fetch_pages(f"http://127.0.0.1:{port}", timeout=1.0)
    finally:
        stop.set()
        sock.close()
