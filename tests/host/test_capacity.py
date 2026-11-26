# SPDX-License-Identifier: GPL-3.0-or-later
"""FSD 13: language selection and the capacity report (FR-CAP-01..09), through tools/capacity.py on the
real upstream data of R1. The tool is what the component's build runs; failing it fails the build."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "components/espeak-ng/tools/capacity.py"
MAP = ROOT / "research/firmware/build/espk_research.map"
sys.path.insert(0, str(ROOT / "tools/ref"))
sys.path.insert(0, str(ROOT / "components/espeak-ng/tools"))


@pytest.fixture(scope="module")
def data():
    import r1

    return r1.build(r1.upstream()) / "espeak-ng-data"


def run(data, *args, expect_ok=True):
    cmd = [sys.executable, str(TOOL), "--data", str(data), *args]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if expect_ok:
        assert p.returncode == 0, p.stdout + p.stderr
    return p


def test_the_menuconfig_offers_the_language_list_and_the_all_option():
    """FR-CAP-01: both options exist as text and bool, with a prompt (shown by menuconfig)."""
    k = (ROOT / "components/espeak-ng/Kconfig").read_text()
    assert re.search(r'config ESPK_LANGUAGES\n\s+string "', k)
    assert re.search(r'config ESPK_LANGUAGES_ALL\n\s+bool "', k)


def test_an_unknown_language_fails_with_the_valid_names(data):
    """FR-CAP-02."""
    p = run(data, "--languages", "pt-br xx", "--default-voice", "pt-br", expect_ok=False)
    assert p.returncode != 0 and "xx" in p.stderr
    assert "pt-br" in p.stderr and "en" in p.stderr, "the message does not list the valid names"


def test_the_default_list_is_english_only(data, tmp_path):
    """FR-CAP-03: with no list the image has en and no other language."""
    import gen_image

    out = tmp_path / "e.img"
    run(data, "--out", str(out))
    names = set(gen_image.read(out.read_bytes()))
    assert "en_dict" in names and not any(n.endswith(("pt_dict", "de_dict", "fr_dict")) for n in names)
    assert sum(n.startswith("lang/") for n in names) == 1


def test_the_initial_voice_must_be_in_the_list(data):
    """FR-CAP-04."""
    p = run(data, "--languages", "en", "--default-voice", "pt-br", expect_ok=False)
    assert p.returncode != 0 and "pt-br" in p.stderr and "en" in p.stderr


def test_the_report_has_the_four_items(data, tmp_path):
    """FR-CAP-05: image and partition size, PSRAM peak, internal static RAM of the component, task stack."""
    if not MAP.is_file():
        pytest.skip("not done (precondition): no built espk_research.map")
    rep = tmp_path / "r.json"
    run(
        data,
        "--languages",
        "pt-br en",
        "--default-voice",
        "pt-br",
        "--partition-bytes",
        str(0x9E0000),
        "--map",
        str(MAP),
        "--task-stack",
        "65536",
        "--task-stack-psram",
        "y",
        "--report",
        str(rep),
    )
    r = json.loads(rep.read_text())
    assert r["image_bytes"] > 0 and r["partition_bytes"] == 0x9E0000
    assert r["psram_peak_bytes"] > 700_000
    assert r["static_ram_internal_bytes"] >= 0 and r["static_ram_internal_bytes"] < 30_000, r
    assert r["task_stack_bytes"] == 65536 and r["task_stack_in"] == "psram"


def test_an_image_larger_than_the_partition_fails_with_the_sizes(data):
    """FR-CAP-06: ALL languages into 1 MiB."""
    p = run(data, "--all", "--default-voice", "en", "--partition-bytes", str(1 << 20), expect_ok=False)
    assert p.returncode != 0
    m = re.search(r"image (\d+) B.*partition (\d+) B.*over by (\d+) B", p.stderr.replace("\n", " "))
    assert m and int(m.group(1)) - int(m.group(2)) == int(m.group(3)), p.stderr


def test_a_peak_above_the_budget_fails(data):
    """FR-CAP-07: budget 512 KB, list en + pt-br."""
    p = run(data, "--languages", "en pt-br", "--default-voice", "en", "--budget-kb", "512", expect_ok=False)
    assert p.returncode != 0 and "512" in p.stderr and "PSRAM" in p.stderr


def test_a_partition_91_percent_full_warns_and_builds(data, tmp_path):
    """FR-CAP-08: the image at 91 % of the partition -> a warning, exit 0; at 80 % no warning."""
    import gen_image

    size = len(gen_image.build(data, ["en"]))
    p = run(
        data, "--languages", "en", "--default-voice", "en", "--partition-bytes", str(int(size / 0.91) + 1)
    )
    assert "WARNING" in p.stdout + p.stderr and "91." in p.stdout + p.stderr
    p = run(data, "--languages", "en", "--default-voice", "en", "--partition-bytes", str(int(size / 0.80)))
    assert "WARNING" not in p.stdout + p.stderr


def test_the_report_follows_the_files_not_a_table(data, tmp_path):
    """FR-CAP-09: make pt_dict 100 000 bytes bigger and the report grows by that much."""
    mod = tmp_path / "data"
    mod.mkdir()
    for f in data.iterdir():
        os.symlink(f, mod / f.name)
    os.remove(mod / "pt_dict")
    (mod / "pt_dict").write_bytes((data / "pt_dict").read_bytes() + b"\0" * 100_000)
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    args = ("--languages", "pt-br", "--default-voice", "pt-br")
    run(data, *args, "--report", str(a))
    run(mod, *args, "--report", str(b))
    ra, rb = json.loads(a.read_text()), json.loads(b.read_text())
    assert rb["image_bytes"] - ra["image_bytes"] == 100_000
    assert rb["psram_peak_bytes"] - ra["psram_peak_bytes"] == 100_000
