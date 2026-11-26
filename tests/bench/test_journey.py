# SPDX-License-Identifier: GPL-3.0-or-later
"""The journey (FSD §28.1): one workflow test per step, in order.

The step 6 (cancel) is JRN-06.
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


def test_jrn_03_say_speaks_through_the_codec(flashed):
    """FR-RES-03, FR-RES-11 (start before done), FR-RES-12: `say` without --mute, default volume 5."""
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    text = PT.encode()
    _m, p = board.command(f"say {PT}", r"^ESPK (done|error)", timeout=60)
    events = [m.event for m in board.markers(p.stdout)]
    assert "start" in events and "done" in events, p.stdout
    assert events.index("start") < events.index("done"), events
    done = next(m for m in board.markers(p.stdout) if m.event == "done")
    assert int(done.fields["samples"]) > 0
    assert int(done.fields["bytes"]) == len(text)
    assert done.fields["underrun"] == "0", done.fields


def test_jrn_06_cancel_in_the_middle_of_a_long_utterance(flashed):
    """FR-RES-10, FR-RES-11, FR-ASY-03: `cancel` during a long say -> `ESPK cancelled` within 100 ms
    (measured on the chip, from the cancel call to the event), no `done` for that say, and it speaks again."""
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    long_text = " ".join([PT] * 29)  # 985 bytes: within the 1 024 limit, seconds of speech
    m, p = board.command(f"say --mute {long_text}", r"^ESPK (start|error)", timeout=20)
    assert m and m.event == "start", p.stdout
    m, p = board.command("cancel", r"^ESPK (cancelled|done|error)", timeout=10)
    assert m and m.event == "cancelled", f"the speech ended before the cancel, or no event: {p.stdout}"
    assert int(m.fields["cancel_ms"]) <= 100, m.fields
    quiet = board.bench("wait-event", "dut", r"^ESPK done", "--timeout", "3")
    assert quiet.returncode == 3, f"a done followed the cancelled: {quiet.stdout}"
    m, p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    assert m and m.event == "done", p.stdout


def test_jrn_04_pt_br_hash_equals_r1(flashed):
    script = f"init en\nvoice pt-br\nsay {PT}\n"
    assert not board.compare(board.board_run(script), board.r1_run(script))


def test_jrn_05_en_hash_equals_r1(flashed):
    script = f"init en\nvoice pt-br\nsay {PT}\nvoice en\nsay {EN}\n"
    assert not board.compare(board.board_run(script), board.r1_run(script))
