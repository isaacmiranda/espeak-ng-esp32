#!/usr/bin/env python3
"""TC-SPK-04 (FSD FR-SPK-04): o PCM dos 10 textos fixos é o mesmo em 3 execuções
e igual à referência gerada com o eSpeak NG do upstream (vectors/speech/pcm.sha256).

  check_speech_pcm.py <speech_pcm> <dir-de-dados> <dir-de-trabalho>
"""
import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEXTS = HERE / "vectors" / "speech" / "texts.txt"
REF = HERE / "vectors" / "speech" / "pcm.sha256"


def run(tool, data, out):
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.pcm"):
        f.unlink()
    subprocess.run([tool, data, str(TEXTS), str(out)], check=True, capture_output=True)
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.glob("*.pcm"))}


def main():
    tool, data, work = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    n = len(TEXTS.read_text(encoding="utf-8").splitlines())
    ref = dict(reversed(line.split()) for line in REF.read_text().splitlines())
    runs = [run(tool, data, work / f"run{i}") for i in range(3)]
    bad = []
    for i, r in enumerate(runs):
        if len(r) != n:
            bad.append(f"execução {i}: {len(r)} PCMs, esperado {n}")
        if r != runs[0]:
            bad.append(f"execução {i} difere da 0")
    for name, h in runs[0].items():
        if ref.get(name) != h:
            bad.append(f"{name}: {h} ≠ referência {ref.get(name)}")
    for b in bad:
        print("FAIL", b)
    print("HOST TC-SPK-04", "failed" if bad else "ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
