# SPDX-License-Identifier: GPL-3.0-or-later
"""Semantically unpredictable sentences (Benoit et al., 1996) from a classified word list (FR-COR-05, 07).

    sus.py --words wordlist-en.tsv --count 50 --seed 20261126 [--lang en|pt-br] --out sentences.tsv

The sentences are grammatical and make no sense, so a listener cannot guess a word from its context. Five
syntactic models take turns; words are drawn with a seeded generator (random.Random: the same sequence on
every platform), without repeating a word of a class while the list lasts. The same seed and the same list
give the same bytes (FR-COR-07). Word list: tab separated, `class word [gender-or-feminine-form]`, classes
noun, adj, verb_t, verb_i, prep. For pt-br, nouns carry a gender (m|f) and adjectives their feminine form.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

MODELS = (
    ("det noun verb_t det noun", "M1"),
    ("det adj noun verb_t det noun", "M2"),
    ("det noun verb_t det adj noun", "M3"),
    ("det noun verb_i prep det noun", "M4"),
    ("det adj noun verb_i prep det noun", "M5"),
)


def load(path: Path) -> dict[str, list[tuple[str, ...]]]:
    words: dict[str, list[tuple[str, ...]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = tuple(line.split("\t"))
        words.setdefault(cols[0], []).append(cols[1:])
    for need in ("noun", "adj", "verb_t", "verb_i", "prep"):
        if not words.get(need):
            sys.exit(f"FATAL: the word list has no {need}")
    return words


class Pool:
    """Draws words without repeating one until the class is used up, then starts over (still seeded)."""

    def __init__(self, items, rng):
        self.items, self.rng, self.left = items, rng, []

    def draw(self):
        if not self.left:
            self.left = list(self.items)
            self.rng.shuffle(self.left)
        return self.left.pop()


def article(lang: str, gender: str) -> str:
    return "the" if lang == "en" else ("a" if gender == "f" else "o")


def generate(words, count: int, seed: int, lang: str = "en") -> list[tuple[str, str]]:
    rng = random.Random(seed)
    pools = {k: Pool(v, rng) for k, v in words.items()}
    out = []
    for n in range(count):
        pattern, label = MODELS[n % len(MODELS)]
        toks, nouns = [], []
        slots = pattern.split()
        for slot in slots:
            if slot == "noun":
                w = pools["noun"].draw()
                nouns.append(w)
                toks.append(w[0])
            elif slot == "adj":
                toks.append("\0adj")  # resolved after the noun it agrees with is known
            elif slot == "det":
                toks.append("\0det")
            else:
                toks.append(pools[slot].draw()[0])
        # agreement (pt-br) and articles, left to right: each det and adj looks at the next noun
        for i, slot in enumerate(slots):
            if slot in ("det", "adj"):
                j = next(k for k in range(i, len(slots)) if slots[k] == "noun")
                noun = nouns[sum(1 for s in slots[: j + 1] if s == "noun") - 1]
                gender = noun[0] if noun else "m"
                if slot == "det":
                    toks[i] = article(lang, gender)
                else:
                    adj = pools["adj"].draw()
                    toks[i] = (
                        adj[0] if lang == "en" or gender != "f" else (adj[1] if len(adj) > 1 else adj[0])
                    )
        sentence = " ".join(toks)
        out.append((label, sentence[0].upper() + sentence[1:] + "."))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--words", type=Path, required=True)
    ap.add_argument("--count", type=int, default=50)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--lang", choices=("en", "pt-br"), default="en")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    rows = generate(load(a.words), a.count, a.seed, a.lang)
    lines = [f"S{n:02d}\t{label}\t{text}" for n, (label, text) in enumerate(rows, 1)]
    a.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
