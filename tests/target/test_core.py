# SPDX-License-Identifier: GPL-3.0-or-later
"""The synchronous core's API on the board (FSD 14) and the console's info/mem/rate (FSD 5.2)."""

import board
import pytest

PT = "Atenção: a bateria está fraca."
LONG = " ".join([PT] * 29)  # 985 bytes: many blocks, seconds of speech


def _ready():
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    return ms


def test_a_second_init_is_refused_and_changes_nothing(flashed):
    """FR-SYN-04: espk_init() twice without espk_deinit() -> ESP_ERR_INVALID_STATE; synthesis keeps going."""
    _ready()
    m, _p = board.command("init", r"^ESPK init")
    assert m.fields["result"] == "ESP_ERR_INVALID_STATE", m.fields
    m, _p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    assert m.event == "done", m


def test_synth_without_init_is_refused_and_init_brings_it_back(flashed):
    """FR-SYN-05: espk_synth() before espk_init() -> ESP_ERR_INVALID_STATE (here after espk_deinit())."""
    _ready()
    m, _p = board.command("deinit", r"^ESPK deinit")
    assert m.fields["result"] == "ESP_OK", m.fields
    m, _p = board.command(f"synth {PT}", r"^ESPK (sync|error)")
    assert m.event == "error" and m.fields["code"] == "ESP_ERR_INVALID_STATE", m
    m, _p = board.command("deinit", r"^ESPK deinit")
    assert m.fields["result"] == "ESP_ERR_INVALID_STATE", "deinit twice"
    m, _p = board.command("init", r"^ESPK init")
    assert m.fields["result"] == "ESP_OK", m.fields


def _cycle():
    m, _p = board.command("mem", r"^ESPK mem")
    before = int(m.fields["internal_free"])
    m, _p = board.command("deinit", r"^ESPK deinit")
    assert m.fields["result"] == "ESP_OK"
    m, _p = board.command("init", r"^ESPK init")
    assert m.fields["result"] == "ESP_OK"
    m, _p = board.command("mem", r"^ESPK mem")
    return before, int(m.fields["internal_free"])


def test_deinit_then_init_is_ready_and_says_what_r1_says(flashed):
    """FR-SYN-11, first half: ready again, a clean engine (R1's bytes from a fresh start), a bounded heap cost
    per cycle. The upstream keeps one voice_t copy per cycle (see the xfail below): 1 344 B."""
    _ready()
    before, after = _cycle()
    assert 0 <= before - after <= 1500, f"internal heap {before} -> {after}"
    script = f"init en\nvoice en\nsay {PT}\n"
    m, _p = board.command("voice en", r"^ESPK voice")
    m, _p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    assert m.event == "done"
    assert m.fields["sha256"] == board.r1_run(script)[0]["sha256"]


@pytest.mark.xfail(strict=True, reason="upstream espeak-ng 1.52.0 leaks one voice_t (1 344 B) per cycle: "
                   "DoVoiceChange() allocates it, espeak_ng_Terminate() never frees it")
def test_deinit_then_init_returns_the_internal_heap_within_1_kb(flashed):
    """FR-SYN-11, the second half: the same free internal heap as before, within 1 KB."""
    _ready()
    before, after = _cycle()
    assert abs(after - before) <= 1024, f"internal heap {before} -> {after}"


def test_the_callback_returning_false_stops_the_synthesis(flashed):
    """FR-SYN-03: false on the 3rd block -> espk_synth() returns ESPK_ERR_CANCELLED (0x7e01), 3 calls."""
    _ready()
    m, _p = board.command(f"cut 3 {LONG}", r"^ESPK (cut|error)", timeout=30)
    assert m.event == "cut" and m.fields["calls"] == "3" and m.fields["result"] == "0x7e01", m
    m, _p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    assert m.event == "done", "the core keeps working after a cut"


def test_defaults_info_and_rate(flashed):
    """FR-SYN-07 (175 ppm, pitch 50), FR-SYN-02 (22 050), FR-RES-08 (volume 5), FR-RES-13 (info fields),
    FR-SYN-08 (rate outside 80..450 refused and unchanged), FR-RES-06 (rate 220 is faster than 175)."""
    ms = _ready()
    boot = ms["boot"].fields
    m, _p = board.command("info", r"^ESPK info")
    f = m.fields
    assert f["rate"] == "22050" == boot["rate"]
    assert f["rate_ppm"] == "175" and f["pitch"] == "50" and f["volume"] == "5"
    assert f["fw"] == boot["fw"] and f["idf"] == boot["idf"] and f["espeak"] == boot["espeak"]
    assert f["langs"] == boot["langs"] and f["voice"] == "en"
    assert int(f["image_bytes"]) > 0 and int(f["image_crc"], 16) != 0
    m, _p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    slow = int(m.fields["audio_ms"])
    for bad in ("79", "451", "abc"):
        m, _p = board.command(f"rate {bad}", r"^ESPK rate")
        assert m.fields == {"err": "ESP_ERR_INVALID_ARG"}, (bad, m.fields)
    m, _p = board.command("info", r"^ESPK info")
    assert m.fields["rate_ppm"] == "175", "a refused rate changed the speed"
    m, _p = board.command("rate 220", r"^ESPK rate")
    assert m.fields == {"ok": "220"}
    m, _p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    assert int(m.fields["audio_ms"]) < slow, "rate 220 did not speak faster than 175"


def test_mem_reports_four_numbers(flashed):
    """FR-RES-14."""
    _ready()
    m, _p = board.command("mem", r"^ESPK mem")
    v = {k: int(x) for k, x in m.fields.items()}
    assert set(v) == {"internal_free", "internal_min", "psram_free", "psram_min"}
    assert all(x > 0 for x in v.values()) and v["internal_min"] <= v["internal_free"]
    assert v["psram_min"] <= v["psram_free"]


def test_a_sync_synth_during_a_say_is_refused(flashed):
    """FR-SYN-10: espk_synth() from another task during a synthesis -> ESP_ERR_INVALID_STATE."""
    _ready()
    m, _p = board.command(f"say --mute {LONG}", r"^ESPK (queued|error)", timeout=20)
    assert m.event == "queued"
    m, _p = board.command(f"synth {PT}", r"^ESPK (sync|error)")
    assert m.event == "error" and m.fields["code"] == "ESP_ERR_INVALID_STATE", m
    m, _p = board.command("cancel", r"^ESPK (cancelled|done)", timeout=10)
    assert m.event == "cancelled"


def test_bss_and_data_copies_are_in_psram_and_init_ms_is_reported(flashed):
    """FR-MEM-02 (the boot line says where the .bss is), FR-MEM-04 (the engine's copies of the data go to
    PSRAM: an init costs the PSRAM 600 KB or more, the internal heap 24 KB at most), FR-MEM-05 (init_ms)."""
    ms = _ready()
    boot = ms["boot"].fields
    assert boot["bss"] == "psram" and int(boot["init_ms"]) > 0
    m, _p = board.command("deinit", r"^ESPK deinit")
    assert m.fields["result"] == "ESP_OK"
    m, _p = board.command("mem", r"^ESPK mem")
    internal0, psram0 = int(m.fields["internal_free"]), int(m.fields["psram_free"])
    m, _p = board.command("init", r"^ESPK init")
    assert m.fields["result"] == "ESP_OK"
    m, _p = board.command("mem", r"^ESPK mem")
    internal1, psram1 = int(m.fields["internal_free"]), int(m.fields["psram_free"])
    assert psram0 - psram1 >= 600_000, f"PSRAM cost of init: {psram0 - psram1}"
    assert internal0 - internal1 <= 24_000, f"internal cost of init: {internal0 - internal1}"


def test_init_with_too_little_psram_is_refused_and_nothing_is_loaded(flashed):
    """FR-CAP-10: with the PSRAM taken (a test seam) below the peak, espk_init() gives ESP_ERR_NO_MEM,
    the component stays UNINIT, and once the PSRAM is back it starts."""
    _ready()
    m, _p = board.command("deinit", r"^ESPK deinit")
    assert m.fields["result"] == "ESP_OK"
    m, _p = board.command("hog 600", r"^ESPK hog")
    assert int(m.fields["psram_free"]) < 800_000, m.fields
    m, _p = board.command("init", r"^ESPK init")
    assert m.fields["result"] == "ESP_ERR_NO_MEM", m.fields
    m, _p = board.command("info", r"^ESPK (info|error)")
    assert m.event == "error" and m.fields["code"] == "ESP_ERR_INVALID_STATE", m  # still UNINIT
    m, _p = board.command("unhog", r"^ESPK unhog")
    m, _p = board.command("init", r"^ESPK init")
    assert m.fields["result"] == "ESP_OK", m.fields
    m, _p = board.command(f"say --mute {PT}", r"^ESPK (done|error)", timeout=30)
    assert m.event == "done"
