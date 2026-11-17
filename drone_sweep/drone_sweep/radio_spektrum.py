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


RADIO_READ_KEYS = (
    "radio_protocol",
    "serialrx_provider",
    "serial_link_class",
    "uart_protocol",
    "receiver_port",
    "serial_ports",
    "uplink_lq",
    "spektrum_channel_count",
    "spektrum_baud",
    "spektrum_sat_bind",
    "expresslrs_spi",
    "rc_protocols",
    "mavlink_radio_status",
    "mavlink_rc_interval_ms",
)


def _radio_link_kind(card: Card) -> str | None:
    elrs = card.fields.get("expresslrs_spi")
    if elrs is not None and elrs.status == "confirmed":
        return "expresslrs_spi"
    features = card.fields.get("features")
    if features is not None and features.status == "confirmed" and isinstance(features.value, dict):
        enabled = features.value.get("enabled") or []
        if any("RX_SPI" in str(item) for item in enabled):
            return "rx_spi"
    provider = card.fields.get("serialrx_provider")
    if provider is not None and provider.status == "confirmed":
        return "uart_serialrx"
    if card.family in {"ardupilot", "mavlink"}:
        return "ardupilot_uart"
    return None


def _radio_summary_source(card: Card) -> str:
    if card.family == "ardupilot":
        return "MAVLink / .BIN"
    if card.family in {"betaflight", "inav"}:
        return "dump all"
    return "MAVLink"


def put_radio_read_summary(card: Card) -> None:
    """Один блок «Радио» для Betaflight, INAV и ArduPilot — те же ключи, что в карточке."""
    summary: dict[str, object] = {"flight_os": card.family}
    for key in RADIO_READ_KEYS:
        field = card.fields.get(key)
        if field is not None and field.status == "confirmed":
            summary[key] = field.value
    link = _radio_link_kind(card)
    if link:
        summary["radio_link_kind"] = link
    orange = card.fields.get("orange_rx_profile")
    if orange is not None and orange.status == "confirmed":
        summary["orange_rx_profile"] = orange.value
    rc = summary.get("rc_protocols")
    if isinstance(rc, dict) and rc.get("bits") == ["All"] and "orange_rx_profile" not in summary:
        summary["rc_protocols_note"] = (
            "RC_PROTOCOLS=All — маска «всё разрешено»; линия DSM/Spektrum фиксируется по MSG "
            "«Rc protocol:» или uart_protocol, а не по биту DSM в маске"
        )
    if len(summary) <= 1:
        return
    source = _radio_summary_source(card)
    detail = "радио и приёмник: dump или MAVLink/.BIN, порты, телеметрия, OrangeRX если есть"
    card.put("radio_read_summary", confirmed(summary, source, detail))
    if card.family in {"ardupilot", "mavlink"}:
        card.put("ardupilot_radio_summary", confirmed(summary, source, detail))


def put_ardupilot_radio_summary(card: Card) -> None:
    """Совместимость: то же, что put_radio_read_summary."""
    put_radio_read_summary(card)


def _enrich_orange_profile(card: Card, profile: dict[str, object]) -> None:
    for key in ("receiver_port", "serial_ports", "serialrx_provider", "radio_protocol"):
        field = card.fields.get(key)
        if field is not None and field.status == "confirmed":
            profile[key] = field.value
    features = card.fields.get("features")
    if features is not None and features.status == "confirmed" and isinstance(features.value, dict):
        enabled = features.value.get("enabled") or []
        spi = [item for item in enabled if "RX_SPI" in str(item)]
        if spi:
            profile["features_rx_spi"] = spi
    if card.fields.get("expresslrs_spi") is not None and card.fields["expresslrs_spi"].status == "confirmed":
        profile["expresslrs_on_fc"] = True
    profile["read_scope"] = (
        "с полётника: serial/SPI dump, bind, порты; прошивку спутника OrangeRX по отдельному USB не читаем"
    )


def refresh_orange_rx_profile(card: Card) -> None:
    """Дополняет orange_rx_profile после nameplate и поздних полей."""
    field = card.fields.get("orange_rx_profile")
    if field is None or field.status != "confirmed" or not isinstance(field.value, dict):
        return
    profile = dict(field.value)
    nameplate = card.fields.get("nameplate_radio")
    if nameplate is not None and nameplate.status == "document":
        profile["nameplate"] = nameplate.value
        profile["vendor_hint"] = "OrangeRX / Spektrum satellite"
    _enrich_orange_profile(card, profile)
    card.put(
        "orange_rx_profile",
        confirmed(profile, field.source, field.reason or ""),
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
    _enrich_orange_profile(card, profile)
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