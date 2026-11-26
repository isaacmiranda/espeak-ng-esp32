# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests that need the board run only with --run-bench (docs/Method/project/bancada.md).

Without it they are skipped, never failed: a bench that is not there is `not done`.
"""

import pytest


def pytest_addoption(parser):
    parser.addoption("--run-bench", action="store_true", default=False,
                     help="run tests that need the board on the bench notebook")


def pytest_configure(config):
    config.addinivalue_line("markers", "bench: needs the board on the bench notebook (--run-bench)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-bench"):
        return
    skip = pytest.mark.skip(reason="not done: needs the bench (--run-bench)")
    for item in items:
        if "bench" in item.keywords:
            item.add_marker(skip)
