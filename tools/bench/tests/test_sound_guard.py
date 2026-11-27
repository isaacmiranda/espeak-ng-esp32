# SPDX-License-Identifier: GPL-3.0-or-later
"""The bench is silent: while bench.yaml forbids sound, the driver refuses what makes the speaker sound."""

from pathlib import Path

import pytest

from bench import actions
from bench.config import DEFAULT_PATH, load, parse

ROLE = {"dut": {"vid_pid": "303a:1001", "chip": "esp32s3", "flash_mb": 16, "psram": True}}


@pytest.mark.parametrize("line", ["say Hello there.", "say  x", "play D03", "play S01", "  say hi"])
def test_a_line_that_would_sound_is_refused(line):
    assert actions.sound_guard(line, sound_allowed=False)


@pytest.mark.parametrize(
    "line",
    [
        "say --mute Hello there.",
        "volume 5",
        "listen open 5",
        "voice en",
        "info",
        "cancel",
        "synth Hello",
        "pcm Hello",
        "say",
        "saying hello",
        "playground",
        "rate 175",
    ],
)
def test_a_silent_line_goes_through(line):
    assert actions.sound_guard(line, sound_allowed=False) is None


def test_sound_allowed_lifts_it():
    assert actions.sound_guard("say Hello there.", sound_allowed=True) is None
    assert actions.sound_guard("play D03", sound_allowed=True) is None


def _artifact(tmp_path: Path, app: str) -> Path:
    (tmp_path / "flash_args").write_text(
        f"--flash_mode dio\n0x0 bootloader/bootloader.bin\n0x20000 {app}.bin\n"
    )
    return tmp_path


def test_an_application_that_speaks_by_itself_is_not_flashed_while_sound_is_forbidden(tmp_path):
    art = _artifact(tmp_path, "espk_waveshare")
    assert "espk_waveshare" in actions.flash_sound_guard(art, ("espk_waveshare",), sound_allowed=False)
    assert actions.flash_sound_guard(art, ("espk_waveshare",), sound_allowed=True) is None
    assert actions.flash_sound_guard(_artifact(tmp_path, "espk_research"), ("espk_waveshare",), False) is None


def test_the_bench_is_silent_unless_the_file_says_allowed():
    assert parse({"project": "p", "link_prefix": "/dev/x-", "roles": ROLE}).sound_allowed is False
    assert (
        parse(
            {"project": "p", "link_prefix": "/dev/x-", "roles": ROLE, "audio": {"bench_sound": "allowed"}}
        ).sound_allowed
        is True
    )
    assert (
        parse(
            {"project": "p", "link_prefix": "/dev/x-", "roles": ROLE, "audio": {"bench_sound": "yes please"}}
        ).sound_allowed
        is False
    )


def test_the_projects_bench_forbids_sound_and_names_the_application_that_speaks_alone():
    b = load(DEFAULT_PATH)
    assert b.sound_allowed is False and "espk_waveshare" in b.sound_apps
