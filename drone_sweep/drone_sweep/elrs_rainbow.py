"""Подбор binding phrase ExpressLRS: словарь и radужная таблица (CIRCL elrs_rainbow / elrs_do_rainbow).

Источник: CIRCL/Drone-Forensic (AGPL-3.0).
"""

from __future__ import annotations

import json
import os
import signal
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Protocol, Sequence

from .elrs_binding import (
    binding_phrase_uid_hex,
    hash_binding_phrases,
    iter_wordlist_lines,
    uid_bytes_to_hex,
)


class RainbowStore(Protocol):
    def get(self, uid_hex: str) -> str | None: ...

    def set_many(self, rows: Sequence[tuple[str, str]]) -> None: ...


@dataclass
class MemoryRainbowStore:
    table: dict[str, str]

    def get(self, uid_hex: str) -> str | None:
        return self.table.get(uid_hex.upper())

    def set_many(self, rows: Sequence[tuple[str, str]]) -> None:
        for key, phrase in rows:
            self.table[key.upper()] = phrase


def make_redis_store(
    *,
    host: str = "127.0.0.1",
    port: int = 6666,
    db: int = 5,
    prefix: str = "elrs_rainbow",
) -> RainbowStore:
    try:
        import redis
    except ImportError as exc:
        raise RuntimeError("для kvrocks/redis нужен пакет redis: pip install redis") from exc

    client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    client.ping()

    class _Store:
        def get(self, uid_hex: str) -> str | None:
            key = f"{prefix}:{uid_hex.upper()}" if prefix else uid_hex.upper()
            return client.get(key)

        def set_many(self, rows: Sequence[tuple[str, str]]) -> None:
            if not rows:
                return
            pipe = client.pipeline()
            for key, phrase in rows:
                redis_key = f"{prefix}:{key.upper()}" if prefix else key.upper()
                pipe.set(redis_key, phrase)
            pipe.execute()

    return _Store()


def lookup_binding_phrase(uid_bytes: Sequence[int], store: RainbowStore) -> str | None:
    return store.get(uid_bytes_to_hex(uid_bytes))


def crack_binding_phrase(uid_bytes: Sequence[int], wordlist: Path, *, encoding: str = "utf-8") -> str | None:
    """Линейный перебор словаря без kvrocks."""
    target = uid_bytes_to_hex(uid_bytes)
    for phrase, _offset in iter_wordlist_lines(wordlist, encoding=encoding):
        if binding_phrase_uid_hex(phrase) == target:
            return phrase
    return None


def _read_wordlist_chunks(
    wordlist: Path,
    *,
    encoding: str,
    chunk_size: int,
    start_offset: int,
) -> Iterator[tuple[list[str], int]]:
    chunk: list[str] = []
    next_offset = 0
    for phrase, offset in iter_wordlist_lines(wordlist, encoding=encoding, start_offset=start_offset):
        chunk.append(phrase)
        next_offset = offset
        if len(chunk) >= chunk_size:
            yield chunk, next_offset
            chunk = []
    if chunk:
        yield chunk, next_offset


def _load_build_status(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data.get("offset", 0)), int(data.get("processed", 0))
    except (OSError, ValueError, json.JSONDecodeError):
        return 0, 0


def _write_build_status(path: Path, offset: int, processed: int) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"offset": offset, "processed": processed}) + "\n", encoding="utf-8")
    tmp.replace(path)


def build_rainbow_table(
    wordlist: Path,
    store: RainbowStore,
    *,
    status_file: Path | None = None,
    chunk_size: int = 10_000,
    processes: int | None = None,
    prefetch: int = 4,
    encoding: str = "utf-8",
    on_progress: Callable[[int, int, int], None] | None = None,
) -> int:
    """Заливка словаря в хранилище; возвращает число обработанных фраз."""
    status_path = status_file or Path("elrs_rainbow_status.json")
    offset, processed = _load_build_status(status_path)
    worker_count = processes if processes is not None else (os.cpu_count() or 1)
    abort = {"stop": False}

    def _handle_signal(signum, _frame) -> None:
        abort["stop"] = True
        signal.signal(signum, signal.SIG_IGN)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    completed = True
    with ProcessPoolExecutor(max_workers=worker_count) as pool:
        pending: dict = {}
        try:
            for batch, batch_offset in _read_wordlist_chunks(
                wordlist,
                encoding=encoding,
                chunk_size=chunk_size,
                start_offset=offset,
            ):
                if abort["stop"]:
                    completed = False
                    break
                future = pool.submit(hash_binding_phrases, batch)
                pending[future] = (batch_offset, len(batch))
                if len(pending) >= max(1, prefetch):
                    processed, offset = _flush_rainbow_futures(
                        pending, store, processed, offset, status_path, on_progress
                    )
            while pending:
                processed, offset = _flush_rainbow_futures(
                    pending, store, processed, offset, status_path, on_progress
                )
        except KeyboardInterrupt:
            completed = False
        finally:
            if completed and not abort["stop"]:
                if status_path.exists():
                    status_path.unlink(missing_ok=True)
            else:
                _write_build_status(status_path, offset, processed)
    return processed


def _flush_rainbow_futures(
    pending: dict,
    store: RainbowStore,
    processed: int,
    offset: int,
    status_path: Path,
    on_progress: Callable[[int, int, int], None] | None,
) -> tuple[int, int]:
    done, _ = wait(pending.keys(), return_when=FIRST_COMPLETED)
    for future in done:
        batch_offset, _ = pending.pop(future)
        rows = future.result()
        if rows:
            store.set_many(rows)
        processed += len(rows)
        offset = batch_offset
        _write_build_status(status_path, offset, processed)
        if on_progress is not None:
            on_progress(len(rows), processed, offset)
    return processed, offset