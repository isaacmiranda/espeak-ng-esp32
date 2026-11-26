# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from bench import actions
from bench.config import load
from bench.ports import BenchError, Found, resolve


def test_repository_bench_yaml_loads():
    b = load()
    assert b.role("dut").chip == "esp32s3"
    assert b.volume_ceiling == 10


def test_udev_rule_needs_a_recorded_serial(bench):
    with pytest.raises(BenchError, match="no serial"):
        actions.udev_rules(bench)


def test_udev_rule_binds_link_to_serial(bench_with_serial):
    (rule,) = actions.udev_rules(bench_with_serial)
    assert 'ATTRS{serial}=="AA:BB"' in rule and 'SYMLINK+="espk-dut"' in rule
    assert 'ATTRS{idVendor}=="303a"' in rule


def test_resolve_prefers_the_udev_link(bench):
    assert resolve(bench, "dut", devices=[], exists=lambda p: p == "/dev/espk-dut") == "/dev/espk-dut"


def test_resolve_without_link_or_device_is_a_precondition(bench):
    with pytest.raises(BenchError, match="not found"):
        resolve(bench, "dut", devices=[], exists=lambda p: False)


def test_resolve_falls_back_to_the_single_match(bench):
    dev = [Found("/dev/ttyACM3", 0x303A, 0x1001, "Z")]
    assert resolve(bench, "dut", devices=dev, exists=lambda p: False) == "/dev/ttyACM3"
