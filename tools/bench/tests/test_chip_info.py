# SPDX-License-Identifier: GPL-3.0-or-later
from bench import actions
from fakes import Out

# Shape of esptool 5.x 'flash-id' output for an ESP32-S3 N16R8 module (recorded format).
ESPTOOL_S3 = """esptool v5.7.0
Connected to ESP32-S3 on /dev/espk-dut:
Chip type:          ESP32-S3 (QFN56) (revision v0.2)
Features:           Wi-Fi, BT 5 (LE), Dual Core + LP Core, 240MHz, Embedded PSRAM 8MB (AP_3v3)
Crystal frequency:  40MHz
MAC:                24:58:7c:aa:bb:cc
Flash Memory Information:
Manufacturer: 46
Device: 4018
Detected flash size: 16MB
Hard resetting via RTS pin...
"""


def test_parses_chip_revision_flash_psram_mac():
    info = actions.parse_chip_info(ESPTOOL_S3)
    assert info == {"chip": "esp32-s3", "revision": "0.2", "mac": "24:58:7c:aa:bb:cc",
                    "flash_mb": "16", "psram_mb": "8"}


def test_matches_bench_yaml(bench):
    out = Out()
    assert actions.chip_info("/dev/x", lambda argv: ESPTOOL_S3, out, expect=bench.role("dut")) == 0
    assert "chip=esp32-s3" in out and "mac=24:58:7c:aa:bb:cc" in out


def test_flash_size_mismatch_fails(bench):
    out = Out()
    text = ESPTOOL_S3.replace("16MB", "4MB")
    assert actions.chip_info("/dev/x", lambda argv: text, out, expect=bench.role("dut")) == 1
    assert any(o.startswith("MISMATCH flash_mb") for o in out)


def test_missing_psram_fails(bench):
    out = Out()
    text = ESPTOOL_S3.replace(", Embedded PSRAM 8MB (AP_3v3)", "")
    assert actions.chip_info("/dev/x", lambda argv: text, out, expect=bench.role("dut")) == 1


def test_esptool_failure_is_not_a_chip(bench):
    out = Out()
    text = "A fatal error occurred: Failed to connect to ESP32-S3: No serial data received."
    assert actions.chip_info("/dev/x", lambda argv: text, out, expect=bench.role("dut")) == 1
    assert "chip=unknown" in out
