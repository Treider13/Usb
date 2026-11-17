"""One HTML page a new operator can read next to the card."""

from __future__ import annotations

import html
import json

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
    "messages_with_rcin": "Строки журнала",
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
    "log_schema": "Что есть в журнале",
    "log_events": "События EV",
    "tlog_schema": "Что есть в телеметрии",
    "mavlink_heartbeat": "HEARTBEAT",
    "mavlink_radio_status": "RADIO_STATUS",
    "mavlink_rc_interval_ms": "Шаг записей RC_CHANNELS, мс",
    "autopilot_version": "Версия прошивки",
    "board_messages": "Прочие строки платы",
    "dataflash_logs": "Журналы на плате",
    "spektrum_channel_count": "Каналы Spektrum",
    "spektrum_baud": "Скорость Spektrum",
    "spektrum_sat_bind": "Импульсы привязки Spektrum",
}

# One short line: what the row is and what a person does with it.
USE = {
    "board_name": "Какая плата. Сверьте с надписью на полётнике.",
    "firmware": "Какая прошивка и какой версии. По ней видно, какой это борт.",
    "frame": "Тип рамы: сколько моторов и какая схема. Нужно, чтобы понять конструкцию борта.",
    "flight_os": "Система на плате. Для опознания, не для настройки.",
    "motor_outputs": "Какие выходы идут на моторы. Смотрите, если мотор молчит не на том канале.",
    "imu": "Как опрашивается гироскоп. Дрожь борта смотрите в вибрации, не здесь.",
    "iomcu": "Вторая микросхема платы, если она есть.",
    "msp_fc_version": "Версия, которую плата назвала сама.",
    "msp_board": "Имя платы из ответа прошивки. Сверьте с корпусом.",
    "msp_build": "Дата и номер сборки. Отличает одну прошивку от другой.",
    "craft_name": "Позывной борта, записанный в полётнике.",
    "pilot_name": "Имя пилота из настроек.",
    "device_uid": "Номер борта. Им отличают один полётник от другого.",
    "mcu_id": "Номер микросхемы. Им отличают плату, даже если имя совпало.",
    "nameplate_vtx": "Надпись с корпуса видеопередатчика. Это не частота этого вылета.",
    "nameplate_radio": "Надпись с корпуса радиомодуля. Протокол по ней не называют.",
    "nameplate_gimbal": "Надпись с корпуса подвеса. Настройка подвеса остаётся отдельно.",
    "stm32_probe": "Какой чип увидели в сохранённом чтении. Сверьте с платой.",
    "stm32_log_contains_write": "В принесённом журнале была запись в чип. Карточка её не повторяет.",
    "serialrx_provider": "Какой протокол приёмника выбран в полётнике.",
    "serial_link_class": "Какого типа связь с пультом.",
    "uart_protocol": "Какой протокол пульта плата приняла. По нему видно, чем связан приёмник.",
    "air_protocol": "Протокол в воздухе. Это не герцы и не скорость пакетов.",
    "uplink_lq": "Насколько живая связь с пульта. Чем ниже, тем ближе отказ связи.",
    "radio_protocol": "Какая прошивка на приёмнике.",
    "receiver_port": "В какой разъём воткнут приёмник.",
    "serial_ports": "Какие разъёмы заняты и чем.",
    "vtx_uart": "Куда подключён видеопередатчик.",
    "packet_rate_log_hz": "Герцы пульта в момент взведения. Это не индекс в настройках приёмника.",
    "radio_tx_packet_rate": "Индекс скорости из пульта. В герцы его не переводят.",
    "radio_binding_rate": "Вариант привязки приёмника. Это индекс, не герцы.",
    "radio_rateinitialidx": "Индекс режима приёмника. Не частота этого вылета.",
    "radio_rate_index": "Индекс режима. Не герцы.",
    "rcin_interval_us": "Как часто журнал пишет стики. Это не скорость радио.",
    "video_frequency_mhz": "На какой частоте картинка. Этот канал ищите в очках.",
    "video_power": "Мощность видео индексом из настроек.",
    "video_power_mw": "Мощность картинки в милливаттах.",
    "video_grid": "Сетка каналов видео из прошивки.",
    "video_grid_lookup": "Канал, сохранённый в настройках. Сам передатчик мог не ответить.",
    "vtx_device_responded": "Ответил ли видеопередатчик. Если нет, частота взята из настроек.",
    "vtx_switch_rules": "Какой тумблер переключает видео.",
    "vtx_enable": "Включено ли видео в настройках. Это не ответ передатчика.",
    "vtx_pitmode_configured": "Тихий режим записан в настройке. Не значит, что он сейчас включён.",
    "vtxtable": "Таблица каналов видео из прошивки.",
    "vtx": "Строки видео в дампе. Это правила тумблера, не текущий канал.",
    "route_source": "Из какого файла взяты точки. Если здесь none, маршрута нет.",
    "route_track": "Где борт был по спутникам. Без точек маршрута нет.",
    "takeoff_lat": "Широта взлёта. Первая точка файла точкой взлёта не считается.",
    "takeoff_lon": "Долгота взлёта. Вместе с широтой это место отрыва.",
    "takeoff_time_us": "Когда в журнале записано взведение.",
    "landing_time_us": "Когда в журнале записана посадка.",
    "flight_duration_us": "Сколько прошло от взведения до посадки по меткам журнала.",
    "home": "Точка дома. От неё считается, как далеко уходил борт.",
    "max_distance_from_home_m": "Насколько далеко борт уходил от дома.",
    "baro_alt": "Высота по давлению. Это не координата и не маршрут.",
    "mission_waypoints": "Точки задания. Это план, не след полёта.",
    "mission_file_source": "Откуда взяты точки задания.",
    "aux": "Что делают тумблеры на пульте.",
    "failsafe": "Что борт делает при отказе связи.",
    "osd": "Что выведено на экран в очках.",
    "osd_layout": "Где на экране в очках какая надпись.",
    "features": "Какие функции прошивки включены.",
    "parameters": "Все настройки платы. Ищите нужное имя. Числа здесь не меняются.",
    "messages": "Что плата написала текстом.",
    "messages_with_rcin": "Текстовые строки журнала: прошивка, протокол пульта, выходы.",
    "modes": "Какой режим полёта был в журнале.",
    "rc_protocols": "Какие протоколы пульта разрешены. «Все» — не имя одного протокола.",
    "mnt1_type": "Какой подвес прописан. Если строки нет, подвеса в настройках нет.",
    "cam1_type": "Как подключена камера. Если строки нет, камеры в настройках нет.",
    "expresslrs_spi": "Настройки приёмника, записанные в полётник.",
    "blackbox_header": "Шапка журнала Betaflight: версия и позывной.",
    "radio_secrets_removed": "Пароли и ключи из чтения убраны. В карточке их нет.",
    "radio_fields_requires_auth": "Страница приёмника просит пароль. Его вводите вы сами, один раз.",
    "radio_page": "Что прочитано со страницы приёмника.",
    "cli_sections": "Настройки из дампа, разложенные по разделам.",
    "cli_commands": "Остальные строки дампа.",
    "log_schema": "Что записано в открытом журнале. Число — сколько раз, не настройка.",
    "log_events": "Взведение и посадка в журнале. По ним видно, был ли вылет.",
    "tlog_schema": "Что есть в телеметрии с земли.",
    "mavlink_heartbeat": "Плата ответила по USB. По этому ответу она опознана.",
    "mavlink_radio_status": "Качество связи в телеметрии. Это не скорость пакетов.",
    "mavlink_rc_interval_ms": "Как часто в телеметрии записаны стики. Не скорость радио.",
    "autopilot_version": "Номер прошивки, который плата отдала по запросу.",
    "board_messages": "Другие строки платы. Читайте текст, отдельного поля из них не вышло.",
    "dataflash_logs": "Файлы журнала в памяти платы. Карточка открывает последний ненулевой.",
    "spektrum_channel_count": "Сколько каналов у Spektrum.",
    "spektrum_baud": "Скорость линии Spektrum.",
    "spektrum_sat_bind": "Импульсы привязки записаны. Команда привязки не отправляется.",
}

GROUP_USE = {
    "Кто это": "Кто этот борт: прошивка, плата и рама.",
    "Радио": "Чем борт связан с пультом и насколько связь живая.",
    "Видео": "На какой частоте картинка и какой мощностью.",
    "Маршрут": "Где борт был. Без спутников со статусом 3D маршрута не будет.",
    "Полётник": "Настройки и то, что плата записала в журнал.",
}

GROUPS = (
    ("Кто это", ("firmware", "board_name", "frame", "flight_os", "motor_outputs", "imu", "iomcu", "msp_board", "msp_fc_version", "msp_build", "craft_name", "pilot_name", "device_uid", "mcu_id", "autopilot_version", "board_messages", "stm32_probe", "stm32_log_contains_write", "nameplate_vtx", "nameplate_radio", "nameplate_gimbal")),
    ("Радио", ("radio_protocol", "receiver_port", "serialrx_provider", "serial_link_class", "uart_protocol", "air_protocol", "uplink_lq", "packet_rate_log_hz", "radio_tx_packet_rate", "radio_binding_rate", "radio_rateinitialidx", "radio_rate_index", "rcin_interval_us", "mavlink_radio_status", "mavlink_rc_interval_ms", "serial_ports", "expresslrs_spi")),
    ("Видео", ("video_frequency_mhz", "video_power", "video_power_mw", "video_grid", "video_grid_lookup", "vtx_uart", "vtx_device_responded", "vtx_enable", "vtx_pitmode_configured", "vtx_switch_rules", "vtxtable", "vtx")),
    ("Маршрут", ("route_source", "route_track", "takeoff_lat", "takeoff_lon", "takeoff_time_us", "landing_time_us", "flight_duration_us", "home", "max_distance_from_home_m", "baro_alt", "mission_waypoints", "mission_file_source")),
)


def _use(name: str) -> str:
    if name in USE:
        return USE[name]
    if name.startswith(("fs_", "batt_fs")):
        return "Что борт делает при отказе связи, газа или батареи."
    if name.startswith("radio_"):
        return "Поле со страницы приёмника. Пароли сюда не попадают."
    if name.startswith("nameplate_"):
        return "Надпись с корпуса. Это не измерение этого вылета."
    return "Прочитано с борта. Строка есть — значение настоящее."


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


# Names a person can use. Everything else in a DataFlash log is bookkeeping.
_LOG_PLAIN = (
    ("GPS", "Спутники, координаты"),
    ("GPS2", "Второй приёмник спутников"),
    ("ORGN", "Дом"),
    ("POS", "Оценка положения, не спутник"),
    ("RCIN", "Стики пульта"),
    ("RCI2", "Дальние каналы пульта"),
    ("RCOU", "Команды на моторы"),
    ("RCO2", "Дальние выходы моторов"),
    ("BARO", "Высота по барометру"),
    ("CTUN", "Высота, которую держал борт"),
    ("ATT", "Крен, тангаж и курс"),
    ("BAT", "Батарея"),
    ("ESC", "Обороты моторов"),
    ("RSSI", "Уровень сигнала приёмника"),
    ("IMU", "Гироскоп и акселерометр"),
    ("VIBE", "Вибрация"),
    ("MODE", "Режим полёта"),
    ("EV", "Взведение и события"),
    ("PARM", "Параметры"),
    ("MSG", "Текстовые строки"),
    ("CMD", "Точки задания"),
    ("ERR", "Ошибки"),
    ("POWR", "Питание платы"),
    ("VER", "Версия прошивки в журнале"),
)
_LOG_WORD = dict(_LOG_PLAIN)


def _log_summary(value: dict) -> str:
    lines = []
    service = 0
    seen = set()
    for name, word in _LOG_PLAIN:
        entry = value.get(name)
        if not isinstance(entry, dict):
            continue
        count = entry.get("count")
        if not count:
            continue
        seen.add(name)
        lines.append(f"<li><strong>{html.escape(word)}</strong> — {html.escape(str(count))} кадров</li>")
    for name, entry in value.items():
        if name in seen or name in _LOG_WORD:
            continue
        if isinstance(entry, dict):
            service += int(entry.get("count") or 0)
    if service:
        lines.append(f"<li>Служебные расчёты платы — {service}. Их читать не нужно.</li>")
    dataflash = any(name in value for name in ("RCIN", "PARM", "BARO", "MSG"))
    if dataflash and "GPS" not in seen and "GPS2" not in seen:
        action = "Спутников в этом журнале нет, поэтому маршрута из него не будет. Смотрите то, что в списке есть: стики, высота, батарея, моторы."
    else:
        action = "Строка есть в списке — она уже разобрана в карточке. Строки нет — плата это не писала, значение не появится."
    intro = "Это состав одного открытого файла. Число — сколько раз плата записала строку. Это не настройка, менять его не нужно."
    return (
        f"<p>{html.escape(intro)}</p><ul>"
        + "".join(lines)
        + f"</ul><p>Что делать: {html.escape(action)}</p>"
    )


def _message_lines(value: list) -> str:
    items = []
    snapshots = []
    for row in value:
        text = str(row.get("text") or "").strip()
        if text:
            items.append(f"<li>{html.escape(text)}</li>")
        sticks = row.get("rcin")
        if isinstance(sticks, dict) and sticks:
            snapshots.append(sticks)
    note = ""
    if snapshots and all(item == snapshots[0] for item in snapshots):
        moved = []
        for key, raw in snapshots[0].items():
            try:
                number = int(float(raw))
            except (TypeError, ValueError):
                continue
            if number < 1400 or number > 1600:
                channel = key[1:] if key.startswith("C") and key[1:].isdigit() else key
                moved.append(f"канал {channel}: {number}")
        if moved:
            note = "<p>Стики в эти строки не менялись. Середина стика — около 1500. " + html.escape(", ".join(moved)) + ".</p>"
    elif snapshots:
        note = "<p>Стики в этих строках менялись. Повтор всех каналов на экран не выводится.</p>"
    return "<ul>" + "".join(items) + "</ul>" + note


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
        return _log_summary(value)
    if isinstance(value, list) and value and all(isinstance(item, dict) and "text" in item for item in value):
        return _message_lines(value)
    if isinstance(value, list) and value and all(isinstance(item, dict) and item.get("name") == "LOG_ENTRY" for item in value):
        return _logs_on_board(value)
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
    if isinstance(value, dict) and isinstance(value.get("bits"), list):
        names = [str(item) for item in value["bits"]]
        if names == ["All"]:
            text = "включены все протоколы пульта. Это маска, не имя одного протокола."
        else:
            text = ", ".join(names) or "в маске нет названных протоколов"
        return f"<p>{html.escape(text)}</p>"
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


def _column_name(key: str) -> str:
    return {"TimeUS": "Метка, мкс", "time_us": "Метка, мкс", "Id": "Событие"}.get(key, key)


def _event_cell(key: str, value) -> str:
    if key == "Id":
        try:
            number = int(value)
        except (TypeError, ValueError):
            return str(value)
        return {10: "взведение", 11: "снятие с взведения"}.get(number, str(number))
    if isinstance(value, (int, float)):
        return _plain_number(value)
    return "" if value is None else str(value)


def _bytes_plain(size: int) -> str:
    if size >= 1024:
        return f"{round(size / 1024)} КБ"
    return f"{size} байт"


def _logs_on_board(rows: list) -> str:
    """LOG_ENTRY list: how many journals sit on the board, and which one this card opened."""
    files = []
    total = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            ident = int(row.get("id"))
            size = int(row.get("size") or 0)
        except (TypeError, ValueError):
            continue
        total = max(total, int(row.get("num_logs") or 0))
        files.append((ident, size))
    if not files:
        return "<p>Плата не прислала ни одного журнала.</p>"
    total = total or len(files)
    nonempty = [item for item in files if item[1] > 0]
    newest = max(nonempty) if nonempty else None
    lines = [f"На плате журналов: {total}."]
    if newest:
        lines.append(f"Эта карточка открыла последний ненулевой: номер {newest[0]}, {_bytes_plain(newest[1])}.")
    earlier = len(nonempty) - (1 if newest else 0)
    if earlier > 0:
        lines.append(f"Более ранних журналов: {earlier}. Эта карточка их не открывает.")
    lines.append("Что делать: читать карточку, она уже по открытому журналу. Старые журналы с платы не стирайте. Другой вылет — это другой номер в этом списке.")
    return "".join(f"<p>{html.escape(line)}</p>" for line in lines)


def _record_table(value) -> str:
    if not isinstance(value, list) or not value or not all(isinstance(item, dict) for item in value):
        return ""
    keys: list[str] = []
    for item in value:
        for key, cell in item.items():
            if key == "mavpackettype":
                continue
            if isinstance(cell, (dict, list)):
                return ""
            if key not in keys:
                keys.append(key)
    shown = value
    note = ""
    if len(value) > 8:
        shown = [value[0], value[-1]]
        note = f"<p>строк {len(value)}, первая и последняя</p>"
    head = "".join(f"<th>{html.escape(_column_name(key))}</th>" for key in keys)
    body = []
    for item in shown:
        cells = "".join(
            f"<td>{html.escape(_event_cell(key, item.get(key)))}</td>"
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
        f'<p class="why">{html.escape(_use(name))}</p>'
        "</article>"
    )


def _flight_block(flight: dict) -> str:
    """A flight with no track and no home is not shown. The gaps list already says so."""
    takeoff = flight.get("takeoff") or None
    landing = flight.get("landing") or None
    home = flight.get("home") or None
    track = flight.get("track") or []
    if not track and not takeoff and not landing and not home:
        return ""
    bits = []
    if takeoff:
        bits.append(f"Точка взлёта: {takeoff.get('lat')}, {takeoff.get('lon')}")
    if landing:
        bits.append(f"Посадка: {landing.get('lat')}, {landing.get('lon')}")
    if home:
        bits.append(f"Дом: {home.get('lat')}, {home.get('lon')}")
    if track:
        bits.append(f"Точек маршрута: {len(track)}")
    if flight.get("route_length_m") is not None:
        bits.append(f"Длина маршрута, м: {round(float(flight['route_length_m']))}")
    if flight.get("max_distance_from_home_m") is not None:
        bits.append(f"Дальше всего от дома, м: {round(float(flight['max_distance_from_home_m']))}")
    index = int(flight.get("index") or 0) + 1
    body = "".join(f"<li>{html.escape(line)}</li>" for line in bits)
    return f'<article class="cell wide"><h3>Вылет {index}</h3><ul>{body}</ul></article>'


def render_html(card: Card, saved_path: str | None = None) -> str:
    buckets: dict[str, list[str]] = {title: [] for title, _names in GROUPS}
    buckets["Полётник"] = []
    for name, item in card.fields.items():
        if item.status in ("missing", "not_applicable"):
            continue
        if name == "messages" and card.fields.get("messages_with_rcin") and card.fields["messages_with_rcin"].status == "confirmed":
            continue
        buckets[_group_of(name)].append(_cell(name, item))
    sections = []
    for title, _names in (*GROUPS, ("Полётник", ())):
        cells = buckets.get(title) or []
        if not cells:
            continue
        blurb = GROUP_USE.get(title, "")
        intro = f'<p class="blurb">{html.escape(blurb)}</p>' if blurb else ""
        sections.append(f"<h2>{html.escape(title)}</h2>{intro}<div class=\"grid\">{''.join(cells)}</div>")
    gap_lines = []
    covered = set()
    for name, item in card.fields.items():
        if item.status != "missing":
            continue
        covered.add(f"{name}: {item.reason}")
        gap_lines.append(
            f'<li class="hole"><span class="key">{html.escape(name)}</span> '
            f"<strong>{html.escape(_label(name))}</strong>. {html.escape(_use(name))} Сейчас этого нет.</li>"
        )
    for line in card.holes:
        if line in covered or any(line.startswith(f"{name}: ") for name in card.fields):
            continue
        gap_lines.append(f'<li class="hole">{html.escape(line)}</li>')
    if gap_lines:
        holes = "<ul class=\"gaps\">" + "".join(gap_lines) + "</ul>"
    else:
        holes = "<p>Нет данных не осталось. Ниже только то, что прочитано.</p>"
    flight_cards = [block for block in (_flight_block(flight) for flight in card.flights) if block]
    flights = "<h2>Вылеты</h2><div class=\"grid\">" + "".join(flight_cards) + "</div>" if flight_cards else ""
    saved = f"<p>Файл отчёта: {html.escape(saved_path)}</p>" if saved_path else ""
    inner = f"""
<h1>Стрела</h1>
<p class="banner">{html.escape(card.family)}. {html.escape(card.raw_banner or "Баннера прошивки нет.")}</p>
<p class="lede">Зелёным отмечено то, что плата ответила. Синим — надпись с шильдика.</p>
{saved}
<ul class="legend">
<li class="confirmed"><span class="stamp">Подтверждено</span> прочитано</li>
<li class="document"><span class="stamp">С шильдика</span> надпись на корпусе</li>
</ul>
<h2>Нет данных</h2>
{holes}
{''.join(sections)}
{flights}
"""
    return page("Стрела — карточка дрона", inner)
