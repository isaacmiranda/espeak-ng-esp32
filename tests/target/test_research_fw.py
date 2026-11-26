# SPDX-License-Identifier: GPL-3.0-or-later
"""FSD §5 (research firmware) and §14 (core) on the board."""

import re

import board


def test_boot_marker_fields(flashed):
    ms, _p = board.boot()
    b = ms["boot"].fields
    for k in ("fw", "commit", "idf", "espeak", "rate", "bss", "langs", "init_ms"):
        assert k in b, f"ESPK boot lacks {k}: {b}"
    manifest = (flashed / "manifest.yaml").read_text()
    assert re.search(rf"^commit: {b['commit']}", manifest, re.M), "boot commit is not the artifact's"
    assert b["espeak"] == "1.52.0" and b["bss"] in ("internal", "psram")
    assert int(b["init_ms"]) >= 0


def test_ready_follows_boot(flashed):
    ms, p = board.boot()
    assert "ready" in ms and "error" not in ms, p.stdout
    lines = [ln for ln in p.stdout.splitlines() if " ESPK " in ln]
    assert lines.index(next(ln for ln in lines if " ESPK boot" in ln)) < \
        lines.index(next(ln for ln in lines if " ESPK ready" in ln))


def test_sample_rate_is_22050(flashed):
    ms, _ = board.boot()
    assert ms["boot"].fields["rate"] == "22050"


def test_say_mute_reports_the_pcm_hash(flashed):
    board.boot()
    m, p = board.command("say --mute Atenção: a bateria está fraca.", r"^ESPK (done|error)")
    assert m and m.event == "done", p.stdout
    for k in ("id", "samples", "synth_ms", "first_ms", "audio_ms", "heap_min", "sha256"):
        assert k in m.fields
    assert int(m.fields["samples"]) > 0 and re.fullmatch(r"[0-9a-f]{64}", m.fields["sha256"])


def test_voice_switch_and_unknown_voice(flashed):
    board.boot()
    m, _ = board.command("voice en", r"^ESPK voice")
    assert m.fields == {"ok": "en"}
    m, _ = board.command("voice xx", r"^ESPK voice")
    assert m.fields == {"err": "not_found"}
    m, _ = board.command("say --mute The battery is low.", r"^ESPK (done|error)")
    assert m.event == "done", "the previous voice is kept after a refused one"
