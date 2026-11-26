# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-REF-03: the board's PCM equals R1's, say by say, from a reset, over the verification corpus."""

import json

import board
import pytest


def test_board_pcm_equals_r1_over_the_verification_corpus(flashed):
    script = board.verify_script()
    diffs = board.compare(board.board_run(script, timeout=60), board.r1_run(script))
    report = board.ROOT / "test-results" / "equivalence-report.json"
    report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps(diffs, ensure_ascii=False, indent=1), encoding="utf-8")
    assert not diffs, f"{len(diffs)} says differ from R1; first: {diffs[0]}"


@pytest.mark.parametrize("voice", ["en"])
def test_board_equals_r1_without_accents(flashed, voice):
    """The part of FR-REF-03 that holds without the wrap: English and unaccented text."""
    script = "init en\nvoice en\n" + "".join(
        f"say {t}\n" for t in ("The battery is low.", "It is 2:30 pm.", "The battery is low."))
    assert not board.compare(board.board_run(script), board.r1_run(script))
