# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-DAT-05 (host reader), FR-DAT-07: the data image of FSD Appendix A."""

import importlib.util
import struct
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "components/espeak-ng/tools/gen_image.py"


def gen():
    if not GEN.exists():
        pytest.xfail("not implemented: gen_image.py")
    spec = importlib.util.spec_from_file_location("gen_image", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def data_dir():
    import sys
    sys.path.insert(0, str(ROOT / "tools/ref"))
    import r1
    return r1.build(r1.upstream()) / "espeak-ng-data"


def test_image_is_deterministic(data_dir):
    g = gen()
    a = g.build(data_dir, ["pt-br", "en"])
    b = g.build(data_dir, ["en", "pt-br"])
    assert a == b


def test_image_round_trip_and_layout(data_dir):
    g = gen()
    img = g.build(data_dir, ["pt-br", "en"])
    magic, fmt, flags, ver, count, payload_size, crc = struct.unpack_from("<4sHH16sIII", img, 0)
    assert (magic, fmt, flags) == (b"ESPK", 1, 0)
    assert ver.rstrip(b"\0") == b"1.52.0"
    head = 36
    table = img[head:head + 72 * count]
    payload = img[head + 72 * count:]
    assert len(payload) == payload_size
    assert zlib.crc32(table + payload) == crc
    names = []
    for i in range(count):
        raw, off, size = struct.unpack_from("<64sII", table, 72 * i)
        name = raw.rstrip(b"\0").decode()
        names.append(name)
        assert off % 4 == 0 and off + size <= payload_size
        src = next(p for p in data_dir.rglob("*") if p.is_file() and
                   p.relative_to(data_dir).as_posix().lower() == name)
        assert payload[off:off + size] == src.read_bytes(), name
    assert names == sorted(names)
    assert set(names) == {"phontab", "phonindex", "phondata", "intonations",
                          "pt_dict", "en_dict", "lang/roa/pt-br", "lang/gmw/en"}
    assert g.read(img) == {n: g.read(img)[n] for n in names}


def test_unknown_voice_is_refused(data_dir):
    g = gen()
    with pytest.raises(SystemExit, match="xx"):
        g.build(data_dir, ["pt-br", "xx"])
