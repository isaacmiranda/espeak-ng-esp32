# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-ERR-01, FR-ERR-02, FR-SEC-01, FR-LOG-01: the public functions never panic on bad input, a refused
call does not disturb the next synthesis, the text limit holds everywhere, the markers keep their format."""

import re
import time

import board

PT = "Atenção: a bateria está fraca."
OVER = "x" * 1025  # one byte above CONFIG_ESPK_MAX_TEXT_LEN

HOSTILE = [
    "say ", "say --mute ", "synth ", "rate", "rate 99999999999999999999", "rate -5", "voice ",
    "voice ../../etc", "voice " + "a" * 200, "cut", "cut x y", "cut -1 hi", "cut 0", "vfs", "vfs ",
    "vfs /espeak", "vfs /espeak/", "vfswrite ", "vfswrite /nowhere", "volume 1e9", "volume -0", "listen",
    "listen open x", "listen close extra", "cancel", "cancel now", "init extra", "deinit extra",
    "taskinfo extra", "info extra", "\x01\x02", "say \x1b[31m",
]


def _ready():
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    return ms


def test_hostile_console_input_never_resets_the_board(flashed):
    """FR-ERR-01: bad input gets an answer or silence, never a panic or a reset (alive keeps counting)."""
    _ready()
    t0 = time.monotonic()
    for line in HOSTILE:
        _m, p = board.command(line, r"^ESPK (?!alive)", timeout=3)  # an answer or the timeout: both fine
        assert "Guru Meditation" not in p.stdout and "Rebooting" not in p.stdout, (line, p.stdout)
    elapsed = time.monotonic() - t0
    q = board.bench("wait-event", "dut", r"^ESPK alive n=\d+", "--timeout", "5")
    n = int(re.search(r"alive n=(\d+)", q.stdout).group(1))
    assert n >= elapsed - 3, f"alive counter {n} after {elapsed:.0f} s: the board reset"
    m, _p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    assert m.event == "done", "the board no longer speaks after the barrage"


def test_a_text_over_the_limit_is_refused_on_the_sync_entry_and_the_next_synthesis_is_clean(flashed):
    """FR-SEC-01 (the limit on every public entry: here espk_synth(); the console stops espk_say() earlier)
    and FR-ERR-02 (the synthesis after the refused call is R1's, from a script without the refused step)."""
    _ready()
    m, _p = board.command(f"synth {OVER}", r"^ESPK (sync|error)", timeout=30)
    assert m.event == "error" and m.fields["code"] == "ESP_ERR_INVALID_SIZE", m
    m, _p = board.command(f"say --mute {OVER}", r"^ESPK (done|error)", timeout=30)
    assert m.event == "error" and m.fields["code"] == "too_long", m
    m, _p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    assert m.event == "done"
    expected = board.r1_run(f"init en\nvoice en\nsay {PT}\n")[0]["sha256"]
    assert m.fields["sha256"] == expected


# FR-LOG-01: a marker is one line, `ESPK <event> key=value ...`, no space inside a value; the fields below are
# the order today. A field is only ever added at the end: the golden list must stay a prefix of what is seen.
GOLDEN = {
    "boot": ["fw", "commit", "idf", "espeak", "rate", "bss", "langs", "init_ms"],
    "queued": ["id", "queue_us"],
    "done": ["id", "samples", "synth_ms", "first_ms", "audio_ms", "heap_min", "sha256", "bytes", "underrun"],
    "cancelled": ["id", "cancel_ms"],
    "info": ["fw", "idf", "espeak", "rate", "image_bytes", "image_crc", "langs", "voice", "rate_ppm", "pitch",
             "volume"],
    "mem": ["internal_free", "internal_min", "psram_free", "psram_min"],
    "cut": ["calls", "result"],
    "sync": ["sha256", "bytes"],
    "taskinfo": ["stack", "psram", "hwm"],
    "vfs": ["size", "head", "tail", "end", "back", "close"],
    "vfswrite": ["open", "create"],
    "init": ["result", "heap"],
    "deinit": ["result", "heap"],
}
LINE = re.compile(r"^ESPK [a-z_]+( [a-z_0-9]+=\S*)*$")


def test_the_markers_keep_their_format_and_field_order(flashed):
    long_text = " ".join([PT] * 29)
    ms = _ready()
    seen = {"boot": ms["boot"]}
    raw = []

    def run(line, expect, timeout=30):
        m, p = board.command(line, expect, timeout=timeout)
        raw.extend(ln.split(" ", 1)[1] for ln in p.stdout.splitlines() if " ESPK " in ln)
        for mk in board.markers(p.stdout):
            seen.setdefault(mk.event, mk)
        return m

    run(f"say --mute {PT}", r"^ESPK (done|error)")
    run(f"say --mute {long_text}", r"^ESPK (queued|error)")
    run("cancel", r"^ESPK (cancelled|done)", 10)
    for line, expect in [("info", r"^ESPK info"), ("mem", r"^ESPK mem"), (f"cut 2 {PT}", r"^ESPK cut"),
                         (f"synth {PT}", r"^ESPK sync"), ("taskinfo", r"^ESPK taskinfo"),
                         ("vfs /espeak/phontab", r"^ESPK vfs"),
                         ("vfswrite /espeak/phontab", r"^ESPK vfswrite"),
                         ("deinit", r"^ESPK deinit"), ("init", r"^ESPK init")]:
        run(line, expect)
    bad = [ln for ln in raw if ln.startswith("ESPK ") and not LINE.match(ln)]
    assert not bad, f"markers off the format: {bad[:3]}"
    for event, golden in GOLDEN.items():
        assert event in seen, f"no {event} marker seen"
        names = list(seen[event].fields)
        assert names[:len(golden)] == golden, f"{event}: fields {names}, the golden prefix is {golden}"
