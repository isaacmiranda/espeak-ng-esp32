# SPDX-License-Identifier: GPL-3.0-or-later
"""The driver's commands. Each takes its I/O as parameters so it is testable
without a board (tools/bench/tests/)."""

from __future__ import annotations

import re
import shlex
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from .config import Bench
from .lines import LineReader, read_lines
from .ports import BenchError, Found, match

OK, FAIL, REFUSED, TIMEOUT, PRECONDITION = 0, 1, 2, 3, 4


# --- discover ---------------------------------------------------------------

def discover(bench: Bench, devices: list[Found], out) -> int:
    """One line per role. Missing required role or an ambiguous match fails."""
    status = OK
    for name, role in sorted(bench.roles.items()):
        hits = match(role, devices)
        if len(hits) == 1:
            h = hits[0]
            out(f"{name} {h.device} serial={h.serial} vid_pid={h.vid:04x}:{h.pid:04x}")
        elif not hits:
            out(f"{name} MISSING{' (required)' if role.required else ''}")
            if role.required:
                status = PRECONDITION
        else:
            out(f"{name} AMBIGUOUS {' '.join(h.device for h in hits)}")
            status = PRECONDITION
    return status


# --- chip-info --------------------------------------------------------------

_CHIP = re.compile(r"Chip (?:type|is):?\s+(ESP32-[A-Z0-9]+)", re.I)
_REV = re.compile(r"revision v?(\d+\.\d+)", re.I)
_MAC = re.compile(r"MAC:\s+([0-9a-f:]{17})", re.I)
_FLASH = re.compile(r"Detected flash size:\s+(\d+)MB", re.I)
_PSRAM = re.compile(r"(?:Embedded )?PSRAM (\d+)MB", re.I)


def parse_chip_info(text: str) -> dict[str, str]:
    info = {}
    for key, rx in (("chip", _CHIP), ("revision", _REV), ("mac", _MAC),
                    ("flash_mb", _FLASH), ("psram_mb", _PSRAM)):
        m = rx.search(text)
        if m:
            info[key] = m.group(1).lower() if key in ("chip", "mac") else m.group(1)
    return info


def chip_info(port: str, run, out, expect=None) -> int:
    """esptool flash-id gives chip, revision, features (PSRAM), MAC and flash size."""
    text = run(["esptool", "--port", port, "--before", "default-reset",
                "--after", "hard-reset", "flash-id"])
    info = parse_chip_info(text)
    for k in ("chip", "revision", "flash_mb", "psram_mb", "mac"):
        out(f"{k}={info.get(k, 'unknown')}")
    if "chip" not in info or "mac" not in info:
        return FAIL
    if expect is not None:
        want = {"chip": expect.chip.replace("esp32", "esp32-"), "flash_mb": str(expect.flash_mb)}
        for k, v in want.items():
            if info.get(k) != v:
                out(f"MISMATCH {k}: bench.yaml says {v}, board says {info.get(k)}")
                return FAIL
        if expect.psram and "psram_mb" not in info:
            out("MISMATCH psram: bench.yaml says yes, board reports none")
            return FAIL
    return OK


# --- flash ------------------------------------------------------------------

def flash_argv(artifact: Path, port: str, chip: str, baud: int = 460800) -> list[str]:
    """esptool argv from the build's flash_args. Offsets are never guessed."""
    fa = artifact / "flash_args"
    if not fa.is_file():
        raise BenchError(f"{artifact} has no flash_args: not a build artifact")
    lines = [ln.strip() for ln in fa.read_text().splitlines() if ln.strip()]
    opts, pairs = [], []
    for ln in lines:
        toks = shlex.split(ln)
        if toks[0].startswith("--"):
            opts += toks
            continue
        if len(toks) != 2 or not toks[0].lower().startswith("0x"):
            raise BenchError(f"flash_args line without offset: {ln!r}")
        path = artifact / toks[1]
        if not path.is_file():
            raise BenchError(f"flash_args names {toks[1]}, missing from {artifact}")
        pairs += [toks[0], str(path)]
    if not pairs:
        raise BenchError("flash_args lists no image")
    return ["esptool", "--chip", chip, "--port", port, "--baud", str(baud),
            "--before", "default-reset", "--after", "hard-reset", "write-flash", *opts, *pairs]


def flash(artifact: Path, port: str, chip: str, call, out) -> int:
    argv = flash_argv(artifact, port, chip)
    out(" ".join(argv))
    return OK if call(argv) == 0 else FAIL


# --- reset ------------------------------------------------------------------

def reset(ser, sleep=time.sleep) -> None:
    """Native USB hard reset: hold EN low through RTS with DTR low (normal boot)."""
    ser.dtr = False
    ser.rts = True
    sleep(0.1)
    ser.rts = False


# --- telemetry, command, wait-event -----------------------------------------

def stamp(line: str, now=None) -> str:
    t = now or datetime.now(UTC)
    return f"{t.isoformat(timespec='milliseconds')} {line}"


def telemetry(ser, seconds: float, out, clock=time.monotonic) -> int:
    for line in read_lines(ser, clock() + seconds, clock):
        out(stamp(line))
    return OK


_VOLUME = re.compile(r"^\s*(?:volume|listen\s+open)\s+(\d+)\b")


def volume_guard(cmd: str, ceiling: int | None, listening: bool) -> str | None:
    """Refuse a volume above the bench ceiling unless a listening session is declared."""
    m = _VOLUME.match(cmd)
    if not m:
        return None
    if ceiling is None:
        return "bench.yaml has no bench_volume_ceiling: refusing any volume command"
    if int(m.group(1)) > ceiling and not listening:
        return (f"volume {m.group(1)} is above the bench ceiling {ceiling}; "
                "only a listening session with people present (--listening) may raise it")
    return None


def command(ser, cmd: str, out, timeout: float = 5.0, expect: str = r"^ESPK ",
            clock=time.monotonic) -> int:
    """Send one console line; print lines until one matches ``expect``."""
    data = (cmd.rstrip("\n") + "\n").encode()
    for i in range(0, len(data), 64):  # small writes: the device RX buffer is short
        ser.write(data[i:i + 64])
    ser.flush()
    rx = re.compile(expect)
    for line in read_lines(ser, clock() + timeout, clock):
        out(stamp(line))
        if rx.search(line):
            return OK
    out(f"TIMEOUT after {timeout}s waiting for /{expect}/")
    return TIMEOUT


def wait_event(ser, pattern: str, timeout: float, out, action=None,
               clock=time.monotonic) -> int:
    """Open the listener first, then act (e.g. reset), then wait for the pattern.

    A timeout is `not done` (exit 3), never a failure of the requirement.
    """
    rx = re.compile(pattern)
    reader = LineReader()
    deadline = clock() + timeout
    if action is not None:
        action()
    while clock() < deadline:
        data = ser.read(ser.in_waiting or 1)
        for line in reader.feed(data) if data else ():
            out(stamp(line))
            if rx.search(line):
                return OK
    out(f"NOT DONE: /{pattern}/ not seen in {timeout}s")
    return TIMEOUT


# --- udev-rule --------------------------------------------------------------

def udev_rules(bench: Bench) -> list[str]:
    rules = []
    for name, role in sorted(bench.roles.items()):
        if not role.serial:
            raise BenchError(f"role {name!r} has no serial in bench.yaml; "
                             "run `bench discover` with the board and record it first")
        rules.append(
            f'SUBSYSTEM=="tty", ATTRS{{idVendor}}=="{role.vid:04x}", '
            f'ATTRS{{idProduct}}=="{role.pid:04x}", ATTRS{{serial}}=="{role.serial}", '
            f'SYMLINK+="{bench.link(name).removeprefix("/dev/")}", MODE="0660", GROUP="dialout"')
    return rules


def run_capture(argv: list[str]) -> str:
    p = subprocess.run(argv, capture_output=True, text=True, check=False)
    return p.stdout + p.stderr
