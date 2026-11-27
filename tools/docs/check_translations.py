# SPDX-License-Identifier: GPL-3.0-or-later
"""Checks the translations of the FSD's table of documents (FR-DOC-01, FR-DOC-02).

    check_translations.py [--root DIR] [--release]

Every translation must carry `source-revision: <hash>` in its first lines. With --release it must also be
current: no commit after that hash may have touched the source. Exit 0 when all hold, 1 otherwise, with one
line per problem.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

REV = re.compile(r"source-revision:\s*([0-9a-f]{7,40})\b")


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def check(root: Path, release: bool) -> list[str]:
    problems = []
    table = yaml.safe_load((root / "tools/docs/translations.yaml").read_text())["translations"]
    for row in table:
        src, tr = row["source"], row["translation"]
        path = root / tr
        if not path.is_file():
            problems.append(f"{tr}: the translation of {src} does not exist")
            continue
        head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:5])
        m = REV.search(head)
        if not m:
            problems.append(f"{tr}: no `source-revision: <hash>` in the first lines")
            continue
        rev = m.group(1)
        if not release:
            continue
        if git(root, "cat-file", "-e", f"{rev}^{{commit}}").returncode != 0:
            problems.append(f"{tr}: source-revision {rev} is not a commit of this repository")
            continue
        newer = git(root, "log", "--format=%h %s", f"{rev}..HEAD", "--", src).stdout.strip()
        if newer:
            listing = newer.replace("\n", "\n    ")
            problems.append(f"{tr}: {src} changed after source-revision {rev}:\n    {listing}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--release", action="store_true")
    a = ap.parse_args(argv)
    problems = check(a.root, a.release)
    for p in problems:
        print(f"FATAL: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
