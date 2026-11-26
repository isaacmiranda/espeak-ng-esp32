# SPDX-License-Identifier: GPL-3.0-or-later
from bench import actions
from bench.ports import Found
from fakes import Out

S3 = (0x303A, 0x1001)


def test_role_found_by_vid_pid_when_no_serial_recorded(bench):
    out = Out()
    assert actions.discover(bench, [Found("/dev/ttyACM0", *S3, "AA:BB")], out) == 0
    assert out == ["dut /dev/ttyACM0 serial=AA:BB vid_pid=303a:1001"]


def test_missing_required_role_fails(bench):
    out = Out()
    assert actions.discover(bench, [Found("/dev/ttyUSB0", 0x10C4, 0xEA60, "x")], out) == 4
    assert out == ["dut MISSING (required)"]


def test_two_candidates_without_serial_is_ambiguous(bench):
    out = Out()
    devs = [Found("/dev/ttyACM0", *S3, "AA"), Found("/dev/ttyACM1", *S3, "BB")]
    assert actions.discover(bench, devs, out) == 4
    assert out[0].startswith("dut AMBIGUOUS")


def test_recorded_serial_selects_the_board_among_extras(bench_with_serial):
    out = Out()
    devs = [Found("/dev/ttyACM0", *S3, "OTHER"), Found("/dev/ttyACM1", *S3, "AA:BB")]
    assert actions.discover(bench_with_serial, devs, out) == 0
    assert "/dev/ttyACM1" in out[0]


def test_recorded_serial_absent_is_missing(bench_with_serial):
    out = Out()
    assert actions.discover(bench_with_serial, [Found("/dev/ttyACM0", *S3, "OTHER")], out) == 4
