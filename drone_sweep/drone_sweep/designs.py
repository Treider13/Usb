"""Five tactical looks for the same card. The words stay plain Russian.

Each look is a choice, not the saved report. The sample numbers are an
example so a person can see what a filled card means. They are not a reading
from a connected board.
"""

from __future__ import annotations

import html


LOOKS = (
    {
        "id": "1",
        "name": "Ночная лампа",
        "line": "Тёмная комната, красный свет, чтобы не слепить глаза.",
        "css": """
body { background: #140806; color: #f0d2c4; font-family: "Liberation Serif", serif; }
.sheet { max-width: 880px; margin: 0 auto; padding: 28px 22px 64px; }
.lamp { width: 92px; height: 92px; border-radius: 50%; background: #8e1c16; margin: 8px 0 18px; animation: breathe 7s ease-in-out infinite; }
h1 { font-weight: 400; font-size: 40px; margin: 0 0 8px; }
.switch a { color: #e7b2a6; }
button, .read { background: #8e1c16; color: #fff; }
.osd { background: #1c0c0a; border: 1px solid #5a2822; }
.osd span { color: #ffb4a8; }
""",
    },
    {
        "id": "2",
        "name": "Полевой бланк",
        "line": "Бумажный лист на ткани. Печать садится медленно, один раз.",
        "css": """
body { background: #3d4634; color: #1c1a14; font-family: "Liberation Serif", serif; }
.sheet { max-width: 920px; margin: 24px auto; background: #e6dcc4; padding: 28px 26px 48px; }
.stamp { display: inline-block; border: 2px solid #7a2a24; color: #7a2a24; padding: 4px 10px; transform: rotate(-6deg); animation: settle 2.8s ease both; }
h1 { font-weight: 400; font-size: 36px; margin: 12px 0 8px; }
.switch a { color: #3d4634; }
button, .read { background: #1c1a14; color: #e6dcc4; }
.osd { background: #1c2418; }
.osd span { color: #d7ecb8; }
""",
    },
    {
        "id": "3",
        "name": "Прибор борта",
        "line": "Цифры как на старом авиаприборе. Горизонт качается медленно.",
        "css": """
body { background: #10110e; color: #e6d7a8; font-family: "Liberation Sans", sans-serif; }
.sheet { max-width: 980px; margin: 0 auto; padding: 20px 18px 56px; }
h1 { font-family: "Liberation Mono", monospace; font-weight: 400; font-size: 28px; letter-spacing: 0.04em; }
.switch a { color: #c8b27a; }
button, .read { background: #c45512; color: #1a1008; }
.osd { background: #070806; min-height: 280px; }
.horizon { position: absolute; left: 24%; right: 24%; top: 54%; height: 2px; background: #e6d7a8; animation: rock 8s ease-in-out infinite; }
.osd span { color: #f0c14a; font-family: "Liberation Mono", monospace; }
""",
    },
    {
        "id": "4",
        "name": "Штабная сетка",
        "line": "Слева экран на сетке, справа словами — что эта цифра значит.",
        "css": """
body { background: #1a261c; color: #e4ecd8; font-family: "Liberation Sans", sans-serif; }
.sheet { max-width: 1040px; margin: 0 auto; padding: 18px 16px 56px; }
.layout { display: grid; grid-template-columns: 1fr; gap: 18px; }
h1 { font-weight: 500; font-size: 32px; color: #d7c27a; }
.switch a { color: #d7c27a; }
button, .read { background: #8c2f2a; color: #f4efe2; }
.osd { background: repeating-linear-gradient(#243528, #243528 27px, #1c2b20 28px), repeating-linear-gradient(90deg, transparent, transparent 27px, #314236 28px); }
.needle { position: absolute; left: 50%; top: 50%; width: 2px; height: 42%; background: #d7c27a; transform-origin: bottom center; animation: turn 18s linear infinite; }
.osd span { color: #f4efe2; }
@media (min-width: 800px) { .layout { grid-template-columns: 1.1fr 0.9fr; } }
""",
    },
    {
        "id": "5",
        "name": "Журнал связи",
        "line": "Строки идут одна за другой, как запись в журнале радиста.",
        "css": """
body { background: #24180f; color: #f0d7a4; font-family: "Liberation Mono", monospace; }
.sheet { max-width: 820px; margin: 0 auto; padding: 22px 16px 64px; }
h1 { font-weight: 400; font-size: 26px; }
.switch a { color: #e7c48a; }
button, .read { background: #f0d7a4; color: #24180f; }
.line { border-bottom: 1px solid #5a4632; padding: 10px 0; animation: reveal 1.2s ease both; }
.line:nth-child(2) { animation-delay: 0.4s; }
.line:nth-child(3) { animation-delay: 0.8s; }
.line:nth-child(4) { animation-delay: 1.2s; }
.caret { display: inline-block; width: 0.6em; height: 1em; background: #f0d7a4; animation: blink 2.4s steps(1) infinite; vertical-align: text-bottom; }
.osd span { color: #f0d7a4; }
""",
    },
)


PLAIN = (
    ("Позывной", "Имя, которое пилот написал на борту.", "Чтобы не перепутать две одинаковые платы."),
    ("Плата", "Модель полётника из чтения прошивки.", "По ней видно, какая это плата и какая прошивка."),
    ("Порт приёмника", "Разъём, к которому прописан приёмник.", "Сюда смотреть провод. Программа провод не переставляет."),
    ("Частота картинки", "Канал видео в мегагерцах.", "На этой частоте очки должны показывать картинку."),
    ("Герцы в журнале", "Сколько раз в секунду журнал записал сглаженные стики.", "Это запись журнала, не скорость радио в воздухе."),
    ("Шаг стиков в журнале", "Пауза между записями стиков.", "Это как часто писали журнал, не как часто летят пакеты."),
    ("Точка взлёта", "Первая нормальная точка GPS сразу после взведения.", "Дом и цифры на экране точкой взлёта не считаются."),
    ("Высота", "Показание барометра в журнале.", "Насколько борт поднимался. Маршрутом это не является."),
    ("Отказ связи", "Что плата настроена сделать, если пульт пропал.", "Это записанная настройка, не доказательство, что отказ уже случился."),
    ("Место на экране", "Куда на картинке выведена цифра.", "Это место надписи, не измерение полёта."),
)

OSD = (
    ("Напряжение", "4%", "8%", "Сколько осталось в батарее, чтобы вовремя сесть."),
    ("Время вылета", "38%", "8%", "Сколько уже длится этот вылет по таймеру прошивки."),
    ("Связь", "70%", "8%", "Насколько уверенно пульт слышит борт. Это не скорость пакетов."),
    ("Режим", "4%", "74%", "Какой режим выбран тумблером: взведён или стабилизация."),
    ("Высота", "62%", "74%", "Цифра в очках. Маршрутом и точкой взлёта она не становится."),
)


def design_page(number: int) -> bytes:
    look = LOOKS[number - 1]
    switches = "".join(
        f'<a href="/design/{item["id"]}"' + (' aria-current="page"' if item["id"] == look["id"] else "") + f'>{html.escape(item["name"])}</a>'
        for item in LOOKS
    )
    rows = "".join(
        "<article class=\"line\">"
        f"<h2>{html.escape(title)}</h2>"
        f"<p>{html.escape(what)}</p>"
        f"<p class=\"why\">{html.escape(why)}</p>"
        "</article>"
        for title, what, why in PLAIN
    )
    marks = "".join(
        f'<span style="left:{left};top:{top}"><b>{html.escape(title)}</b></span>'
        for title, left, top, _why in OSD
    )
    legend = "".join(
        f"<div><b>{html.escape(title)}.</b> {html.escape(why)}</div>"
        for title, _left, _top, why in OSD
    )
    extra = ""
    if look["id"] == "3":
        extra = '<div class="horizon"></div>'
    elif look["id"] == "4":
        extra = '<div class="needle"></div>'
    lamp = '<div class="lamp" aria-hidden="true"></div>' if look["id"] == "1" else ""
    stamp = '<div class="stamp">Пример</div>' if look["id"] == "2" else ""
    caret = '<span class="caret" aria-hidden="true"></span>' if look["id"] == "5" else ""
    document = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(look["name"])}</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; line-height: 1.45; }}
a {{ color: inherit; }}
.switch {{ display: flex; flex-wrap: wrap; gap: 10px 16px; margin: 0 0 18px; }}
.switch a[aria-current="page"] {{ text-decoration: underline; text-underline-offset: 4px; }}
p {{ max-width: 62ch; }}
.why {{ color: inherit; opacity: 0.82; }}
button, .read {{ border: 0; padding: 8px 14px; font: inherit; cursor: pointer; text-decoration: none; display: inline-block; }}
.osd {{ position: relative; min-height: 240px; margin: 16px 0 12px; }}
.osd span {{ position: absolute; max-width: 28%; font-size: 15px; }}
.osd b {{ font-weight: 600; }}
.legend {{ margin: 0 0 28px; padding: 0; }}
.legend div {{ margin: 0 0 8px; max-width: 62ch; }}
h2 {{ font-size: 18px; font-weight: 600; margin: 0; }}
.note {{ font-size: 14px; }}
@keyframes breathe {{ 0%, 100% {{ transform: scale(1); opacity: 0.72; }} 50% {{ transform: scale(1.08); opacity: 1; }} }}
@keyframes settle {{ from {{ opacity: 0; transform: rotate(-14deg) scale(1.2); }} to {{ opacity: 1; transform: rotate(-6deg) scale(1); }} }}
@keyframes rock {{ 0%, 100% {{ transform: rotate(-4deg); }} 50% {{ transform: rotate(4deg); }} }}
@keyframes turn {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
@keyframes reveal {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes blink {{ 0%, 45% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
@media (prefers-reduced-motion: reduce) {{
  * {{ animation: none !important; }}
}}
{look["css"]}
</style>
</head>
<body>
<main class="sheet">
<nav class="switch">{switches}</nav>
{lamp}{stamp}
<h1>{html.escape(look["name"])}</h1>
<p>{html.escape(look["line"])}</p>
<p class="note">Это пример, не ваш борт. Цифры показывают, как читать карточку. Пустая клетка так и остаётся пустой.</p>
<p><a class="read" href="/">Считать борт</a> {caret}</p>
<section class="layout">
<div>
<h2>Экран в очках</h2>
<p>Так пилот видит цифры поверх картинки. Место надписи берётся из прошивки. Само место высотой и маршрутом не является.</p>
<div class="osd" aria-label="Пример раскладки экрана">{extra}{marks}</div>
<div class="legend">{legend}</div>
</div>
<div>
<h2>Что означает строка</h2>
{rows}
</div>
</section>
<p><a href="/">Назад к чтению</a></p>
</main>
</body>
</html>
"""
    return document.encode("utf-8")
