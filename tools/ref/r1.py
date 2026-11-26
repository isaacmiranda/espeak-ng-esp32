# SPDX-License-Identifier: GPL-3.0-or-later
"""R1 — the eSpeak NG upstream built on the host from the pinned tarball (FSD §7, FR-REF-01).

    python tools/ref/r1.py --script <script.txt> --out <records.jsonl>
    python tools/ref/r1.py --voice pt-br --corpus <texts.txt> --out <records.jsonl>

A script is an ordered list of steps: `init <voice>` first, then `voice <voice>`, `rate <wpm>`
and `say <text>`. The engine keeps state between utterances, so the PCM of a `say` depends on
the steps before it: R1 runs the whole script from a clean start and gives one JSON record
per `say`: voice, step, item (the k-th say), text, sha256 and samples of the PCM, rate, the
phoneme transcription (espeak-ng -x, a fresh process) and the upstream version. `--corpus`
is the script `init en`, `voice <voice>`, one `say` per line: the same steps the research
firmware takes from a reset to a voice and a corpus. The build lives in the cache
(ESPK_CACHE, default ~/.cache/espk), never in the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / "components/espeak-ng/tools/upstream.env"
NICE = ["nice", "-n", "15", "ionice", "-c", "2", "-n", "7"]


def upstream() -> dict[str, str]:
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def cache_dir() -> Path:
    base = os.environ.get("ESPK_CACHE") or os.path.join(
        os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "espk")
    return Path(base)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tarball(up: dict[str, str]) -> Path:
    tgz = Path(os.environ.get("ESPK_TARBALL") or cache_dir() / f"espeak-ng-{up['ESPEAK_VER']}.tar.gz")
    if not tgz.exists():
        tgz.parent.mkdir(parents=True, exist_ok=True)
        part = tgz.with_suffix(".part")
        urllib.request.urlretrieve(up["ESPEAK_URL"], part)
        part.rename(tgz)
    got = sha256_file(tgz)
    if got != up["ESPEAK_SHA256"]:
        sys.exit(f"FATAL: sha256 of {tgz} is {got}, expected {up['ESPEAK_SHA256']}")
    return tgz


def build(up: dict[str, str], jobs: int = 2) -> Path:
    """Build the upstream (library, CLI, all languages' data) once, and the PCM harness
    whenever its source changes; return the build dir."""
    ver = up["ESPEAK_VER"]
    b = cache_dir() / f"r1-{ver}-{up['ESPEAK_SHA256'][:12]}"
    stamp = b / "r1.ok"
    src_root = cache_dir() / f"src-{ver}"
    src = src_root / f"espeak-ng-{ver}"
    if not stamp.exists():
        tgz = tarball(up)
        if not src.exists():
            src_root.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tgz) as tf:
                tf.extractall(src_root, filter="data")
        off = ["-DUSE_MBROLA=OFF", "-DUSE_LIBSONIC=OFF", "-DUSE_LIBPCAUDIO=OFF", "-DUSE_ASYNC=OFF",
               "-DUSE_KLATT=OFF", "-DUSE_SPEECHPLAYER=OFF", "-DESPEAK_BUILD_MANPAGES=OFF"]
        subprocess.run(["cmake", "-S", str(src), "-B", str(b), "-G", "Ninja",
                        "-DCMAKE_BUILD_TYPE=Release", *off], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([*NICE, "cmake", "--build", str(b), "-j", str(jobs)],
                       check=True, stdout=subprocess.DEVNULL)
        stamp.write_text(ver + "\n")
    harness = ROOT / "tools/ref/pcm_script.c"
    want = sha256_file(harness)
    marker = b / "pcm_script.sha256"
    if not (b / "pcm_script").exists() or not marker.exists() or marker.read_text().strip() != want:
        subprocess.run(["cc", "-O2", "-I", str(src / "src/include"), str(harness),
                        str(b / "src/libespeak-ng/libespeak-ng.a"), str(b / "src/ucd-tools/libucd.a"),
                        "-lm", "-lpthread", "-o", str(b / "pcm_script")], check=True)
        marker.write_text(want + "\n")
    return b


def phonemes(b: Path, voice: str, text: str, rate: int | None) -> str:
    cli = b / "src/espeak-ng"
    argv = [str(cli), "--path", str(b), "-v", voice, "-q", "-x"]
    if rate:
        argv += ["-s", str(rate)]
    p = subprocess.run([*argv, text], capture_output=True, text=True, check=True)
    return p.stdout.strip()


def parse_script(text: str) -> list[tuple[str, str]]:
    steps = []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        cmd, _, arg = line.partition(" ")
        if cmd not in ("init", "voice", "rate", "say") or not arg:
            sys.exit(f"FATAL: script line {n}: {line!r}")
        steps.append((cmd, arg))
    if not steps or steps[0][0] != "init":
        sys.exit("FATAL: a script starts with `init <voice>`")
    return steps


def corpus_script(voice: str, corpus: Path, rate: int | None = None) -> str:
    lines = ["init en", f"voice {voice}"]
    if rate:
        lines.append(f"rate {rate}")
    lines += [f"say {t}" for t in corpus.read_text(encoding="utf-8").splitlines()]
    return "\n".join(lines) + "\n"


def run(script: str) -> list[dict]:
    up = upstream()
    steps = parse_script(script)
    b = build(up)
    rate = None
    voice = None
    says = []
    for step, (cmd, arg) in enumerate(steps):
        if cmd in ("init", "voice"):
            voice = arg
        elif cmd == "rate":
            rate = int(arg)
        else:
            says.append((step, voice, rate, arg))
    with tempfile.TemporaryDirectory() as tmp:
        sp = Path(tmp, "script.txt")
        sp.write_text(script, encoding="utf-8")
        p = subprocess.run([str(b / "pcm_script"), str(b / "espeak-ng-data"), str(sp), tmp],
                           capture_output=True, text=True)
        if p.returncode != 0:
            sys.exit(f"FATAL: pcm_script exited {p.returncode}: {p.stderr.strip()}")
        sample_rate = int(p.stdout.strip().split("=")[1])
        recs = []
        for k, (step, v, r, text) in enumerate(says):
            pcm = Path(tmp, f"{k:04d}.pcm").read_bytes()
            recs.append({"voice": v, "step": step, "item": k, "text": text,
                         "sha256": hashlib.sha256(pcm).hexdigest(), "samples": len(pcm) // 2,
                         "rate": sample_rate, "phonemes": phonemes(b, v, text, r),
                         "espeak": up["ESPEAK_VER"]})
    return recs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--script", type=Path)
    ap.add_argument("--voice")
    ap.add_argument("--corpus", type=Path)
    ap.add_argument("--rate", type=int)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if bool(a.script) == bool(a.voice and a.corpus):
        ap.error("give --script, or --voice with --corpus")
    script = a.script.read_text(encoding="utf-8") if a.script else corpus_script(a.voice, a.corpus, a.rate)
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in run(script):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
