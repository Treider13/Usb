"""CLI подбора binding phrase ExpressLRS."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .dump_elrs import build_json_payload, compute_hashes, extract_json_objects
from .elrs_binding import binding_phrase_to_uid, parse_uid_bytes, uid_bytes_to_hex
from .elrs_rainbow import (
    build_memory_table,
    build_rainbow_table,
    crack_binding_phrase,
    crack_binding_phrase_from_store,
    load_memory_table,
    lookup_binding_phrase,
    make_redis_store,
    save_memory_table,
)


def _add_redis_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--kvrocks-host", default="127.0.0.1")
    parser.add_argument("--kvrocks-port", type=int, default=6666)
    parser.add_argument("--kvrocks-db", type=int, default=5)
    parser.add_argument("--kvrocks-prefix", default="elrs_rainbow")


def _print_dump_text(md5_hash: str, sha256_hash: str, entries: list, *, debug: bool) -> None:
    print(f"md5: {md5_hash}")
    print(f"sha256: {sha256_hash}")
    for entry in entries:
        if debug:
            print(entry["fragment"])
        if entry["uid"] is not None:
            uid_text = str(entry["uid"]).replace(" ", "").replace("[", "").replace("]", "")
            print(f"uid:{uid_text}")
        if entry.get("wifi_ssid") is not None:
            print(f'wifi-ssid: {entry["wifi_ssid"]}')
        if entry.get("wifi_password") is not None:
            print(f'wifi-password: {entry["wifi_password"]}')


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(prog="strela elrs", description="ExpressLRS: CIRCL rainbow и dump_elrs.")
    sub = parser.add_subparsers(dest="command", required=True)

    uid_cmd = sub.add_parser("uid", help="UID из фразы привязки")
    uid_cmd.add_argument("phrase", help="binding phrase")

    dump_cmd = sub.add_parser("dump", help="JSON из flash-образа (CIRCL dump_elrs)")
    dump_cmd.add_argument("input", type=Path)
    dump_cmd.add_argument("--json", action="store_true")
    dump_cmd.add_argument("--debug", action="store_true")

    crack_cmd = sub.add_parser("crack", help="перебор словаря или RAM-таблицы по UID")
    crack_cmd.add_argument("uid", help="шесть байт через запятую")
    crack_cmd.add_argument("wordlist", type=Path, nargs="?", help="словарь, если нет --memory-table")
    crack_cmd.add_argument("--memory-table", type=Path, help="JSON от build-memory --out")
    crack_cmd.add_argument("--encoding", default="utf-8")

    lookup_cmd = sub.add_parser("lookup", help="фраза из kvrocks")
    lookup_cmd.add_argument("uid")
    _add_redis_flags(lookup_cmd)

    lookup_mem = sub.add_parser("lookup-memory", help="фраза из RAM-таблицы JSON")
    lookup_mem.add_argument("uid")
    lookup_mem.add_argument("table", type=Path)

    build_cmd = sub.add_parser("build-rainbow", help="словарь в kvrocks (elrs_do_rainbow)")
    build_cmd.add_argument("wordlist")
    build_cmd.add_argument("--status-file")
    build_cmd.add_argument("--chunk-size", type=int, default=10_000)
    build_cmd.add_argument("--processes", type=int)
    build_cmd.add_argument("--prefetch", type=int, default=4)
    build_cmd.add_argument("--encoding", default="utf-8")
    _add_redis_flags(build_cmd)

    build_local = sub.add_parser("build-memory", help="RAM-таблица из словаря")
    build_local.add_argument("wordlist", type=Path)
    build_local.add_argument("--out", type=Path, help="куда сохранить JSON для lookup-memory / assemble")
    build_local.add_argument("--encoding", default="utf-8")

    parsed = parser.parse_args(args)
    if parsed.command == "uid":
        uid = binding_phrase_to_uid(parsed.phrase)
        print("UID (dec):", ",".join(str(byte) for byte in uid))
        print("UID (hex):", uid_bytes_to_hex(uid))
        return 0
    if parsed.command == "dump":
        if not parsed.input.is_file():
            print(f"файл не найден: {parsed.input}", file=sys.stderr)
            return 1
        data = parsed.input.read_bytes()
        md5_hash, sha256_hash = compute_hashes(data)
        entries = extract_json_objects(data)
        if parsed.json:
            print(json.dumps(build_json_payload(md5_hash, sha256_hash, entries, debug=parsed.debug), ensure_ascii=False, indent=2))
            return 0
        _print_dump_text(md5_hash, sha256_hash, entries, debug=parsed.debug)
        return 0
    if parsed.command == "crack":
        uid = parse_uid_bytes(parsed.uid)
        if parsed.memory_table is not None:
            if not parsed.memory_table.is_file():
                print(f"таблица не найдена: {parsed.memory_table}", file=sys.stderr)
                return 1
            phrase = crack_binding_phrase_from_store(uid, load_memory_table(parsed.memory_table))
        elif parsed.wordlist is not None:
            if not parsed.wordlist.is_file():
                print(f"словарь не найден: {parsed.wordlist}", file=sys.stderr)
                return 1
            phrase = crack_binding_phrase(uid, parsed.wordlist, encoding=parsed.encoding)
        else:
            print("нужен wordlist или --memory-table", file=sys.stderr)
            return 2
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
    if parsed.command == "lookup-memory":
        if not parsed.table.is_file():
            print(f"таблица не найдена: {parsed.table}", file=sys.stderr)
            return 1
        uid = parse_uid_bytes(parsed.uid)
        phrase = lookup_binding_phrase(uid, load_memory_table(parsed.table))
        if phrase is None:
            print("в таблице нет UID", file=sys.stderr)
            return 1
        print(phrase)
        return 0
    if parsed.command == "build-rainbow":
        if not Path(parsed.wordlist).is_file():
            print(f"словарь не найден: {parsed.wordlist}", file=sys.stderr)
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
            Path(parsed.wordlist),
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
        if not parsed.wordlist.is_file():
            print(f"словарь не найден: {parsed.wordlist}", file=sys.stderr)
            return 1
        store = build_memory_table(parsed.wordlist, encoding=parsed.encoding)
        print(f"записано {len(store.table)} UID")
        if parsed.out is not None:
            save_memory_table(store, parsed.out)
            print(parsed.out)
        return 0
    return 1