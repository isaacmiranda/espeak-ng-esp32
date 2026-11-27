# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-EXM-04: the example's resampler (examples/waveshare-s3-rlcd/main/resample.h) converts the engine's PCM
to another codec rate: a constant stays constant, the length follows the ratio of the rates, a tone keeps
its frequency, and cutting the signal into blocks differently gives the same waveform (to one LSB)."""

import itertools
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "examples/waveshare-s3-rlcd/main"


@pytest.fixture(scope="module")
def cli(tmp_path_factory):
    exe = tmp_path_factory.mktemp("rs") / "resample_cli"
    subprocess.run(["cc", "-O1", "-Wall", "-Werror", "-I", str(EX), str(ROOT / "tests/host/resample_cli.c"),
                    "-lm", "-o", str(exe)], check=True)
    return exe


def run(cli, frm, to, block, kind):
    out = subprocess.run([str(cli), str(frm), str(to), str(block), kind], capture_output=True, text=True,
                         check=True).stdout
    return [int(x) for x in out.split()]


@pytest.mark.parametrize("to", [16000, 44100, 48000, 8000])
def test_a_constant_stays_constant_and_the_length_follows_the_ratio(cli, to):
    y = run(cli, 22050, to, 128, "dc")
    assert set(y[2:]) == {1000}, "the DC level changed"
    assert abs(len(y) - 22050 * to / 22050) <= 2


def test_a_tone_keeps_its_frequency(cli):
    y = run(cli, 22050, 16000, 128, "tone")
    crossings = sum(1 for a, b in itertools.pairwise(y) if a < 0 <= b)
    assert abs(crossings - 440 * len(y) / 16000) <= 2


def test_the_block_size_does_not_change_the_samples(cli):
    """The state carried between blocks is what makes a callback that delivers blocks of any size safe."""
    a = run(cli, 22050, 16000, 1000, "tone")
    for block in (1, 7, 128, 4096):
        b = run(cli, 22050, 16000, block, "tone")
        n = min(len(a), len(b))
        assert abs(len(a) - len(b)) <= 1, f"block {block}: another length"
        assert max(abs(x - y) for x, y in zip(a[:n], b[:n], strict=True)) <= 1, f"block {block} differs"
