"""Скачивание словарей ELRS и RAM-таблицы при установке / обновлении."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .elrs_assemble import search_binding_sources
from .elrs_rainbow import build_and_save_table
from .elrs_resources import INSTALL_PRESET_ORDER, WORDLIST_PRESETS, fetch_wordlist_preset

MANIFEST_VERSION = 2
MANIFEST_NAME = "manifest.json"
DEFAULT_SOURCE = "all"


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
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if manifest.get("version", 1) < 2 and manifest.get("wordlist_passhelp"):
        manifest.setdefault("sources", {})
        manifest["sources"].setdefault(
            "passhelp",
            {
                "wordlist": manifest["wordlist_passhelp"],
                "memory_table": manifest.get("memory_table_passhelp", ""),
                "label": WORDLIST_PRESETS["passhelp"][0],
            },
        )
    return manifest


def _sources(manifest: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    if not manifest:
        return {}
    block = manifest.get("sources")
    return block if isinstance(block, dict) else {}


def list_catalog(data_dir: Path | None = None) -> list[tuple[str, str]]:
    manifest = load_manifest(data_dir)
    sources = _sources(manifest)
    rows: list[tuple[str, str]] = [("all", "Все установленные (combined → elrs_rainbow → rockyou → …)")]
    if "combined" in sources:
        rows.append(("combined", "Объединённый (passhelp + dwyl + moby, без rockyou)"))
    for preset in INSTALL_PRESET_ORDER:
        entry = sources.get(preset)
        if not entry:
            continue
        label = entry.get("label") or WORDLIST_PRESETS.get(preset, (preset, ""))[0]
        rows.append((preset, label))
    return rows


def resolve_source(
    source_id: str,
    data_dir: Path | None = None,
) -> tuple[Path | None, Path | None]:
    manifest = load_manifest(data_dir)
    sources = _sources(manifest)
    if source_id == "all":
        return None, None
    entry = sources.get(source_id)
    if not entry:
        return default_binding_paths(data_dir).get("wordlist"), default_binding_paths(data_dir).get("memory_table")
    wordlist = Path(entry["wordlist"]) if entry.get("wordlist") else None
    table = Path(entry["memory_table"]) if entry.get("memory_table") else None
    wordlist = wordlist if wordlist and wordlist.is_file() else None
    table = table if table and table.is_file() else None
    return wordlist, table


def default_binding_paths(data_dir: Path | None = None) -> dict[str, Path]:
    manifest = load_manifest(data_dir)
    sources = _sources(manifest)
    for key in ("combined", "passhelp", *INSTALL_PRESET_ORDER):
        entry = sources.get(key)
        if not entry:
            continue
        wl = Path(entry.get("wordlist", ""))
        tb = Path(entry.get("memory_table", ""))
        if wl.is_file() and tb.is_file():
            return {"wordlist": wl, "memory_table": tb}
    return {}


def setup_is_ready(data_dir: Path | None = None) -> bool:
    return bool(default_binding_paths(data_dir))


def search_binding_installed(
    uid: list[int],
    source_id: str = DEFAULT_SOURCE,
    *,
    data_dir: Path | None = None,
) -> tuple[str | None, str, str]:
    manifest = load_manifest(data_dir)
    sources = _sources(manifest)
    if source_id != "all":
        wl, tb = resolve_source(source_id, data_dir)
        return search_binding_sources(uid, wl, tb)
    order = [key for key in ("combined", "elrs_rainbow", "rockyou", "passhelp", "dwyl") if key in sources]
    problems: list[str] = []
    for key in order:
        entry = sources[key]
        wl = Path(entry["wordlist"])
        tb = Path(entry["memory_table"])
        phrase, used, problem = search_binding_sources(uid, wl, tb)
        if phrase:
            return phrase, f"{key} ({used})", ""
        if problem:
            problems.append(f"{key}: {problem}")
    wl, tb = default_binding_paths(data_dir).get("wordlist"), default_binding_paths(data_dir).get("memory_table")
    if wl or tb:
        phrase, used, problem = search_binding_sources(uid, wl, tb)
        if phrase:
            return phrase, used, ""
        if problem:
            problems.append(problem)
    return None, "", "; ".join(problems) or "словари не установлены — выполните strela setup"


def _merge_wordlists(paths: list[Path], destination: Path) -> int:
    seen: set[str] = set()
    lines: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            word = line.strip()
            if not word or word in seen:
                continue
            seen.add(word)
            lines.append(word)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


@dataclass
class SetupResult:
    data_dir: Path
    manifest: dict[str, Any]
    created: list[str]
    failed: list[str]


def run_setup(
    *,
    data_dir: Path | None = None,
    force: bool = False,
    quiet: bool = False,
    presets: tuple[str, ...] | None = None,
) -> SetupResult:
    root = resolve_data_dir(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "wordlists").mkdir(parents=True, exist_ok=True)
    (root / "tables").mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(root) or {"version": MANIFEST_VERSION, "data_dir": str(root)}
    sources: dict[str, dict[str, str]] = dict(_sources(manifest))
    created: list[str] = []
    failed: list[str] = []
    ready_wordlists: list[Path] = []

    order = presets if presets is not None else INSTALL_PRESET_ORDER
    for preset in order:
        if preset not in INSTALL_PRESET_ORDER and preset != "elrs_rainbow":
            if not quiet:
                print(f"Пропуск неизвестного пресета {preset}", file=sys.stderr)
            continue
        label = WORDLIST_PRESETS.get(preset, (preset, ""))[0]
        wordlist_path = root / "wordlists" / f"{preset}.txt"
        table_path = root / "tables" / f"{preset}-memory.json"
        timeout = 600.0 if preset == "rockyou" else 240.0
        try:
            if force or not wordlist_path.is_file():
                if not quiet:
                    print(f"Скачиваю словарь {preset}…", file=sys.stderr)
                fetch_wordlist_preset(preset, wordlist_path, timeout=timeout)
                created.append(str(wordlist_path))
            actual_table = table_path.with_suffix(".sqlite") if preset == "rockyou" else table_path
            need_table = force or not (table_path.is_file() or actual_table.is_file())

            def _progress(count: int) -> None:
                if not quiet and preset == "rockyou" and count and count % 500_000 == 0:
                    print(f"  …{count // 1000}k фраз", file=sys.stderr)

            if need_table:
                if not quiet:
                    hint = " (SQLite на диске, мало RAM)" if preset == "rockyou" else ""
                    print(f"Таблица UID для {preset}{hint}…", file=sys.stderr)
                actual_table = build_and_save_table(
                    wordlist_path,
                    table_path,
                    on_progress=_progress if preset == "rockyou" else None,
                )
                created.append(str(actual_table))
            elif actual_table.is_file():
                pass
            sources[preset] = {
                "wordlist": str(wordlist_path),
                "memory_table": str(actual_table if actual_table.is_file() else table_path),
                "label": label,
            }
            if preset != "rockyou":
                ready_wordlists.append(wordlist_path)
        except OSError as exc:
            failed.append(f"{preset}: {exc}")
            if not quiet:
                print(f"Пропуск {preset}: {exc}", file=sys.stderr)
        except ValueError as exc:
            failed.append(f"{preset}: {exc}")
            if not quiet:
                print(f"Пропуск {preset}: {exc}", file=sys.stderr)

    combined_path = root / "wordlists" / "combined.txt"
    combined_table = root / "tables" / "combined-memory.json"
    if ready_wordlists and (force or not combined_table.is_file()):
        count = _merge_wordlists(ready_wordlists, combined_path)
        if not quiet:
            print(f"Объединённый словарь: {count} строк", file=sys.stderr)
        build_and_save_table(combined_path, combined_table)
        sources["combined"] = {
            "wordlist": str(combined_path),
            "memory_table": str(combined_table),
            "label": "Объединённый (passhelp + dwyl + elrs_rainbow + moby)",
        }
        created.append(str(combined_table))

    manifest.update(
        {
            "version": MANIFEST_VERSION,
            "data_dir": str(root),
            "sources": sources,
            "default_source": DEFAULT_SOURCE,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "failed_presets": failed,
            "presets_ready": sorted(sources.keys()),
        }
    )
    manifest_path(root).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if not quiet:
        print(f"Данные Стрелы: {root}", file=sys.stderr)
        if failed:
            print("Не скачано:", ", ".join(failed), file=sys.stderr)
    return SetupResult(data_dir=root, manifest=manifest, created=created, failed=failed)


def ensure_setup(*, quiet: bool = True, data_dir: Path | None = None) -> dict[str, Path]:
    manifest = load_manifest(data_dir)
    if manifest and manifest.get("version", 0) >= MANIFEST_VERSION and _sources(manifest):
        return default_binding_paths(data_dir)
    run_setup(data_dir=data_dir, quiet=quiet, force=bool(manifest))
    return default_binding_paths(data_dir)