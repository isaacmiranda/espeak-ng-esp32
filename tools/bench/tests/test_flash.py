# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from bench import actions
from bench.ports import BenchError
from fakes import Out

FLASH_ARGS = """--flash_mode dio --flash_freq 80m --flash_size 16MB
0x0 bootloader/bootloader.bin
0x10000 espk_research.bin
0x8000 partition_table/partition-table.bin
0xd000 ota_data_initial.bin
0x620000 espeak.img
"""


def make_artifact(tmp_path, args=FLASH_ARGS, skip=()):
    (tmp_path / "flash_args").write_text(args)
    for ln in args.splitlines()[1:]:
        name = ln.split()[-1]
        if name in skip:
            continue
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    return tmp_path


def test_offsets_come_from_flash_args(tmp_path):
    art = make_artifact(tmp_path)
    argv = actions.flash_argv(art, "/dev/espk-dut", "esp32s3")
    i = argv.index("write-flash")
    assert argv[i + 1:i + 7] == ["--flash_mode", "dio", "--flash_freq", "80m", "--flash_size", "16MB"]
    pairs = argv[i + 7:]
    assert pairs[0::2] == ["0x0", "0x10000", "0x8000", "0xd000", "0x620000"]
    assert pairs[-1] == str(art / "espeak.img")


def test_refuses_artifact_without_flash_args(tmp_path):
    with pytest.raises(BenchError, match="no flash_args"):
        actions.flash_argv(tmp_path, "/dev/x", "esp32s3")


def test_refuses_line_without_offset(tmp_path):
    art = make_artifact(tmp_path, FLASH_ARGS.replace("0x620000 espeak.img", "espeak.img"))
    with pytest.raises(BenchError, match="without offset"):
        actions.flash_argv(art, "/dev/x", "esp32s3")


def test_refuses_missing_image(tmp_path):
    art = make_artifact(tmp_path, skip=("espeak.img",))
    with pytest.raises(BenchError, match=r"espeak\.img"):
        actions.flash_argv(art, "/dev/x", "esp32s3")


def test_flash_reports_esptool_failure(tmp_path):
    art = make_artifact(tmp_path)
    assert actions.flash(art, "/dev/x", "esp32s3", lambda argv: 2, Out()) == 1
    assert actions.flash(art, "/dev/x", "esp32s3", lambda argv: 0, Out()) == 0


def test_esptool_runs_from_the_drivers_interpreter(tmp_path):
    import sys

    argv = actions.flash_argv(make_artifact(tmp_path), "/dev/x", "esp32s3")
    assert argv[:3] == [sys.executable, "-m", "esptool"]
