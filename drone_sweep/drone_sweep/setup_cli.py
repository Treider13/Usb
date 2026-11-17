"""Команда strela setup — подготовка данных после pip install."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .strela_bootstrap import run_setup, setup_is_ready


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="strela setup", description="Скачать словари ELRS и RAM-таблицу.")
    parser.add_argument("--data-dir", type=Path, help="каталог данных (или переменная STRELA_DATA)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="обновить все словари (passhelp, dwyl, elrs_rainbow, rockyou) и RAM-таблицы",
    )
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args(argv)
    try:
        run_setup(data_dir=args.data_dir, force=args.force, quiet=args.quiet)
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not args.quiet and setup_is_ready(args.data_dir):
        print("Готово. Запуск: strela serve --port 8765")
    return 0