"""Chrome copied from the Betaflight configurator layout.

Dark surfaces, a left rail, a connect bar, and a red tactical primary
`--primary-500: #e63946` (PC, как app.betaflight.com). The name on the rail is Стрела.
"""

from __future__ import annotations


CSS = """
:root {
  --surface-100: #0c0c0d;
  --surface-200: #17181a;
  --surface-300: #222326;
  --text: #f2f2f2;
  --muted: #a3a3a3;
  --line: #2c2d31;
  --primary-500: #e63946;
  --primary-700: #9f1d28;
  --action: #e63946;
  --success: #96e212;
  --info: #64a5f6;
  --quiet: #b5b5b5;
  --radius: 6px;
  --rail: 228px;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--surface-100);
  color: var(--text);
  font-family: "Segoe UI", "Liberation Sans", sans-serif;
  font-size: 15px;
  line-height: 1.45;
}
.app { display: flex; min-height: 100vh; }
.rail {
  width: var(--rail);
  flex: 0 0 var(--rail);
  background: #090909;
  border-right: 1px solid var(--line);
  padding: 18px 12px;
}
.logo {
  display: block;
  margin: 4px 10px 18px;
  color: var(--primary-500);
  font-weight: 800;
  font-size: 22px;
  letter-spacing: 0.08em;
  text-decoration: none;
  text-transform: uppercase;
}
.rail nav { display: flex; flex-direction: column; gap: 4px; }
.rail a {
  color: var(--text);
  text-decoration: none;
  padding: 9px 12px;
  border-radius: var(--radius);
  border-left: 3px solid transparent;
}
.rail a:hover { background: var(--surface-300); }
.rail a[aria-current="page"] {
  background: var(--surface-200);
  border-left-color: var(--primary-500);
  color: var(--primary-500);
}
.work { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.topbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: #050505;
  border-bottom: 1px solid var(--line);
}
.topbar .spacer { margin-left: auto; }
.connect { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-left: auto; }
.baud, select, input[type="text"], input[type="file"], input:not([type]) {
  padding: 7px 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-300);
  color: var(--text);
  font: inherit;
}
.baud { min-width: 5.2rem; text-align: center; }
label.folder { display: flex; align-items: center; gap: 8px; margin: 0; color: var(--quiet); }
.connect select, .connect input { width: auto; min-width: 14rem; margin: 0; }
button, a.action {
  display: inline-block;
  background: var(--action);
  color: #ffffff;
  text-decoration: none;
  padding: 8px 16px;
  border: 0;
  border-radius: var(--radius);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
a.action.quiet, button.quiet {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--line);
  font-weight: 600;
}
a:focus, button:focus, input:focus, select:focus {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}
.sheet { padding: 22px 28px 56px; max-width: 1180px; }
.hero { padding: 28px 0 8px; }
.hero h1 {
  margin: 0 0 8px;
  font-size: 42px;
  font-weight: 750;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--primary-500);
}
.lede { font-size: 17px; max-width: 68ch; }
.cards { display: grid; grid-template-columns: 1fr; gap: 12px; margin: 22px 0; }
.panel {
  background: var(--surface-200);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px 16px 8px;
}
.panel h2 {
  margin: 0 0 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
  color: var(--text);
  font-size: 16px;
}
.row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
}
.row p { margin: 2px 0 0; color: var(--quiet); font-size: 13px; max-width: 62ch; }
.switch { position: relative; width: 46px; height: 26px; flex: 0 0 46px; }
.switch input { opacity: 0; width: 0; height: 0; position: absolute; }
.track {
  position: absolute; inset: 0;
  background: #3a3a3a;
  border-radius: 13px;
  transition: background 0.15s linear;
}
.track::after {
  content: "";
  position: absolute;
  width: 20px; height: 20px;
  left: 3px; top: 3px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.15s linear;
}
.switch input:checked + .track { background: var(--primary-500); }
.switch input:checked + .track::after { transform: translateX(20px); }
h2.section {
  font-size: 18px;
  color: var(--primary-500);
  border-bottom: 1px solid var(--line);
  padding-bottom: 6px;
}
p { max-width: 72ch; }
ol.steps { padding-left: 1.2em; max-width: 72ch; }
ol.steps li { margin: 8px 0; }
.legend { list-style: none; padding: 0; margin: 16px 0; display: grid; gap: 8px; }
.stamp {
  display: inline-block;
  border: 1px solid var(--text);
  color: var(--text);
  padding: 1px 8px;
  border-radius: var(--radius);
  font-size: 13px;
  white-space: nowrap;
}
.cell.confirmed .stamp, .legend .confirmed .stamp { color: var(--success); border-color: var(--success); }
.cell.document .stamp, .legend .document .stamp { color: var(--info); border-color: var(--info); }
.cell.missing .stamp, .legend .missing .stamp { color: #ff5a5a; border-color: #ff5a5a; }
.cell.not_applicable .stamp, .legend .not_applicable .stamp { color: var(--muted); border-color: var(--muted); }
.grid { display: grid; grid-template-columns: 1fr; gap: 8px; }
.cell { position: relative; background: var(--surface-200); border: 1px solid var(--line); border-radius: var(--radius); padding: 12px 14px; }
.cell h3 { margin: 0 0 4px; font-size: 16px; }
.key { margin: 0; font-family: "Liberation Mono", monospace; font-size: 12px; color: var(--muted); }
.cell .key, .cell .src, .hole .key { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.value table { width: 100%; border-collapse: collapse; font-size: 14px; }
.value th, .value td { border-bottom: 1px solid var(--line); text-align: left; padding: 3px 8px 3px 0; vertical-align: top; font-weight: 400; }
.value th { width: 32%; color: var(--quiet); }
.value pre { white-space: pre-wrap; margin: 4px 0 10px; }
.why, .src { margin: 0; font-size: 14px; color: var(--quiet); }
.blurb { color: var(--quiet); margin: 0 0 10px; }
.hole { border-left: 4px solid #ff5a5a; padding: 4px 0 4px 12px; margin: 12px 0; }
label { display: block; margin: 14px 0; max-width: 72ch; }
label .title { font-weight: 700; }
.help { display: block; color: var(--quiet); font-size: 14px; }
label input, label select { width: 100%; margin-top: 4px; }
.actions { display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0; }
.split { display: grid; grid-template-columns: 1fr; gap: 14px; }
.mono { font-family: "Liberation Mono", monospace; font-size: 13px; }
.num { color: var(--primary-500); font-weight: 700; }
.top-grid { display: grid; gap: 14px; margin: 16px 0; }
.top-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.top-table th, .top-table td { border-bottom: 1px solid var(--line); padding: 6px 8px 6px 0; text-align: left; vertical-align: top; }
.top-table th { color: var(--quiet); font-weight: 600; }
.panel-accent h2 { color: var(--primary-500); border-bottom-color: var(--line); }
.panel.wide { margin-top: 0; }
.value-big code { font-size: 1.35rem; color: var(--success); }
input[type="file"] { width: 100%; margin-top: 4px; }
.usage-bar { display: flex; height: 28px; border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; margin: 12px 0; }
.usage-seg { display: flex; align-items: center; justify-content: center; background: var(--primary-500); color: #fff; font-size: 11px; font-weight: 700; min-width: 2px; border-right: 1px solid var(--surface-100); }
.top-stats { display: grid; grid-template-columns: 1fr auto; gap: 6px 16px; margin: 12px 0; max-width: 22rem; }
.top-stats dt { color: var(--quiet); margin: 0; }
.top-stats dd { margin: 0; }
.top-cinema { margin-top: 14px; padding: 10px 12px; border-left: 3px solid var(--primary-500); background: var(--surface-300); }
.badge-slow { display: inline-block; padding: 2px 8px; background: var(--primary-500); color: #fff; font-size: 11px; font-weight: 700; border-radius: var(--radius); margin-right: 8px; animation: top-pulse 2.4s ease-in-out infinite; }
.top-link { color: var(--primary-500); }
.top-meta { font-size: 13px; color: var(--quiet); }
@keyframes top-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
@media (min-width: 900px) {
  .cards, .split, .top-grid { grid-template-columns: 1fr 1fr; }
  .legend { grid-template-columns: 1fr 1fr; }
  .grid { grid-template-columns: 1fr 1fr; }
  .cell.wide { grid-column: 1 / -1; }
}
@media (max-width: 800px) {
  .app { flex-direction: column; }
  .rail { width: auto; flex-basis: auto; }
  .rail nav { flex-direction: row; flex-wrap: wrap; }
  .sheet { padding: 16px 14px 40px; }
  .hero h1 { font-size: 32px; }
  .connect { margin-left: 0; width: 100%; }
  .connect select, .connect input { min-width: 0; flex: 1 1 10rem; }
}
@media (prefers-reduced-motion: reduce) {
  .track, .track::after { transition: none; }
  .badge-slow { animation: none; }
}
"""

NAV = (
    ("/", "Приветствие"),
    ("/read", "Чтение"),
    ("/assemble", "Файлы"),
    ("/crack", "Подбор"),
    ("/top2026", "ТОП 2026"),
    ("/explain", "Подсказки"),
)


def page(title: str, inner: str, connect: str = "", current: str = "/") -> str:
    links = []
    for href, label in NAV:
        current_attr = ' aria-current="page"' if href == current else ""
        links.append(f'<a href="{href}"{current_attr}>{label}</a>')
    rail = (
        '<aside class="rail"><a class="logo" href="/">Стрела</a><nav>'
        + "".join(links)
        + "</nav></aside>"
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<div class="app">
{rail}
<div class="work">
<header class="topbar">{connect}</header>
<main class="sheet">
{inner}
</main>
</div>
</div>
</body>
</html>
"""
