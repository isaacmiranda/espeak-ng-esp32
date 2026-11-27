# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-LST-01 on the host source (the board source has its own test): WAV files per speed with pseudorandom
names and a map in a separate file. FR-REF-04: the divergence analysis of two PCM streams."""

import json
import re
import struct
import subprocess
import sys
import wave
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ref"))
import diverge  # noqa: E402

TOOL = str(ROOT / "tools/listening/samples.py")
CORPUS = ROOT / "tests/corpus/listen/en.tsv"


def run(tmp, seed, out="s", mapname="m/map.json", speeds="150,200", extra=()):
    return subprocess.run([sys.executable, TOOL, "--corpus", str(CORPUS), "--voice", "en", "--speeds", speeds,
                           "--seed", str(seed), "--out-dir", str(tmp / out), "--map-file", str(tmp / mapname),
                           "--source", "host", "--limit", "3", *extra], capture_output=True, text=True)


def test_one_wav_per_item_and_speed_with_a_pseudorandom_name_and_a_separate_map(tmp_path):
    p = run(tmp_path, 11)
    assert p.returncode == 0, p.stderr
    files = sorted((tmp_path / "s").glob("*.wav"))
    assert len(files) == 6  # 3 items x 2 speeds
    m = json.loads((tmp_path / "m/map.json").read_text())
    assert set(m["files"]) == {f.stem for f in files} and m["seed"] == 11
    for f in files:
        assert re.fullmatch(r"[0-9a-f]{12}", f.stem), "the name says something"
        with wave.open(str(f)) as w:
            fmt = (w.getnchannels(), w.getsampwidth(), w.getframerate())
            assert fmt == (1, 2, 22050) and w.getnframes() > 1000
    info = list(m["files"].values())
    assert {i["speed_ppm"] for i in info} == {150, 200}
    assert {i["item"] for i in info} == {"S01", "S02", "S03"}
    assert not (tmp_path / "s" / "map.json").exists()


def test_the_same_seed_gives_the_same_files_and_another_seed_other_names(tmp_path):
    run(tmp_path, 11, "a", "ma/map.json")
    run(tmp_path, 11, "b", "mb/map.json")
    run(tmp_path, 12, "c", "mc/map.json")
    names = lambda d: sorted(f.name for f in (tmp_path / d).glob("*.wav"))  # noqa: E731
    assert names("a") == names("b") and names("a") != names("c")
    assert all((tmp_path / "a" / n).read_bytes() == (tmp_path / "b" / n).read_bytes() for n in names("a"))


def test_the_map_must_not_sit_next_to_the_samples(tmp_path):
    p = run(tmp_path, 1, out="s", mapname="s/map.json")
    assert p.returncode != 0 and "map file must not be next to the samples" in p.stderr


def pcm(*values):
    return struct.pack(f"<{len(values)}h", *values)


def test_the_divergence_analysis_gives_the_first_sample_the_maximum_difference_and_the_snr():
    """FR-REF-04: item-level facts of a divergence between two PCM streams."""
    a = pcm(*([1000] * 10))
    assert diverge.compare(a, a) == {"equal": True, "first_divergent_sample": None, "max_abs_diff": 0,
                                     "snr_db": None, "samples_a": 10, "samples_b": 10}
    b = pcm(1000, 1000, 1000, 1010, 1000, 990, 1000, 1000, 1000, 1000)
    r = diverge.compare(a, b)
    assert r["equal"] is False and r["first_divergent_sample"] == 3 and r["max_abs_diff"] == 10
    assert r["snr_db"] == pytest.approx(10 * __import__("math").log10(10 * 1000**2 / 200))
    longer = diverge.compare(a, a + pcm(5))
    assert longer["first_divergent_sample"] == 10 and longer["samples_b"] == 11
