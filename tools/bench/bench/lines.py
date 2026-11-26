# SPDX-License-Identifier: GPL-3.0-or-later
"""Line framing and marker parsing for the firmware's serial output.

Markers are one line each: ``ESPK <event> key=value ...`` (FSD FR-LOG-01).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


class LineReader:
    """Splits a byte stream into lines; keeps a partial line until it completes."""

    def __init__(self) -> None:
        self._buf = b""

    def feed(self, data: bytes) -> list[str]:
        self._buf += data
        *done, self._buf = self._buf.split(b"\n")
        return [d.decode("utf-8", "replace").rstrip("\r") for d in done]

    @property
    def pending(self) -> str:
        return self._buf.decode("utf-8", "replace")


@dataclass
class Marker:
    event: str
    fields: dict[str, str] = field(default_factory=dict)


def parse_marker(line: str) -> Marker | None:
    """``ESPK done id=3 sha256=ab`` -> Marker('done', {...}); anything else -> None."""
    parts = line.strip().split()
    if len(parts) < 2 or parts[0] != "ESPK":
        return None
    fields = {}
    for tok in parts[2:]:
        if "=" not in tok:
            return None  # a malformed marker is not a marker
        k, v = tok.split("=", 1)
        fields[k] = v
    return Marker(parts[1], fields)


def read_lines(ser, deadline: float, clock=time.monotonic):
    """Yield complete lines from ``ser`` until ``deadline`` (monotonic seconds)."""
    reader = LineReader()
    while clock() < deadline:
        data = ser.read(ser.in_waiting or 1)
        if data:
            yield from reader.feed(data)
