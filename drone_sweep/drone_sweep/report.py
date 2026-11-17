"""One HTML page a new operator can read next to the card."""

from __future__ import annotations

import html
import json

from .hints import WORKFLOW, hint_for_hole
from .model import Card
from .theme import page


STATUS_WORD = {
    "confirmed": "Подтверждено",
    "document": "С шильдика",
    "missing": "Нет данных",
    "not_applicable": "Не про это",
}

LABELS = {
    "board_name": "Плата",
    "craft_name": "Имя борта",
    "pilot_name": "Имя пилота",
    "device_uid": "Номер устройства",
    "mcu_id": "Номер микросхемы",
    "nameplate_vtx": "Шильдик видеопередатчика",
    "nameplate_radio": "Шильдик радиомодуля",
    "nameplate_gimbal": "Шильдик подвеса",
    "stm32_probe": "Идентификатор STM32",
    "stm32_log_contains_write": "В журнале программатора была запись",
    "serialrx_provider": "Протокол на UART полётника",
    "serial_link_class": "Класс радиолинии",
    "uart_protocol": "Протокол UART",
    "air_protocol": "Протокол в воздухе",
    "uplink_lq": "Качество uplink",
    "radio_protocol": "Прошивка приёмника",
    "receiver_port": "Порт приёмника",
    "serial_ports": "Порты",
    "vtx_uart": "Порт видеопередатчика",
    "packet_rate_log_hz": "Герцы из лога",
    "radio_tx_packet_rate": "Индекс скорости пульта",
    "radio_binding_rate": "Вариант привязки",
    "radio_rateinitialidx": "Индекс режима приёмника",
    "radio_rate_index": "Индекс режима",
    "rcin_interval_us": "Шаг записей RCIN",
    "video_frequency_mhz": "Частота видео, МГц",
    "video_power": "Мощность видео",
    "video_power_mw": "Мощность видео, мВт",
    "video_grid": "Сетка частот",
    "video_grid_lookup": "Сетка и параметры видео",
    "vtx_device_responded": "Ответ видеопередатчика",
    "vtx_switch_rules": "Правила AUX видео",
    "vtx_enable": "Видеопередатчик включён в параметрах",
    "vtx_pitmode_configured": "Pit mode в параметре",
    "vtxtable": "Строки таблицы видео",
    "vtx": "Строки vtx",
    "route_source": "Откуда взят маршрут",
    "route_track": "Точки маршрута",
    "takeoff_lat": "Широта взлёта",
    "takeoff_lon": "Долгота взлёта",
    "takeoff_time_us": "Метка взлёта в логе",
    "landing_time_us": "Метка посадки в логе",
    "flight_duration_us": "Длительность по меткам лога",
    "home": "Дом",
    "max_distance_from_home_m": "Дальше всего от дома, м",
    "baro_alt": "Высота барометра",
    "mission_waypoints": "Точки миссии",
    "mission_file_source": "Файл миссии",
    "aux": "Режимы тумблеров",
    "failsafe": "Отказобезопасность",
    "osd": "Позиции OSD",
    "osd_layout": "Раскладка OSD",
    "features": "Функции прошивки",
    "parameters": "Параметры",
    "messages": "Сообщения лога",
    "messages_with_rcin": "Сообщения рядом с RCIN",
    "modes": "Режимы полёта",
    "rc_protocols": "Маска протоколов",
    "mnt1_type": "Тип подвеса",
    "cam1_type": "Тип камеры",
    "expresslrs_spi": "Настройки ExpressLRS в полётнике",
    "blackbox_header": "Заголовок Blackbox",
    "radio_secrets_removed": "Что вырезано из приёмника",
    "radio_fields_requires_auth": "Страница приёмника закрыта паролем",
    "radio_page": "Все поля приёмника",
    "cli_sections": "Все секции CLI",
    "cli_commands": "Остальные команды CLI",
    "log_schema": "Состав лога",
    "log_events": "События EV",
    "tlog_schema": "Состав tlog",
    "mavlink_heartbeat": "HEARTBEAT",
    "mavlink_radio_status": "RADIO_STATUS",
    "mavlink_rc_interval_ms": "Шаг записей RC_CHANNELS, мс",
    "spektrum_channel_count": "Каналы Spektrum",
    "spektrum_baud": "Скорость Spektrum",
    "spektrum_sat_bind": "Импульсы привязки Spektrum",
}

GROUPS = (
    ("Кто это", ("board_name", "craft_name", "pilot_name", "device_uid", "mcu_id", "stm32_probe", "stm32_log_contains_write", "nameplate_vtx", "nameplate_radio", "nameplate_gimbal")),
    ("Радио", ("radio_protocol", "receiver_port", "serialrx_provider", "serial_link_class", "uart_protocol", "air_protocol", "uplink_lq", "packet_rate_log_hz", "radio_tx_packet_rate", "radio_binding_rate", "radio_rateinitialidx", "radio_rate_index", "rcin_interval_us", "mavlink_radio_status", "mavlink_rc_interval_ms", "serial_ports", "expresslrs_spi")),
    ("Видео", ("video_frequency_mhz", "video_power", "video_power_mw", "video_grid", "video_grid_lookup", "vtx_uart", "vtx_device_responded", "vtx_enable", "vtx_pitmode_configured", "vtx_switch_rules", "vtxtable", "vtx")),
    ("Маршрут", ("route_source", "route_track", "takeoff_lat", "takeoff_lon", "takeoff_time_us", "landing_time_us", "flight_duration_us", "home", "max_distance_from_home_m", "baro_alt", "mission_waypoints", "mission_file_source")),
)


def _label(name: str) -> str:
    if name in LABELS:
        return LABELS[name]
    if name.startswith("radio_"):
        return "Поле приёмника " + name.removeprefix("radio_")
    if name.startswith("fs_") or name.startswith("batt_fs"):
        return "Параметр " + name
    return name


def _group_of(name: str) -> str:
    for title, names in GROUPS:
        if name in names:
            return title
    if name.startswith("nameplate_"):
        return "Кто это"
    if name.startswith("radio_"):
        return "Радио"
    if name.startswith(("video_", "vtx")):
        return "Видео"
    if name.startswith(("route_", "takeoff_", "landing_", "mission_")):
        return "Маршрут"
    return "Полётник"


def _show(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def _value_html(value) -> str:
    if isinstance(value, list) and value and all(isinstance(item, dict) and "settings" in item for item in value):
        blocks = []
        for section in value:
            title = html.escape(str(section.get("name", "")))
            blocks.append(f"<p><strong>{title}</strong></p>")
            blocks.append(_flat_table(section.get("settings") or {}))
            lines = section.get("lines") or []
            if lines:
                blocks.append("<pre>" + html.escape("\n".join(str(line) for line in lines)) + "</pre>")
        return "".join(blocks)
    if isinstance(value, dict) and value and all(isinstance(item, dict) and "count" in item for item in value.values()):
        rows = []
        for name, entry in value.items():
            fields = ", ".join(str(item) for item in entry.get("fields") or [])
            detail = entry.get("note") or ""
            rows_value = entry.get("rows")
            if isinstance(rows_value, list) and len(rows_value) <= 8:
                detail = json.dumps(rows_value, ensure_ascii=False)
            elif isinstance(rows_value, list) and rows_value:
                detail = (
                    f"все {len(rows_value)} кадров записаны в card.json. "
                    f"первая {json.dumps(rows_value[0], ensure_ascii=False)} "
                    f"последняя {json.dumps(rows_value[-1], ensure_ascii=False)}"
                )
            rows.append(
                "<tr>"
                f"<th>{html.escape(str(name))}</th>"
                f"<td>{html.escape(str(entry.get('count', '')))}</td>"
                f"<td>{html.escape(fields)}</td>"
                f"<td>{html.escape(detail)}</td>"
                "</tr>"
            )
        return "<table><tr><th>Тип</th><th>Кадров</th><th>Поля</th><th>Строки</th></tr>" + "".join(rows) + "</table>"
    if isinstance(value, dict) and value and all(isinstance(item, list) for item in value.values()):
        rows = []
        for name, lines in value.items():
            rows.append(
                "<tr>"
                f"<th>{html.escape(str(name))}</th>"
                f"<td>{html.escape(chr(10).join(str(line) for line in lines))}</td>"
                "</tr>"
            )
        return "<table>" + "".join(rows) + "</table>"
    if isinstance(value, dict) and value and all(not isinstance(item, (dict, list)) for item in value.values()):
        return _flat_table(value)
    return html.escape(_show(value))


def _flat_table(value: dict) -> str:
    if not value:
        return "<p>—</p>"
    rows = "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(item))}</td></tr>"
        for key, item in value.items()
    )
    return f"<table>{rows}</table>"


def _cell(name: str, item) -> str:
    shown = _show(item.value)
    wide = " wide" if isinstance(item.value, (dict, list)) or len(shown) > 80 else ""
    status = item.status if item.status in STATUS_WORD else "missing"
    return (
        f'<article class="cell {html.escape(status)}{wide}">'
        f"<h3>{html.escape(_label(name))}</h3>"
        f'<p class="key">{html.escape(name)}</p>'
        f'<p><span class="stamp">{html.escape(STATUS_WORD[status])}</span></p>'
        f'<p class="value">{_value_html(item.value)}</p>'
        f'<p class="why">{html.escape(item.reason)}</p>'
        f'<p class="src">{html.escape(item.source)}</p>'
        "</article>"
    )


def render_html(card: Card, saved_path: str | None = None) -> str:
    buckets: dict[str, list[str]] = {title: [] for title, _names in GROUPS}
    buckets["Полётник"] = []
    for name, item in card.fields.items():
        buckets[_group_of(name)].append(_cell(name, item))
    sections = []
    for title, _names in (*GROUPS, ("Полётник", ())):
        cells = buckets.get(title) or []
        if not cells:
            continue
        sections.append(f"<h2>{html.escape(title)}</h2><div class=\"grid\">{''.join(cells)}</div>")
    steps = "".join(f"<li>{html.escape(line)}</li>" for line in WORKFLOW)
    if card.holes:
        holes = "".join(
            "<div class=\"hole\">"
            f"<p>{html.escape(line)}</p>"
            f"<p>{html.escape(hint_for_hole(line))}</p>"
            "</div>"
            for line in card.holes
        )
    else:
        holes = "<p>Пустых клеток нет. Каждая строка ниже прочитана из файла или помечена как чужая для этой прошивки.</p>"
    journal = "".join(
        f"<li>{html.escape(line['source'])}: {html.escape(line['result'])}. {html.escape(line['detail'])}</li>"
        for line in card.journal
    ) or "<li>Файлов маршрута не передавали.</li>"
    flights = ""
    if card.flights:
        flights = "<h2>Вылеты</h2><div class=\"grid\">" + "".join(
            f'<article class="cell wide"><h3>Вылет {html.escape(str(flight.get("index", "")))}</h3>'
            f'<p class="value">{html.escape(_show(flight))}</p></article>'
            for flight in card.flights
        ) + "</div>"
    saved = f"<p>Файл отчёта: {html.escape(saved_path)}</p>" if saved_path else ""
    inner = f"""
<h1>Стрела</h1>
<p class="banner">{html.escape(card.family)}. {html.escape(card.raw_banner or "Баннера прошивки нет.")}</p>
<p class="lede">Зелёная пометка — значение из файла. Синяя — надпись с шильдика. Красная — данных нет, рядом написано, что делать.</p>
{saved}
<ul class="legend">
<li class="confirmed"><span class="stamp">Подтверждено</span> прочитано из файла</li>
<li class="document"><span class="stamp">С шильдика</span> надпись на корпусе, не этот вылет</li>
<li class="missing"><span class="stamp">Нет данных</span> клетка пустая, причина рядом</li>
<li class="not_applicable"><span class="stamp">Не про это</span> поле другой прошивки</li>
</ul>
<h2>С чего начать</h2>
<ol class="steps">{steps}</ol>
<h2>Чего не хватает</h2>
{holes}
<h2>Где искали маршрут</h2>
<ol class="steps">{journal}</ol>
{''.join(sections)}
{flights}
"""
    return page("Стрела — карточка дрона", inner)
