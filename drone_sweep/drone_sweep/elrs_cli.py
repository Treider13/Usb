"""CLI подбора binding phrase ExpressLRS."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

from .elrs_binding import binding_phrase_to_uid, binding_phrase_uid_hex, iter_wordlist_lines, parse_uid_bytes, uid_bytes_to_hex
from .elrs_rainbow import build_rainbow_table, crack_binding_phrase, lookup_binding_phrase, make_redis_store


def _add_redis_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--kvrocks-host", default="127.0.0.1")
    parser.add_argument("--kvrocks-port", type=int, default=6666)
    parser.add_argument("--kvrocks-db", type=int, default=5)
    parser.add_argument("--kvrocks-prefix", default="elrs_rainbow")


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(prog="strela elrs", description="ExpressLRS binding phrase и rainbow-таблица (CIRCL).")
    sub = parser.add_subparsers(dest="command", required=True)

    uid_cmd = sub.add_parser("uid", help="UID из фразы привязки")
    uid_cmd.add_argument("phrase", help="binding phrase")

    crack_cmd = sub.add_parser("crack", help="перебор словаря по известному UID")
    crack_cmd.add_argument("uid", help="шесть байт через запятую, например 79,4,253,130,33,85")
    crack_cmd.add_argument("wordlist", type=Path)
    crack_cmd.add_argument("--encoding", default="utf-8")

    lookup_cmd = sub.add_parser("lookup", help="фраза из radужной таблицы kvrocks")
    lookup_cmd.add_argument("uid", help="шесть байт через запятую")
    _add_redis_flags(lookup_cmd)

    build_cmd = sub.add_parser("build-rainbow", help="словарь в kvrocks (elrs_do_rainbow)")
    build_cmd.add_argument("wordlist")
    build_cmd.add_argument("--status-file")
    build_cmd.add_argument("--chunk-size", type=int, default=10_000)
    build_cmd.add_argument("--processes", type=int)
    build_cmd.add_argument("--prefetch", type=int, default=4)
    build_cmd.add_argument("--encoding", default="utf-8")
    _add_redis_flags(build_cmd)

    build_local = sub.add_parser("build-memory", help="словарь в RAM (малые списки и тесты)")
    build_local.add_argument("wordlist")
    build_local.add_argument("--encoding", default="utf-8")

    parsed = parser.parse_args(args)
    if parsed.command == "uid":
        uid = binding_phrase_to_uid(parsed.phrase)
        print("UID (dec):", ",".join(str(byte) for byte in uid))
        print("UID (hex):", uid_bytes_to_hex(uid))
        return 0
    if parsed.command == "crack":
        if not parsed.wordlist.is_file():
            print(f"словарь не найден: {parsed.wordlist}", file=sys.stderr)
            return 1
        uid = parse_uid_bytes(parsed.uid)
        phrase = crack_binding_phrase(uid, parsed.wordlist, encoding=parsed.encoding)
        if phrase is None:
            print("фраза не найдена", file=sys.stderr)
            return 1
        print(phrase)
        return 0
    if parsed.command == "lookup":
        uid = parse_uid_bytes(parsed.uid)
        store = make_redis_store(
            host=parsed.kvrocks_host,
            port=parsed.kvrocks_port,
            db=parsed.kvrocks_db,
            prefix=parsed.kvrocks_prefix,
        )
        phrase = lookup_binding_phrase(uid, store)
        if phrase is None:
            print("в таблице нет UID", file=sys.stderr)
            return 1
        print(phrase)
        return 0
    if parsed.command == "build-rainbow":
        wordlist_path = Path(parsed.wordlist)
        if not wordlist_path.is_file():
            print(f"словарь не найден: {wordlist_path}", file=sys.stderr)
            return 1
        store = make_redis_store(
            host=parsed.kvrocks_host,
            port=parsed.kvrocks_port,
            db=parsed.kvrocks_db,
            prefix=parsed.kvrocks_prefix,
        )
        status = Path(parsed.status_file) if parsed.status_file else None

        def progress(batch: int, total: int, offset: int) -> None:
            print(f"записано {batch}, всего {total}, offset={offset}")

        total = build_rainbow_table(
            wordlist_path,
            store,
            status_file=status,
            chunk_size=parsed.chunk_size,
            processes=parsed.processes,
            prefetch=parsed.prefetch,
            encoding=parsed.encoding,
            on_progress=progress,
        )
        print(f"готово, обработано {total}")
        return 0
    if parsed.command == "build-memory":
        table: dict[str, str] = {}
        for phrase, _ in iter_wordlist_lines(Path(parsed.wordlist), encoding=parsed.encoding):
            table[binding_phrase_uid_hex(phrase)] = phrase
        print(f"записано {len(table)} UID")
        return 0
    return 1