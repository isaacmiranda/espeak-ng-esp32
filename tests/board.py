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


def r1_run(script: str) -> list[dict]:
    """R1 (the upstream on the host) running the same script."""
    sys.path.insert(0, str(ROOT / "tools/ref"))
    import r1
    return r1.run(script)


def verify_script() -> str:
    """The verification corpus as a script: the steps the board takes from a reset (FSD §7)."""
    lines = ["init en"]
    for voice in ("pt-br", "en"):
        lines.append(f"voice {voice}")
        for row in (ROOT / f"tests/corpus/verify/{voice}.tsv").read_text(encoding="utf-8").splitlines():
            if row and not row.startswith("#"):
                lines.append("say " + row.split("\t")[3])
    return "\n".join(lines) + "\n"


def board_run(script: str, timeout: float = 30) -> list[dict]:
    """Reset the board, then take the script's steps one by one; one record per `say`."""
    ms, p = boot(timeout)
    assert "ready" in ms, p.stdout
    steps = [ln.partition(" ") for ln in script.splitlines() if ln.strip()]
    assert steps[0][0] == "init", "a script starts with init"
    records = []
    for cmd, _, arg in steps[1:]:
        if cmd == "voice":
            m, _p = command(f"voice {arg}", r"^ESPK voice")
            assert m and m.fields == {"ok": arg}, f"voice {arg}: {m}"
        elif cmd == "say":
            m, _p = command(f"say --mute {arg}", r"^ESPK (done|error)")
            assert m and m.event == "done", f"say {arg!r}: {m}"
            assert int(m.fields["bytes"]) == len(arg.encode()), f"bytes lost on the console line: {m.fields}"
            records.append({"text": arg, "sha256": m.fields["sha256"], "samples": int(m.fields["samples"])})
        else:
            raise AssertionError(f"the board has no step {cmd!r} yet")
    return records


def compare(board_recs: list[dict], r1_recs: list[dict]) -> list[dict]:
    """Say by say: the items where the board's PCM differs from R1's."""
    assert len(board_recs) == len(r1_recs)
    return [{"item": k, "text": b["text"][:50], "board_samples": b["samples"], "r1_samples": r["samples"]}
            for k, (b, r) in enumerate(zip(board_recs, r1_recs, strict=True)) if b["sha256"] != r["sha256"]]
