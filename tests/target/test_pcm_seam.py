# SPDX-License-Identifier: GPL-3.0-or-later
"""The board's own PCM, streamed by its `pcm` command (the seam of FR-LST-01 and FR-REF-04): it equals the host
build's byte for byte, and the sample generator can write it as WAV files."""

import json
import sys
import wave

import board

sys.path.insert(0, str(board.ROOT / "tools/listening"))
sys.path.insert(0, str(board.ROOT / "tools/ref"))
import diverge  # noqa: E402
import r3host  # noqa: E402
import samples  # noqa: E402

CORPUS = board.ROOT / "tests/corpus/listen/en.tsv"


def test_the_pcm_streamed_by_the_board_equals_the_host_build_byte_for_byte(flashed):
    """FR-REF-04 (no divergence to report: first_divergent_sample is None) over three listening items."""
    items = samples.corpus(CORPUS)[:3]
    texts = [t for _i, t in items]
    on_board = samples.board_pcm("en", 175, texts)
    on_host = r3host.pcm("init en\nvoice en\nrate 175\n" + "".join(f"say {t}\n" for t in texts))
    for (item, _t), a, b in zip(items, on_board, on_host, strict=True):
        r = diverge.compare(b, a)
        assert r["equal"], f"{item}: {r}"


def test_the_generator_writes_the_boards_pcm_as_wav_files(flashed, tmp_path):
    """FR-LST-01 from the artifact: two items at one speed, named pseudorandomly, the map apart."""
    out, mapf = tmp_path / "samples", tmp_path / "key/map.json"
    samples.main(["--corpus", str(CORPUS), "--voice", "en", "--speeds", "175", "--seed", "5", "--out-dir", str(out),
                  "--map-file", str(mapf), "--source", "board", "--limit", "2"])
    m = json.loads(mapf.read_text())["files"]
    assert len(m) == 2 and all(v["source"] == "board" for v in m.values())
    items = samples.corpus(CORPUS)[:2]
    expect = r3host.pcm("init en\nvoice en\nrate 175\n" + "".join(f"say {t}\n" for _i, t in items))
    for (name, info), want in zip(sorted(m.items(), key=lambda kv: kv[1]["item"]), expect, strict=True):
        with wave.open(str(out / f"{name}.wav")) as w:
            assert w.getframerate() == 22050 and w.readframes(w.getnframes()) == want, info
