# SPDX-License-Identifier: GPL-3.0-or-later
"""Corpora (FSD 8): the automatic corpus (FR-COR-03), the English listening corpus (FR-COR-05), the licence of
every corpus file (FR-COR-06) and the determinism of the sentence generator (FR-COR-07)."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/corpus"))
import auto_corpus  # noqa: E402
import build_listen  # noqa: E402
import sus  # noqa: E402

WORDS = ROOT / "tools/corpus/wordlist-en.tsv"


def rows(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln.split("\t") for ln in lines if ln and not ln.startswith("#")]


def test_the_automatic_corpus_is_numerals_a_date_and_a_time_and_nothing_else():
    """FR-COR-03: 0 1 2 3 4 5 6 7 8 9 10 100 1000, 2026-11-26 and 14:30, no natural-language text."""
    lines = (ROOT / "tests/corpus/auto/auto.txt").read_text().splitlines()
    numerals = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "100", "1000"]
    assert lines == [*numerals, "2026-11-26", "14:30"]
    assert all(re.fullmatch(r"[0-9:\-]+", ln) for ln in lines), "a letter is in the automatic corpus"
    assert (ROOT / "tests/corpus/auto/auto.txt").read_text() == auto_corpus.text()


def test_the_generator_is_deterministic():
    """FR-COR-07: the same seed and the same list give the same bytes; another seed gives another file."""
    words = sus.load(WORDS)
    a = sus.generate(words, 50, 7)
    assert a == sus.generate(words, 50, 7)
    assert a != sus.generate(words, 50, 8)
    tool = str(ROOT / "tools/corpus/sus.py")
    cmd = [sys.executable, tool, "--words", str(WORDS), "--count", "50", "--seed", "7"]
    out1, out2 = (ROOT / "test-results" / n for n in ("sus1.tsv", "sus2.tsv"))
    out1.parent.mkdir(exist_ok=True)
    subprocess.run([*cmd, "--out", str(out1)], check=True)
    subprocess.run([*cmd, "--out", str(out2)], check=True)
    assert out1.read_bytes() == out2.read_bytes()


def test_the_english_listening_corpus_has_50_unpredictable_and_30_everyday_sentences():
    """FR-COR-05: the committed file is what the generator makes from its recorded seed, byte for byte."""
    path = ROOT / "tests/corpus/listen/en.tsv"
    seed = int(re.search(r"seed (\d+)", path.read_text()).group(1))
    assert path.read_text(encoding="utf-8") == build_listen.build("en", seed)
    r = rows(path)
    assert sum(x[1].startswith("sus-") for x in r) == 50 and sum(x[1] == "daily" for x in r) == 30
    texts = [x[2] for x in r]
    assert len(set(texts)) == len(texts), "a repeated sentence"
    known = {w[0] for ws in sus.load(WORDS).values() for w in ws} | {"the", "The"}
    for rid, cat, text in r:
        if cat.startswith("sus-"):
            words = re.findall(r"[A-Za-z']+", text)
            assert all(w.lower() in known for w in words), f"{rid}: a word outside the list: {text}"
            assert text.endswith(".") and text[0].isupper()


def test_every_corpus_file_has_a_registered_licence_and_no_protected_material_is_in():
    """FR-COR-06: reuse knows a licence for each file of the corpora, and the protected sets are absent."""
    reuse = str(ROOT / ".venv/bin/reuse")
    p = subprocess.run([reuse, "lint", "--json"], cwd=ROOT, capture_output=True, text=True)
    d = json.loads(p.stdout)
    corpus = [f for f in d["files"] if f["path"].startswith(("tests/corpus/", "tools/corpus/"))]
    assert len(corpus) >= 8, "the corpus files were not found"
    unlicensed = [f["path"] for f in corpus if not f["spdx_expressions"]]
    assert not unlicensed, unlicensed
    banned = [f["path"] for f in d["files"] if re.search(r"(^|/)(lsp|alcaim|harvard)[^/]*$", f["path"], re.I)
              and not f["path"].startswith(("seed/", ".claude/"))]
    assert not banned, f"material without a registered permission: {banned}"
