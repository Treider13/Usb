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


def _ports(ports: list[tuple[str, str]] | None) -> list[tuple[str, str]]:
    if ports is not None:
        return ports
    from .usb_read import describe_ports

    return describe_ports()


def connect_bar(ports: list[tuple[str, str]] | None = None) -> str:
    choices = _ports(ports)
    if not choices:
        return '<p class="connect">Порт не виден. Подключите полётник кабелем USB и обновите страницу.</p>'
    options = "".join(
        f'<option value="{html.escape(device)}">{html.escape(label)}</option>'
        for device, label in choices
    )
    return f"""
<form class="connect" method="post" action="/usb">
<select name="port" aria-label="USB-порт">{options}</select>
<span class="baud">115200</span>
<label class="folder">Папка <input name="out" value="strela-out" aria-label="Папка отчёта"></label>
<button type="submit">Считать</button>
</form>
"""


def home_page(ports: list[tuple[str, str]] | None = None) -> bytes:
    inner = """
<section class="hero">
<h1>Стрела</h1>
<p class="lede">Стрела читает полётник и собирает карточку. Она сама отличает Betaflight, INAV, Cleanflight и ArduPilot. В карточке видно, какая плата, какая сборка, какие порты, какая частота картинки и что записано в журнале. В плату ничего не записывается: нет прошивки, нет стирания, нет сохранения настроек.</p>
</section>
<div class="cards">
<article class="panel"><h2>Подключение по USB</h2><p>В верхней полосе выберите порт. Скорость 115200, как в конфигураторе. Кнопка «Считать» открывает порт один раз и снимает только чтение.</p></article>
<article class="panel"><h2>Чтение</h2><p>Окно как у программатора: слева плата и сборка, справа переключатели того, что снимать. Переключатель не прошивает плату.</p></article>
<article class="panel"><h2>Журнал</h2><p>С ArduPilot запрашиваются версия, все параметры и последний журнал .BIN. Если борт взведён, плата журнал не отдаёт, и Стрела взведение не снимает.</p></article>
<article class="panel"><h2>Карточка</h2><p>Пустая клетка остаётся пустой, рядом причина. Зелёная пометка — значение прочитано. Синяя — надпись с шильдика.</p></article>
</div>
<p><a class="action" href="/read">Открыть чтение</a> <a class="action quiet" href="/assemble">Собрать карточку из файлов</a></p>
"""
    return page(APP_NAME, inner, connect=connect_bar(ports), current="/").encode("utf-8")


def read_page(ports: list[tuple[str, str]] | None = None) -> bytes:
    choices = _ports(ports)
    if choices:
        options = "".join(
            f'<option value="{html.escape(device)}">{html.escape(label)}</option>'
            for device, label in choices
        )
        port_field = f'<select name="port" aria-label="USB-порт">{options}</select>'
    else:
        port_field = '<p>Порт не виден. Подключите полётник и обновите страницу.</p>'
    switches = "".join(
        f"""
<div class="row">
<div><strong>{html.escape(title)}</strong><p>{html.escape(help_text)}</p></div>
<label class="switch"><input type="checkbox" name="{html.escape(name)}" value="1" checked><span class="track"></span></label>
</div>
"""
        for name, title, help_text in (
            ("read_msp", "Плата и сборка", "Версия, имя платы, дата сборки и имя борта. Те же ответы MSP, что конфигуратор показывает до прошивки."),
            ("read_dump", "Дамп настроек", "version, status и dump all. Для Betaflight после дампа уходит exit noreboot. Для INAV exit не уходит: он перезагружает плату."),
            ("read_params", "Параметры ArduPilot", "Весь список PARAM_REQUEST_LIST. Пропущенный номер запрашивается ещё раз чтением, значение не пишется."),
            ("read_bin", "Журнал .BIN", "Последний ненулевой журнал с платы. Стирание журнала не отправляется."),
        )
    )
    button = "<p><button type=\"submit\">Считать с платы</button></p>" if choices else ""
    inner = f"""
<h1>Чтение</h1>
<p class="lede">Слева то, что конфигуратор называет платой и сборкой. Справа переключатели: что снять с борта. Кнопка читает. Прошивка на плату не отправляется.</p>
<form method="post" action="/usb">
<input type="hidden" name="chooser" value="1">
<div class="split">
<section class="panel">
<h2>Плата</h2>
<div class="row"><div><strong>Порт</strong><p>Тот же список, что в верхней полосе.</p></div></div>
{port_field}
<p class="baud">115200</p>
<label class="folder">Папка <input name="out" value="strela-out" aria-label="Папка отчёта"></label>
<p>Имя платы, версия и дата сборки появятся в карточке после чтения. Пока борт не ответил, эти строки не выдумываются.</p>
</section>
<section class="panel">
<h2>Сборка</h2>
{switches}
</section>
</div>
{button}
</form>
"""
    return page(f"{APP_NAME} — чтение", inner, connect=connect_bar(ports), current="/read").encode("utf-8")


def _wants(form: dict[str, str]) -> dict | None:
    if form.get("chooser") != "1":
        return None
    return {
        "msp": form.get("read_msp") == "1",
        "dump": form.get("read_dump") == "1",
        "params": form.get("read_params") == "1",
        "bin": form.get("read_bin") == "1",
    }


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
"""
    return page(f"{APP_NAME} — файлы", inner, connect=connect_bar(), current="/assemble").encode("utf-8")


def explain_page() -> bytes:
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in WORKFLOW)
    inner = f"""
<h1>Подсказки</h1>
<p class="lede">Идите по шагам. Если клетка красная, прочитайте причину и сделайте только то, что написано рядом.</p>
<ol class="steps">{steps}</ol>
<p>Если страница приёмника просит пароль, введите его сами один раз. Программа пароли не перебирает.</p>
"""
    return page("Подсказки", inner, connect=connect_bar(), current="/explain").encode("utf-8")


class StrelaHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._send(200, home_page())
        elif self.path.startswith("/read"):
            self._send(200, read_page())
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
            card = assemble(read_usb(picked, log_dir=folder, wants=_wants(form)))
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


class ServeError(Exception):
    pass


def serve(port: int = 8765) -> None:
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), StrelaHandler)
    except OSError as exc:
        raise ServeError(f"Адрес 127.0.0.1:{port} занят ({exc}).") from exc
    print(f"{APP_NAME}: http://127.0.0.1:{port}", flush=True)
    print("Остановка: Ctrl+C", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
