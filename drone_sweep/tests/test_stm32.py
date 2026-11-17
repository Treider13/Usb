"""STM32 identity from a saved programmer log, never from an erase command."""

import pytest

from drone_sweep.assemble import Inputs, assemble
from drone_sweep.stm32 import assert_readonly_programmer, parse_stm32_log
from drone_sweep.usb_read import ReadOnlyError


CUBE = """\
ST-LINK SN  : 00380025313751XXXXXXXXXX
ST-LINK FW  : V3J15M7
Board       : STM32L562E-DK
Voltage     : 3.28V
SWD freq    : 8000 KHz
Connect mode: Under Reset
Reset mode  : Hardware reset
Device ID   : 0x472
Revision ID : Rev Z
Device name : STM32L5xx
Flash size  : 512 KBytes (default)
Device type : MCU
Device CPU  : Cortex-M33
BL Version  : --
"""

PROBE = """\
Found 1 stlink programmers
  version:    V2J29S7
  serial:     303030303030303030303031
  flash:      1048576 (pagesize: 16384)
  sram:       131072
  chipid:     0x413
  dev-type:   STM32F40x_41x
  voltage:    3280 mV
"""


def test_cubeprogrammer_banner_is_stored_without_a_write():
    card = assemble(Inputs(stm32_text=CUBE, banner="unknown board"))
    probe = card.fields["stm32_probe"].value["cubeprogrammer"]
    assert probe["device_id"] == "0x472"
    assert probe["device_name"] == "STM32L5xx"
    assert probe["flash_size"] == "512 KBytes (default)"
    assert probe["device_cpu"] == "Cortex-M33"
    assert card.fields["stm32_probe"].value["log_contains_write"] is False
    assert "stm32_log_contains_write" not in card.fields


def test_erase_in_the_same_log_is_marked_and_not_treated_as_identity():
    text = CUBE + "Erasing memory corresponding to segment 0:\nDownload in Progress:\n"
    card = assemble(Inputs(stm32_text=text))
    assert card.fields["stm32_probe"].value["cubeprogrammer"]["device_id"] == "0x472"
    assert card.fields["stm32_log_contains_write"].value is True
    assert any("не повторяется" in hole for hole in card.holes)


def test_st_info_probe_uses_the_info_c_fields():
    parsed = parse_stm32_log(PROBE)
    info = parsed["st_info"]
    assert info["chipid"] == "0x413"
    assert info["flash_bytes"] == "1048576"
    assert info["page_size"] == "16384"
    assert info["sram_bytes"] == "131072"
    assert info["dev_type"] == "STM32F40x_41x"
    assert info["voltage_mv"] == "3280"
    assert parsed["log_contains_write"] is False


def test_garbage_does_not_become_a_chip_name():
    card = assemble(Inputs(stm32_text="hello\n"))
    assert card.fields["stm32_probe"].status == "missing"


def test_programmer_write_commands_are_refused():
    assert assert_readonly_programmer("STM32_Programmer_CLI --connect port=SWD") == "STM32_Programmer_CLI --connect port=SWD"
    assert "st-info --probe" == assert_readonly_programmer("st-info --probe")
    with pytest.raises(ReadOnlyError):
        assert_readonly_programmer("STM32_Programmer_CLI --connect port=SWD --erase all")
    with pytest.raises(ReadOnlyError):
        assert_readonly_programmer("STM32_Programmer_CLI --connect port=swd --download firmware.hex")
    with pytest.raises(ReadOnlyError):
        assert_readonly_programmer("st-info --flash --something")
