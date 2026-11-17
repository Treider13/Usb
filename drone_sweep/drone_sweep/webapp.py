"""Local menu in the browser. Files stay on this computer."""

from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from .assemble import assemble
from .hints import WORKFLOW
from .menu import APP_NAME, inputs_from_answers, write_report
from .report import render_html
from .theme import page


FORM_FIELDS = (
    ("dump", "dump all полётника", "Файл, который Betaflight или INAV печатает по команде dump all. Если его нет, оставьте пустым."),
    ("boxnames", "Имена режимов", "Ответ MSP_BOXNAMES. Без него нестандартный режим останется номером."),
    ("bin", "Лог .BIN", "Файл ArduPilot с полёта. Маршрут ищется здесь в первую очередь."),
    ("tlog", "Телеметрия .tlog", "Файл наземной станции. Это второй источник маршрута."),
    ("blackbox", "Blackbox", "Файл .bbl или .txt. Из него берётся заголовок и герцы rc_smoothing."),
    ("gps_csv", "GPS CSV", "Таблица, которую записал blackbox_decode. Это третий источник маршрута."),
    ("gpx", "GPX", "Путевые точки. Линия трека в GPX маршрутом полёта не считается."),
    ("waypoints", "Файл .waypoints", "Миссия. Точкой взлёта не становится."),
    ("plan", "Файл .plan", "Миссия QGroundControl. Точкой взлёта не становится."),
    ("radio_json", "Страница приёмника", "JSON, который вы сохранили с http://10.0.0.1. Пароль в файл не кладите."),
    ("radio_image", "Образ приёмника", "Чтение flash. Программа его не стирает."),
    ("stm32", "Журнал STM32", "Сохранённый вывод STM32_Programmer_CLI --connect port=SWD или st-info --probe. Стирание и запись не подходят."),
    ("nameplate_vtx", "Шильдик видеопередатчика", "Текст с корпуса. Это документ, не измеренный канал."),
    ("nameplate_radio", "Шильдик радиомодуля", "Текст с корпуса. Протокол по нему не называется."),
    ("nameplate_gimbal", "Шильдик подвеса", "Текст с корпуса. Параметр подвеса остаётся отдельно."),
    ("out", "Папка отчёта", "Куда положить карточку. Без папки сборка не начнётся."),
)


def home_page(ports: list[tuple[str, str]] | None = None) -> bytes:
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in WORKFLOW)
    choices = ports if ports is not None else []
    if ports is None:
        from .usb_read import describe_ports

        choices = describe_ports()
    if choices:
        options = "".join(
            f'<option value="{html.escape(device)}">{html.escape(label)}</option>'
            for device, label in choices
        )
        usb = f"""
<form method="post" action="/usb">
<label>
<span class="title">USB-порт</span>
<span class="help">Тот же список, что на главной странице конфигуратора: выберите порт, к которому подключён полётник. Скорость 115200.</span>
<select name="port">{options}</select>
</label>
<label>
<span class="title">Папка отчёта</span>
<span class="help">Куда положить карточку после чтения.</span>
<input name="out" value="strela-out">
</label>
<p><button type="submit">Считать</button></p>
</form>
"""
    else:
        usb = "<p>Порт не виден. Подключите полётник кабелем USB и обновите страницу.</p>"
    inner = f"""
<h1>{APP_NAME}</h1>
<p class="lede">Подключите дрон по USB, выберите порт и нажмите «Считать». Программа сама отличит Betaflight, INAV, Cleanflight и MAVLink и снимет только чтение.</p>
<h2>Подключение по USB</h2>
{usb}
<div class="actions">
<a class="action quiet" href="/assemble">Собрать карточку из файлов</a>
<a class="action quiet" href="/explain">Подсказки</a>
</div>
<h2>Порядок</h2>
<ol class="steps">{steps}</ol>
"""
    return page(APP_NAME, inner).encode("utf-8")


def form_page() -> bytes:
    labels = "\n".join(
        "<label>"
        f'<span class="title">{html.escape(title)}</span>'
        f'<span class="help">{html.escape(help_text)}</span>'
        f'<input name="{html.escape(name)}">'
        "</label>"
        for name, title, help_text in FORM_FIELDS
    )
    inner = f"""
<h1>Собрать карточку</h1>
<p class="lede">Впишите пути к файлам на этом компьютере. Пустой путь пропускается. Программа ничего не пишет в полётник.</p>
<form method="post" action="/assemble">
{labels}
<p><button type="submit">Собрать карточку</button></p>
</form>
<p><a class="action quiet" href="/">Назад</a></p>
"""
    return page(f"{APP_NAME} — сборка", inner).encode("utf-8")


def explain_page() -> bytes:
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in WORKFLOW)
    inner = f"""
<h1>Подсказки</h1>
<p class="lede">Идите по шагам. Если клетка красная, прочитайте причину и сделайте только то, что написано рядом.</p>
<ol class="steps">{steps}</ol>
<p>Если страница приёмника просит пароль, введите его сами один раз. Программа пароли не перебирает.</p>
<p><a class="action quiet" href="/">Назад</a></p>
"""
    return page("Подсказки", inner).encode("utf-8")


class StrelaHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._send(200, home_page())
        elif self.path.startswith("/assemble"):
            self._send(200, form_page())
        elif self.path.startswith("/explain"):
            self._send(200, explain_page())
        else:
            self._send(404, page("Нет страницы", "<h1>Такой страницы нет</h1><p><a class=\"action\" href=\"/\">Назад к Стреле</a></p>").encode("utf-8"))

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        form = {key: values[0] for key, values in parse_qs(raw).items()}
        if self.path.startswith("/usb"):
            self._read_usb(form)
            return
        if not self.path.startswith("/assemble"):
            self._send(404, b"not found")
            return
        if not form.get("out", "").strip():
            self._send(400, page("Нужна папка", "<h1>Укажите папку отчёта</h1><p><a class=\"action\" href=\"/assemble\">Назад к форме</a></p>").encode("utf-8"))
            return
        card = assemble(inputs_from_answers(form))
        saved = write_report(card, Path(form["out"].strip()))
        self._send(200, render_html(card, saved_path=str(saved)).encode("utf-8"))

    def _read_usb(self, form: dict[str, str]) -> None:
        from .usb_read import ReadOnlyError, read_usb

        picked = form.get("port", "").strip()
        folder = form.get("out", "").strip()
        if not picked or not folder:
            self._send(400, page("Нужен порт", "<h1>Выберите USB-порт и папку отчёта</h1><p><a class=\"action\" href=\"/\">Назад</a></p>").encode("utf-8"))
            return
        try:
            card = assemble(read_usb(picked))
        except (OSError, ReadOnlyError, ValueError) as exc:
            body = page("Порт не ответил", f"<h1>Порт не ответил</h1><p>{html.escape(str(exc))}</p><p>Карточка не собрана.</p><p><a class=\"action\" href=\"/\">Назад</a></p>").encode("utf-8")
            self._send(400, body)
            return
        saved = write_report(card, Path(folder))
        self._send(200, render_html(card, saved_path=str(saved)).encode("utf-8"))

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
