# SPDX-License-Identifier: GPL-3.0-or-later
"""Refusals that only a differently configured build can show (scripts/variants.sh builds and runs them).

Each test needs its variant's build directory in ESPK_<NAME>_BUILD (checked against that build's
sdkconfig) and the variant's packed artifact in ESPK_ARTIFACT; without them it is `not done (precondition)`.
"""

import os
from pathlib import Path

import board
import pytest


def _variant(name: str, expect: str) -> None:
    d = os.environ.get(f"ESPK_{name.upper()}_BUILD")
    cfg = Path(d) / "sdkconfig" if d else None
    if not cfg or not cfg.is_file():
        pytest.skip(f"not done (precondition): ESPK_{name.upper()}_BUILD does not name the {name} build")
    assert expect in cfg.read_text(), f"the {name} variant was not built with {expect}"


def _refused(code: str) -> dict:
    ms, p = board.boot(timeout=20)
    assert "error" in ms and "ready" not in ms, p.stdout
    assert ms["error"].fields["code"] == code, ms["error"].fields
    assert ms["boot"].fields["langs"] == "none", "an engine was loaded"
    quiet = board.bench("wait-event", "dut", r"^ESPK alive n=3", "--timeout", "8")
    assert quiet.returncode == 0, "no reset-free run after the refusal (panic?): " + quiet.stdout
    return ms


def test_a_missing_partition_label_gets_not_found(flashed):
    """FR-DAT-02 (and FR-DAT-01, the label): ESP_ERR_NOT_FOUND, the component stays UNINIT."""
    _variant("nolabel", 'CONFIG_ESPK_PARTITION_LABEL="nope"')
    _refused("ESP_ERR_NOT_FOUND")


def test_a_wrong_partition_subtype_gets_not_found(flashed):
    """FR-DAT-01: found by label AND subtype; the right label with another subtype is not it."""
    _variant("nosubtype", "CONFIG_ESPK_PARTITION_SUBTYPE=0x41")
    _refused("ESP_ERR_NOT_FOUND")


def test_a_build_without_psram_is_refused_without_loading_the_engine(flashed):
    """FR-MEM-01: espk_init() without initialised PSRAM -> ESP_ERR_NOT_SUPPORTED, nothing loaded."""
    _variant("nopsram", "# CONFIG_SPIRAM is not set")
    _refused("ESP_ERR_NOT_SUPPORTED")
