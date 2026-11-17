"""Read-only ArduPilot details on an open MAVLink port.

The sequence follows ArduPilot GCS_Common.cpp and
AP_Logger_MAVLinkLogTransfer.cpp. The board sends a parameter banner when
it sees PARAM_REQUEST_LIST, and it sends a dataflash log only after a GCS
HEARTBEAT newer than three seconds (MAV_TYPE_GCS = 6). LOG_ERASE is never
sent. PARAM_SET is never sent. The vehicle is not armed and not disarmed.
"""

from __future__ import annotations

from pathlib import Path


REQUEST_AUTOPILOT_CAPABILITIES = 520


def gcs_heartbeat(connection) -> None:
    """Tell the board a ground station is listening. base_mode is 0, so the armed bit stays clear."""
    send = getattr(getattr(connection, "mav", None), "heartbeat_send", None)
    if send is None:
        return
    send(6, 8, 0, 0, 0, 3)


def request_autopilot_version(connection) -> None:
    """MAV_CMD_REQUEST_AUTOPILOT_CAPABILITIES with param1 = 1. ArduPilot then sends AUTOPILOT_VERSION."""
    send = getattr(getattr(connection, "mav", None), "command_long_send", None)
    if send is None:
        return
    send(
        connection.target_system,
        connection.target_component,
        REQUEST_AUTOPILOT_CAPABILITIES,
        0,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
    )


def pull(connection, kinds: tuple[str, ...], timeout: float):
    message = connection.recv_match(type=kinds, blocking=True, timeout=timeout)
    return message


def drain(connection, kinds: tuple[str, ...], rounds: int = 3) -> list:
    found = []
    empty = 0
    while empty < rounds:
        message = pull(connection, kinds, 0.2)
        if message is None:
            empty += 1
            continue
        empty = 0
        found.append(message)
    return found


def read_dataflash(connection, directory: Path | None) -> tuple[list[dict], Path | None, str]:
    """List the logs, then save the newest non-empty one. The board must be disarmed; Strela does not disarm it."""
    gcs_heartbeat(connection)
    texts: list[str] = []
    entries: list = []
    empty = 0
    connection.mav.log_request_list_send(connection.target_system, connection.target_component, 0, 0xFFFF)
    while empty < 4:
        gcs_heartbeat(connection)
        message = pull(connection, ("LOG_ENTRY", "STATUSTEXT"), 0.5)
        if message is None:
            empty += 1
            if _list_complete(entries):
                break
            continue
        empty = 0
        if message.get_type() == "STATUSTEXT":
            texts.append(_text(message))
            if "Disarm for log download" in texts[-1]:
                rows = [_status_row(text) for text in texts]
                return rows, None, (
                    "плата взведена: ArduPilot отвечает «Disarm for log download» и журнал не отдаёт. "
                    "Стрела взведение не снимает."
                )
            continue
        entries.append(message)
        if _list_complete(entries):
            break
    rows = [_entry_row(entry) for entry in entries]
    rows.extend(_status_row(text) for text in texts)
    if not entries:
        return rows, None, "плата не прислала LOG_ENTRY. Журнал не скачан."
    if entries[-1].num_logs == 0:
        return rows, None, "на плате нет журнала .BIN"
    chosen = _newest_with_bytes(entries)
    if chosen is None:
        return rows, None, "журналы на плате есть, но размер каждого 0 байт. Файл не записан."
    if directory is None:
        return rows, None, f"на плате журнал {chosen.id}, {chosen.size} байт. Папка не задана, файл не записан."
    directory.mkdir(parents=True, exist_ok=True)
    payload, note = _download(connection, chosen)
    path = directory / f"ardupilot-{chosen.id}.BIN"
    if len(payload) != int(chosen.size) or not payload.startswith(b"\xa3\x95"):
        if payload:
            path.write_bytes(payload)
            note = (
                f"журнал {chosen.id} скачан не целиком: {len(payload)} из {int(chosen.size)} байт, файл {path.name}. "
                "В карточку он не подставлен."
            )
        return rows, None, note
    path.write_bytes(payload)
    return rows, path, f"скачан журнал {chosen.id} с платы, {int(chosen.size)} байт, файл {path.name}"


def _download(connection, entry) -> tuple[bytes, str]:
    size = int(entry.size)
    chunks: dict[int, bytes] = {}
    stalls = 0
    try:
        while stalls < 6 and _prefix_len(chunks, size) < size:
            offset = _prefix_len(chunks, size)
            connection.mav.log_request_data_send(
                connection.target_system,
                connection.target_component,
                int(entry.id),
                offset,
                size - offset,
            )
            empty = 0
            grew = False
            while empty < 4 and _prefix_len(chunks, size) < size:
                gcs_heartbeat(connection)
                message = pull(connection, ("LOG_DATA", "STATUSTEXT"), 0.5)
                if message is None:
                    empty += 1
                    continue
                if message.get_type() != "LOG_DATA" or int(message.id) != int(entry.id):
                    continue
                count = int(message.count)
                if count <= 0:
                    continue
                piece = bytes(message.data[:count])
                before = _prefix_len(chunks, size)
                chunks[int(message.ofs)] = piece
                if _prefix_len(chunks, size) > before:
                    empty = 0
                    grew = True
            if _prefix_len(chunks, size) >= size:
                break
            stalls = 0 if grew else stalls + 1
    finally:
        end = getattr(connection.mav, "log_request_end_send", None)
        if end is not None:
            end(connection.target_system, connection.target_component)
    payload = _prefix(chunks, size)
    if len(payload) != size:
        return payload, f"журнал {int(entry.id)} оборвался на {len(payload)} из {size} байт"
    return payload, ""


def _list_complete(entries: list) -> bool:
    if not entries:
        return False
    count = int(entries[-1].num_logs)
    if count == 0:
        return True
    ids = {int(entry.id) for entry in entries}
    return len(ids) >= count


def _newest_with_bytes(entries: list):
    usable = [entry for entry in entries if int(entry.size) > 0 and int(entry.id) > 0]
    if not usable:
        return None
    return max(usable, key=lambda entry: int(entry.id))


def _prefix_len(chunks: dict[int, bytes], size: int) -> int:
    return len(_prefix(chunks, size))


def _prefix(chunks: dict[int, bytes], size: int) -> bytes:
    pos = 0
    out = bytearray()
    while pos < size and pos in chunks:
        piece = chunks[pos]
        out += piece
        pos += len(piece)
        if not piece:
            break
    return bytes(out)


def _text(message) -> str:
    raw = message.text
    if isinstance(raw, bytes):
        return raw.decode("latin1", errors="replace").rstrip("\x00").strip()
    return str(raw).rstrip("\x00").strip()


def _status_row(text: str) -> dict:
    return {"name": "STATUSTEXT", "text": text}


def _entry_row(message) -> dict:
    return {
        "name": "LOG_ENTRY",
        "id": int(message.id),
        "num_logs": int(message.num_logs),
        "last_log_num": int(message.last_log_num),
        "time_utc": int(message.time_utc),
        "size": int(message.size),
    }


def version_row(message) -> dict:
    packed = int(message.flight_sw_version)
    board_version = int(message.board_version)
    return {
        "name": "AUTOPILOT_VERSION",
        "flight_sw_version": packed,
        "major": (packed >> 24) & 0xFF,
        "minor": (packed >> 16) & 0xFF,
        "patch": (packed >> 8) & 0xFF,
        "fw_type": packed & 0xFF,
        "board_version": board_version,
        "board_id": board_version >> 16,
        "flight_custom_version": _bytes_text(message.flight_custom_version),
        "vendor_id": int(message.vendor_id),
        "product_id": int(message.product_id),
        "uid2": _uid(message.uid2),
    }


def _bytes_text(value) -> str:
    if isinstance(value, str):
        return value.rstrip("\x00").strip()
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("latin1", errors="replace").rstrip("\x00").strip()
    if isinstance(value, list):
        return bytes(int(item) & 0xFF for item in value).decode("latin1", errors="replace").rstrip("\x00").strip()
    return str(value)


def _uid(value) -> str:
    if isinstance(value, str):
        raw = value.encode("latin1", errors="replace")
    elif isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
    elif isinstance(value, list):
        raw = bytes(int(item) & 0xFF for item in value)
    else:
        return ""
    if not any(raw):
        return ""
    return raw.hex()
