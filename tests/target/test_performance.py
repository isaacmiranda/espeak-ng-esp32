# SPDX-License-Identifier: GPL-3.0-or-later
"""NFR-SYN-01..04 on the reference board, idle, the engine's .bss in the default place (PSRAM), 175 ppm,
over the pt-BR verification corpus. FR-RES-04: --mute and sound give the same PCM hash."""

import re
import time

import board

CORPUS = board.ROOT / "tests/corpus/verify/pt-br.tsv"
PT = "Atenção: a bateria está fraca."


def _items():
    rows = []
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            rid, _cat, _pair, text = line.split("\t")[:4]
            rows.append((rid, text))
    return rows


def _start_pt_br():
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    m, _p = board.command("voice pt-br", r"^ESPK voice")
    assert m.fields == {"ok": "pt-br"}


def _say(text):
    m, p = board.command(f"say --mute {text}", r"^ESPK (done|error)", timeout=60)
    assert m and m.event == "done", (text[:40], p.stdout)
    return {k: int(v) if v.isdigit() else v for k, v in m.fields.items()}


def test_every_item_synthesises_at_half_real_time_or_better_and_starts_within_300_ms(flashed):
    """NFR-SYN-01 (RTF <= 0.5 per item) and NFR-SYN-02 (first PCM <= 300 ms for sentences of <= 20 words)."""
    _start_pt_br()
    slow, late, rows = [], [], []
    for rid, text in _items():
        d = _say(text)
        rtf = d["synth_ms"] / d["audio_ms"]
        rows.append((rid, round(rtf, 3), d["first_ms"]))
        if rtf > 0.5:
            slow.append((rid, round(rtf, 3)))
        if len(text.split()) <= 20 and d["first_ms"] > 300:
            late.append((rid, d["first_ms"]))
    out = board.ROOT / "test-results"
    out.mkdir(exist_ok=True)
    table = "item\trtf\tfirst_ms\n" + "".join(f"{a}\t{b}\t{c}\n" for a, b, c in rows)
    (out / "performance-pt-br.tsv").write_text(table)
    assert not slow, f"RTF above 0.5: {slow}"
    assert not late, f"first block later than 300 ms: {late}"


def test_the_longest_text_does_not_trigger_the_watchdog(flashed):
    """NFR-SYN-03: a text of more than 500 characters from the corpus synthesises with the default 5 s task
    watchdog: no reset (the boot counter does not restart) and the done line arrives."""
    _start_pt_br()
    text = max((t for _r, t in _items()), key=len)
    assert len(text) > 500
    t0 = time.monotonic()
    d = _say(text)
    assert d["samples"] > 0
    q = board.bench("wait-event", "dut", r"^ESPK alive n=\d+", "--timeout", "5")
    n = int(re.search(r"alive n=(\d+)", q.stdout).group(1))
    assert n >= time.monotonic() - t0 - 3, "the board reset during the long synthesis"


def test_fifty_syntheses_in_a_row_leave_the_internal_heap_where_it_was(flashed):
    """NFR-SYN-04: 50 corpus items, no reset, and the internal heap free at the end no more than 1 KB below
    the start. (Read as "no leak": the first synthesis after a voice change frees 2 436 B of transient
    allocations, so the heap ends higher, which is no violation.) From the second synthesis on it is flat."""
    _start_pt_br()
    m, _p = board.command("mem", r"^ESPK mem")
    before = int(m.fields["internal_free"])
    t0 = time.monotonic()
    texts = [t for _r, t in _items()]
    steady = []
    for k in range(50):
        _say(texts[k % len(texts)])
        if k == 1:  # after the first synthesis the engine has settled
            m, _p = board.command("mem", r"^ESPK mem")
            steady.append(int(m.fields["internal_free"]))
    m, _p = board.command("mem", r"^ESPK mem")
    after = int(m.fields["internal_free"])
    q = board.bench("wait-event", "dut", r"^ESPK alive n=\d+", "--timeout", "5")
    n = int(re.search(r"alive n=(\d+)", q.stdout).group(1))
    assert n >= time.monotonic() - t0 - 3, "the board reset during the 50 syntheses"
    assert before - after <= 1024, f"internal heap {before} -> {after}: it shrank by more than 1 KB"
    assert steady[0] - after <= 1024, f"internal heap drifted {steady[0]} -> {after} in 48 syntheses"


def test_mute_and_sound_give_the_same_pcm_hash(flashed):
    """FR-RES-04: say --mute T and say T (default volume 5, inaudible) hash the same PCM."""
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    muted = _say(PT)
    m, p = board.command(f"say {PT}", r"^ESPK (done|error)", timeout=60)
    assert m.event == "done", p.stdout
    # the engine keeps state between says (FSD 7): compare with R1 running the same two says
    r1 = board.r1_run(f"init en\nvoice en\nsay {PT}\nsay {PT}\n")
    assert muted["sha256"] == r1[0]["sha256"] and m.fields["sha256"] == r1[1]["sha256"]


def test_a_muted_session_never_touches_the_codec(flashed):
    """FR-RES-04, nothing in the I2S with --mute: after a boot and several --mute says the codec was never
    initialised, so the amplifier was never woken (the silent bench of 2026-11-27)."""
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    m, _p = board.command("audio", r"^ESPK audio")
    assert m.fields == {"initialised": "0"}, "the codec was initialised at boot"
    for text in (PT, "Hello there.", PT):
        m, _p = board.command(f"say --mute {text}", r"^ESPK (done|error)", timeout=60)
        assert m.event == "done"
    m, _p = board.command("pcm Hello there.", r"^ESPK (pcmdone|error)", timeout=60)
    m, _p = board.command("audio", r"^ESPK audio")
    assert m.fields == {"initialised": "0"}, "a silent command woke the codec"
