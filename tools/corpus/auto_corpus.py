# SPDX-License-Identifier: GPL-3.0-or-later
"""The automatic corpus (FR-COR-03): no text in a natural language, so it is the same for every language.

    auto_corpus.py --out tests/corpus/auto/auto.txt

The numerals 0 1 2 3 4 5 6 7 8 9 10 100 1000, the date 2026-11-26 and the time 14:30, one per line.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ITEMS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "100", "1000", "2026-11-26", "14:30"]


def text() -> str:
    return "\n".join(ITEMS) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
