# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import board


def pytest_collection_modifyitems(config, items):
    for item in items:
        item.add_marker(pytest.mark.bench)


@pytest.fixture(scope="session")
def flashed():
    """P1 of the testing standard: flash the artifact under test once per session."""
    art = board.artifact()
    p = board.bench("flash", "dut", str(art), timeout=300)
    if p.returncode == 4:
        pytest.skip(f"not done (precondition): {p.stderr.strip()}")
    assert p.returncode == 0, p.stdout + p.stderr
    return art
