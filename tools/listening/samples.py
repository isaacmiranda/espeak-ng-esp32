# SPDX-License-Identifier: GPL-3.0-or-later
"""WAV files of the listening corpus at each speed, from the artifact on the board (FR-LST-01).

    samples.py --corpus tests/corpus/listen/en.tsv --voice en --speeds 140,175,210 --seed 20261126 \
               --out-dir samples/ --map-file key/samples-map.json [--source board|host] [--limit N]

Each file is named by a pseudorandom 12-hex name (a hash of the seed, the speed and the item: the name says
nothing about the item or the speed) and the map name -> item, speed and text goes in a separate file, which
must not sit next to the samples. The default source is the board: the PCM is the artifact's own, streamed
by its `pcm` command from a fresh reset at each speed (the engine keeps state between says, so the order is
fixed). The `host` source is the same sources built on the host (R3-host, equal to the board over the
verification corpus): it exists for tests without a board and is labelled in the map.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ref"))
LINE = re.compile(r"ESPK pcmdata off=(\d+) hex=([0-9a-f]+)")
DONE = re.compile(r"ESPK pcmdone samples=(\d+) sha256=([0-9a-f]{64})")


def corpus(path: Path) -> list[tuple[str, str]]:
    rows = [
        ln.split("\t")
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln and not ln.startswith("#")
    ]
    return [(r[0], r[2]) for r in rows]


def name_for(seed: int, speed: int, item: str) -> str:
    return hashlib.sha256(f"{seed}:{speed}:{item}".encode()).hexdigest()[:12]


def write_wav(path: Path, pcm: bytes, rate: int = 22050) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)


def bench(*args: str, timeout: float = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "bench", *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout
    )


def board_pcm(voice: str, speed: int, texts: list[str]) -> list[bytes]:
    """From a reset: the voice, the speed, the texts in order; each PCM is checked against its hash."""
    p = bench("wait-event", "dut", r"^ESPK ready", "--timeout", "20", "--reset")
    if p.returncode != 0:
        sys.exit(f"FATAL: the board did not come up: {p.stdout}{p.stderr}")
    for cmd, expect in ((f"voice {voice}", r"^ESPK voice"), (f"rate {speed}", r"^ESPK rate")):
        p = bench("command", "dut", cmd, "--expect", expect)
        if p.returncode != 0:
            sys.exit(f"FATAL: {cmd!r} failed: {p.stdout}{p.stderr}")
    out = []
    for text in texts:
        p = bench(
            "command",
            "dut",
            f"pcm {text}",
            "--expect",
            r"^ESPK (pcmdone|error)",
            "--timeout",
            "180",
            timeout=240,
        )
        chunks, done = {}, None
        for line in p.stdout.splitlines():
            if m := LINE.search(line):
                chunks[int(m.group(1))] = bytes.fromhex(m.group(2))
            elif m := DONE.search(line):
                done = m
        if done is None:
            sys.exit(f"FATAL: no pcmdone for {text!r}: {p.stdout[-300:]}")
        pcm = b"".join(chunks[k] for k in sorted(chunks))
        if len(pcm) != int(done.group(1)) * 2 or hashlib.sha256(pcm).hexdigest() != done.group(2):
            sys.exit(f"FATAL: the PCM received for {text!r} is not the one the board hashed (a lost line?)")
        out.append(pcm)
    return out


def host_pcm(voice: str, speed: int, texts: list[str]) -> list[bytes]:
    import r3host

    script = f"init en\nvoice {voice}\nrate {speed}\n" + "".join(f"say {t}\n" for t in texts)
    return r3host.pcm(script)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--speeds", required=True, help="words per minute, comma separated")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--map-file", type=Path, required=True)
    ap.add_argument("--source", choices=("board", "host"), default="board")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    out_dir = a.out_dir.resolve()
    if out_dir in a.map_file.resolve().parents or a.map_file.resolve().parent == out_dir:
        sys.exit("FATAL: the map file must not be next to the samples (it says which file is which item)")
    items = corpus(a.corpus)[: a.limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    mapping = {}
    for speed in [int(s) for s in a.speeds.split(",")]:
        pcms = (board_pcm if a.source == "board" else host_pcm)(a.voice, speed, [t for _i, t in items])
        for (item, text), pcm in zip(items, pcms, strict=True):
            name = name_for(a.seed, speed, item)
            write_wav(out_dir / f"{name}.wav", pcm)
            mapping[name] = {
                "item": item,
                "speed_ppm": speed,
                "voice": a.voice,
                "text": text,
                "source": a.source,
            }
    a.map_file.parent.mkdir(parents=True, exist_ok=True)
    a.map_file.write_text(
        json.dumps({"seed": a.seed, "files": mapping}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
