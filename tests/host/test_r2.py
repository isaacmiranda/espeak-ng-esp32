# SPDX-License-Identifier: GPL-3.0-or-later
"""R2, the eSpeak NG of the system, against R1 (FSD 7: FR-REF-05, 06, 07), through tools/ref/r2.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = str(ROOT / "tools/ref/r2.py")

pytestmark = pytest.mark.skipif(
    not Path("/usr/bin/espeak-ng").exists(), reason="not done (precondition): no system espeak-ng"
)


def run(tmp_path, *args):
    out = tmp_path / "r2.json"
    p = subprocess.run([sys.executable, TOOL, *args, "--report", str(out)], capture_output=True, text=True)
    return p, json.loads(out.read_text()) if out.exists() else None


def test_r2_compares_the_api_and_the_cli_of_r1_and_the_system_package(tmp_path):
    """FR-REF-05: PCM of the API, PCM and phonemes of the CLI, per voice; the package version recorded."""
    p, rep = run(tmp_path, "--voices", "pt-br,en,de", "--cli")
    assert p.returncode == 0, p.stderr
    assert rep["system_package"].startswith("espeak-ng 1.52.0") and rep["r1"] == "1.52.0"
    assert rep["items"] == 15 and rep["compared"] == 3 * 15 * 2  # per voice: 15 API pairs and 15 CLI pairs
    assert rep["divergences"] == [] and rep["errors"] == []


def test_a_divergence_is_a_report_row_and_does_not_fail_the_run(tmp_path):
    """FR-REF-06: voice, item, kind, greatest difference per sample, SNR and an attributed cause; exit 0."""
    p, rep = run(tmp_path, "--voices", "fo")
    assert p.returncode == 0
    rows = rep["divergences"]
    assert len(rows) == 15
    for r in rows:
        assert set(r) == {"voice", "item", "entry", "kind", "max_abs_diff", "snr_db", "cause"}
        assert r["voice"] == "fo" and r["kind"] == "pcm" and r["entry"] == "api"
        assert r["cause"] != "unattributed" and "no dictionary" in r["cause"]
    json.dumps(rep, allow_nan=False)  # a valid JSON report: no -Infinity


def test_r2_runs_for_every_voice_of_the_upstream_and_every_divergence_is_explained(tmp_path):
    """FR-REF-07 on the host: all voices through the API with the automatic corpus (the CLI pass over all
    voices is the CI's job, `r2.py --all --cli`)."""
    p, rep = run(tmp_path, "--all")
    assert p.returncode == 0, p.stderr
    assert len(rep["voices"]) >= 141 and rep["items"] == 15 and rep["errors"] == []
    unexplained = [r for r in rep["divergences"] if r["cause"] == "unattributed"]
    assert not unexplained, f"{len(unexplained)} divergences without a cause, first: {unexplained[0]}"
