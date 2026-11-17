"""One HTML page a new operator can read next to the card."""

from __future__ import annotations

import html
import json

from .model import Card


def render_html(card: Card) -> str:
    rows = []
    for name, item in card.fields.items():
        value = "" if item.value is None else html.escape(json.dumps(item.value, ensure_ascii=False)[:2000])
        rows.append(
            "<tr>"
            f"<td>{html.escape(name)}</td>"
            f"<td class='{html.escape(item.status)}'>{html.escape(item.status)}</td>"
            f"<td>{value}</td>"
            f"<td>{html.escape(item.reason)}</td>"
            f"<td>{html.escape(item.source)}</td>"
            "</tr>"
        )
    hints = "".join(f"<li>{html.escape(line)}</li>" for line in card.hints[:12])
    holes = "".join(f"<li>{html.escape(line)}</li>" for line in card.holes)
    journal = "".join(
        f"<li><b>{html.escape(line['source'])}</b> — {html.escape(line['result'])}: {html.escape(line['detail'])}</li>"
        for line in card.journal
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Карточка дрона</title>
<style>
body {{ font-family: sans-serif; margin: 24px; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #ccc; padding: 6px; vertical-align: top; }}
.confirmed {{ background: #e5f6e5; }}
.document {{ background: #e7f0fb; }}
.missing {{ background: #fde8e8; }}
.not_applicable {{ background: #eee; }}
</style>
</head>
<body>
<h1>Карточка дрона — {html.escape(card.family)}</h1>
<p>Баннер: {html.escape(card.raw_banner or "нет")}</p>
<h2>Что делать, если вы здесь первый раз</h2>
<ol>{hints}</ol>
<h2>Где искали маршрут</h2>
<ul>{journal}</ul>
<h2>Дыры</h2>
<ul>{holes}</ul>
<h2>Поля</h2>
<table>
<tr><th>Поле</th><th>Статус</th><th>Значение</th><th>Причина</th><th>Источник</th></tr>
{''.join(rows)}
</table>
</body>
</html>
"""
