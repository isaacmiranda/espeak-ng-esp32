# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-MEM-02: with CONFIG_ESPK_BSS_IN_PSRAM on (the default) the engine's .bss lives in PSRAM (the linker's
placement, read from the ELF's symbol table), and the upstream sources are untouched.

ESPK_BUILD names the firmware build directory to read (default research/firmware/build); the test is
`not done (precondition)` without a built ELF.
"""

import glob
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PSRAM = range(0x3C000000, 0x3E000000)  # ESP32-S3 external RAM, data bus addresses
SYMBOLS = ("phoneme_list", "echo_buf", "frame_pool")


def _nm(elf):
    pattern = ".espressif/tools/xtensa-esp-elf/*/xtensa-esp-elf/bin/xtensa-esp32s3-elf-nm"
    cross = sorted(glob.glob(str(Path.home() / pattern)))
    if not cross:
        pytest.skip("not done (precondition): the Xtensa nm is not installed")
    return subprocess.run([cross[-1], "-C", str(elf)], capture_output=True, text=True, check=True).stdout


def test_the_engine_statics_are_placed_in_psram():
    build = Path(os.environ.get("ESPK_BUILD", ROOT / "research/firmware/build"))
    elf = build / "espk_research.elf"
    if not elf.is_file():
        pytest.skip("not done (precondition): no built espk_research.elf")
    cfg = next((c for c in (build / "sdkconfig", build.parent / "sdkconfig") if c.is_file()), None)
    if cfg is None or "CONFIG_ESPK_BSS_IN_PSRAM=y" not in cfg.read_text():
        pytest.skip("not done (precondition): the build has CONFIG_ESPK_BSS_IN_PSRAM off")
    found = {}
    for line in _nm(elf).splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) == 3 and parts[2].split("$")[0] in SYMBOLS:  # a static is named frame_pool$8
            found[parts[2].split("$")[0]] = int(parts[0], 16)
    assert set(found) == set(SYMBOLS), f"symbols not found: {set(SYMBOLS) - set(found)}"
    outside = {k: hex(v) for k, v in found.items() if v not in PSRAM}
    assert not outside, f"not in PSRAM: {outside}"


def test_the_upstream_sources_are_untouched():
    """The placement is the linker's (components/espeak-ng/linker.lf), never a patch."""
    p = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "components/espeak-ng/upstream"], cwd=ROOT)
    assert p.returncode == 0
