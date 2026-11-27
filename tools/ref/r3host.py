# SPDX-License-Identifier: GPL-3.0-or-later
"""R3-host: the component's own engine sources and configuration, built on the host (FR-REF-02, FR-SEC-02).

The same vendored sources (components/espeak-ng/upstream/) and the same config.h the firmware compiles,
linked with the PCM harness (tools/ref/pcm_script.c) into a host executable, optionally with the
AddressSanitizer. The list of sources is read from the component's CMakeLists.txt: there is one list. The
build lives in the cache (ESPK_CACHE, default ~/.cache/espk), never in the repository.

    python tools/ref/r3host.py --script <script.txt> [--sanitize] --out <records.jsonl>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r1

ROOT = r1.ROOT
COMP = ROOT / "components/espeak-ng"
HARNESS = ROOT / "tools/ref/pcm_script.c"


def sources() -> list[Path]:
    """The upstream objects the firmware builds, from the component's CMakeLists.txt (one list)."""
    text = (COMP / "CMakeLists.txt").read_text()
    vars_ = dict(re.findall(r"^set\((U|D) (\S+)\)", text, re.M))
    body = re.search(r"set\(UPSTREAM_SRCS(.*?)\)", text, re.S).group(1)
    out = []
    for tok in body.split():
        for k, v in vars_.items():
            tok = tok.replace("${" + k + "}", v)
        out.append(COMP / tok)
    return out


def build(sanitize: bool = False) -> Path:
    srcs = sources()
    # the upstream is third-party code, not edited: GCC 14 makes some old C idioms errors, the firmware's
    # toolchain builds them with warnings off (-w), so do the same here
    flags = ["-O1", "-g", "-fwrapv", "-w", "-Wno-error=int-conversion",
             "-Wno-error=incompatible-pointer-types", "-Wno-error=implicit-function-declaration",
             "-DLIBESPEAK_NG_EXPORT=1"]
    if sanitize:
        flags += ["-fsanitize=address", "-fno-omit-frame-pointer"]
    key = hashlib.sha256()
    for p in [HARNESS, COMP / "config/config.h", *srcs]:
        key.update(p.read_bytes())
    key.update(" ".join(flags).encode())
    name = "pcm_script_asan" if sanitize else "pcm_script"
    out = r1.cache_dir() / f"r3host-{key.hexdigest()[:16]}" / name
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    u = COMP / "upstream/src"
    cmd = ["cc", *flags, "-I", str(COMP / "config"), "-I", str(u / "include"), "-I", str(u / "libespeak-ng"),
           "-I", str(u / "ucd-tools/src/include"), str(HARNESS), *map(str, srcs), "-lm", "-lpthread",
           "-o", str(out)]
    subprocess.run([*r1.NICE, *cmd], check=True)
    return out


def data_dir() -> Path:
    return r1.build(r1.upstream()) / "espeak-ng-data"


def run_raw(script: bytes, sanitize: bool = False) -> tuple[subprocess.CompletedProcess, Path]:
    """Run a script (bytes: any text) in a fresh process; the PCM files stay in the returned directory."""
    exe = build(sanitize)
    tmp = Path(tempfile.mkdtemp(prefix="r3host-"))
    sp = tmp / "script.txt"
    sp.write_bytes(script)
    p = subprocess.run([str(exe), str(data_dir()), str(sp), str(tmp)], capture_output=True)
    return p, tmp


def run(script: str, sanitize: bool = False) -> list[dict]:
    """One record per say: sha256 and samples of the PCM, in the format of r1.run (without the phonemes)."""
    steps = r1.parse_script(script)
    n_say = sum(1 for cmd, _ in steps if cmd == "say")
    p, tmp = run_raw(script.encode("utf-8"), sanitize)
    if p.returncode != 0:
        sys.exit(f"FATAL: pcm_script exited {p.returncode}: {p.stderr.decode(errors='replace').strip()}")
    recs = []
    for k in range(n_say):
        pcm = (tmp / f"{k:04d}.pcm").read_bytes()
        recs.append({"item": k, "sha256": hashlib.sha256(pcm).hexdigest(), "samples": len(pcm) // 2})
    return recs


def pcm(script: str, sanitize: bool = False) -> list[bytes]:
    """The PCM bytes of each say, in order (what the board's `pcm` command streams, from the host build)."""
    steps = r1.parse_script(script)
    n_say = sum(1 for cmd, _ in steps if cmd == "say")
    p, tmp = run_raw(script.encode("utf-8"), sanitize)
    if p.returncode != 0:
        sys.exit(f"FATAL: pcm_script exited {p.returncode}: {p.stderr.decode(errors='replace').strip()}")
    return [(tmp / f"{k:04d}.pcm").read_bytes() for k in range(n_say)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--script", type=Path, required=True)
    ap.add_argument("--sanitize", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in run(a.script.read_text(encoding="utf-8"), a.sanitize):
            fh.write(json.dumps(r) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
