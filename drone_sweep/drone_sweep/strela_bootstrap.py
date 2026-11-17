"""Скачивание словарей ELRS и RAM-таблицы при установке / первом запуске."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .elrs_rainbow import build_memory_table, save_memory_table
from .elrs_resources import fetch_wordlist_preset

MANIFEST_VERSION = 1
MANIFEST_NAME = "manifest.json"
DEFAULT_PRESET = "passhelp"


def resolve_data_dir(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    env = os.environ.get("STRELA_DATA", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    xdg = os.environ.get("XDG_DATA_HOME", "").strip()
    if xdg:
        return (Path(xdg) / "strela").resolve()
    return (Path.home() / ".local" / "share" / "strela").resolve()


def manifest_path(data_dir: Path | None = None) -> Path:
    return resolve_data_dir(data_dir) / MANIFEST_NAME


def load_manifest(data_dir: Path | None = None) -> dict[str, Any] | None:
    path = manifest_path(data_dir)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def default_binding_paths(data_dir: Path | None = None) -> dict[str, Path]:
    """Готовые пути для подбора: словарь и JSON RAM-таблица."""
    manifest = load_manifest(data_dir)
    if not manifest:
        return {}
    out: dict[str, Path] = {}
    for key, path_key in (
        ("wordlist", "wordlist_passhelp"),
        ("memory_table", "memory_table_passhelp"),
    ):
        text = manifest.get(path_key)
        if isinstance(text, str) and text:
            path = Path(text)
            if path.is_file():
                out[key] = path
    return out


def setup_is_ready(data_dir: Path | None = None) -> bool:
    paths = default_binding_paths(data_dir)
    return "wordlist" in paths and "memory_table" in paths


@dataclass
class SetupResult:
    data_dir: Path
    manifest: dict[str, Any]
    created: list[str]


def run_setup(
    *,
    data_dir: Path | None = None,
    force: bool = False,
    quiet: bool = False,
) -> SetupResult:
    root = resolve_data_dir(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    wordlist_path = root / "wordlists" / f"{DEFAULT_PRESET}.txt"
    table_path = root / "tables" / f"{DEFAULT_PRESET}-memory.json"
    created: list[str] = []
    manifest = load_manifest(root) or {"version": MANIFEST_VERSION, "data_dir": str(root)}

    if force or not wordlist_path.is_file():
        if not quiet:
            print(f"Скачиваю словарь {DEFAULT_PRESET}…", file=sys.stderr)
        fetch_wordlist_preset(DEFAULT_PRESET, wordlist_path)
        created.append(str(wordlist_path))

    if force or not table_path.is_file():
        if not quiet:
            print("Строю RAM-таблицу UID→фраза…", file=sys.stderr)
        store = build_memory_table(wordlist_path)
        table_path.parent.mkdir(parents=True, exist_ok=True)
        save_memory_table(store, table_path)
        created.append(str(table_path))

    manifest.update(
        {
            "version": MANIFEST_VERSION,
            "data_dir": str(root),
            "wordlist_passhelp": str(wordlist_path),
            "memory_table_passhelp": str(table_path),
            "presets_ready": [DEFAULT_PRESET],
        }
    )
    manifest_path(root).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if not quiet:
        print(f"Данные Стрелы: {root}", file=sys.stderr)
        print(f"Словарь: {wordlist_path}", file=sys.stderr)
        print(f"Таблица: {table_path}", file=sys.stderr)
    return SetupResult(data_dir=root, manifest=manifest, created=created)


def ensure_setup(*, quiet: bool = True, data_dir: Path | None = None) -> dict[str, Path]:
    """При первом запуске докачивает ресурсы ELRS."""
    if setup_is_ready(data_dir):
        return default_binding_paths(data_dir)
    run_setup(data_dir=data_dir, quiet=quiet)
    return default_binding_paths(data_dir)