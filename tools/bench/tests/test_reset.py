# SPDX-License-Identifier: GPL-3.0-or-later
from bench import actions
from bench.ports import open_port
from fakes import FakeSerial


def test_open_never_passes_through_the_reset_state():
    # the kernel raises DTR and RTS together on open; the driver must lower RTS first
    fake = FakeSerial()
    fake._dtr = fake._rts = True
    open_port("/dev/x", factory=lambda url, do_not_open: fake)
    assert fake.lines_log == [("rts", False), ("dtr", False)]
    state = {"dtr": True, "rts": True}
    for line, value in fake.lines_log:
        state[line] = value
        assert not (state["rts"] and not state["dtr"]), "DTR low with RTS high resets the chip"


def test_reset_pulses_rts_with_dtr_low():
    fake = FakeSerial()
    actions.reset(fake, sleep=lambda s: None)
    assert fake.lines_log == [("dtr", False), ("rts", True), ("rts", False)]
