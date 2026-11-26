# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from bench.config import parse

YAML = {
    "project": "espeak-ng-esp32",
    "link_prefix": "/dev/espk-",
    "audio": {"bench_volume_ceiling": 10},
    "roles": {"dut": {"board": "x", "chip": "esp32s3", "flash_mb": 16, "psram": True,
                      "vid_pid": "303a:1001", "serial": None, "required": True}},
}


@pytest.fixture
def bench():
    return parse(YAML)


@pytest.fixture
def bench_with_serial():
    y = {**YAML, "roles": {"dut": {**YAML["roles"]["dut"], "serial": "AA:BB"}}}
    return parse(y)
