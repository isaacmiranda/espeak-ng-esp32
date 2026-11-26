#!/usr/bin/env python3
"""Imagem da partição `espeak` (FSD FR-PLT-06, NFR-SW-02).

  python3 scripts/gen-espeak-image.py <dir-de-dados> <saída.bin>

Formato (little-endian), versão 1:
  0   magic        4 B   b"AAES"
  4   format       u32   1
  8   size         u32   bytes depois do cabeçalho (tabela + dados)
  12  crc32        u32   CRC-32 (IEEE, o do zlib) desses `size` bytes
  16  count        u32   arquivos na tabela
  20  tabela       count × {name[32] (caminho relativo, NUL), offset u32, len u32}
      dados        cada arquivo alinhado a 4 B; offset conta a partir do byte 16
O leitor é firmware/components/l1_speech (espeak_part.c). Determinístico: a
ordem é a dos caminhos ordenados.
"""
import struct
import sys
import zlib
from pathlib import Path

MAGIC = b"AAES"
FORMAT = 1
PART_SIZE = 0x100000          # FSD CON-SW-08
NAME_LEN = 32


def build(data_dir: Path) -> bytes:
    files = sorted(p for p in data_dir.rglob("*") if p.is_file())
    names = [p.relative_to(data_dir).as_posix() for p in files]
    for n in names:
        if len(n.encode()) >= NAME_LEN:
            sys.exit(f"FATAL: nome longo demais para a tabela: {n}")
    table_len = 4 + len(files) * (NAME_LEN + 8)
    off = table_len
    entries, blobs = [], []
    for p, n in zip(files, names):
        b = p.read_bytes()
        off = (off + 3) & ~3
        entries.append((n, off, len(b)))
        blobs.append((off, b))
        off += len(b)
    body = bytearray(off)
    struct.pack_into("<I", body, 0, len(files))
    for i, (n, o, ln) in enumerate(entries):
        struct.pack_into(f"<{NAME_LEN}sII", body, 4 + i * (NAME_LEN + 8), n.encode(), o, ln)
    for o, b in blobs:
        body[o:o + len(b)] = b
    head = MAGIC + struct.pack("<III", FORMAT, len(body), zlib.crc32(body))
    img = head + bytes(body)
    if len(img) > PART_SIZE:
        sys.exit(f"FATAL: imagem de {len(img)} B não cabe na partição de {PART_SIZE} B")
    return img


def main():
    img = build(Path(sys.argv[1]))
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(img)
    print(f"espeak.bin: {len(img)} B, crc32={struct.unpack_from('<I', img, 12)[0]:08x}")


if __name__ == "__main__":
    main()
