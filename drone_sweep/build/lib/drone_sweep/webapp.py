"""Local menu in the browser. Files stay on this computer."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from .assemble import assemble
from .hints import WORKFLOW
from .menu import APP_NAME, inputs_from_answers, write_report
from .report import render_html


def home_page() -> bytes:
    steps = "".join(f"<li>{step}</li>" for step in WORKFLOW)
    body = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{APP_NAME}</title>
<style>
body {{ font-family: sans-serif; margin: 32px; max-width: 860px; }}
a.button {{ display: inline-block; margin-right: 12px; padding: 8px 12px; background: #1f4e79; color: white; text-decoration: none; }}
label {{ display: block; margin-top: 10px; }}
input {{ width: 100%; padding: 6px; }}
</style>
</head>
<body>
<h1>{APP_NAME}</h1>
<p>Программа читает уже снятые файлы и собирает карточку. Она не подбирает пароль и не пишет в полётник.</p>
<p><a class="button" href="/assemble">Собрать карточку</a> <a class="button" href="/explain">Подсказки</a></p>
<h2>Порядок</h2>
<ol>{steps}</ol>
</body>
</html>
"""
    return body.encode("utf-8")


def form_page() -> bytes:
    fields = (
        ("dump", "dump all"),
        ("boxnames", "имена режимов"),
        ("bin", ".BIN"),
        ("tlog", ".tlog"),
        ("blackbox", "Blackbox"),
        ("gps_csv", "GPS CSV"),
        ("gpx", "GPX"),
        ("waypoints", ".waypoints"),
        ("plan", ".plan"),
        ("radio_json", "JSON приёмника"),
        ("radio_image", "образ приёмника"),
        ("nameplate_vtx", "шильдик VTX"),
        ("nameplate_radio", "шильдик радио"),
        ("nameplate_gimbal", "шильдик подвеса"),
        ("out", "папка отчёта"),
    )
    labels = "\n".join(
        f'<label>{title}<input name="{name}" placeholder="путь на этом компьютере, можно оставить пустым"></label>'
        for name, title in fields
    )
    body = f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><title>{APP_NAME} — сборка</title></head>
<body>
<h1>Сборка карточки</h1>
<p>Впишите пути к файлам, которые уже лежат на компьютере. Пустой путь пропускается.</p>
<form method="post" action="/assemble">
{labels}
<p><button type="submit">Собрать</button></p>
</form>
<p><a href="/">Назад</a></p>
</body>
</html>
"""
    return body.encode("utf-8")


def explain_page() -> bytes:
    steps = "".join(f"<li>{step}</li>" for step in WORKFLOW)
    body = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Подсказки</title></head>
<body><h1>Подсказки</h1><ol>{steps}</ol>
<p>Если страница приёмника просит пароль, введите его сами один раз. Программа пароли не перебирает.</p>
<p><a href="/">Назад</a></p></body></html>"""
    return body.encode("utf-8")


class StrelaHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._send(200, home_page())
        elif self.path.startswith("/assemble"):
            self._send(200, form_page())
        elif self.path.startswith("/explain"):
            self._send(200, explain_page())
        else:
            self._send(404, b"not found")

    def do_POST(self) -> None:
        if not self.path.startswith("/assemble"):
            self._send(404, b"not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        form = {key: values[0] for key, values in parse_qs(raw).items()}
        if not form.get("out", "").strip():
            self._send(400, "Укажите папку отчёта.".encode("utf-8"))
            return
        card = assemble(inputs_from_answers(form))
        page = write_report(card, Path(form["out"].strip()))
        html = render_html(card)
        note = f"<p>Файл отчёта: {page}</p>".encode("utf-8")
        self._send(200, note + html.encode("utf-8"))

    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, code: int, body: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(port: int = 8765) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), StrelaHandler)
    print(f"{APP_NAME}: http://127.0.0.1:{port}")
    server.serve_forever()
