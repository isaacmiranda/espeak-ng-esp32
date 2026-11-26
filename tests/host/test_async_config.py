# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-ASY-06: the build fails with CONFIG_ESPK_TASK_STACK below 49 152 B (configure step only)."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FW = ROOT / "research/firmware"


def _configure(tmp_path, stack):
    if not (Path.home() / "esp/esp-idf-v5.5.5/export.sh").is_file():
        pytest.skip("not done (precondition): the pinned ESP-IDF is not installed")
    img = tmp_path / "img"
    img.write_bytes(b"x")
    defaults = tmp_path / "stack.defaults"
    defaults.write_text(f"CONFIG_ESPK_TASK_STACK={stack}\n")
    return subprocess.run(
        ["nice", "-n", "15", "ionice", "-c", "2", "-n", "7", str(ROOT / "scripts/idf.sh"), "env",
         f"ESPK_IMAGE={img}", "idf.py", "-B", str(tmp_path / "b"), "-G", "Ninja", "-D",
         f"SDKCONFIG={tmp_path / 'sdkconfig'}", f"-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;{defaults}",
         "reconfigure"],
        cwd=FW, capture_output=True, text=True, timeout=600)


def test_a_stack_below_the_floor_fails_the_build(tmp_path):
    p = _configure(tmp_path, 32768)
    assert p.returncode != 0 and "FR-ASY-06" in p.stdout + p.stderr, (p.stdout + p.stderr)[-800:]


def test_the_floor_itself_configures(tmp_path):
    p = _configure(tmp_path, 49152)
    assert p.returncode == 0, (p.stdout + p.stderr)[-800:]
