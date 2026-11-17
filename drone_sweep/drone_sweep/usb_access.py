"""Linux permission for the flight-controller serial node.

Betaflight Configurator adds the user to the dialout group. That applies at
the next login. INAV ships a udev rule with MODE="0666" for the same USB ids.
This module installs that rule on the tty node and opens a matching port that
is already plugged in.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


RULE_NAME = "99-strela.rules"
# (vendor, product) pairs copied into the udev rule.
SERIAL_IDS = (
    ("0483", "5740"),
    ("2e3c", "5740"),
    ("314b", "5740"),
    ("0483", "374e"),
    ("1209", "5740"),
    ("1209", "5741"),
    ("0403", "6001"),
    ("10c4", "ea60"),
    ("10c4", "ea61"),
    ("10c4", "ea62"),
)


def rules_text() -> str:
    return (Path(__file__).parent / "linux" / RULE_NAME).read_text(encoding="utf-8")


def usb_ids(sysfs_device: Path) -> tuple[str, str] | None:
    """Vendor and product from a tty device directory, walking up to the USB parent."""
    current = sysfs_device
    for _ in range(8):
        vendor = current / "idVendor"
        product = current / "idProduct"
        if vendor.is_file() and product.is_file():
            return vendor.read_text(encoding="ascii").strip().lower(), product.read_text(encoding="ascii").strip().lower()
        if current.parent == current:
            break
        current = current.parent
    return None


def matching_ports(dev_dir: Path = Path("/dev"), sysfs: Path = Path("/sys/class/tty")) -> list[Path]:
    found = []
    for pattern in ("ttyACM*", "ttyUSB*"):
        for node in sorted(dev_dir.glob(pattern)):
            ids = usb_ids(sysfs / node.name / "device")
            if ids in SERIAL_IDS:
                found.append(node)
    return found


def install_usb_access(argv0: str) -> int:
    if os.geteuid() != 0:
        print("Строка [Errno 13] — это текст ошибки, не команда.")
        print("Правило доступа ставится так:")
        print(f"sudo {argv0} allow-usb")
        return 2
    destination = Path("/etc/udev/rules.d") / RULE_NAME
    destination.write_text(rules_text(), encoding="utf-8")
    subprocess.run(["udevadm", "control", "--reload-rules"], check=False)
    subprocess.run(["udevadm", "trigger", "--subsystem-match=tty", "--action=change"], check=False)
    opened = []
    for node in matching_ports():
        os.chmod(node, 0o666)
        opened.append(str(node))
    print(f"Записано {destination}.")
    if opened:
        print("Открыты сейчас: " + ", ".join(opened))
    else:
        print("Подходящий порт сейчас не вставлен. Вставьте кабель и нажмите «Считать».")
    sudo_user = os.environ.get("SUDO_USER", "")
    if sudo_user and sudo_user != "root":
        subprocess.run(["usermod", "-aG", "dialout", sudo_user], check=False)
        print(f"{sudo_user} добавлен в группу dialout, как в инструкции Betaflight. Группа заработает после нового входа в систему.")
    return 0
