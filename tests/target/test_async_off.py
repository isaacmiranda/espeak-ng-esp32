# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-ASY-08: with CONFIG_ESPK_ASYNC off, say and cancel are ESP_ERR_NOT_SUPPORTED and no task exists.

ESPK_SYNC_BUILD names the build directory of the variant without the layer (checked to really have it off);
ESPK_ARTIFACT names that variant's packed artifact, flashed on the board.
"""

import os
from pathlib import Path

import board
import pytest


def _precondition():
    d = os.environ.get("ESPK_SYNC_BUILD")
    cfg = Path(d) / "sdkconfig" if d else None
    if not cfg or not cfg.is_file():
        pytest.skip("not done (precondition): ESPK_SYNC_BUILD does not name the variant's build")
    assert "# CONFIG_ESPK_ASYNC is not set" in cfg.read_text(), "the variant has the layer on"


def test_say_and_cancel_are_not_supported_and_there_is_no_task(flashed):
    _precondition()
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    m, _p = board.command("say --mute Hello there.", r"^ESPK (queued|error)")
    assert m.event == "error" and m.fields["code"] == "ESP_ERR_NOT_SUPPORTED", m
    m, _p = board.command("cancel", r"^ESPK cancel")
    assert m.fields == {"err": "ESP_ERR_NOT_SUPPORTED"}, m
    m, _p = board.command("taskinfo", r"^ESPK taskinfo")
    assert m.fields == {} and "none" in str(m), m
    m, _p = board.command("synth Hello there.", r"^ESPK (sync|error)", timeout=30)
    assert m.event == "sync", "the synchronous core must keep working"
