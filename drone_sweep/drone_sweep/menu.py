"""Стрела: меню для человека, который снимает дрон первый раз."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .assemble import Inputs, assemble
from .elrs_http import RadioAuthRequired, fetch_pages, normalize_pages
from .hints import WORKFLOW
from .report import render_html
from .usb_read import ReadOnlyError, assert_readonly_cli, collect_flight_controller, open_betaflight_port


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
    lines.append("Пароль страницы приёмника вводится один раз. Подбор не запускается.")
    lines.append("Команды set, save, reboot и reset в приёмник и полётник не отправляются.")
    return "\n".join(lines)


def list_usb_ports(directory: Path = Path("/dev")) -> list[str]:
    if not directory.is_dir():
        return []
    found = []
    for pattern in ("ttyACM*", "ttyUSB*"):
        found.extend(str(path) for path in sorted(directory.glob(pattern)))
    return found


def run_menu(input_lines: list[str], output: list[str] | None = None, port_opener=None) -> str:
    """Numbered menu. `input_lines` are the operator's answers, in order."""
    answers_box: list[str] = list(input_lines)
    written: list[str] = output if output is not None else []

    def say(text: str) -> None:
        written.append(text)

    def ask(prompt: str) -> str:
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
            say("Стрела отправит только #, dump all и MSP_BOXNAMES. set, save и serialpassthrough не отправляются.")
            picked = ask("Путь порта, чтобы снять dump all и собрать карточку. Enter — не читать.").strip()
            if not picked:
                continue
            folder = ask("Папка отчёта").strip()
            if not folder:
                say("Папка отчёта обязательна. Порт не открывался.")
                continue
            try:
                port = open_betaflight_port(picked) if port_opener is None else port_opener(picked)
                dump_text, boxes = collect_flight_controller(port)
            except (OSError, ReadOnlyError, ValueError) as exc:
                say(f"Порт не ответил: {exc}. Карточка из пустого ответа не собрана.")
                continue
            if "betaflight" not in dump_text.lower() and "inav" not in dump_text.lower() and "cleanflight" not in dump_text.lower():
                say("В ответе порта нет баннера Betaflight, INAV или Cleanflight. Карточка не собрана, значения не выдуманы.")
                continue
            card = assemble(Inputs(dump_text=dump_text, boxnames=boxes))
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
    if not args or args == ["menu"]:
        print(run_menu(_stdin_lines()))
        return 0
    if args[0] == "explain":
        print(explain_text())
        return 0
    if args[0] == "serve":
        from .webapp import serve

        port = 8765
        if len(args) >= 3 and args[1] == "--port":
            port = int(args[2])
        serve(port)
        return 0
    if args[0] == "assemble":
        from .__main__ import main as assemble_main

        return assemble_main(args)
    if args[0] == "check-command":
        try:
            print(guard_cli(" ".join(args[1:])))
        except ReadOnlyError as exc:
            print(exc)
            return 2
        return 0
    print(explain_text())
    print("Команды: strela, strela explain, strela serve --port 8765, strela assemble ...")
    return 1


def _stdin_lines() -> list[str]:
    return [line.rstrip("\n") for line in sys.stdin]
