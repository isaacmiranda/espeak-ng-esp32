# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-ASY-01, 02, 04, 05, 07: the asynchronous layer on the board (the normal build)."""

import board

PT = "Atenção: a bateria está fraca."
LONG = " ".join([PT] * 29)  # 985 bytes: seconds of speech


def _ready():
    ms, p = board.boot()
    assert "ready" in ms, p.stdout


def test_say_returns_in_5_ms_and_the_say_is_still_speaking(flashed):
    """FR-ASY-01: espk_say() queues a long text and returns in <= 5 ms (measured on the chip)."""
    _ready()
    m, p = board.command(f"say --mute {LONG}", r"^ESPK (queued|error)", timeout=20)
    assert m and m.event == "queued", p.stdout
    assert int(m.fields["queue_us"]) <= 5000, m.fields
    m, p = board.command("cancel", r"^ESPK (cancelled|done|error)", timeout=10)
    assert m and m.event == "cancelled", f"the say was not still running: {p.stdout}"


def test_start_and_done_carry_the_id_and_the_fields(flashed):
    """FR-ASY-02: START and DONE with the request's id; DONE with samples, synth_ms and first_ms."""
    _ready()
    _m, p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    ms = {m.event: m for m in board.markers(p.stdout)}
    assert {"queued", "start", "done"} <= set(ms), p.stdout
    assert ms["queued"].fields["id"] == ms["start"].fields["id"] == ms["done"].fields["id"]
    d = ms["done"].fields
    assert int(d["samples"]) > 0 and int(d["synth_ms"]) > 0 and int(d["first_ms"]) >= 0


def test_a_full_queue_refuses_with_no_mem_and_the_queued_ones_never_speak(flashed):
    """FR-ASY-04 (one speaking, QUEUE_LEN=4 waiting, one more) and FR-RES-10 (the queue is dropped)."""
    _ready()
    seen = []
    m, p = board.command(f"say --mute {LONG}", r"^ESPK (queued|error)", timeout=20)
    seen.append(p.stdout)
    assert m.event == "queued"
    for _ in range(4):
        m, p = board.command(f"say --mute {PT}", r"^ESPK (queued|error)", timeout=20)
        seen.append(p.stdout)
        assert m.event == "queued", p.stdout
    m, p = board.command(f"say --mute {PT}", r"^ESPK (queued|error)", timeout=20)
    assert m.event == "error" and m.fields["code"] == "ESP_ERR_NO_MEM", p.stdout
    m, p = board.command("cancel", r"^ESPK (cancelled|done)", timeout=10)
    seen.append(p.stdout)
    assert m.event == "cancelled", p.stdout
    text = "\n".join(seen)
    for queued_id in (2, 3, 4, 5):
        assert f"start id={queued_id}" not in text, f"queued request {queued_id} spoke:\n{text}"
    _m, p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    assert "start id=" in p.stdout and "done id=" in p.stdout, p.stdout


def test_the_task_stack_is_65536_bytes_in_psram(flashed):
    """FR-ASY-05."""
    _ready()
    m, _p = board.command("taskinfo", r"^ESPK taskinfo")
    assert m.fields["stack"] == "65536" and m.fields["psram"] == "1", m.fields


def test_the_async_path_gives_the_same_hash_as_the_sync_core(flashed):
    """FR-ASY-07: the same text, each from a clean init, through espk_say() and through espk_synth()."""
    _ready()
    m, _p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    assert m.event == "done"
    async_hash = m.fields["sha256"]
    _ready()
    m, _p = board.command(f"synth {PT}", r"^ESPK (sync|error)", timeout=30)
    assert m.event == "sync", m
    assert m.fields["sha256"] == async_hash
