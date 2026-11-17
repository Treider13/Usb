"""Демо-страница «Тактический ТОП 2026» (аналитика сценариев USB, учебные данные)."""

from __future__ import annotations

import html

# Учебные приоритеты под домен Стрелы; не разведданные.
TOP_ROWS = (
    (1, "FPV-конфиг BF/INAV", 96, "0.25×", "Dump"),
    (2, "ExpressLRS UART", 93, "0.5×", "RX"),
    (3, "ArduPilot .BIN", 90, "0.25×", "LOG"),
    (4, "VTX_FREQ / band", 87, "1×", "VTX"),
    (5, "Mesh телеметрия", 84, "0.5×", "LINK"),
)


def _usage_bar() -> str:
    parts = []
    for rank, _title, score, _slo, _tag in TOP_ROWS:
        parts.append(
            f'<span class="usage-seg" style="flex:{score} 1 0" title="#{rank} {score}">'
            f'<span class="usage-lbl">{rank}</span></span>'
        )
    return f'<div class="usage-bar">{"".join(parts)}</div>'


def render_top_inner() -> str:
    rows = "".join(
        f"<tr><td>{n}</td><td>{html.escape(title)}</td>"
        f'<td class="num">{score}</td><td class="mono">{html.escape(slo)}</td>'
        f'<td class="mono">{html.escape(tag)}</td></tr>'
        for n, title, score, slo, tag in TOP_ROWS
    )
    lead = TOP_ROWS[0]
    avg = sum(r[2] for r in TOP_ROWS) // len(TOP_ROWS)
    slow_count = sum(1 for r in TOP_ROWS if r[3].startswith("0.25"))
    return f"""
<section class="hero top-hero">
<h1>Тактический топ 2026</h1>
<p class="lede">Приоритеты чтения борта по USB для Стрелы. Учебная аналитика: slow-mo помечает сценарии, где полезен разбор по кадрам (dump, .BIN).</p>
<p class="top-meta mono">SIG READONLY · DESKTOP · layout как <a class="top-link" href="https://app.betaflight.com/">Betaflight</a></p>
</section>
<div class="top-grid">
<article class="panel panel-accent">
<h2>Приоритеты чтения USB</h2>
<table class="top-table">
<thead><tr><th>#</th><th>Сценарий</th><th>Балл</th><th>Slow</th><th>Тег</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</article>
<article class="panel panel-accent">
<h2>Метрики</h2>
<p class="help">Красная шкала — доля приоритета в рейтинге (демо).</p>
{_usage_bar()}
<dl class="top-stats">
<dt>Лидер</dt><dd class="num">{lead[2]}</dd>
<dt>Средний балл</dt><dd class="num">{avg}</dd>
<dt>Slow 0.25×</dt><dd class="num">{slow_count}</dd>
</dl>
<div class="top-cinema" aria-hidden="true">
<span class="badge-slow">SLOW-MO {html.escape(lead[3])}</span>
<span class="mono top-tc">TARGET #{lead[0]} · {html.escape(lead[1])}</span>
</div>
</article>
</div>
<article class="panel panel-accent wide">
<h2>Метод</h2>
<p>Веса: полезность для карточки, частота в поле, сложность чтения. Пересчёт — демо. Для реальных данных позже подключим статистику отчётов.</p>
</article>
"""