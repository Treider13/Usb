"""Build one card from the files of a single vehicle."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .blackbox import parse_gps_csv, parse_header_file
from .dump import parse_boxnames, parse_dump
from .enums_ardupilot import CAMERA_TYPE_45, MOUNT_TYPE_45, rc_protocols_45
from .hashing import sha256_bytes, sha256_file
from .hints import WORKFLOW, hint_for_hole
from .logs import load_bin, load_tlog
from .mission_files import parse_gpx, parse_plan, parse_qgc_waypoints
from .model import Card, confirmed, document, missing, not_applicable
from .radio import parse_radio_image, parse_radio_json
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
    banner: str = ""
    auth_declined: bool = False


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
    _route(card, inputs, rows)
    _applicability(card)
    _holes(card)
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


def _file_record(path: Path, kind: str) -> dict[str, str]:
    return {"kind": kind, "path": str(path), "sha256": sha256_file(path)}


def _vehicle_fields(card: Card, dump, rows: list[dict]) -> None:
    if dump is not None:
        if dump.board_name:
            card.put("board_name", confirmed(dump.board_name, "dump all"))
        else:
            card.put("board_name", missing("в dump all нет строки board_name", "dump all"))
        for key in ("craft_name", "pilot_name"):
            if key in dump.settings and dump.settings[key] != "":
                card.put(key, confirmed(dump.settings[key], "dump all"))
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
        card.put("osd", confirmed(dump.osd, "dump all") if dump.osd else missing("в dump all нет osd_*", "dump all"))
        provider = dump.settings.get("serialrx_provider")
        if provider is not None:
            card.put("serialrx_provider", confirmed(provider, "dump all"))
        else:
            card.put("serialrx_provider", missing("в dump all нет serialrx_provider", "dump all"))
        express = {key: value for key, value in dump.settings.items() if key.startswith("expresslrs_")}
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
        _known_params(card, params)
        _baro(card, rows)
        _messages_with_rcin(card, rows, messages)


def _known_params(card: Card, params: dict) -> None:
    if "RC_PROTOCOLS" in params:
        value = int(params["RC_PROTOCOLS"])
        card.put(
            "rc_protocols",
            confirmed(
                {"value": value, "bits": rc_protocols_45(value)},
                "bin PARM",
                "маска Copter 4.5: значение 1 — бит All, это не имя протокола линии",
            ),
        )
    if "MNT1_TYPE" in params:
        value = int(params["MNT1_TYPE"])
        card.put(
            "mnt1_type",
            confirmed(
                {"value": value, "label": MOUNT_TYPE_45.get(value, "unknown enum")},
                "bin PARM",
            ),
        )
    if "CAM1_TYPE" in params:
        value = int(params["CAM1_TYPE"])
        card.put(
            "cam1_type",
            confirmed({"value": value, "label": CAMERA_TYPE_45.get(value, "unknown enum")}, "bin PARM"),
        )
    if "VTX_ENABLE" in params:
        card.put("vtx_enable", confirmed(params["VTX_ENABLE"], "bin PARM"))
        card.put(
            "vtx_device_responded",
            missing("опроса видеопередатчика не было. VTX_ENABLE не является ответом устройства.", "bin PARM"),
        )
    for name in ("FS_THR_ENABLE", "FS_GCS_ENABLE", "FS_EKF_ACTION", "BATT_FS_CRT_ACT", "FS_CRASH_CHECK"):
        if name in params:
            card.put(name.lower(), confirmed(params[name], "bin PARM"))


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
        else:
            card.put("radio_protocol", missing("строки прошивки приёмника нет", "radio"))
        return
    if reading.removed_secrets:
        card.put(
            "radio_secrets_removed",
            confirmed(sorted(set(reading.removed_secrets)), "redact", "значения не сохранены"),
        )
    if reading.firmware is None:
        card.put("radio_protocol", missing("в странице или образе нет строки MILELRS, ExpressLRS или mLRS", "radio"))
        return
    card.put("radio_protocol", confirmed(reading.firmware, "radio firmware string"))
    for key in ("version", "model", "chip", "domain", "uid", "serial_protocol", "uart_baud", "rate_index", "rateinitialidx", "model_id"):
        if key in reading.fields:
            card.put(f"radio_{key}", confirmed(reading.fields[key], "radio"))
    if reading.firmware == "MILELRS":
        for key in ("custom_freq", "binding_rate", "swarm_id", "vx_table", "vx_bands"):
            field_name = f"radio_{key}"
            if key in reading.fields:
                card.put(field_name, confirmed(reading.fields[key], "radio"))
            else:
                card.put(field_name, missing(f"прошивка MILELRS, поля {key} в чтении нет", "radio"))
    else:
        for key in ("custom_freq", "binding_rate", "swarm_id", "vx_table", "vx_bands"):
            card.put(
                f"radio_{key}",
                not_applicable(f"словарь MILELRS не применяется к {reading.firmware}", "radio"),
            )


def _nameplates(card: Card, plates: dict[str, str]) -> None:
    for key, value in plates.items():
        card.put(f"nameplate_{key}", document(value, "nameplate", "шильдик, не этот вылет и не протокол"))


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
            if "Craft name" in header and "craft_name" not in card.fields:
                card.put("craft_name", confirmed(header["Craft name"], "blackbox H"))
            if "rc_smoothing_rx_smoothed" in header:
                card.put(
                    "packet_rate_log_hz",
                    confirmed(header["rc_smoothing_rx_smoothed"], "blackbox H", "это не индекс скорости приёмника"),
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
    ardu = card.family == "ardupilot"
    if ardu:
        for name, reason in (
            ("craft_name", "имя борта CLI Betaflight/INAV"),
            ("pilot_name", "имя пилота CLI Betaflight/INAV"),
            ("aux", "режимы aux есть у Betaflight/INAV"),
            ("vtxtable", "vtxtable есть у Betaflight/INAV"),
            ("vtx", "строки vtx есть у Betaflight/INAV"),
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
        card.holes.append(
            "GPS-сообщений со статусом 3D в .BIN нет. .tlog не дал точек. "
            "Кадров GPS Blackbox нет. GPX треком полёта не считается. "
            "Маршрут и точка взлёта — missing, источник none. "
            "Высота барометра и курс отрыва треком не являются."
        )
