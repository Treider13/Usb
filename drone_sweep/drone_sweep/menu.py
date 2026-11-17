"""Стрела: меню для человека, который снимает дрон первый раз."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .assemble import Inputs, assemble
from .elrs_http import RadioAuthRequired, fetch_pages, normalize_pages
from .hints import WORKFLOW
from .report import render_html
from .usb_read import ReadOnlyError, assert_readonly_cli, describe_ports, read_usb


APP_NAME = "Стрела"

QUESTIONS = (
    ("dump", "Файл dump all (Enter — пропустить)"),
    ("boxnames", "Файл имён режимов MSP_BOXNAMES, через точку с запятой"),
    ("bin", "Файл .BIN ArduPilot"),
    ("tlog", "Файл .tlog"),
    ("blackbox", "Файл Blackbox .bbl или .txt"),
    ("gps_csv", "GPS CSV от blackbox_decode"),
    ("gpx", "GPX с путевыми точками"),
    ("waypoints", "Файл .waypoints"),
    ("plan", "Файл .plan"),
    ("radio_json", "Сохранённый JSON страницы приёмника"),
    ("radio_image", "Образ flash приёмника"),
    ("binding_wordlist", "Словарь binding phrase (Enter — не подбирать)"),
    ("binding_memory_table", "JSON RAM-таблицы (Enter — пропустить)"),
    ("nameplate_vtx", "Шильдик видеопередатчика"),
    ("nameplate_radio", "Шильдик радиомодуля"),
    ("nameplate_gimbal", "Шильдик подвеса"),
    ("stm32", "Файл журнала STM32_Programmer_CLI или st-info. Enter — пропустить"),
    ("out", "Папка отчёта"),
)


def inputs_from_answers(answers: dict[str, str]) -> Inputs:
    def path_of(key: str) -> Path | None:
        text = answers.get(key, "").strip()
        return Path(text) if text else None

    def text_of(path: Path | None) -> str | None:
        if path is None:
            return None
        return path.read_text(encoding="utf-8", errors="replace")

    radio_path = path_of("radio_json")
    radio_json = json.loads(text_of(radio_path) or "null") if radio_path else None
    image_path = path_of("radio_image")
    plates = {}
    for key, label in (("vtx", "nameplate_vtx"), ("radio", "nameplate_radio"), ("gimbal", "nameplate_gimbal")):
        value = answers.get(label, "").strip()
        if value:
            plates[key] = value
    return Inputs(
        dump_text=text_of(path_of("dump")),
        boxnames=text_of(path_of("boxnames")),
        bin_path=path_of("bin"),
        tlog_path=path_of("tlog"),
        blackbox_path=path_of("blackbox"),
        gps_csv_path=path_of("gps_csv"),
        gpx_path=path_of("gpx"),
        waypoints_path=path_of("waypoints"),
        plan_path=path_of("plan"),
        radio_json=radio_json,
        radio_image=image_path.read_bytes() if image_path else None,
        nameplates=plates,
        stm32_text=text_of(path_of("stm32")),
        auth_declined=answers.get("auth_declined", "").strip() in {"1", "yes", "да"},
        binding_wordlist=path_of("binding_wordlist"),
        binding_memory_table=path_of("binding_memory_table"),
    )


def write_report(card, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "card.json").write_text(json.dumps(card.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    page = folder / "report.html"
    page.write_text(render_html(card), encoding="utf-8")
    return page


def explain_text() -> str:
    lines = [f"{APP_NAME}. Карточка собирается из файлов. Пустое поле остаётся пустым.", ""]
    lines.extend(f"{index}. {line}" for index, line in enumerate(WORKFLOW, start=1))
    lines.append("")
    lines.append("Пароль страницы приёмника вводится один раз. Сам он не подбирается.")
    lines.append("Фраза привязки ExpressLRS ищется только если указан словарь или JSON-таблица. Текст фразы в карточку не пишется.")
    lines.append("Команды set, save, reboot и reset в приёмник и полётник не отправляются.")
    return "\n".join(lines)


def list_usb_ports(directory: Path | None = None) -> list[str]:
    if directory is not None:
        if not directory.is_dir():
            return []
        found = []
        for pattern in ("ttyACM*", "ttyUSB*"):
            found.extend(str(path) for path in sorted(directory.glob(pattern)))
        return found
    return [device for device, _label in describe_ports()]


def run_menu(
    input_lines: list[str] | None = None,
    output: list[str] | None = None,
    port_opener=None,
    echo: bool = False,
) -> str:
    """Numbered menu. A list of answers is for tests. A terminal asks one line at a time."""
    answers_box: list[str] | None = None if input_lines is None else list(input_lines)
    written: list[str] = output if output is not None else []

    def say(text: str) -> None:
        written.append(text)
        if echo:
            print(text, flush=True)

    def ask(prompt: str) -> str:
        if answers_box is None:
            try:
                answer = input(prompt + " ")
            except EOFError:
                answer = ""
            written.append(prompt)
            return answer.strip()
        say(prompt)
        if not answers_box:
            return ""
        return answers_box.pop(0)

    say(f"{APP_NAME}")
    while True:
        say("1. Собрать карточку из файлов")
        say("2. Подсказки")
        say("3. Какие USB-порты видны")
        say("4. Прочитать страницу приёмника по адресу")
        say("5. Выход")
        choice = ask("Номер").strip()
        if choice == "1":
            answers = {key: ask(label) for key, label in QUESTIONS}
            if not answers.get("out", "").strip():
                say("Папка отчёта обязательна. Карточка не записана.")
                continue
            card = assemble(inputs_from_answers(answers))
            page = write_report(card, Path(answers["out"].strip()))
            say(f"Отчёт: {page}")
            say(f"Дыр: {len(card.holes)}. Источник маршрута: {card.fields['route_source'].value}")
        elif choice == "2":
            say(explain_text())
        elif choice == "3":
            ports = list_usb_ports()
            say("Порты: " + (", ".join(ports) if ports else "не найдены. Подключите полётник кабелем USB и откройте меню снова."))
            say("Кнопка чтения сама отличает Betaflight, INAV, Cleanflight и ArduPilot. Сначала MSP или список параметров, для полётника с CLI затем dump all. У ArduPilot запрашиваются версия, параметры и последний журнал .BIN. LOG_ERASE не отправляется, взведение не снимается. У Betaflight после дампа уходит exit noreboot: голый exit в cli.c перезагружает плату. У INAV exit вызывает cliReboot, поэтому не отправляется. set, save и serialpassthrough не отправляются.")
            picked = ask("Путь порта. Enter — не читать.").strip()
            if not picked:
                continue
            folder = ask("Папка отчёта").strip()
            if not folder:
                say("Папка отчёта обязательна. Порт не открывался.")
                continue
            try:
                card_inputs = read_usb(picked, port_opener=port_opener, log_dir=folder)
            except (OSError, ReadOnlyError, ValueError) as exc:
                say(f"Порт не ответил: {exc}. Карточка из пустого ответа не собрана.")
                continue
            dump_text = card_inputs.dump_text or ""
            if card_inputs.mavlink_rows is None and "betaflight" not in dump_text.lower() and "inav" not in dump_text.lower() and "cleanflight" not in dump_text.lower():
                say("В ответе порта нет баннера Betaflight, INAV или Cleanflight и нет HEARTBEAT. Карточка не собрана, значения не выдуманы.")
                continue
            card = assemble(card_inputs)
            page = write_report(card, Path(folder))
            say(f"Отчёт: {page}")
            receiver = card.fields.get("receiver_port")
            if receiver is not None and receiver.status == "confirmed":
                say(f"Приёмник назначен на {receiver.value}. Проход UART не включён.")
            say(f"Дыр: {len(card.holes)}. Источник маршрута: {card.fields['route_source'].value}")
        elif choice == "4":
            base = ask("Адрес, обычно http://10.0.0.1").strip()
            if not base:
                say("Адрес пуст. Страница не запрашивалась.")
                continue
            try:
                pages = fetch_pages(base)
            except RadioAuthRequired:
                say("Страница просит пароль. Введите его сами в браузере, сохраните JSON и вернитесь в пункт 1. Повторных попыток нет.")
                continue
            except OSError as exc:
                say(f"Страница не открылась: {exc}. Проверьте, что компьютер в сети приёмника, а не в сети роутера.")
                continue
            normalized = normalize_pages(pages)
            folder = Path(ask("Папка отчёта").strip() or "strela-out")
            card = assemble(Inputs(radio_json=normalized))
            page = write_report(card, folder)
            say(f"Отчёт: {page}")
        elif choice in {"5", "0", ""}:
            say("Выход")
            break
        else:
            say("Такого пункта нет. Введите число от 1 до 5.")
    return "\n".join(written)


def guard_cli(command: str) -> str:
    return assert_readonly_cli(command)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        return _dispatch(args)
    except KeyboardInterrupt:
        print("Стрела остановлена.")
        return 130


def _dispatch(args: list[str]) -> int:
    if args and args[0] == "serve":
        from .webapp import ServeError, serve

        try:
            port = _serve_port(args)
        except ValueError as exc:
            print(exc)
            return 2
        try:
            serve(port)
        except ServeError as exc:
            print(exc)
            return 2
        return 0
    if not args or args == ["menu"]:
        if sys.stdin.isatty():
            run_menu(echo=True)
        else:
            print(run_menu(_stdin_lines()))
        return 0
    if args[0] == "explain":
        print(explain_text())
        return 0
    if args[0] == "assemble":
        from .__main__ import main as assemble_main

        return assemble_main(args)
    if args[0] == "elrs":
        from .elrs_cli import main as elrs_main

        return elrs_main(args[1:])
    if args[0] == "check-command":
        try:
            print(guard_cli(" ".join(args[1:])))
        except ReadOnlyError as exc:
            print(exc)
            return 2
        return 0
    print(explain_text())
    print(
        "Команды: strela, strela explain, strela serve --port 8765, strela assemble ..., "
        "strela elrs uid|dump|crack|lookup|lookup-memory|build-rainbow|build-memory ..."
    )
    return 1


def _serve_port(args: list[str]) -> int:
    if len(args) == 1:
        return 8765
    raw = ""
    if len(args) == 2 and args[1].startswith("--port="):
        raw = args[1].split("=", 1)[1]
    elif len(args) == 3 and args[1] == "--port":
        raw = args[2]
    else:
        raise ValueError("Команда: strela serve --port 8765")
    try:
        port = int(raw)
    except ValueError:
        raise ValueError(f"Номер порта должен быть числом: {raw}") from None
    if not 0 <= port <= 65535:
        raise ValueError(f"Номер порта вне диапазона: {port}")
    return port


def _stdin_lines() -> list[str]:
    return [line.rstrip("\n") for line in sys.stdin]
