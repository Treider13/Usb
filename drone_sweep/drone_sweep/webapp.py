"""Local menu in the browser. Files stay on this computer."""

from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .assemble import assemble
from .hints import WORKFLOW
from .menu import APP_NAME, _log_id, inputs_from_answers, write_report
from .report import render_html
from .theme import page
from .top2026 import render_top_inner


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
    ("radio_image", "Образ приёмника", "Файл образа приёмника."),
    ("binding_wordlist", "Словарь binding phrase", "ExpressLRS/MILELRS: подбор по UID. Пусто — не подбирать."),
    ("binding_memory_table", "JSON RAM-таблицы", "Файл от strela elrs build-memory --out. Альтернатива словарю."),
    ("stm32", "Журнал STM32", "Сохранённый вывод STM32_Programmer_CLI --connect port=SWD или st-info --probe. Стирание и запись не подходят."),
    ("diff", "diff all", "Сохранённый ответ diff all. Это отличия от заводских, не запись на плату."),
    ("wp", "wp INAV", "Сохранённый ответ команды wp. load, save и reset в этот файл не кладите."),
    ("nameplate_vtx", "Шильдик видеопередатчика", "Текст с корпуса. Это документ, не измеренный канал."),
    ("nameplate_radio", "Шильдик радиомодуля", "Текст с корпуса. Протокол по нему не называется."),
    ("nameplate_gimbal", "Шильдик подвеса", "Текст с корпуса. Параметр подвеса остаётся отдельно."),
    ("out", "Папка отчёта", "Куда положить карточку. Без папки сборка не начнётся."),
)

_MULTIPART = ' enctype="multipart/form-data"'

_ASSEMBLE_FILE_KEYS = tuple(
    name
    for name, _, _ in FORM_FIELDS
    if name != "out" and not name.startswith("nameplate_")
)


def _file_or_path_label(name: str, title: str, *, accept: str = "") -> str:
    accept_attr = f' accept="{html.escape(accept)}"' if accept else ""
    return (
        "<label>"
        f'<span class="title">{html.escape(title)}</span>'
        f'<input type="file" name="{html.escape(name)}_file"{accept_attr}>'
        f'<span class="help">или путь на этом ПК</span>'
        f'<input name="{html.escape(name)}" placeholder="/path/...">'
        "</label>"
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
<label class="folder">Журнал <input name="log_id" value="" aria-label="Номер журнала ArduPilot" placeholder="последний"></label>
<button type="submit">Считать</button>
</form>
"""


def home_page(ports: list[tuple[str, str]] | None = None) -> bytes:
    inner = f"""
<section class="hero">
<h1>Стрела</h1>
<p class="lede">Стрела читает борт по USB и собирает карточку: прошивка, полётник, тип рамы, приёмник, картинка и журнал.</p>
</section>
<div class="cards">
<article class="panel"><h2>Подключение по USB</h2><p>В верхней полосе выберите порт. Скорость 115200. Кнопка «Считать».</p></article>
<article class="panel"><h2>Чтение</h2><p>Слева порт и папка. Справа — плата, дамп, параметры и журнал .BIN.</p></article>
<article class="panel"><h2>Карточка</h2><p>Зелёным — то, что плата ответила. Чего не хватает — коротким списком.</p></article>
</div>
<article class="panel wide">
<h2>Binding phrase из образа ELRS</h2>
<p class="help">Без пароля Wi‑Fi: загрузите дамп flash. Словарь подхватится из <code>strela setup</code>, если установка уже была.</p>
<form method="post" action="/crack"{_MULTIPART}>
<input type="hidden" name="action" value="phrase_from_flash">
<label>Образ .bin / Intel HEX <input type="file" name="flash_file" accept=".bin,.hex,.txt"></label>
<label>Словарь <input type="file" name="binding_wordlist_file" accept=".txt,.lst"></label>
<label>или JSON RAM-таблица <input type="file" name="memory_table_file" accept=".json"></label>
<p><button type="submit">Получить binding phrase</button></p>
</form>
<p><a class="action quiet" href="/crack">Все инструменты подбора</a></p>
</article>
<p><a class="action" href="/read">Открыть чтение</a> <a class="action quiet" href="/assemble">Собрать карточку из файлов</a> <a class="action quiet" href="/crack">Подбор (ELRS/MILELRS)</a> <a class="action quiet" href="/top2026">ТОП 2026</a></p>
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
            ("read_msp", "Плата и сборка", "Версия, имя полётника, дата сборки и позывной борта."),
            ("read_dump", "Дамп настроек", "version, status и dump all."),
            ("read_params", "Параметры ArduPilot", "Весь список параметров."),
            ("read_bin", "Журнал .BIN", "Последний журнал с платы."),
        )
    )
    button = "<p><button type=\"submit\">Считать с платы</button></p>" if choices else ""
    inner = f"""
<h1>Чтение</h1>
<p class="lede">Слева порт и папка. Справа — что снять с борта.</p>
<form method="post" action="/usb">
<input type="hidden" name="chooser" value="1">
<div class="split">
<section class="panel">
<h2>Плата</h2>
<div class="row"><div><strong>Порт</strong><p>Тот же список, что в верхней полосе.</p></div></div>
{port_field}
<p class="baud">115200</p>
<label class="folder">Папка <input name="out" value="strela-out" aria-label="Папка отчёта"></label>
<label class="folder">Журнал <input name="log_id" value="" aria-label="Номер журнала ArduPilot" placeholder="последний"></label>
<p>Имя полётника, прошивка и тип рамы появятся в карточке после чтения. Пустой номер журнала — последний непустой .BIN.</p>
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
    labels_parts: list[str] = []
    for name, title, help_text in FORM_FIELDS:
        if name == "out":
            labels_parts.append(
                "<label>"
                f'<span class="title">{html.escape(title)}</span>'
                f'<span class="help">{html.escape(help_text)}</span>'
                f'<input name="{html.escape(name)}">'
                "</label>"
            )
            continue
        if name.startswith("nameplate_"):
            labels_parts.append(
                "<label>"
                f'<span class="title">{html.escape(title)}</span>'
                f'<span class="help">{html.escape(help_text)}</span>'
                f'<input name="{html.escape(name)}">'
                "</label>"
            )
            continue
        labels_parts.append(
            _file_or_path_label(name, title)
            + f'<span class="help">{html.escape(help_text)}</span>'
        )
    labels = "\n".join(labels_parts)
    inner = f"""
<h1>Собрать карточку</h1>
<p class="lede">Выберите файлы с компьютера или впишите пути. Пустое поле пропускается. Программа ничего не пишет в полётник.</p>
<form method="post" action="/assemble"{_MULTIPART}>
{labels}
<p><button type="submit">Собрать карточку</button></p>
</form>
"""
    return page(f"{APP_NAME} — файлы", inner, connect=connect_bar(), current="/assemble").encode("utf-8")


def _bundled_elrs_defaults() -> dict[str, str]:
    from .strela_bootstrap import default_binding_paths

    return {key: str(path) for key, path in default_binding_paths().items()}


def _dict_source_select() -> str:
    from .strela_bootstrap import list_catalog

    options = "".join(
        f'<option value="{html.escape(key)}">{html.escape(label)}</option>'
        for key, label in list_catalog()
    )
    return f'<label>Словари <select name="dict_source">{options}</select></label>'


def _drone_port_select() -> str:
    choices = _ports(None)
    if not choices:
        return "<p class='help'>USB не виден — подключите полётник и обновите страницу.</p>"
    options = '<option value="">— не читать USB —</option>' + "".join(
        f'<option value="{html.escape(device)}">{html.escape(label)}</option>'
        for device, label in choices
    )
    return f'<label>USB полётник <select name="drone_port">{options}</select></label>'


def crack_page(result: str = "", prefill_uid: str = "") -> bytes:
    result_block = f'<section class="report">{result}</section>' if result else ""
    uid_value = html.escape(prefill_uid)
    bundled = _bundled_elrs_defaults()
    bundled_wordlist = html.escape(bundled.get("wordlist", ""))
    bundled_table = html.escape(bundled.get("memory_table", ""))
    bundled_note = ""
    if bundled:
        bundled_note = (
            "<p class='help'>Словарь из установки: "
            f"<code>{bundled_wordlist or bundled_table}</code> — можно не выбирать файл, если <code>strela setup</code> уже выполнен.</p>"
        )
    inner = f"""
<h1>Подбор</h1>
<p class="lede">Словари и ссылки — <a href="/top2026#elrs-wordlists">ТОП 2026 → ELRS</a>. Как <a href="https://github.com/CIRCL/Drone-Forensic/tree/main/elrs">CIRCL Drone-Forensic elrs/</a>:
UID из binding phrase, JSON из flash, подбор фразы. Работает для <strong>ExpressLRS</strong> и <strong>MILELRS</strong>.
<strong>OrangeRX</strong> — протокол DSM, сюда не подходит. Пароль Wi‑Fi не нужен — нужен словарь binding phrase.</p>
{bundled_note}
{result_block}
<article class="panel wide panel-accent">
<h2>Считать с борта (USB + Wi‑Fi модуля)</h2>
<p class="help">Дрон на USB и/или приёмник в Wi‑Fi ExpressLRS RX. Пароль Wi‑Fi — только для WebUI (<code>expresslrs</code>), не binding phrase.</p>
<form method="post" action="/crack"{_MULTIPART}>
<input type="hidden" name="action" value="read_drone">
{_drone_port_select()}
<label>Адрес модуля <input name="radio_base" value="http://10.0.0.1"></label>
<label>Пароль Wi‑Fi WebUI <input name="wifi_password" type="password" placeholder="expresslrs" autocomplete="off"></label>
{_dict_source_select()}
<p><button type="submit">Считать и подобрать фразу</button></p>
</form>
</article>
<article class="panel wide panel-accent">
<h2>Фраза из образа за один шаг</h2>
<form method="post" action="/crack"{_MULTIPART}>
<input type="hidden" name="action" value="phrase_from_flash">
{_dict_source_select()}
<label>Образ с ПК <input type="file" name="flash_file" accept=".bin,.hex,.txt"></label>
<span class="help">или путь <input name="flash_path"></span>
<label>Словарь с ПК <input type="file" name="binding_wordlist_file" accept=".txt,.lst"></label>
<span class="help">или путь <input name="binding_wordlist" value="{bundled_wordlist}"></span>
<label>JSON RAM-таблица <input type="file" name="memory_table_file" accept=".json"></label>
<span class="help">или путь <input name="memory_table" value="{bundled_table}"></span>
<p><button type="submit">UID из образа → binding phrase</button></p>
</form>
</article>
<div class="cards">
<article class="panel">
<h2>UID из фразы</h2>
<form method="post" action="/crack"{_MULTIPART}>
<input type="hidden" name="action" value="uid">
<label>Binding phrase <input name="phrase" placeholder="например test"></label>
<p><button type="submit">Посчитать UID</button></p>
</form>
</article>
<article class="panel">
<h2>Разбор flash / HEX</h2>
<form method="post" action="/crack"{_MULTIPART}>
<input type="hidden" name="action" value="dump">
<label>Файл с ПК <input type="file" name="flash_file" accept=".bin,.hex,.txt"></label>
<span class="help">или путь <input name="flash_path"></span>
<p><button type="submit">Извлечь UID и Wi‑Fi (без пароля)</button></p>
</form>
</article>
<article class="panel">
<h2>Подбор фразы по UID</h2>
<form method="post" action="/crack"{_MULTIPART}>
<input type="hidden" name="action" value="crack">
{_dict_source_select()}
<label>UID (через запятую или hex) <input name="uid" value="{uid_value}" placeholder="79,4,253,130,33,85"></label>
<label>Словарь с ПК <input type="file" name="binding_wordlist_file" accept=".txt,.lst"></label>
<span class="help">или путь <input name="binding_wordlist" value="{bundled_wordlist}"></span>
<label>JSON таблица <input type="file" name="memory_table_file" accept=".json"></label>
<span class="help">или путь <input name="memory_table" value="{bundled_table}"></span>
<p><button type="submit">Подобрать</button></p>
</form>
</article>
<article class="panel">
<h2>Собрать RAM-таблицу</h2>
<form method="post" action="/crack"{_MULTIPART}>
<input type="hidden" name="action" value="build_memory">
<label>Словарь <input type="file" name="memory_wordlist_file" accept=".txt,.lst"></label>
<span class="help">или путь <input name="memory_wordlist"></span>
<label>Сохранить JSON на диск <input name="memory_out"></label>
<p><button type="submit">Построить таблицу</button></p>
</form>
</article>
</div>
<article class="panel cell wide">
<h2>Карточка с подбором</h2>
<form method="post" action="/crack"{_MULTIPART}>
<input type="hidden" name="action" value="assemble">
<div class="grid">
{_file_or_path_label("radio_json_path", "JSON приёмника", accept=".json")}
{_file_or_path_label("radio_image_path", "Образ flash", accept=".bin,.hex")}
{_file_or_path_label("assemble_wordlist", "Словарь")}
{_file_or_path_label("assemble_memory", "JSON таблица", accept=".json")}
<label>Папка отчёта <input name="out" value="strela-out"></label>
</div>
<p><button type="submit">Собрать карточку</button></p>
</form>
<p class="help">В card.json будет статус <code>radio_binding_phrase_crack</code>, текст фразы не сохраняется.</p>
</article>
"""
    return page(f"{APP_NAME} — подбор", inner, connect=connect_bar(), current="/crack").encode("utf-8")


def top_page(ports: list[tuple[str, str]] | None = None) -> bytes:
    inner = render_top_inner()
    return page(f"{APP_NAME} — ТОП 2026", inner, connect=connect_bar(ports), current="/top2026").encode(
        "utf-8"
    )


def explain_page() -> bytes:
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in WORKFLOW)
    inner = f"""
<h1>Подсказки</h1>
<p class="lede">Идите по шагам. Если клетка красная, прочитайте причину и сделайте только то, что написано рядом.</p>
<ol class="steps">{steps}</ol>
<p>Если страница приёмника просит пароль Wi‑Fi, введите его сами один раз — это не вкладка «Подбор».</p>
<p>Binding phrase ExpressLRS/MILELRS — вкладка <a href="/crack">Подбор</a> (как CIRCL elrs).</p>
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
        elif self.path.startswith("/crack"):
            self._send(200, crack_page())
        elif self.path.startswith("/top2026"):
            self._send(200, top_page())
        elif self.path.startswith("/explain"):
            self._send(200, explain_page())
        else:
            self._send(404, page("Нет страницы", "<h1>Такой страницы нет</h1><p><a class=\"action\" href=\"/\">Назад к Стреле</a></p>").encode("utf-8"))

    def do_POST(self) -> None:
        from .webapp_forms import merge_uploaded_paths, parse_post_body

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type")
        form, files = parse_post_body(content_type, body)
        if self.path.startswith("/usb"):
            self._read_usb(form)
            return
        if self.path.startswith("/crack"):
            self._send(200, crack_response(form, files))
            return
        if not self.path.startswith("/assemble"):
            self._send(404, b"not found")
            return
        if not form.get("out", "").strip():
            self._send(400, page("Нужна папка", "<h1>Укажите папку отчёта</h1><p><a class=\"action\" href=\"/assemble\">Назад к форме</a></p>").encode("utf-8"))
            return
        merged = merge_uploaded_paths(form, files, _ASSEMBLE_FILE_KEYS)
        bundled = _bundled_elrs_defaults()
        if not merged.get("binding_wordlist", "").strip() and bundled.get("wordlist"):
            merged["binding_wordlist"] = bundled["wordlist"]
        if not merged.get("binding_memory_table", "").strip() and bundled.get("memory_table"):
            merged["binding_memory_table"] = bundled["memory_table"]
        card = assemble(inputs_from_answers(merged))
        saved = write_report(card, Path(form["out"].strip()))
        self._send(200, render_html(card, saved_path=str(saved)).encode("utf-8"))

    def _read_usb(self, form: dict[str, str]) -> None:
        from .usb_read import ReadOnlyError, read_usb

        picked = form.get("port", "").strip()
        folder = form.get("out", "").strip()
        if not picked or not folder:
            self._send(400, page("Нужен порт", "<h1>Выберите USB-порт и папку отчёта</h1><p><a class=\"action\" href=\"/\">Назад</a></p>").encode("utf-8"))
            return
        log_id, log_error = _log_id(form.get("log_id", "").strip())
        if log_error:
            self._send(400, page("Номер журнала", f"<h1>Номер журнала</h1><p>{html.escape(log_error)}</p><p><a class=\"action\" href=\"/read\">Назад</a></p>").encode("utf-8"))
            return
        try:
            card = assemble(read_usb(picked, log_dir=folder, wants=_wants(form), log_id=log_id))
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


def crack_response(form: dict[str, str], files: dict | None = None) -> bytes:
    from .elrs_ui import handle_elrs_form

    _ok, fragment, prefill_uid = handle_elrs_form(form, files or {})
    if fragment.lstrip().startswith("<!DOCTYPE"):
        return fragment.encode("utf-8")
    return crack_page(fragment, prefill_uid=prefill_uid)


def serve(port: int = 8765) -> None:
    from .strela_bootstrap import ensure_setup

    ensure_setup(quiet=True)
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
