"""Build one card from the files of a single vehicle."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ardupilot_vtx import describe as describe_ardupilot_vtx
from .banner import frame_from_params, mav_type_word, parse_banner_lines
from .blackbox import parse_gps_csv, parse_header_file
from .dump import master_or_unique, parse_boxnames, parse_dump
from .vtx import inav_grid, inav_saved_frequency, parse_video_grid, parse_vtx_rules, selected_channel
from .enums_ardupilot import CAMERA_TYPE_45, MOUNT_TYPE_45, rc_protocols_45
from .hashing import sha256_bytes, sha256_file
from .hints import WORKFLOW, hint_for_hole
from .logs import load_bin, load_tlog
from .mission_files import parse_gpx, parse_plan, parse_qgc_waypoints
from .model import Card, confirmed, document, missing, not_applicable
from .ports import ardupilot_ports, decode_osd_position, parse_betaflight_serial
from .radio import parse_radio_image, parse_radio_json
from .stm32 import parse_stm32_log
from .route import (
    arm_pairs,
    bin_gps_points,
    bin_pos_count,
    build_flights,
    home_from_orgn,
    tlog_points,
)


@dataclass
class Inputs:
    dump_text: str | None = None
    boxnames: str | None = None
    bin_path: Path | None = None
    tlog_path: Path | None = None
    blackbox_path: Path | None = None
    gps_csv_path: Path | None = None
    gpx_path: Path | None = None
    waypoints_path: Path | None = None
    plan_path: Path | None = None
    radio_json: Any = None
    radio_image: bytes | None = None
    nameplates: dict[str, str] = field(default_factory=dict)
    stm32_text: str | None = None
    banner: str = ""
    auth_declined: bool = False
    mavlink_rows: list[dict] | None = None
    read_note: str = ""
    msp_identity: dict | None = None


def assemble(inputs: Inputs) -> Card:
    family, banner = _family(inputs)
    card = Card(family=family, raw_banner=banner)
    card.hints.extend(WORKFLOW)
    rows: list[dict] = []
    if inputs.bin_path is not None:
        rows = load_bin(inputs.bin_path)
        card.files.append(_file_record(inputs.bin_path, "bin"))
        if family == "unknown":
            family = "ardupilot"
            card.family = family
            for row in rows:
                if row.get("name") == "MSG" and str(row.get("Message", "")).startswith("Ardu"):
                    card.raw_banner = str(row["Message"])
                    break

    dump = parse_dump(inputs.dump_text, parse_boxnames(inputs.boxnames)) if inputs.dump_text else None
    if dump is not None and dump.family in ("betaflight", "inav", "cleanflight"):
        family = dump.family
        card.family = family
        card.raw_banner = dump.banner or card.raw_banner

    _vehicle_fields(card, dump, rows)
    _radio_fields(card, inputs)
    _nameplates(card, inputs.nameplates)
    _stm32(card, inputs.stm32_text)
    if inputs.mavlink_rows:
        _absorb_mavlink(card, inputs.mavlink_rows, source="usb")
    if inputs.msp_identity:
        _msp_identity(card, inputs.msp_identity)
    _route(card, inputs, rows)
    _applicability(card)
    _holes(card)
    if inputs.read_note:
        card.holes.append(inputs.read_note)
    return card


def _family(inputs: Inputs) -> tuple[str, str]:
    banner = inputs.banner.strip()
    head = banner.lower()
    if head.startswith("betaflight") or "# betaflight" in head:
        return "betaflight", banner
    if head.startswith("inav") or "# inav" in head:
        return "inav", banner
    if head.startswith("arducopter") or head.startswith("arduplane") or head.startswith("ardupilot"):
        return "ardupilot", banner
    if inputs.dump_text:
        parsed = parse_dump(inputs.dump_text)
        if parsed.family != "unknown":
            return parsed.family, parsed.banner
    if inputs.bin_path is not None:
        return "ardupilot", banner
    return "unknown", banner


def effective_settings(dump) -> dict[str, str]:
    """Settings used by the named cells. Disagreements stay only in cli_sections."""
    merged = dict(dump.settings)
    grouped: dict[str, list[str]] = {}
    for section in dump.sections:
        if str(section["name"]).lower().startswith("master"):
            continue
        for key, value in section["settings"].items():
            grouped.setdefault(key, []).append(value)
    for key, values in grouped.items():
        if key not in merged and values and all(item == values[0] for item in values):
            merged[key] = values[0]
    return merged


def _plain(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("latin1", errors="replace").rstrip("\x00")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def log_inventory(rows: list[dict]) -> dict[str, dict]:
    """Every DataFlash or tlog message type, with every row."""
    grouped: dict[str, list[dict]] = {}
    order: list[str] = []
    for row in rows:
        name = str(row.get("name") or "")
        if name not in grouped:
            order.append(name)
            grouped[name] = []
        grouped[name].append({key: _plain(value) for key, value in row.items() if key != "name"})
    inventory: dict[str, dict] = {}
    for name in order:
        items = grouped[name]
        entry: dict = {
            "count": len(items),
            "fields": list(items[0].keys()) if items else [],
            "rows": items,
        }
        inventory[name] = entry
    return inventory


def _file_record(path: Path, kind: str) -> dict[str, str]:
    return {"kind": kind, "path": str(path), "sha256": sha256_file(path)}


def _vehicle_fields(card: Card, dump, rows: list[dict]) -> None:
    if dump is not None:
        if dump.board_name:
            card.put("board_name", confirmed(dump.board_name, "dump all"))
        else:
            card.put("board_name", missing("в dump all нет строки board_name", "dump all"))
        for key in ("craft_name", "pilot_name"):
            value = master_or_unique(dump, key)
            if value:
                card.put(key, confirmed(value, "dump all"))
            else:
                card.put(key, missing(f"в dump all нет {key}", "dump all"))
        modes = [
            {
                "mode_id": item.mode_id,
                "name": item.name,
                "channel": item.channel,
                "range_start": item.range_start,
                "range_end": item.range_end,
            }
            for item in dump.aux
        ]
        card.put("aux", confirmed(modes, "dump all"))
        unnamed = [item.mode_id for item in dump.aux if not item.name]
        if unnamed:
            card.holes.append(
                "Имена режимов "
                + ", ".join(str(item) for item in unnamed)
                + " не пришли из MSP_BOXNAMES. Номер режима записан, слово не выдумано."
            )
        card.put("failsafe", confirmed(dump.failsafe, "dump all") if dump.failsafe else missing("в dump all нет failsafe_*", "dump all"))
        card.put("vtxtable", confirmed(dump.vtxtable, "dump all") if dump.vtxtable else missing("в dump all нет vtxtable", "dump all"))
        card.put("vtx", confirmed(dump.vtx, "dump all") if dump.vtx else missing("в dump all нет строк vtx", "dump all"))
        _betaflight_video(card, dump)
        card.put("osd", confirmed(dump.osd, "dump all") if dump.osd else missing("в dump all нет osd_*", "dump all"))
        _osd_layout(card, dump.osd, card.family)
        _betaflight_ports(card, dump)
        if dump.features_enabled or dump.features_disabled:
            card.put(
                "features",
                confirmed(
                    {"enabled": dump.features_enabled, "disabled": dump.features_disabled},
                    "dump feature",
                    "строка feature без минуса включена, с минусом выключена",
                ),
            )
        else:
            card.put("features", missing("в dump all нет строк feature", "dump all"))
        if dump.mcu_id:
            card.put("mcu_id", confirmed(dump.mcu_id, "dump all"))
        else:
            card.put("mcu_id", missing("в dump all нет mcu_id", "dump all"))
        if dump.sections:
            card.put(
                "cli_sections",
                confirmed(
                    dump.sections,
                    "dump all",
                    "каждая секция master, profile и rateprofile сохранена отдельно",
                ),
            )
        else:
            card.put("cli_sections", missing("в dump all нет строк set и нет других команд", "dump all"))
        if dump.commands:
            card.put(
                "cli_commands",
                confirmed(dump.commands, "dump all", "строки resource, timer, dma, mixer и остальные команды"),
            )
        provider = master_or_unique(dump, "serialrx_provider")
        if provider is not None:
            card.put("serialrx_provider", confirmed(provider, "dump all"))
            _serialrx_class(card, provider)
        else:
            card.put("serialrx_provider", missing("в dump all нет serialrx_provider", "dump all"))
        spi = master_or_unique(dump, "rx_spi_protocol")
        if spi is not None and spi.strip().upper() == "SPEKTRUM":
            current = card.fields.get("radio_protocol")
            if current is None or current.status != "confirmed":
                card.put(
                    "radio_protocol",
                    confirmed(
                        "SPEKTRUM",
                        "dump rx_spi_protocol",
                        "RX_SPI_CYRF6936_DSM, имя SPEKTRUM в lookupTableRxSpi Betaflight 4.5",
                    ),
                )
            if "serial_link_class" not in card.fields:
                card.put("serial_link_class", confirmed("DSM2/DSMX", "betaflight rx_spi.h"))
        bind = master_or_unique(dump, "spektrum_sat_bind")
        if bind is not None:
            card.put(
                "spektrum_sat_bind",
                confirmed(bind, "dump spektrum_sat_bind", "0 — привязка выключена, максимум в spektrum.h равен 10. Команда bind не отправляется."),
            )
        express = {}
        for section in dump.sections:
            for key, value in section["settings"].items():
                if key.startswith("expresslrs_"):
                    express[f"{section['name']}.{key}" if key in express else key] = value
        if express:
            card.put("expresslrs_spi", confirmed(express, "dump all"))
        card.put(
            "vtx_device_responded",
            missing("опроса видеопередатчика не было. Строки vtx — это сохранённая таблица, не ответ устройства.", "dump all"),
        )
    if card.family == "ardupilot":
        params = {}
        messages = []
        modes = []
        for row in rows:
            if row.get("name") == "PARM":
                params[str(row.get("Name"))] = row.get("Value")
            elif row.get("name") == "MSG":
                messages.append({"time_us": row.get("TimeUS"), "text": row.get("Message")})
            elif row.get("name") == "MODE":
                modes.append(
                    {
                        "time_us": row.get("TimeUS"),
                        "mode": row.get("Mode"),
                        "mode_num": row.get("ModeNum"),
                    }
                )
        card.put("parameters", confirmed(params, "bin PARM") if params else missing("в .BIN нет PARM", "bin"))
        card.put("messages", confirmed(messages, "bin MSG") if messages else missing("в .BIN нет MSG", "bin"))
        card.put("modes", confirmed(modes, "bin MODE") if modes else missing("в .BIN нет MODE", "bin"))
        card.put("log_schema", confirmed(log_inventory(rows), "bin DFReader", "каждый тип сообщения и каждый кадр"))
        events = [dict(row) for row in rows if row.get("name") == "EV"]
        for event in events:
            event.pop("name", None)
        if events:
            card.put("log_events", confirmed(events, "bin EV"))
        _known_params(card, params)
        _ardupilot_ports(card, params)
        _learn_banner(card, [str(item.get("text") or "") for item in messages], "bin MSG")
        _baro(card, rows)
        _messages_with_rcin(card, rows, messages)
        _rcin_interval(card, rows)


def _osd_layout(card: Card, osd: dict[str, str], family: str = "betaflight") -> None:
    layout = []
    for name, raw in osd.items():
        if not name.endswith("_pos"):
            continue
        try:
            value = int(raw, 10)
        except ValueError:
            continue
        cell = decode_osd_position(value, family)
        cell["name"] = name
        layout.append(cell)
    if layout:
        reason = (
            "координаты символа по OSD_X и OSD_Y из osd.h INAV"
            if family == "inav"
            else "координаты символа по OSD_X и OSD_Y из osd.h Betaflight 4.5"
        )
        card.put("osd_layout", confirmed(layout, "dump osd_*_pos", reason))


def _betaflight_ports(card: Card, dump) -> None:
    ports = parse_betaflight_serial(dump.serial_lines, card.family)
    if not ports:
        card.put("serial_ports", missing("в dump all нет строк serial в формате 4.5", "dump all"))
        card.put("receiver_port", missing("нет строки serial с битом RX_SERIAL", "dump all"))
        return
    header = "serial.h INAV" if card.family == "inav" else "serial.h Betaflight 4.5"
    card.put(
        "serial_ports",
        confirmed(ports, "dump serial", f"идентификатор и маска из {header}"),
    )
    receivers = [port for port in ports if "RX_SERIAL" in port["functions"]]
    if len(receivers) == 1:
        card.put(
            "receiver_port",
            confirmed(
                receivers[0]["port"],
                "dump serial",
                "порт с битом FUNCTION_RX_SERIAL. Проход UART программа не включает.",
            ),
        )
    elif not receivers:
        card.put("receiver_port", missing("ни один порт не имеет бита RX_SERIAL", "dump serial"))
    else:
        card.put(
            "receiver_port",
            missing(
                "бит RX_SERIAL стоит на нескольких портах: " + ", ".join(port["port"] for port in receivers),
                "dump serial",
            ),
        )
    video = [
        port["port"]
        for port in ports
        if "VTX_SMARTAUDIO" in port["functions"] or "VTX_TRAMP" in port["functions"]
    ]
    if video:
        card.put(
            "vtx_uart",
            confirmed(video, "dump serial", "порт, на котором в маске стоит SmartAudio или Tramp"),
        )


def _ardupilot_ports(card: Card, params: dict, source: str = "bin PARM") -> None:
    ports = ardupilot_ports(params)
    if not ports:
        card.put("serial_ports", missing("в PARM нет SERIALn_PROTOCOL и SERIALn_BAUD", source))
        return
    card.put(
        "serial_ports",
        confirmed(ports, source, "SerialProtocol и map_baudrate из AP_SerialManager Copter 4.5"),
    )
    receivers = [port["port"] for port in ports if port.get("receiver")]
    if len(receivers) == 1:
        card.put(
            "receiver_port",
            confirmed(receivers[0], source, "протокол приёмника из SERIALn_PROTOCOL. Проход UART не включается."),
        )
    elif not receivers:
        card.put("receiver_port", missing("среди SERIALn_PROTOCOL нет протокола приёмника", source))
    else:
        card.put("receiver_port", missing("протоколы приёмника на нескольких портах: " + ", ".join(receivers), source))


def _betaflight_video(card: Card, dump) -> None:
    grid = parse_video_grid(dump.vtxtable)
    if grid.bands:
        card.put(
            "video_grid",
            confirmed(
                {
                    "bands": grid.bands,
                    "power_mw": grid.power_mw,
                    "power_labels": grid.power_labels,
                },
                "dump vtxtable",
                "частоты в МГц из строк vtxtable band, нумерация диапазонов с 1",
            ),
        )
    selected = selected_channel(effective_settings(dump), grid)
    if selected["frequency_mhz"] is None and selected["band"] is None and selected["vtx_freq_mhz"] in (None, 0):
        card.put(
            "video_frequency_mhz",
            missing("нет vtx_freq и нет пары vtx_band/vtx_channel, которая есть в vtxtable", "dump all"),
        )
    elif selected["frequency_mhz"] is None:
        card.put(
            "video_frequency_mhz",
            missing("vtx_band/vtx_channel не попали в таблицу этого дампа", "dump all"),
        )
    else:
        card.put(
            "video_frequency_mhz",
            confirmed(selected["frequency_mhz"], f"dump {selected['frequency_source']}", "сохранённая настройка, не ответ передатчика"),
        )
    if card.family == "inav" and selected["frequency_mhz"] is None:
        mhz, detail = inav_saved_frequency(effective_settings(dump))
        if mhz is not None:
            card.put("video_frequency_mhz", confirmed(mhz, detail, "таблица прошивки INAV, не ответ передатчика"))
            group_raw = effective_settings(dump).get("vtx_frequency_group", "0")
            group = 2 if str(group_raw).upper() in {"2", "FREQUENCYGROUP_1G3"} else 0
            grid_value = inav_grid(group)
            if grid_value is not None and "video_grid" not in card.fields:
                card.put("video_grid", confirmed(grid_value, detail, "сетка из vtx_string.c, нумерация диапазонов с 1"))
        else:
            card.put("video_frequency_mhz", missing(detail, "dump all"))
    if selected["power"] is not None:
        card.put("video_power", confirmed(selected["power"], "dump vtx_power + vtxtable powervalues"))
    rules = parse_vtx_rules(dump.vtx, grid)
    if rules:
        card.put(
            "vtx_switch_rules",
            confirmed(rules, "dump vtx", "это условия AUX, не текущий канал"),
        )


def _rcin_interval(card: Card, rows: list[dict]) -> None:
    stamps = sorted(
        float(row["TimeUS"])
        for row in rows
        if row.get("name") == "RCIN" and row.get("TimeUS") is not None
    )
    deltas = [right - left for left, right in zip(stamps, stamps[1:]) if right > left]
    if not deltas:
        card.put("rcin_interval_us", missing("в .BIN меньше двух сообщений RCIN", "bin RCIN"))
        return
    deltas.sort()
    card.put(
        "rcin_interval_us",
        confirmed(
            deltas[len(deltas) // 2],
            "bin RCIN",
            "медиана шага записей RCIN, не пакетрейт радиолинии",
        ),
    )


def _serialrx_class(card: Card, provider: str) -> None:
    """Names from Betaflight src/main/rx/rx.h SerialRXType.

    SPEKTRUM2048 and SPEKTRUM1024 are the DSM2/DSMX class. OrangeRX
    satellites use that class. The sticker OrangeRX is not itself a
    protocol name. Channel counts and baud are SPEKTRUM_* in spektrum.h,
    the same numbers in Betaflight 4.5 and INAV.
    """
    name = provider.strip().upper()
    if name in {"SPEKTRUM2048", "SPEKTRUM1024"}:
        channels = 12 if name == "SPEKTRUM2048" else 7
        card.put("serial_link_class", confirmed("DSM2/DSMX", "betaflight rx.h"))
        card.put(
            "radio_protocol",
            confirmed(name, "dump serialrx_provider", "класс DSM2/DSMX, приёмники OrangeRX входят в него"),
        )
        card.put(
            "spektrum_channel_count",
            confirmed(channels, "spektrum.h", "SPEKTRUM_2048_CHANNEL_COUNT или SPEKTRUM_1024_CHANNEL_COUNT"),
        )
        card.put(
            "spektrum_baud",
            confirmed(115200, "spektrum.h", "SPEKTRUM_BAUDRATE, скорость драйвера, не измерение вылета"),
        )
        card.put(
            "uplink_lq",
            not_applicable("в rx.h у SPEKTRUM нет источника LQ класса CRSF", "betaflight rx.h"),
        )
        return
    if name == "CRSF":
        card.put("uart_protocol", confirmed("CRSF", "dump all"))
        card.put(
            "air_protocol",
            missing("CRSF на UART не называет протокол в воздухе", "dump all"),
        )


def _whole(value) -> int | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != int(number):
        return None
    return int(number)


def _banner_may_set(card: Card, name: str, source: str) -> bool:
    current = card.fields.get(name)
    if current is None or current.status != "confirmed":
        return True
    if "MSP" in current.source or "AUTOPILOT_VERSION" in current.source:
        return False
    return source.endswith("STATUSTEXT") and "STATUSTEXT" not in current.source


def _learn_banner(card: Card, lines: list[str], source: str) -> None:
    found = parse_banner_lines(lines)
    if found["firmware"]:
        card.put("firmware", confirmed(found["firmware"], source, "строка прошивки, которую плата прислала сама"))
        card.raw_banner = found["firmware"]
    if found["board_name"] and (card.fields.get("board_name") is None or _banner_may_set(card, "board_name", source)):
        card.put(
            "board_name",
            confirmed(found["board_name"], source, "имя полётника из строки баннера, следом номер микросхемы"),
        )
    if found["mcu_id"] and _banner_may_set(card, "mcu_id", source):
        card.put(
            "mcu_id",
            confirmed(found["mcu_id"], source, "номер микросхемы из той же строки, что имя полётника"),
        )
    if found["frame"]:
        current = card.fields.get("frame")
        if (
            current is not None
            and current.status == "confirmed"
            and current.value != found["frame"]
            and "FRAME" in current.source
        ):
            card.holes.append(
                f"Тип рамы в параметрах ({current.value}) и в строке Frame: {found['frame_raw']} различаются. В карточке строка платы."
            )
        card.put("frame", confirmed(found["frame"], source, f"строка платы Frame: {found['frame_raw']}"))
    if found["os"]:
        card.put("flight_os", confirmed(found["os"], source, "строка системы из баннера"))
    if found["outputs"]:
        card.put("motor_outputs", confirmed(found["outputs"], source, "строка RCOut из баннера"))
    if found["imu"]:
        card.put("imu", confirmed(found["imu"], source, "строка IMU из баннера"))
    if found["iomcu"]:
        card.put("iomcu", confirmed(found["iomcu"], source, "строка IOMCU из баннера"))
    if found["rest"]:
        card.put("board_messages", confirmed(found["rest"], source, "остальные строки платы"))


def _known_params(card: Card, params: dict, source: str = "bin PARM") -> None:
    if "RC_PROTOCOLS" in params:
        value = int(params["RC_PROTOCOLS"])
        card.put(
            "rc_protocols",
            confirmed(
                {"value": value, "bits": rc_protocols_45(value)},
                source,
                "маска Copter 4.5: значение 1 — бит All, это не имя протокола линии",
            ),
        )
    if "MNT1_TYPE" in params:
        value = int(params["MNT1_TYPE"])
        card.put(
            "mnt1_type",
            confirmed(
                {"value": value, "label": MOUNT_TYPE_45.get(value, "unknown enum")},
                source,
            ),
        )
    if "CAM1_TYPE" in params:
        value = int(params["CAM1_TYPE"])
        card.put(
            "cam1_type",
            confirmed({"value": value, "label": CAMERA_TYPE_45.get(value, "unknown enum")}, source),
        )
    if "VTX_ENABLE" in params:
        card.put("vtx_enable", confirmed(params["VTX_ENABLE"], source))
        card.put(
            "vtx_device_responded",
            missing("опроса видеопередатчика не было. VTX_ENABLE не является ответом устройства.", source),
        )
    video = describe_ardupilot_vtx(params)
    if video is not None:
        card.put(
            "video_grid_lookup",
            confirmed(video, "AP_VideoTX VIDEO_CHANNELS + PARM", "сохранённые параметры, не ответ передатчика"),
        )
        if video["stored_frequency_mhz"]:
            card.put("video_frequency_mhz", confirmed(video["stored_frequency_mhz"], f"{source} VTX_FREQ"))
        elif video["table_frequency_mhz"] is not None:
            card.put(
                "video_frequency_mhz",
                confirmed(video["table_frequency_mhz"], "AP_VideoTX VIDEO_CHANNELS"),
            )
        else:
            card.put("video_frequency_mhz", missing("VTX_FREQ пуст и BAND/CHANNEL вне таблицы", source))
        if video["stored_frequency_mhz"] and video["table_frequency_mhz"] not in (None, video["stored_frequency_mhz"]):
            card.holes.append(
                "VTX_FREQ и частота из VTX_BAND/VTX_CHANNEL по таблице AP_VideoTX не совпали. Оба значения сохранены."
            )
        if video["power_mw"] is not None:
            card.put("video_power_mw", confirmed(video["power_mw"], f"{source} VTX_POWER", "милливатты, как в параметре"))
        if video["pitmode_bit"] is not None:
            card.put(
                "vtx_pitmode_configured",
                confirmed(video["pitmode_bit"], f"{source} VTX_OPTIONS bit 0", "бит настройки, не ответ устройства"),
            )
    for name in ("FS_THR_ENABLE", "FS_GCS_ENABLE", "FS_EKF_ACTION", "BATT_FS_CRT_ACT", "FS_CRASH_CHECK"):
        if name in params:
            card.put(name.lower(), confirmed(params[name], source))
    if "frame" not in card.fields and "FRAME_CLASS" in params:
        klass = _whole(params.get("FRAME_CLASS"))
        kind = _whole(params["FRAME_TYPE"]) if "FRAME_TYPE" in params else None
        if klass is not None:
            named = frame_from_params(klass, kind)
            if named is not None:
                words, raw = named
                card.put(
                    "frame",
                    confirmed(words, f"{source} FRAME_CLASS", f"в параметрах {raw}. Строки Frame в баннере не было."),
                )


def _baro(card: Card, rows: list[dict]) -> None:
    altitudes = []
    for row in rows:
        if row.get("name") not in ("BARO", "CTUN"):
            continue
        alt = row.get("Alt")
        if alt is None:
            continue
        altitudes.append(float(alt))
    if not altitudes:
        card.put("baro_alt", missing("в .BIN нет BARO.Alt и CTUN.Alt", "bin"))
        return
    card.put(
        "baro_alt",
        confirmed(
            {"min": min(altitudes), "max": max(altitudes), "samples": len(altitudes)},
            "bin BARO/CTUN",
            "барометр, не координаты",
        ),
    )


def _messages_with_rcin(card: Card, rows: list[dict], messages: list[dict]) -> None:
    rcins = [row for row in rows if row.get("name") == "RCIN" and row.get("TimeUS") is not None]
    joined = []
    for message in messages:
        stamp = message.get("time_us")
        nearest = None
        if stamp is not None and rcins:
            nearest = min(rcins, key=lambda row: abs(float(row["TimeUS"]) - float(stamp)))
            if abs(float(nearest["TimeUS"]) - float(stamp)) > 100_000:
                nearest = None
        channels = None
        if nearest is not None:
            channels = {
                key: nearest[key]
                for key in nearest
                if key.startswith("C") and key[1:].isdigit()
            }
        joined.append({"time_us": stamp, "text": message.get("text"), "rcin": channels})
    if joined:
        card.put("messages_with_rcin", confirmed(joined, "bin MSG+RCIN", "совпадение по TimeUS, не расшифровка скрипта"))


def _radio_fields(card: Card, inputs: Inputs) -> None:
    reading = None
    if inputs.auth_declined:
        card.put("radio_fields_requires_auth", confirmed(True, "radio page"))
        card.put("radio_protocol", missing("оператор не ввёл пароль страницы", "auth_declined"))
        card.holes.append("Страница приёмника запросила пароль, ввода не было.")
        return
    if inputs.radio_json is not None:
        reading = parse_radio_json(inputs.radio_json)
        card.files.append({"kind": "radio_json_redacted", "sha256": sha256_bytes(reading.redacted)})
    elif inputs.radio_image is not None:
        reading = parse_radio_image(inputs.radio_image)
        card.files.append(
            {
                "kind": "radio_image_redacted",
                "sha256": sha256_bytes(reading.redacted),
                "sha256_original": sha256_bytes(inputs.radio_image),
            }
        )
    if reading is None:
        if "expresslrs_spi" in card.fields:
            card.put("radio_protocol", confirmed("ExpressLRS", "dump all expresslrs_*"))
        elif card.fields.get("radio_protocol") is None or card.fields["radio_protocol"].status != "confirmed":
            card.put("radio_protocol", missing("строки прошивки приёмника нет", "radio"))
        return
    if reading.removed_secrets:
        card.put(
            "radio_secrets_removed",
            confirmed(sorted(set(reading.removed_secrets)), "redact", "значения не сохранены"),
        )
    if reading.fields:
        card.put(
            "radio_page",
            confirmed(reading.fields, "radio", "все поля страницы или образа после вырезания секретов"),
        )
    if reading.firmware is None:
        card.put("radio_protocol", missing("в странице или образе нет строки MILELRS, ExpressLRS или mLRS", "radio"))
        return
    card.put("radio_protocol", confirmed(reading.firmware, "radio firmware string"))
    rate_reasons = {
        "rate_index": "номер режима в настройке приёмника, без перевода в герцы",
        "rateinitialidx": "rateInitialIdx из options, не частота этого вылета",
        "tx_packet_rate": "значение из экспорта пульта, не частота из лога полёта",
        "binding_rate": "BINDING_RATE — вариант привязки, не измеренный пакетрейт вылета",
        "vx_table": "таблица в странице приёмника, не параметр VTX полётника",
        "vx_bands": "таблица в странице приёмника, не параметр VTX полётника",
    }
    for key in ("version", "model", "chip", "domain", "uid", "serial_protocol", "uart_baud", "rate_index", "rateinitialidx", "model_id", "tx_packet_rate", "target", "module_type", "git_commit", "lua_name", "wifi_mode", "uid_type"):
        if key in reading.fields:
            card.put(f"radio_{key}", confirmed(reading.fields[key], "radio", rate_reasons.get(key, "")))
    if reading.firmware == "MILELRS":
        for key in ("custom_freq", "binding_rate", "swarm_id", "vx_table", "vx_bands"):
            field_name = f"radio_{key}"
            if key in reading.fields:
                card.put(field_name, confirmed(reading.fields[key], "radio", rate_reasons.get(key, "")))
            else:
                card.put(field_name, missing(f"прошивка MILELRS, поля {key} в чтении нет", "radio"))
    else:
        for key in ("custom_freq", "binding_rate", "swarm_id", "vx_table", "vx_bands"):
            card.put(
                f"radio_{key}",
                not_applicable(f"словарь MILELRS не применяется к {reading.firmware}", "radio"),
            )


def _stm32(card: Card, text: str | None) -> None:
    if text is None:
        return
    parsed = parse_stm32_log(text)
    if parsed is None:
        card.put("stm32_probe", missing("в файле нет строк Device ID и нет строк st-info --probe", "stm32 log"))
        return
    card.put(
        "stm32_probe",
        confirmed(parsed, "stm32 log", "строки подключения STM32_Programmer_CLI или st-info, без чтения памяти прошивки"),
    )
    if parsed.get("log_contains_write"):
        card.put(
            "stm32_log_contains_write",
            confirmed(True, "stm32 log", "в журнале есть стирание или запись. Стрела эту команду не повторяет."),
        )
        card.holes.append("Журнал STM32 содержит стирание или запись. Идентификатор чипа сохранён, команда не повторяется.")


def _msp_identity(card: Card, identity: dict) -> None:
    """Board and build from MSP, the same replies the configurator shows before a flash."""
    version = identity.get("fc_version")
    if version:
        card.put(
            "msp_fc_version",
            confirmed(version, "MSP_FC_VERSION", version.get("layout", "")),
        )
    board = identity.get("board")
    if board:
        card.put(
            "msp_board",
            confirmed(board, "MSP_BOARD_INFO", "идентификатор, имя цели и OSD из ответа MSP_BOARD_INFO"),
        )
        if board.get("board_name") and "board_name" not in card.fields:
            card.put("board_name", confirmed(board["board_name"], "MSP_BOARD_INFO"))
    build = identity.get("build")
    if build:
        card.put("msp_build", confirmed(build, "MSP_BUILD_INFO", "дата сборки и короткий git из MSP_BUILD_INFO"))
    craft = identity.get("craft_name")
    if craft and "craft_name" not in card.fields:
        card.put("craft_name", confirmed(craft, "MSP_NAME"))


def _nameplates(card: Card, plates: dict[str, str]) -> None:
    for key, value in plates.items():
        card.put(f"nameplate_{key}", document(value, "nameplate", "шильдик, не этот вылет и не протокол"))


def _absorb_mavlink(card: Card, rows: list[dict], source: str = "tlog") -> None:
    """Fields a MAVLink stream actually contains: heartbeat, parameters, radio status, RC spacing."""
    beats = [row for row in rows if row.get("name") == "HEARTBEAT"]
    if beats:
        beat = {key: _plain(value) for key, value in beats[0].items() if key != "name"}
        card.put("mavlink_heartbeat", confirmed(beat, f"{source} HEARTBEAT"))
        if card.family == "unknown":
            card.family = "ardupilot" if beat.get("autopilot") == 3 else "mavlink"
            card.raw_banner = card.raw_banner or "MAVLink HEARTBEAT"
    elif card.family == "unknown" and rows:
        card.family = "mavlink"
        card.raw_banner = card.raw_banner or f"MAVLink {source}"
    params: dict[str, Any] = {}
    for row in rows:
        if row.get("name") != "PARAM_VALUE":
            continue
        name = str(_plain(row.get("param_id")) or "").strip().strip("\x00")
        if name:
            params[name] = _plain(row.get("param_value"))
    if params and (card.fields.get("parameters") is None or card.fields["parameters"].status != "confirmed"):
        card.put("parameters", confirmed(params, f"{source} PARAM_VALUE", f"прочитано параметров: {len(params)}"))
        _known_params(card, params, source=f"{source} PARAM_VALUE")
        _ardupilot_ports(card, params, source=f"{source} PARAM_VALUE")
    versions = [row for row in rows if row.get("name") == "AUTOPILOT_VERSION"]
    if versions:
        version = versions[0]
        card.put(
            "autopilot_version",
            confirmed(
                version,
                f"{source} AUTOPILOT_VERSION",
                "номер прошивки из flight_sw_version. Старшие 16 бит board_version — это APJ_BOARD_ID.",
            ),
        )
        if version.get("uid2") and "mcu_id" not in card.fields:
            card.put("mcu_id", confirmed(version["uid2"], f"{source} AUTOPILOT_VERSION", "uid2 из AUTOPILOT_VERSION"))
        banner = f"{version.get('major')}.{version.get('minor')}.{version.get('patch')}"
        custom = version.get("flight_custom_version") or ""
        if custom:
            banner = f"{banner} {custom}"
        if not card.raw_banner or card.raw_banner == "MAVLink HEARTBEAT":
            card.raw_banner = banner
    texts = [str(row.get("text") or "") for row in rows if row.get("name") == "STATUSTEXT" and row.get("text")]
    if texts:
        _learn_banner(card, texts, f"{source} STATUSTEXT")
    if "frame" not in card.fields and beats:
        word = mav_type_word(int(beats[0].get("type") or -1))
        if word:
            card.put(
                "frame",
                confirmed(word, f"{source} HEARTBEAT", "MAV_TYPE из HEARTBEAT. Строки Frame плата не прислала."),
            )
    logs = [row for row in rows if row.get("name") == "LOG_ENTRY"]
    if logs:
        card.put(
            "dataflash_logs",
            confirmed(logs, f"{source} LOG_ENTRY", "список журналов на плате. Стирание не отправлялось."),
        )
    radios = [row for row in rows if row.get("name") == "RADIO_STATUS"]
    if radios:
        kept = {
            key: _plain(value)
            for key, value in radios[-1].items()
            if key not in {"name", "mavpackettype"}
        }
        card.put(
            "mavlink_radio_status",
            confirmed(kept, f"{source} RADIO_STATUS", "качество линии из сообщения RADIO_STATUS, не пакетрейт"),
        )
    stamps = sorted(
        float(row["time_boot_ms"])
        for row in rows
        if row.get("name") == "RC_CHANNELS" and row.get("time_boot_ms") is not None
    )
    deltas = [right - left for left, right in zip(stamps, stamps[1:]) if right > left]
    if len(deltas) >= 1:
        deltas.sort()
        card.put(
            "mavlink_rc_interval_ms",
            confirmed(
                deltas[len(deltas) // 2],
                f"{source} RC_CHANNELS",
                "медиана шага записей RC_CHANNELS, не пакетрейт радиолинии",
            ),
        )


def _route(card: Card, inputs: Inputs, rows: list[dict]) -> None:
    journal: list[dict[str, str]] = []
    bin_points: list[dict] = []
    pairs: list[tuple[float, float | None]] = []
    home = None
    if inputs.bin_path is None:
        journal.append({"source": "bin", "result": "absent", "detail": "файл .BIN не передан"})
    else:
        bin_points, seen, weak = bin_gps_points(rows)
        pairs = arm_pairs(rows)
        home = home_from_orgn(rows)
        pos = bin_pos_count(rows)
        journal.append(
            {
                "source": "bin_pos",
                "result": "ignored",
                "detail": f"сообщений POS: {pos}. POS не является GPS-треком",
            }
        )
        if seen and not bin_points:
            journal.append({"source": "bin", "result": "present_no_fix", "detail": f"строк GPS: {seen}, из них без 3D: {weak}"})
        if home is None:
            journal.append({"source": "bin_orgn", "result": "absent", "detail": "ORGN type 1 (ahrs_home) нет"})
        else:
            journal.append({"source": "bin_orgn", "result": "found", "detail": "дом взят из ORGN type 1"})
        params = {}
        if "parameters" in card.fields and card.fields["parameters"].value:
            params = card.fields["parameters"].value
        found_parm = [name for name in ("WP_HOME", "HOME_POS", "HOME") if name in params]
        journal.append(
            {
                "source": "parm_home",
                "result": "ignored" if found_parm else "absent",
                "detail": "WP_HOME, HOME_POS и HOME точкой взлёта не назначаются"
                + (f"; в PARM встретились {found_parm}" if found_parm else ""),
            }
        )

    tlog_pts: list[dict] = []
    tlog_home = None
    if inputs.tlog_path is None:
        journal.append({"source": "tlog", "result": "absent", "detail": ".tlog не предоставлен"})
    else:
        card.files.append(_file_record(inputs.tlog_path, "tlog"))
        tlog_rows = load_tlog(inputs.tlog_path)
        card.put(
            "tlog_schema",
            confirmed(log_inventory(tlog_rows), "tlog", "каждый тип сообщения и каждый кадр"),
        )
        _absorb_mavlink(card, tlog_rows)
        tlog_pts, tlog_home, weak = tlog_points(tlog_rows)
        if not tlog_pts:
            journal.append({"source": "tlog", "result": "present_no_fix" if weak else "absent", "detail": f"слабых GPS_RAW_INT: {weak}"})
        if home is None and tlog_home is not None:
            home = tlog_home

    blackbox_points: list[dict] = []
    if inputs.blackbox_path is not None:
        card.files.append(_file_record(inputs.blackbox_path, "blackbox"))
        header = parse_header_file(inputs.blackbox_path)
        if header:
            card.put("blackbox_header", confirmed(header, "blackbox H"))
            if card.family == "unknown":
                label = " ".join(
                    header.get(key, "") for key in ("Firmware type", "Firmware revision")
                ).strip()
                folded = label.lower()
                if "inav" in folded:
                    card.family = "inav"
                elif "betaflight" in folded or "cleanflight" in folded:
                    card.family = "betaflight" if "betaflight" in folded else "cleanflight"
                elif "ardu" in folded:
                    card.family = "ardupilot"
                if card.family != "unknown" and not card.raw_banner:
                    card.raw_banner = label
            if "Craft name" in header and "craft_name" not in card.fields:
                card.put("craft_name", confirmed(header["Craft name"], "blackbox H"))
            if "rc_smoothing_rx_smoothed" in header:
                card.put(
                    "packet_rate_log_hz",
                    confirmed(
                        header["rc_smoothing_rx_smoothed"],
                        "blackbox H",
                        "rc_smoothing_rx_smoothed в герцах на момент арминга. Это не индекс ExpressLRS и не шаг RCIN.",
                    ),
                )
            if "DeviceUID" in header:
                card.put("device_uid", confirmed(header["DeviceUID"], "blackbox H"))
    if inputs.gps_csv_path is not None:
        card.files.append(_file_record(inputs.gps_csv_path, "blackbox_gps_csv"))
        blackbox_points = parse_gps_csv(inputs.gps_csv_path)
        if not blackbox_points:
            journal.append({"source": "blackbox", "result": "absent", "detail": "GPS CSV без точек"})
    elif inputs.blackbox_path is not None:
        journal.append(
            {
                "source": "blackbox",
                "result": "header_only",
                "detail": "заголовок прочитан. Трек из двоичных G-кадров берётся только из GPS CSV blackbox_decode",
            }
        )
    else:
        journal.append({"source": "blackbox", "result": "absent", "detail": "Blackbox не передан"})

    mission: list[dict] = []
    mission_source = "none"
    if inputs.gpx_path is not None:
        card.files.append(_file_record(inputs.gpx_path, "gpx"))
        gpx = parse_gpx(inputs.gpx_path)
        journal.append(
            {
                "source": "gpx",
                "result": "track_not_used" if gpx["track_points_not_used"] else "no_track",
                "detail": f"trkpt {len(gpx['track_points_not_used'])} не становятся маршрутом полёта; wpt/rte {len(gpx['waypoints'])}",
            }
        )
        if gpx["waypoints"]:
            mission = gpx["waypoints"]
            mission_source = str(inputs.gpx_path)
    else:
        journal.append({"source": "gpx", "result": "absent", "detail": "GPX не передан"})
    if inputs.waypoints_path is not None:
        card.files.append(_file_record(inputs.waypoints_path, "waypoints"))
        mission = parse_qgc_waypoints(inputs.waypoints_path)
        mission_source = str(inputs.waypoints_path)
    if inputs.plan_path is not None:
        card.files.append(_file_record(inputs.plan_path, "plan"))
        mission = parse_plan(inputs.plan_path)
        mission_source = str(inputs.plan_path)
    cmd_points = _cmd_points(rows)
    if cmd_points and not mission:
        mission = cmd_points
        mission_source = "bin CMD"
    journal.append({"source": "osd_ocr", "result": "not_used", "detail": "координаты с OSD треком не считаются"})
    journal.append({"source": "exif", "result": "not_used", "detail": "EXIF — точка съёмки, не маршрут"})

    flights, route_journal = build_flights(bin_points, pairs, tlog_pts, blackbox_points, home)
    # build_flights also journals the winner. Keep the search log in front.
    if inputs.bin_path is not None and not bin_points:
        # build_flights adds its own bin absent line only when bin is empty of points.
        pass
    card.journal = journal + route_journal
    card.flights = flights
    _publish_route(card, flights, mission, mission_source)


def _cmd_points(rows: list[dict]) -> list[dict]:
    points = []
    for row in rows:
        if row.get("name") != "CMD":
            continue
        lat = row.get("Lat")
        lon = row.get("Lng")
        if lat is None or lon is None:
            continue
        if float(lat) == 0.0 and float(lon) == 0.0:
            continue
        points.append({"lat": float(lat), "lon": float(lon), "alt": row.get("Alt"), "command": row.get("CId")})
    return points


def _publish_route(card: Card, flights: list[dict], mission: list[dict], mission_source: str) -> None:
    if not flights:
        card.put("route_source", confirmed("none", "route"))
        card.put("route_track", missing("источников с GPS-точками нет", "route"))
        return
    flight = flights[0]
    source = flight["route_source"]
    card.put("route_source", confirmed(source, "route"))
    if flight["track"]:
        card.put("route_track", confirmed(flight["track"], source))
        if flight["route_length_m"] is not None:
            card.put(
                "route_length_m",
                confirmed(flight["route_length_m"], "computed_from=route_track"),
            )
        else:
            card.put("route_length_m", missing("в треке меньше двух точек", source))
    else:
        card.put("route_track", missing("ни один источник не дал GPS-точек этого вылета", "route"))
        card.put("route_length_m", missing("трека нет", "route"))
    if flight["takeoff"] is not None:
        card.put("takeoff_lat", confirmed(flight["takeoff"]["lat"], source))
        card.put("takeoff_lon", confirmed(flight["takeoff"]["lon"], source))
        if flight["takeoff"].get("alt") is not None:
            card.put("takeoff_alt", confirmed(flight["takeoff"]["alt"], source, "высота из GPS, не барометр"))
        else:
            card.put("takeoff_alt", missing("в точке взлёта нет высоты GPS", source))
    else:
        reason = "нет GPS 3D в пределах 1 с после арминга" if flight["arm_time_us"] is not None else "события арминга нет, первая точка треком взлёта не назначается"
        card.put("takeoff_lat", missing(reason, "route"))
        card.put("takeoff_lon", missing(reason, "route"))
        card.put("takeoff_alt", missing(reason, "route"))
    if flight["arm_time_us"] is not None:
        card.put("takeoff_time_us", confirmed(flight["arm_time_us"], "bin EV Id 10", "микросекунды от старта контроллера"))
    else:
        card.put("takeoff_time_us", missing("в логе нет EV Id 10 (ARMED)", "bin"))
    if flight["landing"] is not None:
        card.put("landing_lat", confirmed(flight["landing"]["lat"], source))
        card.put("landing_lon", confirmed(flight["landing"]["lon"], source))
    else:
        card.put("landing_lat", missing("нет GPS 3D у дизарма", "route"))
        card.put("landing_lon", missing("нет GPS 3D у дизарма", "route"))
    if flight["disarm_time_us"] is not None:
        card.put("landing_time_us", confirmed(flight["disarm_time_us"], "bin EV Id 11", "микросекунды от старта контроллера, не длительность"))
        if flight["arm_time_us"] is not None:
            card.put(
                "flight_duration_us",
                confirmed(flight["disarm_time_us"] - flight["arm_time_us"], "bin EV", "разность меток лога, не время суток"),
            )
    else:
        card.put("landing_time_us", missing("в логе нет EV Id 11 (DISARMED)", "bin"))
    if flight["home"] is not None and flight["max_distance_from_home_m"] is not None:
        card.put("home", confirmed(flight["home"], flight["home"]["source"]))
        card.put(
            "max_distance_from_home_m",
            confirmed(flight["max_distance_from_home_m"], "computed_from=route_track+home"),
        )
    else:
        card.put("home", missing("ORGN type 1 и HOME_POSITION нет", "route"))
        card.put("max_distance_from_home_m", missing("нет дома или нет трека", "route"))
    if mission:
        card.put("mission_waypoints", confirmed(mission, mission_source))
        card.put("mission_file_source", confirmed(mission_source, mission_source))
    else:
        card.put("mission_waypoints", missing("CMD, GPX wpt/rte, .waypoints и .plan не дали точек", "mission"))
        card.put("mission_file_source", confirmed("none", "mission"))


def _applicability(card: Card) -> None:
    beta = card.family in ("betaflight", "inav", "cleanflight")
    ardu = card.family in ("ardupilot", "mavlink")
    if ardu:
        for name, reason in (
            ("craft_name", "имя борта CLI Betaflight/INAV"),
            ("pilot_name", "имя пилота CLI Betaflight/INAV"),
            ("aux", "режимы aux есть у Betaflight/INAV"),
            ("vtxtable", "vtxtable есть у Betaflight/INAV"),
            ("vtx", "строки vtx есть у Betaflight/INAV"),
            ("osd", "позиции osd_* есть у Betaflight/INAV"),
            ("features", "строки feature есть у Betaflight/INAV"),
            ("serialrx_provider", "serialrx_provider есть у Betaflight/INAV"),
        ):
            if name not in card.fields:
                card.put(name, not_applicable(reason, "family"))
    if beta:
        for name in ("parameters", "mnt1_type", "cam1_type"):
            if name not in card.fields:
                card.put(name, not_applicable("поле параметра ArduPilot", "family"))
    protocol = card.fields.get("radio_protocol")
    if protocol is None:
        return
    if protocol.status == "confirmed" and protocol.value != "MILELRS":
        for key in ("radio_custom_freq", "radio_binding_rate", "radio_swarm_id", "radio_vx_table", "radio_vx_bands"):
            if key not in card.fields:
                card.put(key, not_applicable("поля MILELRS", "radio"))
    if protocol.status != "confirmed":
        for key in ("radio_custom_freq", "radio_binding_rate", "radio_swarm_id", "radio_vx_table", "radio_vx_bands"):
            if key not in card.fields:
                card.put(key, not_applicable("словарь приёмника не выбран: нет строки прошивки", "radio"))


def _holes(card: Card) -> None:
    for name, item in card.fields.items():
        if item.status == "missing":
            text = f"{name}: {item.reason}"
            card.holes.append(text)
            card.hints.append(hint_for_hole(text))
    source = card.fields.get("route_source")
    if source is not None and source.value == "none":
        card.holes.append("Маршрута нет, источник none. GPS 3D в журнале нет, .tlog пуст, Blackbox GPS нет.")
