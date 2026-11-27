# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-CAP-11 (the capacity numbers of the README are the generated ones) and CON-PLT-04 (the README says,
per chip, "verified on the board" only for the ESP32-S3 and "built in CI" for the chips the CI builds)."""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/docs"))
sys.path.insert(0, str(ROOT / "tools/ref"))
import capacity_table  # noqa: E402
import r1  # noqa: E402


def _block(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    a = text.index(capacity_table.START)
    return text[a : text.index(capacity_table.END) + len(capacity_table.END)]


def test_the_capacity_block_of_each_readme_is_the_generated_one():
    generated = capacity_table.table(r1.build(r1.upstream()) / "espeak-ng-data")
    assert _block("README.md") == generated
    assert _block("README.pt-BR.md") == generated


def test_the_readme_levels_per_chip_match_what_the_ci_builds():
    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    chips = set(ci["jobs"]["examples"]["strategy"]["matrix"]["chip"])
    assert chips == {"esp32", "esp32s2", "esp32s3", "esp32p4"}
    for name, verified, built in (
        ("README.md", "verified on the board", "built in CI"),
        ("README.pt-BR.md", "verificado na placa", "compilado no CI"),
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        rows = {m.group(1): m.group(2) for m in re.finditer(r"^\| ([^|]+?) \| ([^|]+?) \|$", text, re.M)}
        assert rows["ESP32-S3"].startswith(verified)
        other = next(v for k, v in rows.items() if "ESP32-P4" in k)
        assert other.startswith(built) and verified not in other
