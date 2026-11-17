"""Публичные словари и ссылки для подбора binding phrase (ExpressLRS / MILELRS).

Источники: CIRCL Drone-Forensic, MUSTARDTIGERFPV/ELRS-Rainbow-Tables, passhelp, SecLists.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

# CIRCL в примере elrs_do_rainbow.py указывает rockyou.txt; MUSTARDTIGERFPV тянет
# passhelp + moby + rockyou (см. get_wordstxt.sh в ELRS-Rainbow-Tables).
WORDLIST_PRESETS: dict[str, tuple[str, str]] = {
    "passhelp": (
        "passhelp/wordlist (~11k англ. слов, базовый набор для ELRS rainbow)",
        "https://raw.githubusercontent.com/passhelp/wordlist/master/words.txt",
    ),
    "rockyou": (
        "rockyou (~14M паролей; долго, но как в примере CIRCL elrs_do_rainbow)",
        "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt",
    ),
}

EXTRA_WORDLIST_URLS: tuple[tuple[str, str], ...] = (
    (
        "dwyl/english-words",
        "https://raw.githubusercontent.com/dwyl/english-words/master/words.txt",
    ),
    (
        "SecLists (папка Passwords)",
        "https://github.com/danielmiessler/SecLists/tree/master/Passwords",
    ),
)

TOOL_LINKS: tuple[tuple[str, str, str], ...] = (
    (
        "CIRCL Drone-Forensic elrs/",
        "https://github.com/CIRCL/Drone-Forensic/tree/main/elrs",
        "dump_elrs, uid, rainbow в kvrocks — эталон для Стрелы",
    ),
    (
        "ELRS-Rainbow-Tables",
        "https://github.com/MUSTARDTIGERFPV/ELRS-Rainbow-Tables",
        "Go-таблица из words.txt, ~618k однословных кандидатов",
    ),
    (
        "ExpressLRS Docs — binding",
        "https://www.expresslrs.org/quick-start/binding/",
        "фраза ≠ пароль Wi‑Fi; Wi‑Fi только для WebUI прошивки",
    ),
    (
        "ExpressLRS User Defines",
        "https://www.expresslrs.org/software/user-defines/",
        "MY_BINDING_PHRASE и md5 в прошивку",
    ),
)

FORUM_HINTS: tuple[str, ...] = (
    "ExpressLRS Discord и GitHub Discussions — типовые фразы и прошивки вендоров (например iloveiflight).",
    "FPV-сообщества (r/fpv, rcgroups) — обсуждение bind phrase, не взлом Wi‑Fi.",
    "MILELRS — та же формула UID, что у ExpressLRS; дамп flash или JSON страницы модуля.",
)


@dataclass(frozen=True)
class FetchResult:
    path: Path
    preset: str
    bytes_written: int


def fetch_wordlist_preset(preset: str, destination: Path, *, timeout: float = 120.0) -> FetchResult:
    if preset not in WORDLIST_PRESETS:
        known = ", ".join(sorted(WORDLIST_PRESETS))
        raise ValueError(f"неизвестный пресет {preset!r}; доступны: {known}")
    _label, url = WORDLIST_PRESETS[preset]
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(url, timeout=timeout) as response:
            data = response.read()
    except URLError as exc:
        raise OSError(f"не удалось скачать {url}: {exc}") from exc
    destination.write_bytes(data)
    return FetchResult(path=destination, preset=preset, bytes_written=len(data))


def render_elrs_resources_html() -> str:
    preset_rows = "".join(
        f"<tr><td class='mono'>{html.escape(key)}</td>"
        f"<td>{html.escape(label)}</td>"
        f"<td class='mono'><a class='top-link' href='{html.escape(url)}'>{html.escape(url)}</a></td></tr>"
        for key, (label, url) in WORDLIST_PRESETS.items()
    )
    tool_rows = "".join(
        f"<tr><td><a class='top-link' href='{html.escape(url)}'>{html.escape(name)}</a></td>"
        f"<td>{html.escape(note)}</td></tr>"
        for name, url, note in TOOL_LINKS
    )
    forums = "".join(f"<li>{html.escape(line)}</li>" for line in FORUM_HINTS)
    return f"""
<article class="panel panel-accent wide" id="elrs-wordlists">
<h2>ELRS / MILELRS: словари и инструменты (2026)</h2>
<p class="help"><strong>Пароль Wi‑Fi</strong> (часто заводской <code>expresslrs</code>) — только чтобы зайти в WebUI на <code>10.0.0.1</code> и сменить прошивку.
<strong>Binding phrase</strong> — отдельно: в прошивку попадает md5-фраза, из неё UID. Стрела подбирает phrase по UID из <em>дампа flash</em> или JSON, без Wi‑Fi.</p>
<ol class="steps">
<li>Снять образ .bin / HEX или JSON со страницы модуля (пароль Wi‑Fi не обязателен, если уже есть дамп).</li>
<li>Вкладка <a href="/crack">Подбор</a>: «фраза из образа» + словарь ниже (или RAM-таблица от <code>strela elrs build-memory</code>).</li>
<li>Если в JSON flash уже лежит <code>binding-phrase</code> — Стрела покажет её сразу, без словаря.</li>
</ol>
<h3 class="section">Словари на GitHub</h3>
<table class="top-table">
<thead><tr><th>Пресет CLI</th><th>Описание</th><th>URL</th></tr></thead>
<tbody>{preset_rows}</tbody>
</table>
<p class="help">При установке: <code>strela setup</code> (или <code>install.sh</code>) — скачивает
<code>passhelp</code> и строит RAM-таблицу. Вручную:
<code>strela elrs fetch-wordlist passhelp --out words.txt</code>,
<code>strela elrs build-memory words.txt --out elrs-table.json</code>.</p>
<h3 class="section">Кто ещё реализовал</h3>
<table class="top-table">
<thead><tr><th>Проект</th><th>Зачем</th></tr></thead>
<tbody>{tool_rows}</tbody>
</table>
<h3 class="section">Форумы и заметки</h3>
<ul class="steps">{forums}</ul>
</article>
"""