# SPDX-License-Identifier: GPL-3.0-or-later
"""CER and WER of the synthesised listening corpus, transcribed by the pinned whisper.cpp (FSD section 9).

    report.py --out report.json [--md report.md] [--langs pt-br,en] [--speeds 140,175,220] [--limit N]
              [--auto-langs de,es,fr] [--commit <sha>]

The corpus is synthesised on the host (R1-equal PCM), written as WAV, transcribed, normalised and compared
with the reference text. The report is deterministic: no date, no path, keys sorted, rows in corpus order
(FR-ASR-04). It names the whisper.cpp tag, the model hash, the component commit and the normalisation
(FR-ASR-03), and every number travels with the caveat of FR-ASR-05.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/listening"))
sys.path.insert(0, str(ROOT / "tools/corpus"))

CAVEAT = "estimativa por reconhecimento automático; não é medida de inteligibilidade com ouvintes"
NORMALISATION = (
    "Unicode NFC; minúsculas; pontuação removida (exceto dígitos); acentos mantidos; "
    "espaços colapsados; CER sobre os caracteres sem espaços, WER sobre as palavras"
)
SPEEDS = (140, 175, 220)
# eSpeak voice -> Whisper language code (the languages of the image that the model supports)
WHISPER_LANG = {
    "pt-br": "pt", "en": "en", "de": "de", "es": "es", "fr": "fr", "it": "it", "nl": "nl", "pl": "pl",
    "ru": "ru", "tr": "tr", "sv": "sv", "da": "da", "fi": "fi", "cs": "cs", "el": "el", "hu": "hu",
}  # fmt: skip
ACCENT = re.compile(r"[áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ]")


def normalise(text: str) -> str:
    t = unicodedata.normalize("NFC", text).lower()
    t = "".join(c if (c.isalnum() or c.isspace()) else " " for c in t)
    return " ".join(t.split())


def edit_distance(a, b) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def cer_wer(reference: str, hypothesis: str) -> tuple[int, int, int, int]:
    """(char errors, char count, word errors, word count) of the normalised texts."""
    r, h = normalise(reference), normalise(hypothesis)
    rc, hc = r.replace(" ", ""), h.replace(" ", "")
    return edit_distance(rc, hc), len(rc), edit_distance(r.split(), h.split()), len(r.split())


def kind_of(row: list[str]) -> str:
    return {"word": "words", "daily": "daily"}.get(row[1], "sus" if row[1].startswith("sus-") else row[1])


def load_corpus(path: Path) -> list[tuple[str, str, str]]:
    rows = [ln.split("\t") for ln in path.read_text(encoding="utf-8").splitlines() if ln and not ln[0] == "#"]
    return [(r[0], kind_of(r), r[2]) for r in rows]


class Whisper:
    """The pinned whisper.cpp CLI: greedy decoding, no temperature fallback, fixed threads."""

    def __init__(self, binary: Path, model: Path):
        self.binary, self.model = binary, model

    def transcribe(self, wav: Path, lang: str) -> str:
        p = subprocess.run(
            ["nice", "-n", "15", "ionice", "-c", "2", "-n", "7", str(self.binary), "-m", str(self.model),
             "-l", lang, "-t", "2", "-bo", "1", "-bs", "1", "-tp", "0.0", "-nt", "-np", "-f", str(wav)],
            capture_output=True, text=True, check=True,
        )  # fmt: skip
        return " ".join(p.stdout.split())


def synth(voice: str, speed: int, texts: list[str], directory: Path) -> list[Path]:
    import samples

    out = []
    for n, pcm in enumerate(samples.host_pcm(voice, speed, texts)):
        path = directory / f"{voice}-{speed}-{n:04d}.wav"
        samples.write_wav(path, pcm)
        out.append(path)
    return out


def rate(errors: int, total: int) -> float | None:
    return round(errors / total, 4) if total else None


def summarise(rows: list[dict], keys: tuple[str, ...]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    out = []
    for key in sorted(groups, key=lambda k: tuple(str(x) for x in k)):
        g = groups[key]
        ce, cn = sum(r["char_errors"] for r in g), sum(r["chars"] for r in g)
        we, wn = sum(r["word_errors"] for r in g), sum(r["words"] for r in g)
        cell = dict(zip(keys, key, strict=True))
        cell.update(items=len(g), cer=rate(ce, cn), wer=rate(we, wn))
        if cn == 0:
            cell["reason"] = "reference without characters"
        out.append(cell)
    return out


def evaluate(transcriber, corpora: dict[str, list[tuple[str, str, str]]], speeds, work: Path) -> list[dict]:
    rows = []
    for lang, items in corpora.items():
        code = WHISPER_LANG[lang]
        for speed in speeds:
            wavs = synth(lang, speed, [t for _i, _k, t in items], work)
            for (item_id, kind, text), wav in zip(items, wavs, strict=True):
                hyp = transcriber.transcribe(wav, code)
                ce, cn, we, wn = cer_wer(text, hyp)
                rows.append(
                    {"lang": lang, "speed": speed, "kind": kind,
                     "condition": "accent" if ACCENT.search(text) else "plain",
                     "id": item_id, "reference": text, "hypothesis": hyp,
                     "char_errors": ce, "chars": cn, "word_errors": we, "words": wn}
                )  # fmt: skip
    return rows


def build_report(rows: list[dict], pins: dict[str, str], commit: str, omitted: dict[str, str]) -> dict:
    pt = [r for r in rows if r["lang"] == "pt-br" and r["kind"] != "auto"]
    return {
        "caveat": CAVEAT,
        "whisper_cpp": pins["WHISPER_TAG"],
        "model": pins["MODEL_NAME"],
        "model_sha256": pins["MODEL_SHA256"],
        "component_commit": commit,
        "normalisation": NORMALISATION,
        "speeds_ppm": sorted({r["speed"] for r in rows}),
        "by_lang_speed_kind": summarise(rows, ("lang", "speed", "kind")),
        "pt_br_by_condition": summarise(pt, ("speed", "condition")),
        "languages_omitted": omitted,
        "items": rows,
    }


def markdown(rep: dict) -> str:
    head = ["# ASR estimate (CER/WER)", "", f"> {rep['caveat']}", "",
            f"whisper.cpp `{rep['whisper_cpp']}`, model `{rep['model']}` (sha256 `{rep['model_sha256']}`), "
            f"component `{rep['component_commit']}`.", "", f"Normalisation: {rep['normalisation']}.", "",
            "| language | ppm | corpus | items | CER | WER |", "|---|---|---|---|---|---|"]  # fmt: skip
    for c in rep["by_lang_speed_kind"]:
        head.append(f"| {c['lang']} | {c['speed']} | {c['kind']} | {c['items']} | {c['cer']} | {c['wer']} |")
    head += [
        "",
        "pt-BR by condition:",
        "",
        "| ppm | condition | items | CER | WER |",
        "|---|---|---|---|---|",
    ]
    for c in rep["pt_br_by_condition"]:
        head.append(f"| {c['speed']} | {c['condition']} | {c['items']} | {c['cer']} | {c['wer']} |")
    for lang, why in rep["languages_omitted"].items():
        head.append(f"\nomitted: {lang}: {why}")
    return "\n".join(head) + "\n"


def pins() -> dict[str, str]:
    out = {}
    for ln in (ROOT / "tools/asr/pins.env").read_text().splitlines():
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            out[k] = v
    return out


def auto_items() -> list[tuple[str, str, str]]:
    import auto_corpus

    return [(f"A{n:02d}", "auto", t) for n, t in enumerate(auto_corpus.ITEMS, 1)]


def run(transcriber, langs, auto_langs, speeds, limit, commit, work: Path) -> dict:
    corpora = {}
    for lang in langs:
        items = load_corpus(ROOT / f"tests/corpus/listen/{lang}.tsv")
        corpora[lang] = items[:limit] if limit else items
    omitted = {}
    for lang in auto_langs:
        if lang in WHISPER_LANG:
            corpora[lang] = auto_items()
        else:
            omitted[lang] = "the Whisper model does not support this language"
    return build_report(evaluate(transcriber, corpora, speeds, work), pins(), commit, omitted)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--md", type=Path)
    ap.add_argument("--langs", default="pt-br,en")
    ap.add_argument("--auto-langs", default="")
    ap.add_argument("--speeds", default=",".join(map(str, SPEEDS)))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--commit", default="unknown")
    a = ap.parse_args(argv)
    setup = subprocess.run([str(ROOT / "scripts/whisper-setup.sh")], capture_output=True, text=True)
    if setup.returncode:
        sys.exit(setup.stderr)
    binary, model = (Path(x) for x in setup.stdout.split())
    with tempfile.TemporaryDirectory(dir=model.parent) as tmp:
        rep = run(
            Whisper(binary, model), [x for x in a.langs.split(",") if x],
            [x for x in a.auto_langs.split(",") if x],
            [int(s) for s in a.speeds.split(",")], a.limit, a.commit, Path(tmp),
        )  # fmt: skip
    a.out.write_text(json.dumps(rep, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if a.md:
        a.md.write_text(markdown(rep), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
