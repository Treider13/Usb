"""Command line. `assemble` reads files. It does not open a radio password attack."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .assemble import Inputs, assemble
from .hints import WORKFLOW
from .report import render_html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="drone-sweep")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("explain", help="короткий порядок работы")
    build = sub.add_parser("assemble", help="собрать карточку из уже снятых файлов")
    build.add_argument("--dump", type=Path)
    build.add_argument("--boxnames", type=Path)
    build.add_argument("--bin", type=Path)
    build.add_argument("--tlog", type=Path)
    build.add_argument("--blackbox", type=Path)
    build.add_argument("--gps-csv", type=Path)
    build.add_argument("--gpx", type=Path)
    build.add_argument("--waypoints", type=Path)
    build.add_argument("--plan", type=Path)
    build.add_argument("--radio-json", type=Path)
    build.add_argument("--radio-image", type=Path)
    build.add_argument("--stm32", type=Path, help="сохранённый вывод STM32_Programmer_CLI --connect или st-info --probe")
    build.add_argument("--nameplate", action="append", default=[], help="ключ=текст шильдика, например vtx=Skyzone")
    build.add_argument("--banner", default="")
    build.add_argument("--auth-declined", action="store_true")
    build.add_argument(
        "--binding-wordlist",
        type=Path,
        help="словарь binding phrase ExpressLRS; при наличии radio_uid только статус, без сохранения фразы",
    )
    build.add_argument(
        "--binding-memory-table",
        type=Path,
        help="JSON радужной таблицы в RAM (strela elrs build-memory --out)",
    )
    build.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "explain":
        for index, line in enumerate(WORKFLOW, start=1):
            print(f"{index}. {line}")
        return 0
    plates = {}
    for item in args.nameplate:
        if "=" not in item:
            raise SystemExit(f"шильдик должен быть ключ=текст: {item}")
        key, value = item.split("=", 1)
        plates[key.strip()] = value.strip()
    radio_json = None
    if args.radio_json is not None:
        radio_json = json.loads(args.radio_json.read_text(encoding="utf-8"))
    radio_image = args.radio_image.read_bytes() if args.radio_image is not None else None
    card = assemble(
        Inputs(
            dump_text=args.dump.read_text(encoding="utf-8", errors="replace") if args.dump else None,
            boxnames=args.boxnames.read_text(encoding="utf-8", errors="replace") if args.boxnames else None,
            bin_path=args.bin,
            tlog_path=args.tlog,
            blackbox_path=args.blackbox,
            gps_csv_path=args.gps_csv,
            gpx_path=args.gpx,
            waypoints_path=args.waypoints,
            plan_path=args.plan,
            radio_json=radio_json,
            radio_image=radio_image,
            nameplates=plates,
            stm32_text=args.stm32.read_text(encoding="utf-8", errors="replace") if args.stm32 else None,
            banner=args.banner,
            auth_declined=args.auth_declined,
            binding_wordlist=args.binding_wordlist,
            binding_memory_table=args.binding_memory_table,
        )
    )
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "card.json").write_text(
        json.dumps(card.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out / "report.html").write_text(render_html(card), encoding="utf-8")
    print(args.out / "report.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
