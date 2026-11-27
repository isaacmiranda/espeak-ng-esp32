# SPDX-License-Identifier: GPL-3.0-or-later
"""R2: the eSpeak NG of the system, compared with R1 (FSD 7: FR-REF-05, FR-REF-06, FR-REF-07).

    r2.py [--voices pt-br,en | --all] [--cli] [--corpus tests/corpus/auto/auto.txt] --report r2-report.json

R1 is the pinned upstream built on the host (tools/ref/r1.py); R2 is the package of the system (its version
goes in the report). Always through the same entry point: the PCM of R1's synchronous API with the PCM of
the system library's synchronous API (ctypes), and with --cli the PCM and the phonemes of R1's CLI with those
of the system's CLI. For every voice of the upstream (--all) or the ones named. A divergence is a row of the
report (voice, item, kind phonemes|pcm|both, entry, greatest per-sample difference, SNR, cause) and never
fails the run: the exit code is 0 whenever the comparison itself ran.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diverge
import r1

ROOT = r1.ROOT
SYS_PARENT = Path("/usr/lib/x86_64-linux-gnu")
SYS_CLI = "/usr/bin/espeak-ng"
CAUSES = ROOT / "tools/ref/r2-causes.tsv"


def system_package() -> str:
    p = subprocess.run(
        ["dpkg-query", "-W", "-f=${Package} ${Version}", "espeak-ng"], capture_output=True, text=True
    )
    return p.stdout.strip() or "unknown"


def voices(data: Path) -> list[str]:
    sys.path.insert(0, str(ROOT / "components/espeak-ng/tools"))
    import gen_image

    return sorted(gen_image.voice_files(data))


def known_causes() -> dict[tuple[str, str, str], str]:
    out = {}
    if CAUSES.exists():
        for line in CAUSES.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                voice, entry, kind, cause = line.split("\t")
                out[(voice, entry, kind)] = cause
    return out


def r1_api(b: Path, voice: str, texts: list[str]) -> list[bytes] | None:
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp, "s.txt")
        script.write_text(
            "init en\n" + f"voice {voice}\n" + "".join(f"say {t}\n" for t in texts), encoding="utf-8"
        )
        p = subprocess.run(
            [str(b / "pcm_script"), str(b / "espeak-ng-data"), str(script), tmp], capture_output=True
        )
        if p.returncode != 0:
            return None
        return [Path(tmp, f"{k:04d}.pcm").read_bytes() for k in range(len(texts))]


def r2_api(voice: str, texts: list[str]) -> list[bytes] | None:
    with tempfile.TemporaryDirectory() as tmp:
        p = subprocess.run(
            [
                sys.executable,
                "-I",
                str(ROOT / "tools/ref/r2_api.py"),
                str(SYS_PARENT / "espeak-ng-data"),
                voice,
                tmp,
            ],
            input="\n".join(texts) + "\n",
            capture_output=True,
            text=True,
        )
        if p.returncode != 0:
            return None
        return [Path(tmp, f"{k:04d}.pcm").read_bytes() for k in range(len(texts))]


def cli(exe: str, parent: Path, voice: str, text: str) -> tuple[bytes | None, str | None]:
    """The CLI's PCM (the WAV on stdout without its 44-byte header) and phonemes, or None where it refuses."""
    base = [exe, "--path", str(parent), "-v", voice]
    w = subprocess.run([*base, "--stdout", text], capture_output=True)
    f = subprocess.run([*base, "-q", "-x", text], capture_output=True, text=True)
    return (
        w.stdout[44:] if w.returncode == 0 and len(w.stdout) >= 44 else None,
        f.stdout.strip() if f.returncode == 0 else None,
    )


def row(voice, item, entry, kind, a: bytes | None, b: bytes | None, causes) -> dict:
    d = diverge.compare(a or b"", b or b"") if kind != "phonemes" else {"max_abs_diff": None, "snr_db": None}
    snr = d["snr_db"] if d["snr_db"] is not None and math.isfinite(d["snr_db"]) else None  # null: undefined
    cause = next(
        (
            causes[k]
            for k in ((voice, entry, kind), (voice, entry, "*"), (voice, "*", kind), (voice, "*", "*"))
            if k in causes
        ),
        "unattributed",
    )
    return {
        "voice": voice,
        "item": item,
        "entry": entry,
        "kind": kind,
        "max_abs_diff": d["max_abs_diff"],
        "snr_db": snr,
        "cause": cause,
    }


def compare(voice_list: list[str], texts: list[str], with_cli: bool) -> dict:
    b = r1.build(r1.upstream())
    causes = known_causes()
    rows, errors, compared = [], [], 0
    for v in voice_list:
        a1, a2 = r1_api(b, v, texts), r2_api(v, texts)
        if a1 is None or a2 is None:
            errors.append({"voice": v, "entry": "api", "why": "R1 refused" if a1 is None else "R2 refused"})
        else:
            for k, (x, y) in enumerate(zip(a1, a2, strict=True)):
                compared += 1
                if x != y:
                    rows.append(row(v, texts[k], "api", "pcm", x, y, causes))
        if not with_cli:
            continue
        for t in texts:
            (p1, f1), (p2, f2) = cli(str(b / "src/espeak-ng"), b, v, t), cli(SYS_CLI, SYS_PARENT, v, t)
            if p1 is None or p2 is None:
                errors.append({"voice": v, "entry": "cli", "item": t, "why": "a CLI refused"})
                continue
            compared += 1
            pcm_diff, ph_diff = p1 != p2, f1 != f2
            if pcm_diff or ph_diff:
                kind = "both" if pcm_diff and ph_diff else ("pcm" if pcm_diff else "phonemes")
                rows.append(row(v, t, "cli", kind, p1, p2, causes))
    return {
        "system_package": system_package(),
        "r1": r1.upstream()["ESPEAK_VER"],
        "voices": voice_list,
        "items": len(texts),
        "compared": compared,
        "divergences": rows,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--voices")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--cli", action="store_true")
    ap.add_argument("--corpus", type=Path, default=ROOT / "tests/corpus/auto/auto.txt")
    ap.add_argument("--report", type=Path, required=True)
    a = ap.parse_args(argv)
    if bool(a.voices) == a.all:
        ap.error("give --voices or --all")
    data = r1.build(r1.upstream()) / "espeak-ng-data"
    chosen = voices(data) if a.all else a.voices.split(",")
    texts = [ln for ln in a.corpus.read_text(encoding="utf-8").splitlines() if ln.strip()]
    report = compare(chosen, texts, a.cli)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"R2 against {report['system_package']}: {len(chosen)} voices, {report['compared']} comparisons, "
        f"{len(report['divergences'])} divergences, {len(report['errors'])} not comparable"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
