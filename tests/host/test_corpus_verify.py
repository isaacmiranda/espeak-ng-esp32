# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-COR-01, FR-COR-02: the verification corpus covers phenomena, not frequency.

Format: tests/corpus/verify/<voice>.tsv, one item per line: id<TAB>category<TAB>pair<TAB>text.
`pair` is the id of the accented item an unaccented item mirrors, or "-".
"""

import csv
import unicodedata
from pathlib import Path

import pytest

DIR = Path(__file__).resolve().parents[1] / "corpus/verify"
VOICES = ["pt-br", "en"]
CATEGORIES = {"accent", "number", "time", "date", "money", "punctuation", "abbreviation", "long"}
PT_ACCENTED = set("áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ")


def load(voice):
    path = DIR / f"{voice}.tsv"
    if not path.exists():
        pytest.xfail(f"not implemented: {path.name}")
    with open(path, encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.reader(fh, delimiter="\t") if r and not r[0].startswith("#")]
    assert all(len(r) == 4 for r in rows), "every line has id, category, pair, text"
    return [dict(id=r[0], category=r[1], pair=r[2], text=r[3]) for r in rows]


def strip_accents(text):
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


@pytest.mark.parametrize("voice", VOICES)
def test_size_and_categories(voice):
    items = load(voice)
    assert 45 <= len(items) <= 55
    assert len({i["id"] for i in items}) == len(items), "ids are unique"
    assert {i["category"] for i in items} >= CATEGORIES
    assert any(len(i["text"]) > 500 for i in items if i["category"] == "long")
    assert all("\t" not in i["text"] and i["text"].strip() == i["text"] for i in items)
    if voice == "pt-br":
        text = "".join(i["text"] for i in items)
        missing = PT_ACCENTED - set(text)
        assert not missing, f"accented letters not covered: {''.join(sorted(missing))}"
        money = " ".join(i["text"] for i in items if i["category"] == "money")
        assert "R$" in money
    else:
        assert "US$" in " ".join(i["text"] for i in items if i["category"] == "money") or \
               "$" in " ".join(i["text"] for i in items if i["category"] == "money")


def test_accented_items_have_unaccented_pairs():
    items = load("pt-br")
    by_id = {i["id"]: i for i in items}
    accented = [i for i in items if set(i["text"]) & PT_ACCENTED]
    pairs = {i["pair"]: i for i in items if i["pair"] != "-"}
    for a in accented:
        assert a["id"] in pairs, f"{a['id']} has no unaccented pair"
        pair = pairs[a["id"]]["text"]
        assert pair == strip_accents(a["text"]), f"pair of {a['id']} is not the stripped text"
    for p in pairs.values():
        assert p["pair"] in by_id, f"{p['id']} points at a missing item"
        assert not set(p["text"]) & PT_ACCENTED
