"""Field-card appearance shared by the menu and the report.

The sheet is a paper form on a map-green table. Brass is only the top
edge. Green, blue and red are ink stamps for the four statuses, not a
dashboard palette.
"""

from __future__ import annotations


CSS = """
:root {
  --map: #243028;
  --paper: #d9d3bf;
  --ink: #1c1e18;
  --brass: #8a7344;
  --green: #1f4d32;
  --blue: #1e3a5f;
  --red: #8e2f2a;
  --mute: #5c584e;
  --quiet: #3a3d34;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--map);
  color: var(--ink);
  font-family: "Liberation Sans", "Noto Sans", sans-serif;
  font-size: 17px;
  line-height: 1.45;
}
.sheet {
  max-width: 920px;
  margin: 28px auto;
  background: var(--paper);
  border-top: 10px solid var(--brass);
  padding: 28px 32px 48px;
}
h1 {
  font-family: "Liberation Serif", "DejaVu Serif", serif;
  font-weight: 400;
  font-size: 48px;
  line-height: 1.05;
  margin: 0 0 8px;
}
h2 {
  font-family: "Liberation Serif", "DejaVu Serif", serif;
  font-weight: 400;
  font-size: 28px;
  line-height: 1.2;
  margin: 32px 0 8px;
  border-bottom: 1px solid var(--ink);
  padding-bottom: 4px;
}
p { max-width: 68ch; }
.lede { font-size: 18px; }
.banner { margin-top: 0; color: var(--quiet); }
.actions { display: flex; flex-wrap: wrap; gap: 12px; margin: 20px 0; }
a.action, button {
  display: inline-block;
  background: var(--ink);
  color: var(--paper);
  text-decoration: none;
  padding: 10px 16px;
  border: 0;
  font: inherit;
  cursor: pointer;
}
a.action.quiet {
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--ink);
}
a:focus, button:focus, input:focus, select:focus {
  outline: 2px solid var(--brass);
  outline-offset: 2px;
}
ol.steps { padding-left: 1.2em; max-width: 68ch; }
ol.steps li { margin: 8px 0; }
.legend { list-style: none; padding: 0; margin: 16px 0; display: grid; gap: 8px; }
.legend li { display: flex; align-items: flex-start; gap: 8px; }
.stamp {
  display: inline-block;
  border: 1px solid var(--ink);
  color: var(--ink);
  padding: 1px 8px;
  font-size: 14px;
  white-space: nowrap;
}
.cell.confirmed .stamp, .legend .confirmed .stamp { color: var(--green); border-color: var(--green); }
.cell.document .stamp, .legend .document .stamp { color: var(--blue); border-color: var(--blue); }
.cell.missing .stamp, .legend .missing .stamp { color: var(--red); border-color: var(--red); }
.cell.not_applicable .stamp, .legend .not_applicable .stamp { color: var(--mute); border-color: var(--mute); }
label .title { font-weight: 700; }
.grid { display: grid; grid-template-columns: 1fr; }
.cell { border-bottom: 1px solid rgba(28, 30, 24, 0.28); padding: 12px 16px 12px 0; }
.cell h3 { margin: 0 0 4px; font-size: 17px; font-weight: 700; color: var(--ink); }
.key { margin: 0; font-family: "JetBrains Mono", "Liberation Mono", monospace; font-size: 12px; color: var(--mute); }
.value table { width: 100%; border-collapse: collapse; font-size: 14px; }
.value th, .value td { border-bottom: 1px solid rgba(28, 30, 24, 0.2); text-align: left; padding: 3px 8px 3px 0; vertical-align: top; font-weight: 400; }
.value th { width: 32%; }
.value pre { white-space: pre-wrap; margin: 4px 0 10px; }
.why, .src { margin: 0; font-size: 14px; color: var(--quiet); }
.hole { border-left: 4px solid var(--red); padding: 4px 0 4px 12px; margin: 12px 0; }
.hole p { margin: 4px 0; }
label { display: block; margin: 16px 0; max-width: 68ch; }
.help { display: block; color: var(--quiet); font-size: 14px; }
input, select {
  width: 100%;
  margin-top: 4px;
  padding: 8px;
  background: #efeadd;
  border: 1px solid var(--ink);
  color: var(--ink);
  font: inherit;
}
@media (min-width: 760px) {
  .legend { grid-template-columns: 1fr 1fr; }
  .grid { grid-template-columns: 1fr 1fr; }
  .cell.wide { grid-column: 1 / -1; }
}
@media (max-width: 640px) {
  .sheet { margin: 0; padding: 20px 16px 36px; }
  h1 { font-size: 36px; }
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
