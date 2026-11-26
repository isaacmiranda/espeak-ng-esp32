# SPDX-License-Identifier: GPL-3.0-or-later
"""Helpers for target and bench tests: everything goes through `python -m bench` (never a raw port)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/bench"))
from bench.lines import parse_marker  # noqa: E402


def bench(*args: str, timeout: float = 120) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "bench", *args], cwd=ROOT, capture_output=True,
                          text=True, timeout=timeout)


def markers(text: str) -> list:
    out = []
    for line in text.splitlines():
        m = parse_marker(line.split(" ", 1)[1] if " " in line else line)
        if m:
            out.append(m)
    return out


def artifact() -> Path:
    """The artifact under test: ESPK_ARTIFACT (CI release) — never a guess."""
    a = os.environ.get("ESPK_ARTIFACT")
    if not a or not (Path(a) / "flash_args").is_file():
        pytest.skip("not done (precondition): ESPK_ARTIFACT does not name an artifact with flash_args")
    return Path(a)


def boot(timeout: float = 30) -> dict:
    """Reset with the listener open; return {event: Marker} of everything up to ESPK ready/error."""
    p = bench("wait-event", "dut", r"^ESPK (ready|error)", "--timeout", str(timeout), "--reset")
    if p.returncode == 4:
        pytest.skip(f"not done (precondition): {p.stderr.strip()}")
    return {m.event: m for m in markers(p.stdout)}, p


def command(line: str, expect: str = r"^ESPK ", timeout: float = 30):
    p = bench("command", "dut", line, "--expect", expect, "--timeout", str(timeout))
    if p.returncode == 4:
        pytest.skip(f"not done (precondition): {p.stderr.strip()}")
    ms = markers(p.stdout)
    return (ms[-1] if ms else None), p
