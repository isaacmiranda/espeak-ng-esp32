# SPDX-License-Identifier: GPL-3.0-or-later
"""The listening tools that need no board: the Latin-square lists (FR-LST-02), the answer recorder
(FR-LST-04)."""

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/listening"))
import latin_square  # noqa: E402
import record  # noqa: E402

ITEMS = [f"S{n:02d}" for n in range(1, 51)] + [f"D{n:02d}" for n in range(1, 31)]  # the 80 of the en corpus
COND = ["ppm140", "ppm175", "ppm210"]


def test_the_lists_are_a_latin_square_over_the_speed_conditions():
    """FR-LST-02 with 81 items (a multiple of the 3 conditions)."""
    items = [*ITEMS, "X01"]
    r = latin_square.lists(items, COND, seed=20261126)
    assert len(r["lists"]) == 3
    per_item = {i: [] for i in items}
    for lst in r["lists"]:
        assert sorted(t["item"] for t in lst["trials"]) == sorted(items), "an item is not once in a list"
        counts = Counter(t["condition"] for t in lst["trials"])
        assert set(counts.values()) == {len(items) // 3}
        for t in lst["trials"]:
            per_item[t["item"]].append(t["condition"])
    assert all(sorted(c) == sorted(COND) for c in per_item.values()), "an item misses a condition"


def test_the_lists_come_from_the_recorded_seed():
    a = latin_square.lists(ITEMS[:60], COND, 5)
    assert a == latin_square.lists(ITEMS[:60], COND, 5) and a["seed"] == 5
    assert a != latin_square.lists(ITEMS[:60], COND, 6)


def test_items_that_do_not_fit_the_blocks_are_refused():
    with pytest.raises(SystemExit):
        latin_square.lists(ITEMS, COND, 1)  # 80 items, 3 conditions
    with pytest.raises(SystemExit):
        latin_square.lists(ITEMS[:60], ["a", "a", "b"], 1)


def test_the_cli_writes_the_lists_for_a_corpus_file(tmp_path):
    out = tmp_path / "lists.json"
    corpus = tmp_path / "c.tsv"
    corpus.write_text("".join(f"{i}\tx\ttext\n" for i in ITEMS[:78]))
    tool = str(ROOT / "tools/listening/latin_square.py")
    subprocess.run([sys.executable, tool, "--items", str(corpus), "--conditions", "a,b,c", "--seed", "3",
                    "--out", str(out)], check=True)
    assert json.loads(out.read_text())["seed"] == 3


def test_the_key_file_inside_the_repository_is_refused(tmp_path):
    """FR-LST-04: the key that names people stays outside the repository."""
    with pytest.raises(SystemExit):
        record.enroll(ROOT / "test-results/key.json", "Maria da Silva")
    assert record.enroll(tmp_path / "key.json", "Maria da Silva").startswith("L-")


def test_a_person_gets_the_same_code_and_the_responses_carry_no_identity(tmp_path):
    key, resp = tmp_path / "key.json", tmp_path / "r.jsonl"
    a = record.enroll(key, "Maria da Silva")
    b = record.enroll(key, "João Souza")
    assert a != b and record.enroll(key, "Maria da Silva") == a
    row = {"listener": a, "list": 2, "item": "S07", "condition": "ppm175", "answer": "the words"}
    record.add(resp, row)
    text = resp.read_text()
    assert a in text and "Maria" not in text and "Silva" not in text
    assert (key.stat().st_mode & 0o777) == 0o600


def test_fields_that_could_identify_a_person_are_refused(tmp_path):
    base = {"listener": "L-0001", "list": 1, "item": "S01", "condition": "c", "answer": "x"}
    for bad in ({"name": "Maria"}, {"email": "a@b.c"}, {"identity": "Maria"}):
        with pytest.raises(SystemExit):
            record.add(tmp_path / "r.jsonl", {**base, **bad})
    with pytest.raises(SystemExit):
        record.add(tmp_path / "r.jsonl", {**base, "listener": "Maria"})  # a name instead of a code
    assert not (tmp_path / "r.jsonl").exists()
