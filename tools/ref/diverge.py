# SPDX-License-Identifier: GPL-3.0-or-later
"""Where and how much two PCM streams differ (FR-REF-04, FR-REF-06).

    diverge.py a.pcm b.pcm

16-bit signed little-endian mono. Prints, as JSON, whether they are equal, the index of the first sample
that differs, the greatest absolute difference per sample, and the SNR in dB of b against a as the
reference. Streams of different length differ at the first index past the shorter one.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path


def samples(b: bytes) -> tuple[int, ...]:
    return struct.unpack(f"<{len(b) // 2}h", b[: len(b) // 2 * 2])


def compare(a: bytes, b: bytes) -> dict:
    x, y = samples(a), samples(b)
    n = min(len(x), len(y))
    first = next((i for i in range(n) if x[i] != y[i]), None)
    if first is None and len(x) != len(y):
        first = n
    diffs = [abs(x[i] - y[i]) for i in range(n)]
    noise = sum((x[i] - y[i]) ** 2 for i in range(n)) + sum(v * v for v in (x[n:] if len(x) > n else y[n:]))
    signal = sum(v * v for v in x)
    snr = math.inf if noise == 0 else (-math.inf if signal == 0 else 10 * math.log10(signal / noise))
    return {
        "equal": first is None,
        "first_divergent_sample": first,
        "max_abs_diff": max(diffs, default=0),
        "snr_db": None if math.isinf(snr) and snr > 0 else snr,
        "samples_a": len(x),
        "samples_b": len(y),
    }


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print(__doc__.splitlines()[0], file=sys.stderr)
        return 2
    r = compare(Path(argv[0]).read_bytes(), Path(argv[1]).read_bytes())
    print(json.dumps(r))
    return 0 if r["equal"] else 1


if __name__ == "__main__":
    sys.exit(main())
