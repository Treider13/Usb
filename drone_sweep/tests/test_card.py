import json
from pathlib import Path

import pytest

from drone_sweep.assemble import Inputs, assemble
from drone_sweep.dump import parse_dump
from drone_sweep.enums_ardupilot import rc_protocols_45
from drone_sweep.model import Item
from drone_sweep.radio import parse_radio_image, parse_radio_json
from drone_sweep.usb_read import ReadOnlyError, ScriptedPort, assert_readonly_cli, msp_request, read_boxnames, read_cli
from tests.bin_builder import write_bin


ROOT = Path(__file__).parent


def _parm(time_us: int, name: str, value: float) -> tuple:
    return ("PARM", "QNf", "TimeUS,Name,Value", (time_us, name.encode("ascii"), value))


def _gps(time_us: int, status: int, lat: float, lon: float, alt_m: float) -> tuple:
    # L is degrees×1e7. e is centimetres. Status 3 is GPS_OK_FIX_3D.
    return (
        "GPS",
        "QBLLe",
        "TimeUS,Status,Lat,Lng,Alt",
        (time_us, status, int(round(lat * 1e7)), int(round(lon * 1e7)), int(round(alt_m * 100))),
    )


def _orgn(time_us: int, kind: int, lat: float, lon: float) -> tuple:
    return (
        "ORGN",
        "QBLLe",
        "TimeUS,Type,Lat,Lng,Alt",
        (time_us, kind, int(round(lat * 1e7)), int(round(lon * 1e7)), 0),
    )


def _ev(time_us: int, code: int) -> tuple:
    return ("EV", "QB", "TimeUS,Id", (time_us, code))


def _pos(time_us: int, lat: float, lon: float) -> tuple:
    return (
        "POS",
        "QLL",
        "TimeUS,Lat,Lng",
        (time_us, int(round(lat * 1e7)), int(round(lon * 1e7))),
    )


def _msg(time_us: int, text: str) -> tuple:
    return ("MSG", "QZ", "TimeUS,Message", (time_us, text.encode("ascii")))


def _baro(time_us: int, alt: float) -> tuple:
    return ("BARO", "Qf", "TimeUS,Alt", (time_us, alt))


def _rcin(time_us: int, channel_11: int) -> tuple:
    channels = [1500] * 14
    channels[10] = channel_11
    return ("RCIN", "Q" + "h" * 14, "TimeUS," + ",".join(f"C{i}" for i in range(1, 15)), (time_us, *channels))


DUMP = """\
# Betaflight / STM32F405 (S405) 4.5.0 Jan 01 2025 / GIT
board_name TANTOF405_V2
mcu_id 0032001e3233510738363334
set craft_name = Blink
set pilot_name = B162-483
aux 0 0 0 1700 2100 0 0
aux 1 1 1 900 1300 0 0
aux 2 40 2 1300 1700 0 0
set failsafe_procedure = DROP
set serialrx_provider = CRSF
vtxtable bands 1
vtxtable band 1 A A CUSTOM 6110
vtx 0 3 1 2 1 900 1100
set osd_vbat_pos = 234
"""

BOXES = ";".join(["ARM"] + ["ANGLE"] + [""] * 38 + ["LAZYFLY"])


def test_dump_keeps_custom_mode_name_only_from_boxnames():
    parsed = parse_dump(DUMP, BOXES.split(";"))
    assert parsed.family == "betaflight"
    assert parsed.board_name == "TANTOF405_V2"
    assert parsed.aux[0].name == "ARM"
    assert parsed.aux[1].name == "ANGLE"
    assert parsed.aux[2].mode_id == 40
    assert parsed.aux[2].name == "LAZYFLY"
    assert parsed.aux[2].range_start == 1300
    unnamed = parse_dump(DUMP, [])
    assert unnamed.aux[2].name is None


def test_b162_card_from_dump_and_blackbox(tmp_path: Path):
    blackbox = tmp_path / "flight.bbl"
    blackbox.write_text(
        "\n".join(
            [
                "H Product:Blackbox flight data recorder",
                "H Firmware revision:Betaflight 4.5.0",
                "H Craft name:Blink",
                "H DeviceUID:0032001e3233510738363334",
                "H rc_smoothing_rx_smoothed:250",
                "",
            ]
        ),
        encoding="ascii",
    )
    gps = tmp_path / "flight.gps.csv"
    gps.write_text(
        "time (us),GPS_numSat,GPS_coord[0],GPS_coord[1],GPS_altitude\n"
        "1000,10,48.1000000,37.6000000,120\n"
        "2000,10,48.1010000,37.6010000,125\n",
        encoding="ascii",
    )
    card = assemble(
        Inputs(
            dump_text=DUMP,
            boxnames=BOXES,
            blackbox_path=blackbox,
            gps_csv_path=gps,
            radio_json={
                "version": "MILELRS_v437",
                "model": "LR1824 Dual RX V2.0",
                "CUSTOM_FREQ": "1900-1920",
                "BINDING_RATE": "44",
                "SWARM_ID": "5,1,8,100,2",
                "binding_phrase": "do-not-keep",
                "RX_KEY": "do-not-keep-key",
            },
            nameplates={"vtx": "Skyzone VT7550"},
        )
    )
    assert card.family == "betaflight"
    assert card.fields["craft_name"].value == "Blink"
    assert card.fields["pilot_name"].value == "B162-483"
    assert card.fields["aux"].value[2]["name"] == "LAZYFLY"
    assert card.fields["vtxtable"].status == "confirmed"
    assert card.fields["packet_rate_log_hz"].value == "250"
    assert card.fields["radio_protocol"].value == "MILELRS"
    assert card.fields["radio_custom_freq"].value == "1900-1920"
    assert card.fields["radio_binding_rate"].value == "44"
    assert card.fields["nameplate_vtx"].status == "document"
    assert card.fields["vtx_device_responded"].status == "missing"
    assert card.fields["vtx_device_responded"].value is None
    assert card.fields["route_source"].value == "blackbox"
    assert card.fields["takeoff_lat"].status == "missing"
    dumped = json.dumps(card.to_dict())
    assert "do-not-keep" not in dumped
    assert "do-not-keep-key" not in dumped


def test_no_gps_bin_is_missing_not_a_guess(tmp_path: Path):
    path = tmp_path / "nogs.bin"
    write_bin(
        path,
        [
            _msg(1_000_000, "ArduCopter V4.5.7"),
            _parm(1_000_000, "RC_PROTOCOLS", 1),
            _parm(1_000_000, "MNT1_TYPE", 8),
            _parm(1_000_000, "CAM1_TYPE", 4),
            _parm(1_000_000, "VTX_ENABLE", 0),
            _parm(1_000_000, "FS_THR_ENABLE", 0),
            _ev(13_000_000, 10),
            _baro(13_000_000, 75.0),
            _baro(20_000_000, 158.0),
            _msg(20_000_000, "Drop script is running"),
            _rcin(20_000_000, 982),
            _ev(60_000_000, 11),
            _pos(13_000_000, 55.0, 37.0),
        ],
    )
    card = assemble(Inputs(bin_path=path, nameplates={"radio": "Ebyte E22-400M22S", "gimbal": "STorM32"}))
    assert card.family == "ardupilot"
    assert card.fields["route_source"].value == "none"
    assert card.fields["route_track"].status == "missing"
    assert card.fields["takeoff_lat"].status == "missing"
    assert card.fields["takeoff_time_us"].value == 13_000_000
    assert card.fields["landing_time_us"].value == 60_000_000
    assert card.fields["flight_duration_us"].value == 47_000_000
    assert card.fields["baro_alt"].value["min"] == 75.0
    assert card.fields["baro_alt"].value["max"] == 158.0
    assert card.fields["baro_alt"].reason.startswith("барометр")
    assert card.fields["rc_protocols"].value["bits"] == ["All"]
    assert card.fields["mnt1_type"].value["label"] == "Siyi"
    assert card.fields["cam1_type"].value["label"] == "Mount"
    assert card.fields["nameplate_gimbal"].value == "STorM32"
    assert card.fields["mnt1_type"].value["label"] != card.fields["nameplate_gimbal"].value
    assert card.fields["vtx_device_responded"].status == "missing"
    assert card.fields["radio_protocol"].status == "missing"
    assert card.fields["radio_swarm_id"].status == "not_applicable"
    assert card.fields["craft_name"].status == "not_applicable"
    assert card.fields["aux"].status == "not_applicable"
    joined = card.fields["messages_with_rcin"].value
    drop = next(item for item in joined if item["text"] == "Drop script is running")
    assert drop["rcin"]["C11"] == 982
    assert any("источник none" in hole for hole in card.holes)
    assert any(line["source"] == "bin_pos" and line["result"] == "ignored" for line in card.journal)


def test_gps_track_uses_3d_fix_at_arm_not_the_first_point(tmp_path: Path):
    path = tmp_path / "gps.bin"
    home_lat, home_lon = 50.0, 30.0
    write_bin(
        path,
        [
            _orgn(500_000, 0, 1.0, 1.0),
            _orgn(500_000, 1, home_lat, home_lon),
            _gps(800_000, 3, 49.0, 30.0, 10.0),
            _ev(1_000_000, 10),
            _gps(1_200_000, 2, 10.0, 10.0, 1.0),
            _gps(1_400_000, 3, 50.010, 30.010, 120.0),
            _gps(2_000_000, 3, 50.020, 30.020, 140.0),
            _ev(3_000_000, 11),
            _gps(3_100_000, 3, 50.021, 30.021, 90.0),
        ],
    )
    card = assemble(Inputs(bin_path=path))
    assert card.fields["route_source"].value == "bin"
    assert card.fields["takeoff_lat"].value == pytest.approx(50.010, abs=1e-6)
    assert card.fields["takeoff_lat"].value != pytest.approx(49.0, abs=1e-3)
    assert card.fields["landing_lat"].value == pytest.approx(50.020, abs=1e-6)
    assert card.fields["home"].value["lat"] == pytest.approx(home_lat)
    assert card.fields["route_length_m"].status == "confirmed"
    assert card.fields["route_length_m"].source == "computed_from=route_track"
    assert card.fields["max_distance_from_home_m"].value > 1000
    assert len(card.fields["route_track"].value) == 2


def test_status_two_and_pos_do_not_make_a_track(tmp_path: Path):
    path = tmp_path / "weak.bin"
    write_bin(
        path,
        [
            _gps(1_000_000, 2, 50.0, 30.0, 10.0),
            _pos(1_000_000, 50.0, 30.0),
        ],
    )
    card = assemble(Inputs(bin_path=path))
    assert card.fields["route_source"].value == "none"
    assert card.fields["route_track"].status == "missing"
    assert any(line["result"] == "present_no_fix" for line in card.journal)


def test_two_arm_cycles_are_two_flights(tmp_path: Path):
    path = tmp_path / "two.bin"
    write_bin(
        path,
        [
            _ev(1_000_000, 10),
            _gps(1_100_000, 3, 50.0, 30.0, 100.0),
            _gps(1_200_000, 3, 50.001, 30.001, 110.0),
            _ev(2_000_000, 11),
            _ev(5_000_000, 10),
            _gps(5_100_000, 3, 51.0, 31.0, 80.0),
            _ev(6_000_000, 11),
        ],
    )
    card = assemble(Inputs(bin_path=path))
    assert len(card.flights) == 2
    assert card.flights[0]["takeoff"]["lat"] == pytest.approx(50.0)
    assert card.flights[1]["takeoff"]["lat"] == pytest.approx(51.0)


def test_gpx_track_does_not_replace_a_missing_log(tmp_path: Path):
    gpx = tmp_path / "track.gpx"
    gpx.write_text(
        """<?xml version="1.0"?>
        <gpx>
          <trk><trkseg>
            <trkpt lat="50.0" lon="30.0"><ele>100</ele></trkpt>
            <trkpt lat="50.1" lon="30.1"><ele>110</ele></trkpt>
          </trkseg></trk>
          <wpt lat="50.2" lon="30.2"><ele>0</ele></wpt>
        </gpx>
        """,
        encoding="utf-8",
    )
    card = assemble(Inputs(gpx_path=gpx, banner="ArduCopter V4.5.7"))
    assert card.fields["route_source"].value == "none"
    assert card.fields["mission_waypoints"].status == "confirmed"
    assert card.fields["mission_waypoints"].value[0]["lat"] == 50.2


def test_waypoints_file(tmp_path: Path):
    path = tmp_path / "mission.waypoints"
    path.write_text(
        "QGC WPL 110\n0\t1\t0\t16\t0\t0\t0\t0\t50.5\t30.5\t100\t1\n",
        encoding="utf-8",
    )
    card = assemble(Inputs(waypoints_path=path, banner="ArduCopter V4.5.7"))
    assert card.fields["mission_waypoints"].value[0]["lat"] == 50.5
    assert card.fields["route_track"].status == "missing"


def test_radio_image_selects_milelrs_and_drops_the_key():
    blob = b"\x00MILELRS_v437\nCUSTOM_FREQ=1900-1920\nBINDING_RATE=44\nRX_KEY=super-secret\n"
    reading = parse_radio_image(blob)
    assert reading.firmware == "MILELRS"
    assert b"super-secret" not in reading.redacted
    assert "RX_KEY" in "".join(reading.removed_secrets).upper() or "rx_key" in reading.removed_secrets
    card = assemble(Inputs(radio_image=blob, banner="Betaflight 4.5.0"))
    dumped = json.dumps(card.to_dict())
    assert "super-secret" not in dumped
    assert card.fields["radio_binding_rate"].value == "44"


def test_expresslrs_does_not_get_milelrs_fields():
    card = assemble(
        Inputs(
            banner="Betaflight 4.5.0",
            radio_json={"version": "ExpressLRS 3.5.3", "uid": "01:02", "rate_index": "3", "binding_phrase": "hidden"},
        )
    )
    assert card.fields["radio_protocol"].value == "ExpressLRS"
    assert card.fields["radio_swarm_id"].status == "not_applicable"
    assert card.fields["radio_rate_index"].value == "3"
    assert "hidden" not in json.dumps(card.to_dict())


def test_auth_declined_is_a_hole():
    card = assemble(Inputs(banner="INAV 7.1.0", auth_declined=True))
    assert card.fields["radio_fields_requires_auth"].value is True
    assert card.fields["radio_protocol"].status == "missing"
    assert card.fields["radio_protocol"].source == "auth_declined"


def test_rc_protocols_value_one_is_all():
    assert rc_protocols_45(1) == ["All"]
    assert rc_protocols_45(8) == ["SBUS"]
    assert "CRSF" in rc_protocols_45(512)


def test_cli_rejects_writes():
    with pytest.raises(ReadOnlyError):
        assert_readonly_cli("set craft_name = Blink")
    with pytest.raises(ReadOnlyError):
        assert_readonly_cli("save")
    with pytest.raises(ReadOnlyError):
        assert_readonly_cli("serialpassthrough 1 420000")
    assert assert_readonly_cli("dump all") == "dump all"
    assert assert_readonly_cli("diff all") == "diff all"
    assert assert_readonly_cli("wp") == "wp"
    assert assert_readonly_cli("version") == "version"
    with pytest.raises(ReadOnlyError):
        assert_readonly_cli("wp load")
    with pytest.raises(ReadOnlyError):
        assert_readonly_cli("wp save")


def test_msp_boxnames_roundtrip():
    frame = msp_request(116)
    assert frame.startswith(b"$M<")
    # size, code, checksum. A write-range code is refused.
    with pytest.raises(ReadOnlyError):
        msp_request(200)
    payload = b"ARM;ANGLE"
    size = len(payload)
    code = 116
    checksum = size ^ code
    for byte in payload:
        checksum ^= byte
    reply = bytes([ord("$"), ord("M"), ord(">"), size, code]) + payload + bytes([checksum])
    port = ScriptedPort(chunks=[reply])
    assert read_boxnames(port) == "ARM;ANGLE"


def test_cli_session_sends_only_the_allowlist():
    port = ScriptedPort(chunks=[b"# Betaflight\r\n", b"Betaflight 4.5.0\r\n#\r\n", b"craft_name = Blink\r\n#\r\n"])
    text = read_cli(port, ["version", "get craft_name"])
    assert "Betaflight" in text
    written = b"".join(port.written)
    assert b"save" not in written
    assert b"dump all" not in written
    assert b"version\n" in written


def test_unknown_banner_does_not_invent_a_family():
    card = assemble(Inputs(banner="HELLO DEVICE"))
    assert card.family == "unknown"
    assert card.fields["route_source"].value == "none"


def test_tlog_track_is_used_when_the_bin_has_no_gps(tmp_path: Path):
    from pymavlink.dialects.v20 import ardupilotmega as dialect

    bin_path = tmp_path / "empty.bin"
    write_bin(bin_path, [_msg(1, "ArduCopter V4.5.7"), _ev(1_000_000, 10), _ev(2_000_000, 11)])
    tlog = tmp_path / "flight.tlog"
    import struct
    with tlog.open("wb") as handle:
        link = dialect.MAVLink(handle)
        link.srcSystem = 1
        for usec, lat, lon, alt in (
            (1_000_000, 48.2, 37.7, 100_000),
            (2_000_000, 48.21, 37.71, 120_000),
        ):
            # mavutil reads a .tlog as 8-byte big-endian microseconds plus a frame.
            handle.write(struct.pack(">Q", usec))
            link.gps_raw_int_send(usec, 3, int(lat * 1e7), int(lon * 1e7), alt, 100, 100, 0, 0, 12)
    card = assemble(Inputs(bin_path=bin_path, tlog_path=tlog))
    # The .BIN has the arm clock and no GPS. The .tlog has the track.
    # The clocks are not aligned, so the arm time stays and the takeoff
    # coordinate stays empty. The track itself is still the tlog.
    assert card.fields["route_source"].value == "tlog"
    assert card.fields["takeoff_lat"].status == "missing"
    assert card.fields["takeoff_time_us"].value == 1_000_000
    assert card.fields["route_track"].value[0]["lat"] == pytest.approx(48.2)


def test_cli_writes_html(tmp_path: Path):
    from drone_sweep.__main__ import main

    dump = tmp_path / "dump.txt"
    dump.write_text(DUMP, encoding="utf-8")
    out = tmp_path / "out"
    assert main(["assemble", "--dump", str(dump), "--boxnames", str(_write(tmp_path)), "--out", str(out)]) == 0
    text = (out / "report.html").read_text(encoding="utf-8")
    assert "Blink" in text
    assert "LAZYFLY" in text


def _write(tmp_path: Path) -> Path:
    path = tmp_path / "boxes.txt"
    path.write_text(BOXES, encoding="utf-8")
    return path


def test_bad_status_cannot_be_constructed():
    with pytest.raises(ValueError):
        Item("inferred", 1)
    with pytest.raises(ValueError):
        Item("derived", 1)


def test_json_redact_nested():
    reading = parse_radio_json({"info": {"password": "x", "uid": "aa"}, "ALT_KEYS": ["k"]})
    assert reading.fields["uid"] == "aa"
    assert "password" in reading.removed_secrets
    assert "x" not in reading.redacted.decode()
