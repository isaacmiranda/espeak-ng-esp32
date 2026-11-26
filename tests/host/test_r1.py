# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-REF-01: R1 — the upstream built on the host from the pinned tarball."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R1 = ROOT / "tools/ref/r1.py"


ITEMS = ["Atenção: bateria fraca.", "São 14h30."]
ITEMS_EN = ["The battery is low.", "It is 2:30 pm."]


def run_r1(tmp_path, lang, items):
    corpus = tmp_path / f"{lang}.txt"
    corpus.write_text("\n".join(items) + "\n", encoding="utf-8")
    out = tmp_path / f"{lang}.jsonl"
    p = subprocess.run([sys.executable, str(R1), "--voice", lang, "--corpus", str(corpus), "--out", str(out)],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]


def test_r1_hash_and_phonemes_per_item_and_language(tmp_path):
    for lang, items in (("pt-br", ITEMS), ("en", ITEMS_EN)):
        recs = run_r1(tmp_path, lang, items)
        assert [r["item"] for r in recs] == list(range(len(items)))
        for r, text in zip(recs, items, strict=True):
            assert r["voice"] == lang and r["text"] == text
            assert re.fullmatch(r"[0-9a-f]{64}", r["sha256"])
            assert r["samples"] > 0 and r["rate"] == 22050
            assert r["phonemes"].strip()
            assert r["espeak"] == "1.52.0"
    # the same corpus twice gives the same hashes (a reference that drifts is no reference)
    assert run_r1(tmp_path, "en", ITEMS_EN) == run_r1(tmp_path, "en", ITEMS_EN)
