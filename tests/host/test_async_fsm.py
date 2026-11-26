# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-ASY-09: every (state x event) pair of the async layer's table (FSD 15.2) gives the table's state,
action and return code. The table below is transcribed row by row from the FSD; the unlisted pairs must
change nothing."""

import itertools
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "components/espeak-ng/src"

STATES = ["UNINIT", "IDLE", "SPEAKING", "CANCELLING"]
EVENTS = ["INIT_OK", "INIT_FAIL", "SAY", "SAY_TOO_BIG", "CANCEL", "DEINIT", "TEXT_END", "ENGINE_ERROR",
          "SYNTH_STOPPED"]

# (state, waiting, event) -> (new state, new waiting, result, actions)   capacity is 4 everywhere
TABLE = {
    ("UNINIT", 0, "INIT_OK"): ("IDLE", 0, "OK", "CREATE_TASK"),
    ("UNINIT", 0, "INIT_FAIL"): ("UNINIT", 0, "PASS", "-"),
    ("UNINIT", 0, "SAY"): ("UNINIT", 0, "INVALID_STATE", "-"),
    ("UNINIT", 0, "CANCEL"): ("UNINIT", 0, "INVALID_STATE", "-"),
    ("IDLE", 0, "SAY"): ("SPEAKING", 0, "OK", "ENQUEUE,EVT_START"),
    ("IDLE", 0, "SAY_TOO_BIG"): ("IDLE", 0, "INVALID_SIZE", "-"),
    ("IDLE", 0, "CANCEL"): ("IDLE", 0, "OK", "-"),
    ("IDLE", 0, "DEINIT"): ("UNINIT", 0, "OK", "END_TASK"),
    ("SPEAKING", 0, "SAY"): ("SPEAKING", 1, "OK", "ENQUEUE"),
    ("SPEAKING", 3, "SAY"): ("SPEAKING", 4, "OK", "ENQUEUE"),
    ("SPEAKING", 4, "SAY"): ("SPEAKING", 4, "NO_MEM", "-"),
    ("SPEAKING", 0, "TEXT_END"): ("IDLE", 0, "OK", "EVT_DONE"),
    ("SPEAKING", 2, "TEXT_END"): ("SPEAKING", 1, "OK", "EVT_DONE,EVT_START"),
    ("SPEAKING", 2, "CANCEL"): ("CANCELLING", 0, "OK", "STOP,CLEAR_QUEUE"),
    ("SPEAKING", 2, "ENGINE_ERROR"): ("IDLE", 0, "OK", "CLEAR_QUEUE,EVT_ERROR"),
    ("SPEAKING", 2, "DEINIT"): ("UNINIT", 0, "OK", "STOP,CLEAR_QUEUE,END_TASK"),
    ("CANCELLING", 0, "SYNTH_STOPPED"): ("IDLE", 0, "OK", "EVT_CANCELLED"),
    ("CANCELLING", 0, "SAY"): ("CANCELLING", 1, "OK", "ENQUEUE"),
    ("CANCELLING", 4, "SAY"): ("CANCELLING", 4, "NO_MEM", "-"),
    ("CANCELLING", 0, "CANCEL"): ("CANCELLING", 0, "OK", "-"),
    # not in the table, decided here (spec-delta proposal): a text too big is refused in every live state; a
    # say taken while CANCELLING speaks right after the CANCELLED; a deinit while CANCELLING ends the task
    ("SPEAKING", 1, "SAY_TOO_BIG"): ("SPEAKING", 1, "INVALID_SIZE", "-"),
    ("CANCELLING", 1, "SAY_TOO_BIG"): ("CANCELLING", 1, "INVALID_SIZE", "-"),
    ("CANCELLING", 2, "SYNTH_STOPPED"): ("SPEAKING", 1, "OK", "EVT_CANCELLED,EVT_START"),
    ("CANCELLING", 0, "DEINIT"): ("UNINIT", 0, "OK", "END_TASK"),
}


@pytest.fixture(scope="module")
def cli(tmp_path_factory):
    exe = tmp_path_factory.mktemp("fsm") / "fsm_cli"
    subprocess.run(["cc", "-O1", "-Wall", "-Werror", "-I", str(SRC), str(ROOT / "tests/host/fsm_cli.c"),
                    str(SRC / "espk_fsm.c"), "-o", str(exe)], check=True)
    return exe


def run(cli, rows):
    text = "".join(f"{s} {w} 4 {e}\n" for s, w, e in rows)
    out = subprocess.run([str(cli)], input=text, capture_output=True, text=True, check=True).stdout
    return [tuple(line.split()) for line in out.splitlines()]


def test_every_row_of_the_table(cli):
    got = run(cli, list(TABLE))
    for (key, want), g in zip(TABLE.items(), got, strict=True):
        assert (g[0], int(g[1]), g[2], g[3]) == want, f"{key}: got {g}, table says {want}"


def test_pairs_outside_the_table_change_nothing(cli):
    listed = {(s, e) for s, _w, e in TABLE}
    rows = [(s, 1, e) for s, e in itertools.product(STATES, EVENTS) if (s, e) not in listed]
    for (s, w, e), g in zip(rows, run(cli, rows), strict=True):
        assert (g[0], int(g[1]), g[2], g[3]) == (s, w, "INVALID_STATE", "-"), f"{s} {e}: {g}"
