# SPDX-License-Identifier: GPL-3.0-or-later
"""FSD 12 on the board: the data partition, its checks and its read-only VFS.

The bad-image cases flash a copy of the artifact under test with the data image altered, and restore the
artifact afterwards (P2 of the testing standard): a board left with a broken image would fail the next test.
"""

import errno
import shutil
import struct
import zlib
from pathlib import Path

import board
import pytest

MOUNT = "/espeak"
HEADER = 36
ENTRY = 72


def _image_path(artifact: Path) -> Path:
    for line in (artifact / "flash_args").read_text().splitlines()[1:]:
        if line.strip().endswith(".img"):
            return artifact / line.split()[1]
    raise AssertionError("the artifact has no data image in flash_args")


def _parse(img: bytes):
    _magic, _fmt, _flags, _ver, count, payload_size, crc = struct.unpack_from("<4sHH16sIII", img, 0)
    table = img[HEADER:HEADER + ENTRY * count]
    payload = img[HEADER + ENTRY * count:]
    files = {}
    for i in range(count):
        raw, off, size = struct.unpack_from("<64sII", table, ENTRY * i)
        files[raw.rstrip(b"\0").decode()] = payload[off:off + size]
    assert zlib.crc32(table + payload) == crc and len(payload) == payload_size
    return files


@pytest.fixture
def broken(flashed, tmp_path):
    """Flash a copy of the artifact with the image mutated by the caller; restore the artifact at the end."""
    def make(mutate):
        copy = tmp_path / "art"
        shutil.copytree(flashed, copy)
        img_file = _image_path(copy)
        img = bytearray(img_file.read_bytes())
        mutate(img)
        img_file.write_bytes(bytes(img))
        p = board.bench("flash", "dut", str(copy), timeout=300)
        assert p.returncode == 0, p.stdout + p.stderr
    yield make
    p = board.bench("flash", "dut", str(flashed), timeout=300)  # cleanup: the artifact under test again
    assert p.returncode == 0, "the cleanup could not restore the artifact: " + p.stdout + p.stderr


def _boot_error():
    ms, p = board.boot(timeout=20)
    assert "error" in ms and "ready" not in ms, p.stdout
    return ms["error"].fields["code"], ms["boot"].fields


def test_a_corrupted_image_gets_invalid_crc_and_the_engine_is_not_started(broken):
    """FR-DAT-03: a flipped payload byte -> ESP_ERR_INVALID_CRC, no languages loaded, no engine."""
    broken(lambda img: img.__setitem__(len(img) - 100, img[len(img) - 100] ^ 0xFF))
    code, boot = _boot_error()
    assert code == "ESP_ERR_INVALID_CRC" and boot["langs"] == "none", (code, boot)


def test_a_wrong_magic_gets_invalid_crc(broken):
    """FR-DAT-03: a magic other than ESPK -> ESP_ERR_INVALID_CRC."""
    broken(lambda img: img.__setitem__(slice(0, 4), b"XXXX"))
    code, _boot = _boot_error()
    assert code == "ESP_ERR_INVALID_CRC"


def test_another_engine_version_gets_invalid_version(broken):
    """FR-DAT-04: espeak_version different from the compiled engine's -> ESP_ERR_INVALID_VERSION."""
    broken(lambda img: img.__setitem__(slice(8, 24), b"1.51.0".ljust(16, b"\0")))
    code, _boot = _boot_error()
    assert code == "ESP_ERR_INVALID_VERSION"


def test_the_vfs_serves_every_file_of_the_image_read_only(flashed):
    """FR-DAT-05: open, fstat, read, lseek and close give the image's bytes; FR-DAT-06: write and create fail
    with EROFS."""
    files = _parse(_image_path(flashed).read_bytes())
    names = sorted(files)
    sample = [names[0], names[-1], "phontab", "phondata", next(n for n in names if n.startswith("lang/"))]
    ms, p = board.boot()
    assert "ready" in ms, p.stdout
    for name in sample:
        data = files[name]
        m, _p = board.command(f"vfs {MOUNT}/{name}", r"^ESPK vfs", timeout=30)
        f = m.fields
        assert "err" not in f, (name, f)
        assert int(f["size"]) == len(data) == int(f["end"]), (name, f)
        assert f["head"] == data[:16].hex() and f["close"] == "0"
        if len(data) >= 4:
            assert f["tail"] == data[-4:].hex() and int(f["back"]) == len(data) - 4, (name, f)
    m, _p = board.command(f"vfs {MOUNT}/no/such/file", r"^ESPK vfs")
    assert m.fields == {"err": str(errno.ENOENT)}
    m, _p = board.command(f"vfswrite {MOUNT}/phontab", r"^ESPK vfswrite")
    assert m.fields == {"open": str(errno.EROFS), "create": str(errno.EROFS)}, m.fields
