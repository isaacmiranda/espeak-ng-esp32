# SPDX-License-Identifier: GPL-3.0-or-later
from bench import actions
from fakes import FakeClock, FakeSerial, Out


def test_reply_is_returned_after_echo_and_logs():
    out = Out()
    fake = FakeSerial([b"info\n", b"I (5) x: y\n", b"ESPK info rate=22050\n"])
    assert actions.command(fake, "info", out, clock=FakeClock()) == 0
    assert fake.written == b"info\n"
    assert out[-1].endswith("ESPK info rate=22050")


def test_timeout_is_reported():
    out = Out()
    assert actions.command(FakeSerial([b"info\n"]), "info", out, timeout=0.5,
                           clock=FakeClock(0.1)) == 3
    assert out[-1].startswith("TIMEOUT")


def test_partial_reply_is_not_a_reply():
    out = Out()
    assert actions.command(FakeSerial([b"ESPK inf"]), "info", out, timeout=0.5,
                           clock=FakeClock(0.1)) == 3


def test_long_line_is_written_in_small_chunks():
    fake = FakeSerial([b"ESPK done id=1\n"])
    actions.command(fake, "say " + "a" * 300, Out(), clock=FakeClock())
    assert max(len(w) for w in fake.writes) <= 64
    assert fake.written == ("say " + "a" * 300 + "\n").encode()


def test_volume_above_ceiling_refused_without_listening_session():
    assert actions.volume_guard("volume 11", 10, listening=False)
    assert actions.volume_guard("listen open 60", 10, listening=False)
    assert actions.volume_guard("volume 10", 10, listening=False) is None
    assert actions.volume_guard("volume 60", 10, listening=True) is None
    assert actions.volume_guard("say volume 99", 10, listening=False) is None


def test_no_ceiling_configured_refuses_any_volume():
    assert actions.volume_guard("volume 1", None, listening=True)
