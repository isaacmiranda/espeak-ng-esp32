# SPDX-License-Identifier: GPL-3.0-or-later
from bench import actions
from bench.ports import open_port
from fakes import FakeSerial


def test_port_opens_with_both_lines_low():
    fake = FakeSerial()
    ser = open_port("/dev/x", factory=lambda url, do_not_open: fake)
    assert ser.open_lines == (False, False)


def test_reset_pulses_rts_with_dtr_low():
    fake = FakeSerial()
    actions.reset(fake, sleep=lambda s: None)
    assert fake.lines_log == [("dtr", False), ("rts", True), ("rts", False)]
