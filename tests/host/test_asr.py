# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-ASR-01..04, 06 on the host with a stand-in transcriber (no model needed): the report has the four
dimensions, names its inputs, is identical in two runs, and states the caveat; the setup refuses a model
with another hash. The real whisper.cpp run is the release job's."""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/asr"))
import report  # noqa: E402


class Echo:
    """Hears the text of the item exactly, except that it drops every accent: a known, countable error."""

    def __init__(self, texts):
        self.by_wav, self.texts = {}, texts

    def transcribe(self, wav, lang):
        n = int(wav.stem.rsplit("-", 1)[1])
        text = self.texts[(wav.stem.rsplit("-", 2)[0], n)]
        import unicodedata

        return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))


@pytest.fixture(scope="module")
def work():
    base = Path.home() / ".cache/espk/tmp"
    base.mkdir(parents=True, exist_ok=True)
    d = Path(tempfile.mkdtemp(dir=base))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def make(work, speeds=(140, 175, 220)):
    corp = {
        "pt-br": report.load_corpus(ROOT / "tests/corpus/listen/pt-br.tsv"),
        "en": report.load_corpus(ROOT / "tests/corpus/listen/en.tsv"),
    }
    corp = {k: [v[0], *v[200:203], *v[-3:]] if k == "pt-br" else v[:4] for k, v in corp.items()}  # words, sus, daily
    texts = {(lang, i): t for lang, items in corp.items() for i, (_a, _b, t) in enumerate(items)}
    out = work / "w"
    out.mkdir(exist_ok=True)
    rows = report.evaluate(Echo(texts), corp, speeds, out)
    return report.build_report(rows, report.pins(), "abc1234", {"xx": "the Whisper model does not support this language"})


def test_metrics_normalise_and_count_errors():
    assert report.normalise("  Olá,  MUNDO! 14:30 ") == "olá mundo 14 30"
    assert report.cer_wer("casa", "casa") == (0, 4, 0, 1)
    assert report.cer_wer("a casa", "a caza") == (1, 5, 1, 2)
    assert report.cer_wer("ação", "acao")[0] == 2


def test_the_report_has_the_four_dimensions_and_names_its_inputs(work):
    rep = make(work)
    assert {"lang", "speed", "kind", "items", "cer", "wer"} <= set(rep["by_lang_speed_kind"][0])
    langs = {c["lang"] for c in rep["by_lang_speed_kind"]}
    assert langs == {"pt-br", "en"} and rep["speeds_ppm"] == [140, 175, 220]
    assert {c["kind"] for c in rep["by_lang_speed_kind"] if c["lang"] == "pt-br"} == {"words", "sus", "daily"}
    assert {c["condition"] for c in rep["pt_br_by_condition"]} == {"accent", "plain"}
    for k in ("whisper_cpp", "model", "model_sha256", "component_commit", "normalisation", "caveat"):
        assert rep[k], k
    assert re.fullmatch(r"[0-9a-f]{64}", rep["model_sha256"]) and rep["whisper_cpp"].startswith("v")
    assert all(c["cer"] is not None or c.get("reason") for c in rep["by_lang_speed_kind"])
    en = [c for c in rep["by_lang_speed_kind"] if c["lang"] == "en"]
    assert all(c["cer"] == 0 for c in en), "the stand-in hears English (no accents) exactly"
    accent = next(c for c in rep["pt_br_by_condition"] if c["condition"] == "accent")
    plain = next(c for c in rep["pt_br_by_condition"] if c["condition"] == "plain")
    assert accent["cer"] > 0 and plain["cer"] == 0, "accent errors show up only in the accented condition"


def test_two_runs_give_the_same_report_and_the_caveat_travels_with_the_numbers(work):
    a, b = make(work), make(work)
    ja = json.dumps(a, sort_keys=True, ensure_ascii=False)
    assert ja == json.dumps(b, sort_keys=True, ensure_ascii=False)
    md = report.markdown(a)
    assert report.CAVEAT in md and "inteligib" not in md.lower().replace("medida de inteligibilidade", "")
    assert a["caveat"] == report.CAVEAT


def test_a_language_the_model_does_not_support_is_listed_as_omitted(work):
    rep = make(work)
    assert rep["languages_omitted"] == {"xx": "the Whisper model does not support this language"}
    got = report.run(Echo({}), [], ["xx"], (175,), None, "c", work)
    assert "xx" in got["languages_omitted"]


def test_the_setup_refuses_a_model_with_another_hash(tmp_path):
    cache = tmp_path / "cache"
    pins = report.pins()
    src = cache / "whisper" / f"whisper.cpp-{pins['WHISPER_TAG']}"
    (src / "build/bin").mkdir(parents=True)
    exe = src / "build/bin/whisper-cli"
    exe.write_text("#!/bin/sh\n")
    exe.chmod(0o755)
    (cache / "whisper" / pins["MODEL_NAME"]).write_bytes(b"not the model")
    p = subprocess.run([str(ROOT / "scripts/whisper-setup.sh")], env={"PATH": "/usr/bin:/bin", "ESPK_CACHE": str(cache)},
                       capture_output=True, text=True)  # fmt: skip
    assert p.returncode == 1 and "FATAL: sha256 of the model" in p.stderr
    assert not (cache / "whisper" / pins["MODEL_NAME"]).exists()
