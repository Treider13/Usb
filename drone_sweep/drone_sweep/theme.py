"""Configurator-style chrome in red.

Betaflight Configurator paints a dark surface, a top bar, and a gold
primary (`--color-primary-500` is #ffbb00) with a separate action button.
This sheet keeps that layout. The gold is replaced by red.
"""

from __future__ import annotations


CSS = """
:root {
  --surface-100: hsl(0, 0%, 8%);
  --surface-200: hsl(0, 0%, 12%);
  --surface-300: hsl(0, 0%, 16%);
  --text: hsl(0, 0%, 96%);
  --muted: hsl(0, 0%, 68%);
  --line: hsl(0, 0%, 22%);
  --primary-500: #ff2b2b;
  --primary-700: #9d1010;
  --action: #e2123f;
  --success: #96e212;
  --info: #64a5f6;
  --quiet: hsl(0, 0%, 72%);
  --radius: 0.35rem;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--surface-100);
  color: var(--text);
  font-family: "Segoe UI", "Liberation Sans", sans-serif;
  font-size: 16px;
  line-height: 1.45;
}
.sheet {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 20px 48px;
}
.topbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin: 0 -20px 20px;
  padding: 10px 16px;
  background: #050505;
  border-bottom: 1px solid var(--line);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}
.brand {
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--primary-500);
  text-decoration: none;
}
label.folder {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: var(--quiet);
  font-size: 14px;
}
.connect {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.baud {
  min-width: 5.5rem;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-300);
  color: var(--text);
  text-align: center;
}
h1 {
  font-weight: 600;
  font-size: 32px;
  line-height: 1.15;
  margin: 8px 0;
  color: var(--text);
}
h2 {
  font-weight: 600;
  font-size: 18px;
  line-height: 1.2;
  margin: 28px 0 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--line);
  color: var(--primary-500);
}
p { max-width: 72ch; }
.lede { font-size: 16px; color: var(--text); }
.banner { margin-top: 0; color: var(--quiet); }
.actions { display: flex; flex-wrap: wrap; gap: 12px; margin: 20px 0; }
a.action, button {
  display: inline-block;
  background: var(--action);
  color: #fff;
  text-decoration: none;
  padding: 8px 16px;
  border: 1px solid var(--primary-700);
  border-radius: var(--radius);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
a.action.quiet {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--line);
  font-weight: 600;
}
a:focus, button:focus, input:focus, select:focus {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}
ol.steps { padding-left: 1.2em; max-width: 72ch; }
ol.steps li { margin: 8px 0; }
.legend { list-style: none; padding: 0; margin: 16px 0; display: grid; gap: 8px; }
.legend li { display: flex; align-items: flex-start; gap: 8px; }
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
.cell.missing .stamp, .legend .missing .stamp { color: var(--primary-500); border-color: var(--primary-500); }
.cell.not_applicable .stamp, .legend .not_applicable .stamp { color: var(--muted); border-color: var(--muted); }
label .title { font-weight: 700; }
.grid { display: grid; grid-template-columns: 1fr; gap: 8px; }
.cell {
  background: var(--surface-200);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 12px 14px;
}
.cell h3 { margin: 0 0 4px; font-size: 16px; font-weight: 700; color: var(--text); }
.key { margin: 0; font-family: "JetBrains Mono", "Liberation Mono", monospace; font-size: 12px; color: var(--muted); }
.value table { width: 100%; border-collapse: collapse; font-size: 14px; }
.value th, .value td { border-bottom: 1px solid var(--line); text-align: left; padding: 3px 8px 3px 0; vertical-align: top; font-weight: 400; }
.value th { width: 32%; color: var(--quiet); }
.value pre { white-space: pre-wrap; margin: 4px 0 10px; }
.why, .src { margin: 0; font-size: 14px; color: var(--quiet); }
.hole { border-left: 4px solid var(--primary-500); padding: 4px 0 4px 12px; margin: 12px 0; }
.hole p { margin: 4px 0; }
label { display: block; margin: 16px 0; max-width: 72ch; }
.help { display: block; color: var(--quiet); font-size: 14px; }
input, select {
  width: 100%;
  margin-top: 4px;
  padding: 8px;
  background: var(--surface-300);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  color: var(--text);
  font: inherit;
}
.connect select, .connect input { width: auto; min-width: 16rem; margin: 0; }
@media (min-width: 760px) {
  .legend { grid-template-columns: 1fr 1fr; }
  .grid { grid-template-columns: 1fr 1fr; }
  .cell.wide { grid-column: 1 / -1; }
}
@media (max-width: 640px) {
  .sheet { padding: 0 12px 36px; }
  .connect { margin-left: 0; width: 100%; }
  .connect select, .connect input { min-width: 0; flex: 1 1 12rem; }
  h1 { font-size: 26px; }
}
@media (prefers-reduced-motion: reduce) {
  * { scroll-behavior: auto; }
}
"""


def page(title: str, inner: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<main class="sheet">
{inner}
</main>
</body>
</html>
"""
