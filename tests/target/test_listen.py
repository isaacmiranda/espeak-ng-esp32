# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-LST-03: `play <id>` speaks an item of the listening corpus through the speaker, at the volume of the
session (here the default 5, inaudible by design), and answers ESPK done with the PCM hash."""

import sys

import board

sys.path.insert(0, str(board.ROOT / "tools/listening"))
import samples


def _expected_hash(voice, text):
    return board.r1_run(f"init en\nvoice {voice}\nsay {text}\n")[0]["sha256"]


def test_play_speaks_a_listening_item_with_the_hash_of_its_pcm(flashed):
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    corpus = dict(samples.corpus(board.ROOT / "tests/corpus/listen/en.tsv"))
    m, _p = board.command("voice en", r"^ESPK voice")
    m, p = board.command("play D03", r"^ESPK (done|error)", timeout=60)
    assert m.event == "done", p.stdout
    assert "ESPK start" in p.stdout
    assert int(m.fields["bytes"]) == len(corpus["D03"].encode()) and m.fields["underrun"] == "0"
    assert m.fields["sha256"] == _expected_hash("en", corpus["D03"])


def test_play_takes_the_item_from_the_corpus_of_the_current_voice(flashed):
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    pt = dict(samples.corpus(board.ROOT / "tests/corpus/listen/pt-br.tsv"))
    m, _p = board.command("voice pt-br", r"^ESPK voice")
    m, p = board.command("play D05", r"^ESPK (done|error)", timeout=60)
    assert m.event == "done", p.stdout
    assert int(m.fields["bytes"]) == len(pt["D05"].encode())
    assert m.fields["sha256"] == _expected_hash("pt-br", pt["D05"])
