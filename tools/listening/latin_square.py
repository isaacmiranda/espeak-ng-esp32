# SPDX-License-Identifier: GPL-3.0-or-later
"""Presentation lists in a Latin square, by speed condition (FR-LST-02).

    latin_square.py --items tests/corpus/listen/en.tsv --conditions ppm140,ppm175,ppm210 --seed 20261126 \
                    --out lists.json

K conditions, N items (N a multiple of K). The items are shuffled and cut into K blocks; list j gives block
b the condition (b + j) mod K of a shuffled condition order, so across the K lists every item is heard once
in every condition, and inside a list every condition has N / K items. The trials of a list are then
shuffled. Everything comes from the seed (random.Random), written in the output: the same seed gives the
same lists.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path


def lists(items: list[str], conditions: list[str], seed: int) -> dict:
    k = len(conditions)
    if k < 2 or len(set(conditions)) != k:
        sys.exit("FATAL: at least two different conditions are needed")
    if len(items) % k or len(set(items)) != len(items):
        sys.exit(f"FATAL: {len(items)} items cannot be cut into {k} equal blocks of different items")
    rng = random.Random(seed)
    shuffled = list(items)
    rng.shuffle(shuffled)
    size = len(items) // k
    blocks = [shuffled[b * size : (b + 1) * size] for b in range(k)]
    order = list(conditions)
    rng.shuffle(order)
    out = []
    for j in range(k):
        trials = [
            {"item": item, "condition": order[(b + j) % k]}
            for b, block in enumerate(blocks)
            for item in block
        ]
        rng.shuffle(trials)
        out.append({"list": j + 1, "trials": trials})
    return {"seed": seed, "conditions": conditions, "lists": out}


def item_ids(path: Path) -> list[str]:
    rows = [
        ln.split("\t")
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln and not ln.startswith("#")
    ]
    return [r[0] for r in rows]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--items", type=Path, required=True, help="a corpus TSV: id, category, text")
    ap.add_argument("--conditions", required=True, help="comma separated, e.g. ppm140,ppm175,ppm210")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    result = lists(item_ids(a.items), a.conditions.split(","), a.seed)
    a.out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
