# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-EXM-01 and FR-EXM-03: the examples, flashed on the reference board, do what the FSD says.

scripts/examples.sh builds, packs and flashes an example and runs this file with ESPK_EXAMPLE (hello or
waveshare-s3-rlcd) and ESPK_EXAMPLE_ARTIFACT set; without them the tests are `not done (precondition)`. The
example replaces the research firmware on the shared board: the script's caller restores it.
"""

import os
import re
import sys
from pathlib import Path

import board
import pytest

sys.path.insert(0, str(board.ROOT / "tools/ref"))
import r3host

HELLO = "Hello from eSpeak NG on the ESP32."


def _example(name):
    art = os.environ.get("ESPK_EXAMPLE_ARTIFACT")
    if os.environ.get("ESPK_EXAMPLE") != name or not art or not (Path(art) / "flash_args").is_file():
        pytest.skip(f"not done (precondition): ESPK_EXAMPLE does not name {name} with its artifact")
    p = board.bench("flash", "dut", art, timeout=300)
    if p.returncode == 2 and "forbids sound" in p.stderr:  # speaks at boot: the bench is silent
        pytest.skip(f"not done (precondition): {p.stderr.strip()}")
    assert p.returncode == 0, p.stdout + p.stderr


def _log(pattern, timeout=40):
    p = board.bench("wait-event", "dut", pattern, "--timeout", str(timeout), "--reset")
    assert p.returncode == 0, p.stdout + p.stderr
    return next(ln for ln in p.stdout.splitlines() if re.search(pattern, ln))


def test_hello_logs_the_rate_the_duration_and_the_hash_of_its_pcm_without_playing_it():
    """FR-EXM-01: one sentence in the default voice; the hash is the host build's for the same sentence."""
    _example("hello")
    line = _log(r"espk-hello: rate=\d+ duration_ms=\d+ sha256=[0-9a-f]{64}")
    f = dict(kv.split("=") for kv in line.split("espk-hello: ")[1].split())
    assert f["rate"] == "22050" and int(f["duration_ms"]) > 500
    assert f["sha256"] == r3host.run(f"init en\nvoice en\nsay {HELLO}\n")[0]["sha256"]


def test_the_waveshare_example_speaks_pt_br_through_the_codec_at_volume_5():
    """FR-EXM-03: the sentence in pt-BR through the ES8311, volume 5, no underrun; the hash of the engine's
    PCM is the host build's for the same sentence."""
    _example("waveshare-s3-rlcd")
    line = _log(r"espk-ws: said voice=pt-br volume=5 underrun=\d+ .* sha256=[0-9a-f]{64}")
    f = dict(kv.split("=") for kv in line.split("espk-ws: said ")[1].split())
    assert f["volume"] == "5" and f["underrun"] == "0" and f["codec_rate"] == f["engine_rate"] == "22050"
    sentence = "Atenção: a bateria está fraca."
    assert f["sha256"] == r3host.run(f"init en\nvoice pt-br\nsay {sentence}\n")[0]["sha256"]
