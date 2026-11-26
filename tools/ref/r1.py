# SPDX-License-Identifier: GPL-3.0-or-later
"""R1 — the eSpeak NG upstream built on the host from the pinned tarball (FSD FR-REF-01).

    python tools/ref/r1.py --voice pt-br --corpus <texts.txt> --out <records.jsonl> [--rate 175]

One JSON record per line of the corpus: voice, item, text, sha256 and samples of the PCM,
rate, the phoneme transcription (espeak-ng -x) and the upstream version. The build lives
in the cache (ESPK_CACHE, default ~/.cache/espk), never in the repository.
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
    """Build the upstream (library, CLI, all languages' data) once; return the build dir."""
    ver = up["ESPEAK_VER"]
    b = cache_dir() / f"r1-{ver}-{up['ESPEAK_SHA256'][:12]}"
    stamp = b / "r1.ok"
    if stamp.exists():
        return b
    tgz = tarball(up)
    src_root = cache_dir() / f"src-{ver}"
    if not (src_root / f"espeak-ng-{ver}").exists():
        src_root.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tgz) as tf:
            tf.extractall(src_root, filter="data")
    src = src_root / f"espeak-ng-{ver}"
    off = ["-DUSE_MBROLA=OFF", "-DUSE_LIBSONIC=OFF", "-DUSE_LIBPCAUDIO=OFF", "-DUSE_ASYNC=OFF",
           "-DUSE_KLATT=OFF", "-DUSE_SPEECHPLAYER=OFF", "-DESPEAK_BUILD_MANPAGES=OFF"]
    subprocess.run(["cmake", "-S", str(src), "-B", str(b), "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release", *off],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run([*NICE, "cmake", "--build", str(b), "-j", str(jobs)],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["cc", "-O2", "-I", str(src / "src/include"), str(ROOT / "tools/ref/pcm_dump.c"),
                    str(b / "src/libespeak-ng/libespeak-ng.a"), str(b / "src/ucd-tools/libucd.a"),
                    "-lm", "-lpthread", "-o", str(b / "pcm_dump")], check=True)
    stamp.write_text(ver + "\n")
    return b


def phonemes(b: Path, voice: str, text: str, rate: int | None) -> str:
    cli = b / "src/espeak-ng"
    argv = [str(cli), "--path", str(b), "-v", voice, "-q", "-x"]
    if rate:
        argv += ["-s", str(rate)]
    p = subprocess.run([*argv, text], capture_output=True, text=True, check=True)
    return p.stdout.strip()


def run(voice: str, corpus: Path, rate: int | None = None) -> list[dict]:
    up = upstream()
    b = build(up)
    texts = corpus.read_text(encoding="utf-8").splitlines()
    with tempfile.TemporaryDirectory() as tmp:
        argv = [str(b / "pcm_dump"), str(b / "espeak-ng-data"), voice, str(corpus), tmp]
        if rate:
            argv.append(str(rate))
        p = subprocess.run(argv, capture_output=True, text=True)
        if p.returncode != 0:
            sys.exit(f"FATAL: pcm_dump exited {p.returncode}: {p.stderr.strip()}")
        sample_rate = int(p.stdout.strip().split("=")[1])
        recs = []
        for i, text in enumerate(texts):
            pcm = Path(tmp, f"{i:04d}.pcm").read_bytes()
            recs.append({"voice": voice, "item": i, "text": text,
                         "sha256": hashlib.sha256(pcm).hexdigest(), "samples": len(pcm) // 2,
                         "rate": sample_rate, "phonemes": phonemes(b, voice, text, rate),
                         "espeak": up["ESPEAK_VER"]})
    return recs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--voice", required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--rate", type=int)
    a = ap.parse_args(argv)
    recs = run(a.voice, a.corpus, a.rate)
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
