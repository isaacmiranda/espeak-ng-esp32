# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-COR-04: the pt-BR listening corpus holds the 200 most frequent words of the pinned Leipzig list (no
one-letter word), 50 unpredictable sentences built from words of that list with gender agreement, and the 30
everyday sentences; the file is what the generator makes from its recorded seed, byte for byte."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parent
sys.path.insert(0, str(ROOT / "tools/corpus"))
import build_listen  # noqa: E402
import leipzig  # noqa: E402
import sus  # noqa: E402

FILE = ROOT / "tests/corpus/listen/pt-br.tsv"


def rows():
    return [
        ln.split("\t")
        for ln in FILE.read_text(encoding="utf-8").splitlines()
        if ln and not ln.startswith("#")
    ]


def test_the_list_is_pinned_by_sha256_and_labelled_as_not_specific_to_pt_br():
    assert re.fullmatch(r"[0-9a-f]{64}", leipzig.SHA256)
    assert leipzig.NAME == "por_news_2022_10K" and "não específica de pt-BR" in leipzig.LABEL
    assert "não específica de pt-BR" in FILE.read_text(encoding="utf-8")
    assert "CC-BY-4.0" in FILE.read_text(encoding="utf-8").splitlines()[0]


def test_the_corpus_has_200_words_50_sentences_and_30_daily_and_no_one_letter_word():
    r = rows()
    words = [x[2] for x in r if x[1] == "word"]
    assert len(words) == 200 and len(set(words)) == 200
    assert all(len(w) > 1 for w in words)
    assert words == leipzig.top(200)
    assert sum(x[1].startswith("sus-") for x in r) == 50 and sum(x[1] == "daily" for x in r) == 30


def test_every_word_of_the_sentences_is_a_word_of_the_leipzig_list_and_genders_agree():
    known = {w for w, _ in leipzig.frequency()}
    lists = sus.load(ROOT / "tools/corpus/wordlist-pt-br.tsv")
    gender = {n[0]: n[1] for n in lists["noun"]}
    for cls in lists.values():
        for entry in cls:
            assert all(w in known for w in entry if w not in ("m", "f")), entry
    adjectives = {a[0]: a[1] for a in lists["adj"]}
    forms = {f for f in adjectives.values()}
    for _id, _cat, text in (x for x in rows() if x[1].startswith("sus-")):
        toks = text.rstrip(".").lower().split()
        assert all(t in known or t in ("o", "a") for t in toks), text
        for i, tok in enumerate(toks):
            if tok not in ("o", "a"):
                continue
            j = i + 1
            if toks[j] in adjectives or toks[j] in forms:
                j += 1
            assert toks[j] in gender, text
            assert (tok == "a") == (gender[toks[j]] == "f"), text
            if j == i + 2:  # an adjective between: its form follows the noun's gender
                masculine = next(m for m, f in adjectives.items() if toks[i + 1] in (m, f))
                want = adjectives[masculine] if gender[toks[j]] == "f" else masculine
                assert toks[i + 1] == want, text


def test_the_committed_file_is_what_the_generator_makes_from_its_seed():
    assert FILE.read_text(encoding="utf-8") == build_listen.build("pt-br", build_listen.DEFAULT_SEED)
    tool = str(ROOT / "tools/corpus/build_listen.py")
    assert subprocess.run([sys.executable, tool, "--help"], capture_output=True).returncode == 0
