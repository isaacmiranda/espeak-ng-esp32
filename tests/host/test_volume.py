# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-RES-07, FR-RES-08, FR-RES-09: the firmware's volume ceiling and listening session (pure parser)."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "research/firmware/main"


@pytest.fixture(scope="module")
def cli(tmp_path_factory):
    exe = tmp_path_factory.mktemp("vol") / "volume_cli"
    subprocess.run(["cc", "-O1", "-Wall", "-Werror", "-I", str(MAIN), str(ROOT / "tests/host/volume_cli.c"),
                    str(MAIN / "espk_volume.c"), "-o", str(exe)], check=True)
    return exe


def run(cli, *lines):
    out = subprocess.run([str(cli)], input="\n".join(lines) + "\n", capture_output=True, text=True,
                         check=True).stdout
    return out.splitlines()


def test_default_volume_is_5(cli):
    assert run(cli, "volume") == ["ESPK volume ok=5"]


def test_above_the_ceiling_is_refused_without_a_session_and_the_volume_stays(cli):
    assert run(cli, "volume 11", "volume", "volume 10", "volume 0", "volume 100") == [
        "ESPK volume err=ceiling", "ESPK volume ok=5", "ESPK volume ok=10", "ESPK volume ok=0",
        "ESPK volume err=ceiling"]


def test_listening_session_allows_up_to_100_until_close(cli):
    assert run(cli, "listen open 60", "volume 60", "volume 100", "listen close", "volume 60", "volume") == [
        "ESPK listen ok=open", "ESPK volume ok=60", "ESPK volume ok=100", "ESPK listen ok=close",
        "ESPK volume err=ceiling", "ESPK volume ok=5"]


def test_close_returns_to_the_default_volume(cli):
    assert run(cli, "listen open 60", "volume", "listen close", "volume") == [
        "ESPK listen ok=open", "ESPK volume ok=60", "ESPK listen ok=close", "ESPK volume ok=5"]


@pytest.mark.parametrize("line", ["volume 101", "volume -1", "volume abc", "volume 5x", "volume 1000",
                                  "listen open 101", "listen open"])
def test_malformed_arguments_are_refused_and_change_nothing(cli, line):
    out = run(cli, line, "volume")
    assert "err=" in out[0] and out[1] == "ESPK volume ok=5"


def test_other_lines_are_not_ours(cli):
    assert run(cli, "say hello", "voices", "volumes") == ["unhandled"] * 3
