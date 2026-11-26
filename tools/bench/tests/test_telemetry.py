# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime

from bench import actions
from bench.lines import LineReader, parse_marker
from fakes import FakeClock, FakeSerial, Out


def test_complete_lines_are_stamped():
    out = Out()
    fake = FakeSerial([b"ESPK boot fw=0.0.1\r\nESPK ready\n"])
    actions.telemetry(fake, 1.0, out, clock=FakeClock())
    assert [o.split(" ", 1)[1] for o in out] == ["ESPK boot fw=0.0.1", "ESPK ready"]


def test_truncated_line_waits_for_its_end():
    r = LineReader()
    assert r.feed(b"ESPK do") == []
    assert r.feed(b"ne id=1\nESPK st") == ["ESPK done id=1"]
    assert r.pending == "ESPK st"


def test_interleaved_log_and_marker_lines():
    r = LineReader()
    got = r.feed(b"I (123) espk: init\nESPK ready\nW (124) x: y\n")
    assert [parse_marker(g) for g in got][1].event == "ready"
    assert parse_marker(got[0]) is None and parse_marker(got[2]) is None


def test_marker_fields_and_malformed_marker():
    m = parse_marker("ESPK done id=3 samples=100 sha256=ab12")
    assert m.event == "done" and m.fields == {"id": "3", "samples": "100", "sha256": "ab12"}
    assert parse_marker("ESPK done id=3 garbage") is None


def test_invalid_utf8_does_not_break_framing():
    assert LineReader().feed(b"\xffESPK ready\n") == ["�ESPK ready"]


def test_stamp_format():
    t = datetime(2026, 11, 26, 12, 0, 0, 5000, tzinfo=UTC)
    assert actions.stamp("x", now=t) == "2026-11-26T12:00:00.005+00:00 x"
