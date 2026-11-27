# SPDX-License-Identifier: GPL-3.0-or-later
"""Records the answers of the internal listening, with a pseudonymous listener code (FR-LST-04).

    record.py enroll --key-file ~/keys/listeners.json --identity "who they are"     -> prints the code
    record.py add --responses test-results/listening.jsonl --listener L-1a2b --list 2 --item S07 \
                  --condition ppm175 --answer "the heard words"

The key that maps a person to a code lives in a file OUTSIDE the repository: the tool refuses a key path
inside it. The responses carry the code and nothing that identifies a person: only the fields below are
accepted. Data that could identify a listener never enters git (the responses default to test-results/,
which is ignored).
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

FIELDS = ("listener", "list", "item", "condition", "answer", "volume", "distance_cm", "noise_note")
REPO = Path(__file__).resolve().parents[2]


def inside_repo(path: Path) -> bool:
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=REPO, capture_output=True, text=True)
    top = Path(root.stdout.strip() or REPO).resolve()
    return top in path.resolve().parents or path.resolve() == top


def enroll(key_file: Path, identity: str) -> str:
    """The code of a person: always the same; a new one for a new person. The key stays out of the repo."""
    if inside_repo(key_file):
        sys.exit("FATAL: the key file must be outside the repository (it maps people to codes)")
    key = json.loads(key_file.read_text()) if key_file.exists() else {}
    if identity not in key:
        used = set(key.values())
        while True:
            code = "L-" + secrets.token_hex(2)
            if code not in used:
                break
        key[identity] = code
        key_file.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(key, indent=1, ensure_ascii=False) + "\n")
    return key[identity]


def add(responses: Path, record: dict) -> None:
    extra = set(record) - set(FIELDS)
    if extra:
        sys.exit(f"FATAL: fields not accepted (they could identify a person): {sorted(extra)}")
    for need in ("listener", "list", "item", "condition", "answer"):
        if need not in record:
            sys.exit(f"FATAL: missing {need}")
    if not str(record["listener"]).startswith("L-"):
        sys.exit("FATAL: the listener must be a pseudonymous code (L-xxxx), not a name")
    record = {**record, "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    responses.parent.mkdir(parents=True, exist_ok=True)
    with open(responses, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("enroll")
    e.add_argument("--key-file", type=Path, required=True)
    e.add_argument("--identity", required=True)
    r = sub.add_parser("add")
    r.add_argument("--responses", type=Path, default=REPO / "test-results/listening.jsonl")
    r.add_argument("--listener", required=True)
    r.add_argument("--list", type=int, required=True)
    r.add_argument("--item", required=True)
    r.add_argument("--condition", required=True)
    r.add_argument("--answer", required=True)
    r.add_argument("--volume", type=int)
    r.add_argument("--distance-cm", type=int, dest="distance_cm")
    r.add_argument("--noise-note", dest="noise_note")
    a = ap.parse_args(argv)
    if a.cmd == "enroll":
        print(enroll(a.key_file, a.identity))
    else:
        rec = {k: v for k, v in vars(a).items() if k not in ("cmd", "responses") and v is not None}
        add(a.responses, rec)
    return 0


if __name__ == "__main__":
    sys.exit(main())
