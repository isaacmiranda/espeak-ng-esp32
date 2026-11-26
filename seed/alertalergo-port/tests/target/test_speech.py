"""Fala no DUT (FSD §18.2, FR-PLT-06, FR-TCN-09).

O responsável liberou som audível em 2026-11-08; mesmo assim os testes não
mudam o volume (o build de teste começa em 5, FR-TCN-07). Se a fala é
inteligível é verificação manual (FR-SPK-07, NFR-SPK-01).
"""
import re

import dut as dutlib
import pytest
from test_clock import SEARCHING, cmd

FINAL = r"^SPEECH (done|abort|fail) "


@pytest.fixture
def searching(flashed, port, results_dir, request):
    log = results_dir / f"serial-{request.node.name}.log"
    ok, lines = dutlib.boot(port, log, until=SEARCHING)
    assert ok is not None, "o DUT não chegou a «buscando»"
    return log, [ln for _, ln in dutlib.app_markers(lines)]


def say(port, log, text, timeout=15.0, raw=False):
    """`speech say <texto>` até o marcador final; devolve [(t, marcador)] (ou
    todas as linhas, com o log do IDF, se `raw`)."""
    ok, lines = dutlib.command(port, log, f"speech say {text}", until=FINAL, timeout=timeout)
    m = dutlib.app_markers(lines)
    assert ok is not None, f"«{text}» sem marcador final de fala: {[ln for _, ln in m]}"
    return lines if raw else m


@pytest.mark.plan("TC-SPK-21")
@pytest.mark.variants("test")
def test_speech_data_ready_at_boot(searching):
    _, boot = searching
    ready = [x for x in boot if x.startswith("SPEECH ready")]
    assert ready == ["SPEECH ready=1"], f"dados da fala: {ready}"
    i = next(i for i, x in enumerate(boot) if x.startswith("UI screen=splash"))
    assert boot.index("SPEECH ready=1") > i, "conferência dos dados antes do splash (FR-PLT-06)"


@pytest.mark.plan("TC-SPK-22")
@pytest.mark.variants("test")
def test_speech_say_start_then_done(port, searching):
    log, _ = searching
    m = say(port, log, "Bateria fraca.")
    sp = [ln for _, ln in m if ln.startswith("SPEECH ")]
    assert "TCN ok cmd=speech_say" in [ln for _, ln in m]
    assert len(sp) == 2 and sp[0].startswith("SPEECH start ") and sp[1].startswith("SPEECH done "), sp
    s, d = dutlib.fields(sp[0]), dutlib.fields(sp[1])
    assert s["chars"] == "14", sp[0]                       # FR-SPK-02: code points
    assert s["id"] == d["id"], sp
    assert 300 <= int(d["ms"]) <= 5000, f"fala de «Bateria fraca.» durou {d['ms']} ms"
    # depois do início, o PA liga; no fim, desliga (o mesmo caminho dos tons)
    audio = [ln for _, ln in m if ln.startswith("AUDIO pa=")]
    assert audio == ["AUDIO pa=1", "AUDIO pa=0"], audio
    _, lines = dutlib.command(port, log, "speech say", until=r"^(TCN ok cmd=|tcn: failed)", timeout=5.0)
    assert any(ln.startswith("tcn: failed") for _, ln in lines), "`speech say` vazio aceito"


@pytest.mark.plan("TC-SPK-23")
@pytest.mark.variants("test")
def test_battery_low_speaks_after_tone(port, searching):
    log, _ = searching
    cmd(port, log, "batt override 57", "batt_override")
    _, lines = dutlib.command(port, log, "batt override 15", until=FINAL, timeout=15.0)
    m = dutlib.app_markers(lines)
    tone = [t for t, ln in m if ln.startswith("AUDIO play clip=low_battery ")]
    start = [(t, ln) for t, ln in m if ln.startswith("SPEECH start ")]
    final = [ln for _, ln in m if re.match(FINAL, ln)]
    assert tone and start, f"tom e fala: {[ln for _, ln in m]}"
    assert dutlib.fields(start[0][1])["chars"] == str(len("Bateria fraca. Carregue o aparelho.")), start
    assert final and final[0].startswith("SPEECH done "), final
    dt = start[0][0] - tone[0]
    assert 0 < dt <= 1.5, f"fala {dt:.2f} s depois do tom (FR-ALR-04: ≤ 1,5 s)"
    dutlib.command(port, log, "batt override off", until=r"^TCN ok cmd=batt_override$")


@pytest.mark.plan("TC-SPK-24")
@pytest.mark.variants("test")
def test_long_run_of_speech_without_watchdog(port, searching):
    """FR-SPK-03 e FR-SPK-06: 50 falas seguidas sem task_wdt nem reinício, e a
    heap interna mínima ≥ 32 KB em todas."""
    log, _ = searching
    text = "Atenção. Paciente, joao pereira. Alergia a, sulfametoxazol."
    heap = []
    for i in range(50):
        m = [ln for _, ln in say(port, log, text, timeout=20.0, raw=True)]
        bad = [x for x in m if "task_wdt" in x or x.startswith("BOOT ") or "Guru Meditation" in x
               or "rst:" in x]
        assert not bad, f"fala {i}: {bad}"
        done = [x for x in m if x.startswith("SPEECH done ")]
        assert done, f"fala {i} sem done: {[x for x in m if x.startswith('SPEECH')]}"
        heap.append(int(dutlib.fields(done[0])["heap_min"]))
    assert min(heap) >= 32768, f"heap interna mínima {min(heap)} B < 32 KB (FR-SPK-06)"
