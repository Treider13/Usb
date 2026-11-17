"""OrangeRX / Spektrum DSM: одна схема для Betaflight, INAV и ArduPilot."""

from __future__ import annotations

import re

from .model import Card, confirmed, missing, not_applicable

DSM_SERIAL_PROVIDERS = frozenset({"SPEKTRUM2048", "SPEKTRUM1024"})
DSM_PROTOCOL_NAMES = frozenset({"SPEKTRUM", "SPEKTRUM2048", "SPEKTRUM1024"})


def apply_spektrum_serial_provider(card: Card, provider: str, *, source: str) -> None:
    """serialrx_provider = SPEKTRUM2048 / 1024 — UART OrangeRX / DSM."""
    name = provider.strip().upper()
    if name not in DSM_SERIAL_PROVIDERS:
        return
    channels = 12 if name == "SPEKTRUM2048" else 7
    card.put("serial_link_class", confirmed("DSM2/DSMX", "betaflight rx.h"))
    card.put(
        "radio_protocol",
        confirmed(name, source, "класс DSM2/DSMX, приёмники OrangeRX входят в него"),
    )
    card.put(
        "spektrum_channel_count",
        confirmed(channels, "spektrum.h", "SPEKTRUM_2048_CHANNEL_COUNT или SPEKTRUM_1024_CHANNEL_COUNT"),
    )
    card.put(
        "spektrum_baud",
        confirmed(115200, "spektrum.h", "SPEKTRUM_BAUDRATE, скорость драйвера"),
    )
    card.put(
        "uplink_lq",
        not_applicable("в rx.h у SPEKTRUM нет источника LQ класса CRSF", "betaflight rx.h"),
    )
    _put_orange_profile(card, name, channels)


def apply_spektrum_spi(card: Card, *, serial_provider: str | None, source: str) -> None:
    """rx_spi_protocol = SPEKTRUM (CYRF, встроенный DSM)."""
    if "serial_link_class" not in card.fields:
        card.put("serial_link_class", confirmed("DSM2/DSMX", "betaflight rx_spi.h"))
    provider = (serial_provider or "").strip().upper()
    if provider in DSM_SERIAL_PROVIDERS:
        channels = 12 if provider == "SPEKTRUM2048" else 7
        proto = provider
    else:
        channels = 12
        proto = "SPEKTRUM"
    if "spektrum_channel_count" not in card.fields:
        card.put(
            "spektrum_channel_count",
            confirmed(
                channels,
                "spektrum.h",
                "SPI CYRF: 12 каналов, если в dump нет SPEKTRUM2048/1024",
            ),
        )
    if "spektrum_baud" not in card.fields:
        card.put("spektrum_baud", confirmed(115200, "spektrum.h", "SPI DSM"))
    card.put(
        "uplink_lq",
        not_applicable("у SPI DSM нет CRSF LQ", "betaflight rx_spi.h"),
    )
    _put_orange_profile(card, proto, channels)


def apply_ardupilot_dsm(
    card: Card,
    *,
    rc_protocol_bits: list[str] | None,
    uart_protocol: str | None,
    source: str,
) -> None:
    """ArduPilot: DSM в RC_PROTOCOLS или в MSG «Rc protocol: …»."""
    dsm = False
    if rc_protocol_bits and "DSM" in rc_protocol_bits:
        dsm = True
    if uart_protocol:
        low = uart_protocol.lower()
        if "dsm" in low or "spektrum" in low:
            dsm = True
    if not dsm:
        return
    if "serial_link_class" not in card.fields:
        card.put("serial_link_class", confirmed("DSM2/DSMX", "ArduPilot RC DSM"))
    if card.fields.get("radio_protocol") is None or card.fields["radio_protocol"].status != "confirmed":
        label = "DSM"
        if uart_protocol:
            label = uart_protocol
        card.put(
            "radio_protocol",
            confirmed(label, source, "OrangeRX и Spektrum satellite — класс DSM, не ELRS"),
        )
    if "spektrum_channel_count" not in card.fields:
        card.put(
            "spektrum_channel_count",
            confirmed(12, "ArduPilot DSM", "типично DSMX 12 кан; точное число — в параметрах пульта"),
        )
    if "spektrum_baud" not in card.fields:
        card.put("spektrum_baud", confirmed(115200, "ArduPilot DSM", "стандартная линия Spektrum"))
    proto_field = card.fields.get("radio_protocol")
    proto = str(proto_field.value) if proto_field and proto_field.status == "confirmed" else "DSM"
    _put_orange_profile(card, proto, int(card.fields["spektrum_channel_count"].value) if card.fields.get("spektrum_channel_count") else 12)


def put_ardupilot_radio_summary(card: Card) -> None:
    """Собирает радио-блок ArduPilot в один словарь (как dump у BF)."""
    summary: dict[str, object] = {}
    for key in (
        "rc_protocols",
        "uart_protocol",
        "mavlink_radio_status",
        "mavlink_rc_interval_ms",
        "receiver_port",
        "serial_ports",
        "radio_protocol",
        "serial_link_class",
        "spektrum_channel_count",
        "spektrum_baud",
    ):
        field = card.fields.get(key)
        if field is not None and field.status == "confirmed":
            summary[key] = field.value
    if not summary:
        return
    card.put(
        "ardupilot_radio_summary",
        confirmed(
            summary,
            "MAVLink / .BIN",
            "радио и приёмник: параметры, RADIO_STATUS, порты",
        ),
    )


def _put_orange_profile(card: Card, protocol: str, channels: int) -> None:
    nameplate = card.fields.get("nameplate_radio")
    profile: dict[str, object] = {
        "protocol": protocol,
        "link_class": "DSM2/DSMX",
        "channels": channels,
        "baud": 115200,
        "vendor_hint": "OrangeRX / Spektrum satellite" if nameplate else "DSM/Spektrum",
    }
    if nameplate is not None and nameplate.status == "document":
        profile["nameplate"] = nameplate.value
    bind = card.fields.get("spektrum_sat_bind")
    if bind is not None and bind.status == "confirmed":
        profile["bind_setting"] = bind.value
    card.put(
        "orange_rx_profile",
        confirmed(
            profile,
            "dump / параметры",
            "OrangeRX считывается с полётника: provider, SPI, bind; сателлит отдельно не снимаем",
        ),
    )


def dsm_from_message(text: str) -> str | None:
    if not text:
        return None
    low = text.lower()
    if low.startswith("rc protocol:"):
        return text.split(":", 1)[1].strip()
    if re.search(r"\bdsm\b|\bspektrum\b", low):
        return text.strip()
    return None