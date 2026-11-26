# SPDX-License-Identifier: GPL-3.0-or-later
"""A fake serial port and a fake clock: the driver is tested without a board."""

from __future__ import annotations


class FakeClock:
    def __init__(self, step: float = 0.01) -> None:
        self.t = 0.0
        self.step = step

    def __call__(self) -> float:
        self.t += self.step
        return self.t


class FakeSerial:
    """Records control-line changes and writes; serves scripted input chunks.

    ``chunks`` are returned one per read; ``after_action`` chunks become
    readable only once ``rts`` has gone high and low again (a reset).
    """

    def __init__(self, chunks=(), after_reset=()) -> None:
        self._chunks = list(chunks)
        self._after_reset = list(after_reset)
        self.lines_log: list[tuple[str, bool]] = []
        self.written = b""
        self.writes: list[bytes] = []
        self.is_open = False
        self.open_lines = None
        self._dtr = None
        self._rts = None
        self.baudrate = None
        self.timeout = None

    # control lines
    @property
    def dtr(self):
        return self._dtr

    @dtr.setter
    def dtr(self, v):
        self._dtr = v
        self.lines_log.append(("dtr", v))

    @property
    def rts(self):
        return self._rts

    @rts.setter
    def rts(self, v):
        if self._rts and not v and self._after_reset:
            self._chunks += self._after_reset
            self._after_reset = []
        self._rts = v
        self.lines_log.append(("rts", v))

    def open(self):
        self.open_lines = (self._dtr, self._rts)
        self.is_open = True

    def close(self):
        self.is_open = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    @property
    def in_waiting(self):
        return len(self._chunks[0]) if self._chunks else 0

    def read(self, n=1):
        return self._chunks.pop(0) if self._chunks else b""

    def write(self, data):
        self.writes.append(bytes(data))
        self.written += data
        return len(data)

    def flush(self):
        pass


class Out(list):
    def __call__(self, line):
        self.append(line)
