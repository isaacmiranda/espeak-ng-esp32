# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-ENG-05: with CONFIG_ESPK_UCD_WRAP off (the "intact" mode) the component builds and works.

ESPK_INTACT_BUILD names the build directory of the intact variant (its ELF is read with nm);
ESPK_ARTIFACT names that variant's packed artifact, flashed on the board.
"""

import json
import os
import subprocess
from pathlib import Path

import board
import pytest


def _build_dir() -> Path:
    d = os.environ.get("ESPK_INTACT_BUILD")
    if not d or not (Path(d) / "espk_research.elf").is_file():
        pytest.skip("not done (precondition): ESPK_INTACT_BUILD does not name the intact variant's build")
    return Path(d)


def test_intact_elf_has_no_wrap_symbols():
    elf = _build_dir() / "espk_research.elf"
    nm = subprocess.run(["nm", str(elf)], capture_output=True, text=True, check=False)
    if nm.returncode != 0:  # the ESP-IDF cross nm, when the host one cannot read the ELF
        nm = subprocess.run(["xtensa-esp32s3-elf-nm", str(elf)], capture_output=True, text=True, check=True)
    assert "__wrap_isw" not in nm.stdout


def test_intact_board_diverges_from_r1_starting_at_the_first_accented_item(flashed):
    """The engine keeps state between says, so once an accent is misread later items drift too (even
    English): in a sequence the divergence starts at the first accented item and never before it."""
    script = board.verify_script()
    says = [ln[4:] for ln in script.splitlines() if ln.startswith("say ")]
    diffs = board.compare(board.board_run(script, timeout=60), board.r1_run(script))
    report = board.ROOT / "test-results" / "equivalence-report-intact.json"
    report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps(diffs, ensure_ascii=False, indent=1), encoding="utf-8")
    assert diffs, "the intact board equals R1 on accented text: the wrap would not be needed"
    first_accent = next(k for k, t in enumerate(says) if not t.isascii())
    first_diff = min(d["item"] for d in diffs)
    assert first_diff == first_accent, f"first divergence at {first_diff}, first accent at {first_accent}"


def test_intact_board_equals_r1_without_accents(flashed):
    """What holds without the wrap (as TC-REF-03-noaccent): English and unaccented text from a reset."""
    script = "init en\nvoice en\n" + "".join(
        f"say {t}\n" for t in ("The battery is low.", "It is 2:30 pm.", "The battery is low."))
    assert not board.compare(board.board_run(script), board.r1_run(script))
