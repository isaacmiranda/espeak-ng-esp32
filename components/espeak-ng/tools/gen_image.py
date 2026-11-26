# SPDX-License-Identifier: GPL-3.0-or-later
"""Data image of the espeak-ng component (FSD §12.2 and Appendix A).

    python gen_image.py --data <espeak-ng-data> --voices pt-br,en --out espeak.img

Header (little-endian, 36 bytes): magic "ESPK", format_version u16 = 1, flags u16 = 0,
espeak_version char[16], file_count u32, payload_size u32, crc32 u32 (IEEE, over the
table and the payload). Then the table, file_count x {name char[64], offset u32,
size u32}, sorted by name; then the payload, each file starting on a 4-byte boundary,
offsets counted from the start of the payload. Names are paths relative to the mount
point, in lower case. The same data and voices always give the same bytes (FR-DAT-07).
"""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

MAGIC = b"ESPK"
FORMAT = 1
HEADER = struct.Struct("<4sHH16sIII")
ENTRY = struct.Struct("<64sII")
COMMON = ("phontab", "phonindex", "phondata", "intonations")


def voice_files(data: Path) -> dict[str, Path]:
    """Voice id (the file name, lower case) -> voice file, for every voice under lang/."""
    return {p.name.lower(): p for p in sorted((data / "lang").rglob("*")) if p.is_file()}


def dictionary_of(voice_file: Path) -> str:
    """`dictionary X` if the voice names one, else the base of its first `language` line."""
    lang = None
    for line in voice_file.read_text(encoding="utf-8", errors="replace").splitlines():
        words = line.split()
        if len(words) >= 2 and words[0] == "dictionary":
            return words[1]
        if len(words) >= 2 and words[0] == "language" and lang is None:
            lang = words[1]
    if lang is None:
        sys.exit(f"FATAL: {voice_file} names no language")
    return lang.split("-")[0]


def select(data: Path, voices: list[str]) -> dict[str, Path]:
    """Image name -> source file for the common files plus each voice and its dictionary."""
    known = voice_files(data)
    files = {n: data / n for n in COMMON}
    for v in voices:
        vf = known.get(v.lower())
        if vf is None:
            sys.exit(f"FATAL: voice {v!r} is not in {data}/lang (known: {', '.join(sorted(known))})")
        files[vf.relative_to(data).as_posix().lower()] = vf
        d = f"{dictionary_of(vf)}_dict"
        if not (data / d).is_file():
            sys.exit(f"FATAL: dictionary {d} of voice {v!r} is missing from {data}")
        files[d] = data / d
    return files


def build(data: Path, voices: list[str], espeak_version: str = "1.52.0") -> bytes:
    files = select(Path(data), voices)
    names = sorted(files)
    for n in names:
        if len(n.encode()) >= 64:
            sys.exit(f"FATAL: name too long for the table: {n}")
    payload = bytearray()
    table = bytearray()
    for n in names:
        payload += b"\0" * (-len(payload) % 4)
        blob = files[n].read_bytes()
        table += ENTRY.pack(n.encode(), len(payload), len(blob))
        payload += blob
    crc = zlib.crc32(bytes(table) + bytes(payload))
    head = HEADER.pack(MAGIC, FORMAT, 0, espeak_version.encode(), len(names), len(payload), crc)
    return head + bytes(table) + bytes(payload)


def read(img: bytes) -> dict[str, bytes]:
    """Reference reader: name -> bytes. Raises ValueError on a bad magic, version or CRC."""
    magic, fmt, _flags, _ver, count, size, crc = HEADER.unpack_from(img, 0)
    if magic != MAGIC or fmt != FORMAT:
        raise ValueError("bad magic or format")
    start = HEADER.size + ENTRY.size * count
    if zlib.crc32(img[HEADER.size:start + size]) != crc:
        raise ValueError("bad crc")
    out = {}
    for i in range(count):
        raw, off, ln = ENTRY.unpack_from(img, HEADER.size + ENTRY.size * i)
        out[raw.rstrip(b"\0").decode()] = img[start + off:start + off + ln]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--voices", required=True, help="comma-separated voice ids, e.g. pt-br,en")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--espeak-version", default="1.52.0")
    a = ap.parse_args(argv)
    img = build(a.data, [v for v in a.voices.split(",") if v], a.espeak_version)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(img)
    h = HEADER.unpack_from(img, 0)
    print(f"{a.out}: {len(img)} B, {h[4]} files, crc32={h[6]:08x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
