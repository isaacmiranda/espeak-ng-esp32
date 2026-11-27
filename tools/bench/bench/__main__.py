# SPDX-License-Identifier: GPL-3.0-or-later
"""python -m bench <command> — the only way this project touches the board.

Exit codes: 0 ok · 1 failed · 2 refused/usage · 3 timeout (not done) · 4 bench precondition unmet.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import actions
from .config import load
from .ports import BenchError, list_devices, open_port, resolve


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bench", description=__doc__)
    p.add_argument("--config", help="bench.yaml (default: repository root)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("discover", help="list roles of bench.yaml with the device found")
    s = sub.add_parser("chip-info", help="chip, revision, flash, PSRAM and MAC")
    s.add_argument("role")
    s = sub.add_parser("flash", help="write an artifact using its flash_args")
    s.add_argument("role")
    s.add_argument("artifact", type=Path)
    s = sub.add_parser("reset", help="hard reset through the native USB lines")
    s.add_argument("role")
    s = sub.add_parser("telemetry", help="print timestamped lines from the board")
    s.add_argument("role")
    s.add_argument("--seconds", type=float, default=10.0)
    s = sub.add_parser("command", help="send one console line and print the reply")
    s.add_argument("role")
    s.add_argument("line")
    s.add_argument("--timeout", type=float, default=5.0)
    s.add_argument("--expect", default=r"^ESPK ")
    s.add_argument("--listening", action="store_true",
                   help="a listening session with people present: allows volume above the ceiling")
    s = sub.add_parser("wait-event", help="open the listener, optionally reset, wait for a pattern")
    s.add_argument("role")
    s.add_argument("pattern")
    s.add_argument("--timeout", type=float, required=True)
    s.add_argument("--reset", action="store_true", help="reset after the listener is open")
    sub.add_parser("udev-rule", help="print the udev rules for the roles of bench.yaml")
    a = p.parse_args(argv)

    out = print
    try:
        bench = load(a.config)
        if a.cmd == "discover":
            return actions.discover(bench, list_devices(), out)
        if a.cmd == "udev-rule":
            for r in actions.udev_rules(bench):
                out(r)
            return actions.OK
        port = resolve(bench, a.role)
        role = bench.role(a.role)
        if a.cmd == "chip-info":
            return actions.chip_info(port, actions.run_capture, out, expect=role)
        if a.cmd == "flash":
            why = actions.flash_sound_guard(Path(a.artifact), bench.sound_apps, bench.sound_allowed)
            if why:
                print(f"REFUSED: {why}", file=sys.stderr)
                return actions.REFUSED
            return actions.flash(a.artifact, port, role.chip,
                                 lambda argv: subprocess.call(argv), out)
        if a.cmd == "command":
            why = actions.sound_guard(a.line, bench.sound_allowed) or actions.volume_guard(
                a.line, bench.volume_ceiling, a.listening)
            if why:
                print(f"REFUSED: {why}", file=sys.stderr)
                return actions.REFUSED
        with open_port(port) as ser:
            if a.cmd == "reset":
                actions.reset(ser)
                return actions.OK
            if a.cmd == "telemetry":
                return actions.telemetry(ser, a.seconds, out)
            if a.cmd == "command":
                return actions.command(ser, a.line, out, a.timeout, a.expect)
            if a.cmd == "wait-event":
                act = (lambda: actions.reset(ser)) if a.reset else None
                return actions.wait_event(ser, a.pattern, a.timeout, out, act)
    except BenchError as e:
        print(f"BENCH: {e}", file=sys.stderr)
        return actions.PRECONDITION
    return actions.REFUSED


if __name__ == "__main__":
    sys.exit(main())
