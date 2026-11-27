# SPDX-License-Identifier: GPL-3.0-or-later
"""Builds the listening corpus files tests/corpus/listen/<lang>.tsv (FR-COR-04, FR-COR-05).

    build_listen.py --lang en [--seed 20261126]

en: 50 semantically unpredictable sentences (tools/corpus/sus.py over wordlist-en.tsv) and 30 everyday
sentences written for this project (daily-en.txt). pt-br: the 30 everyday sentences; the 200-word list and
the 50 unpredictable sentences wait for the choice of the frequency list (FR-COR-04). The seed is written
in the file. Each row: id, category, text. Same seed, same bytes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sus

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "tests/corpus/listen"
DEFAULT_SEED = 20261126
SPDX = "SPDX-License" + "-Identifier: GPL-3.0-or-later"  # the header of the file written, not of this one


def build(lang: str, seed: int) -> str:
    daily = [ln for ln in (HERE / f"daily-{lang}.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
    rows = [f"D{n:02d}\tdaily\t{t}" for n, t in enumerate(daily, 1)]
    head = [
        "# " + SPDX,
        f"# Listening corpus {lang} (FR-COR-04, FR-COR-05): id, category, text.",
        "# Built by tools/corpus/build_listen.py; do not edit by hand.",
        "# daily: everyday sentences of a device that speaks, written for this project.",
    ]
    if lang == "en":
        words = sus.load(HERE / "wordlist-en.tsv")
        unpredictable = sus.generate(words, 50, seed, "en")
        rows = [f"S{n:02d}\tsus-{label}\t{text}" for n, (label, text) in enumerate(unpredictable, 1)] + rows
        head.append(f"# sus: semantically unpredictable sentences (Benoit et al., 1996 method), seed {seed}.")
    else:
        head.append(
            "# pending (FR-COR-04): the 200 most frequent words and the 50 unpredictable sentences "
            "wait for the choice of the pt-BR frequency list."
        )
    return "\n".join(head + rows) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lang", choices=("en", "pt-br"), required=True)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{a.lang}.tsv").write_text(build(a.lang, a.seed), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
