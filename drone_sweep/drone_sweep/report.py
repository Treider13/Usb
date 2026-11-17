"""One HTML page a new operator can read next to the card."""

from __future__ import annotations

import html
import json

from .hints import WORKFLOW
from .model import Card
from .theme import page


STATUS_WORD = {
    "confirmed": "Подтверждено",
    "document": "С шильдика",
    "missing": "Нет данных",
    "not_applicable": "Не про это",
}

LABELS = {
    "board_name": "Полётник",
    "firmware": "Прошивка",
    "frame": "Тип рамы",
    "flight_os": "Система платы",
    "motor_outputs": "Выходы моторов",
    "imu": "Гироскоп",
    "iomcu": "Сопроцессор",
    "msp_fc_version": "Версия прошивки MSP",
    "msp_board": "Плата из MSP",
    "msp_build": "Сборка",
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
    "autopilot_version": "Версия прошивки",
    "board_messages": "Прочие строки платы",
    "dataflash_logs": "Журналы на плате",
    "spektrum_channel_count": "Каналы Spektrum",
    "spektrum_baud": "Скорость Spektrum",
    "spektrum_sat_bind": "Импульсы привязки Spektrum",
    "cli_diff": "Отличия от заводских",
    "flight_timeline": "Лента событий",
    "blackbox_arm": "Первая точка Blackbox",
    "blackbox_disarm": "Последняя точка Blackbox",
    "inav_waypoints": "Точки wp INAV",
}

GROUPS = (
    ("Кто это", ("firmware", "board_name", "frame", "flight_os", "motor_outputs", "imu", "iomcu", "msp_board", "msp_fc_version", "msp_build", "craft_name", "pilot_name", "device_uid", "mcu_id", "autopilot_version", "board_messages", "stm32_probe", "stm32_log_contains_write", "nameplate_vtx", "nameplate_radio", "nameplate_gimbal")),
    ("Радио", ("radio_protocol", "receiver_port", "serialrx_provider", "serial_link_class", "uart_protocol", "air_protocol", "uplink_lq", "packet_rate_log_hz", "radio_tx_packet_rate", "radio_binding_rate", "radio_rateinitialidx", "radio_rate_index", "rcin_interval_us", "mavlink_radio_status", "mavlink_rc_interval_ms", "serial_ports", "expresslrs_spi")),
    ("Видео", ("video_frequency_mhz", "video_power", "video_power_mw", "video_grid", "video_grid_lookup", "vtx_uart", "vtx_device_responded", "vtx_enable", "vtx_pitmode_configured", "vtx_switch_rules", "vtxtable", "vtx")),
    ("Маршрут", ("route_source", "route_track", "takeoff_lat", "takeoff_lon", "takeoff_time_us", "landing_time_us", "flight_duration_us", "home", "max_distance_from_home_m", "baro_alt", "mission_waypoints", "mission_file_source", "blackbox_arm", "blackbox_disarm", "inav_waypoints")),
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
    if name.startswith(("route_", "takeoff_", "landing_", "mission_", "blackbox_")) or name == "inav_waypoints":
        return "Маршрут"
    if name in {"cli_diff", "flight_timeline"}:
        return "Полётник"
    return "Полётник"


def _plain_number(value) -> str:
    if isinstance(value, float) and value == int(value) and abs(value) < 1_000_000_000:
        return str(int(value))
    return str(value)


def _show(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return _plain_number(value)
    return json.dumps(value, ensure_ascii=False, indent=2)


def _value_html(value) -> str:
    if isinstance(value, list) and value and all(isinstance(item, str) for item in value):
        return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in value) + "</ul>"
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
            if isinstance(rows_value, list) and rows_value and not detail:
                detail = f"кадров {len(rows_value)}"
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
    table = _record_table(value)
    if table:
        return table
    return html.escape(_show(value))


def _flat_table(value: dict) -> str:
    if not value:
        return "<p>—</p>"
    rows = "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(_plain_number(item) if isinstance(item, (int, float)) else str(item))}</td></tr>"
        for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
    )
    return f"<table>{rows}</table>"


def _record_table(value) -> str:
    if not isinstance(value, list) or not value or not all(isinstance(item, dict) for item in value):
        return ""
    keys: list[str] = []
    for item in value:
        for key, cell in item.items():
            if isinstance(cell, (dict, list)):
                return ""
            if key not in keys:
                keys.append(key)
    shown = value
    note = ""
    if len(value) > 8:
        shown = [value[0], value[-1]]
        note = f"<p>строк {len(value)}, первая и последняя</p>"
    head = "".join(f"<th>{html.escape(str(key))}</th>" for key in keys)
    body = []
    for item in shown:
        cells = "".join(
            f"<td>{html.escape(_plain_number(item.get(key)) if isinstance(item.get(key), (int, float)) else str(item.get(key, '')))}</td>"
            for key in keys
        )
        body.append(f"<tr>{cells}</tr>")
    return note + "<table><tr>" + head + "</tr>" + "".join(body) + "</table>"


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
        if item.status in ("missing", "not_applicable"):
            continue
        buckets[_group_of(name)].append(_cell(name, item))
    sections = []
    for title, _names in (*GROUPS, ("Полётник", ())):
        cells = buckets.get(title) or []
        if not cells:
            continue
        sections.append(f"<h2>{html.escape(title)}</h2><div class=\"grid\">{''.join(cells)}</div>")
    steps = "".join(f"<li>{html.escape(line)}</li>" for line in WORKFLOW)
    gap_lines = []
    covered = set()
    for name, item in card.fields.items():
        if item.status != "missing":
            continue
        covered.add(f"{name}: {item.reason}")
        gap_lines.append(
            f'<li class="hole"><span class="key">{html.escape(name)}</span> '
            f"<strong>{html.escape(_label(name))}</strong> — {html.escape(item.reason)}</li>"
        )
    for line in card.holes:
        if line in covered or any(line.startswith(f"{name}: ") for name in card.fields):
            continue
        gap_lines.append(f'<li class="hole">{html.escape(line)}</li>')
    if gap_lines:
        holes = "<ul class=\"gaps\">" + "".join(gap_lines) + "</ul>"
    else:
        holes = "<p>Нет данных не осталось. Ниже только то, что прочитано.</p>"
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
    file_rows = []
    for record in card.files:
        file_rows.append(
            "<tr>"
            f"<td>{html.escape(str(record.get('kind', '')))}</td>"
            f"<td>{html.escape(str(record.get('path', '')))}</td>"
            f"<td>{html.escape(str(record.get('sha256', '')))}</td>"
            "</tr>"
        )
    files = ""
    if file_rows:
        files = (
            "<h2>Файлы и хеши</h2><table><tr><th>Что</th><th>Путь</th><th>sha256</th></tr>"
            + "".join(file_rows)
            + "</table>"
        )
    command_line = ""
    if card.commands:
        command_line = "<p>Команды чтения: " + html.escape(", ".join(card.commands)) + "</p>"
    inner = f"""
<h1>Стрела</h1>
<p class="banner">{html.escape(card.family)}. {html.escape(card.raw_banner or "Баннера прошивки нет.")}</p>
<p class="lede">Зелёным отмечено то, что плата ответила. Синим — надпись с шильдика.</p>
{saved}
{command_line}
{files}
<ul class="legend">
<li class="confirmed"><span class="stamp">Подтверждено</span> прочитано</li>
<li class="document"><span class="stamp">С шильдика</span> надпись на корпусе</li>
</ul>
<h2>С чего начать</h2>
<ol class="steps">{steps}</ol>
<h2>Нет данных</h2>
{holes}
<h2>Где искали маршрут</h2>
<ol class="steps">{journal}</ol>
{''.join(sections)}
{flights}
"""
    return page("Стрела — карточка дрона", inner)
