# SPDX-License-Identifier: GPL-3.0-or-later
from bench import actions
from fakes import FakeClock, FakeSerial, Out


def test_pattern_already_flowing():
    out = Out()
    fake = FakeSerial([b"ESPK boot fw=1\n", b"ESPK ready\n"])
    assert actions.wait_event(fake, r"ESPK ready", 1.0, out, clock=FakeClock()) == 0


def test_listener_is_open_before_the_reset():
    out = Out()
    fake = FakeSerial(after_reset=[b"ESPK boot fw=1\n"])
    act = lambda: actions.reset(fake, sleep=lambda s: None)  # noqa: E731
    assert actions.wait_event(fake, r"^ESPK boot", 1.0, out, action=act, clock=FakeClock()) == 0


def test_pattern_never_seen_is_not_done():
    out = Out()
    fake = FakeSerial([b"ESPK boot fw=1\n"])
    assert actions.wait_event(fake, r"ESPK ready", 0.5, out, clock=FakeClock(0.1)) == 3
    assert out[-1].startswith("NOT DONE")


def test_pattern_after_timeout_is_not_seen():
    out = Out()
    fake = FakeSerial([b""] * 20 + [b"ESPK ready\n"])
    assert actions.wait_event(fake, r"ESPK ready", 0.5, out, clock=FakeClock(0.1)) == 3
