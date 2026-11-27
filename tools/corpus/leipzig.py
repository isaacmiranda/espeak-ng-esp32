# SPDX-License-Identifier: GPL-3.0-or-later
"""The Leipzig Corpora Collection pt list used for the pt-BR listening corpus (FR-COR-04).

    leipzig.py [--top 200]

`por_news_2022_10K` is Portuguese news text (10 000 sentences, Leipzig Corpora Collection, CC BY 4.0). It is
**Portuguese, not specific to pt-BR**: the label of every file derived from it says so. The tarball is
downloaded once into the cache and its SHA-256 is checked before anything is read. The frequency list folds
case, keeps only alphabetic tokens and drops the one-letter words; ties break alphabetically (same bytes
every time).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tarfile
import urllib.request
from collections import Counter
from pathlib import Path

NAME = "por_news_2022_10K"
URL = f"https://downloads.wortschatz-leipzig.de/corpora/{NAME}.tar.gz"
SHA256 = "59aeb4ab1d701d396c3d87e682c3a19b1670b836ce3b931ed5723db6bf1ba48b"
LABEL = "português (Leipzig), não específica de pt-BR"


def cache_dir() -> Path:
    base = os.environ.get("ESPK_CACHE") or os.path.join(
        os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "espk"
    )
    return Path(base) / "leipzig"


def tarball() -> Path:
    tgz = cache_dir() / f"{NAME}.tar.gz"
    if not tgz.exists():
        tgz.parent.mkdir(parents=True, exist_ok=True)
        part = tgz.with_suffix(".part")
        urllib.request.urlretrieve(URL, part)
        part.rename(tgz)
    got = hashlib.sha256(tgz.read_bytes()).hexdigest()
    if got != SHA256:
        sys.exit(f"FATAL: sha256 of {tgz} is {got}, expected {SHA256}")
    return tgz


def frequency() -> list[tuple[str, int]]:
    """(word, count) for the alphabetic words of two or more letters, most frequent first."""
    counts: Counter[str] = Counter()
    with tarfile.open(tarball()) as tf:
        member = tf.extractfile(f"{NAME}/{NAME}-words.txt")
        assert member is not None
        for line in member.read().decode("utf-8").splitlines():
            _id, word, n = line.split("\t")
            if word.isalpha() and len(word) > 1:
                counts[word.lower()] += int(n)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def top(n: int = 200) -> list[str]:
    return [w for w, _ in frequency()[:n]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--top", type=int, default=200)
    a = ap.parse_args(argv)
    print("\n".join(top(a.top)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
