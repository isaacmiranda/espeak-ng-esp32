# SPDX-License-Identifier: GPL-3.0-or-later
"""The journey (FSD §28.1): one workflow test per step, in order.

JRN-03 (audio) and JRN-06 (cancel) arrive with those features.
"""

import sys

import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import board

pytestmark = pytest.mark.bench
PT = "Atenção: a bateria está fraca."
EN = "Attention: the battery is low."


@pytest.fixture(scope="module")
def flashed():
    art = board.artifact()
    p = board.bench("flash", "dut", str(art), timeout=300)
    if p.returncode == 4:
        pytest.skip(f"not done (precondition): {p.stderr.strip()}")
    assert p.returncode == 0, p.stdout + p.stderr
    return art


def test_jrn_01_boot_carries_the_artifact_commit(flashed):
    ms, _p = board.boot()
    commit = ms["boot"].fields["commit"]
    assert f"commit: {commit}" in (flashed / "manifest.yaml").read_text()


def test_jrn_02_ready(flashed):
    ms, p = board.boot()
    assert "ready" in ms, p.stdout


def test_jrn_04_pt_br_hash_equals_r1(flashed):
    script = f"init en\nvoice pt-br\nsay {PT}\n"
    assert not board.compare(board.board_run(script), board.r1_run(script))


def test_jrn_05_en_hash_equals_r1(flashed):
    script = f"init en\nvoice pt-br\nsay {PT}\nvoice en\nsay {EN}\n"
    assert not board.compare(board.board_run(script), board.r1_run(script))
