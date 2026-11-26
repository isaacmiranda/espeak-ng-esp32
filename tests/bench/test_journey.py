# SPDX-License-Identifier: GPL-3.0-or-later
"""The journey (FSD §28.1): one workflow test per step, in order.

JRN-03 (audio) and JRN-06 (cancel) arrive with those features.
"""

import json
import subprocess
import sys

import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import board

pytestmark = pytest.mark.bench
PT = "Atenção: a bateria está fraca."
EN = "Attention: the battery is low."


def r1_hash(voice, text, tmp_path):
    c = tmp_path / f"{voice}.txt"
    c.write_text(text + "\n", encoding="utf-8")
    out = tmp_path / f"{voice}.jsonl"
    subprocess.run([sys.executable, str(board.ROOT / "tools/ref/r1.py"), "--voice", voice,
                    "--corpus", str(c), "--out", str(out)], check=True)
    return json.loads(out.read_text(encoding="utf-8").splitlines()[0])["sha256"]


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


def test_jrn_04_pt_br_hash_equals_r1(flashed, tmp_path):
    board.boot()
    m, p = board.command(f"say --mute {PT}", r"^ESPK (done|error)")
    assert m.event == "done", p.stdout
    assert m.fields["sha256"] == r1_hash("pt-br", PT, tmp_path)


def test_jrn_05_en_hash_equals_r1(flashed, tmp_path):
    m, _ = board.command("voice en", r"^ESPK voice")
    assert m.fields == {"ok": "en"}
    m, p = board.command(f"say --mute {EN}", r"^ESPK (done|error)")
    assert m.event == "done", p.stdout
    assert m.fields["sha256"] == r1_hash("en", EN, tmp_path)
