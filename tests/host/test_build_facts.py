# SPDX-License-Identifier: GPL-3.0-or-later
"""Facts about what is built, read from the files: CON-ENG-03, CON-PLT-01, CON-PLT-02, CON-PLT-05.

The map test reads ESPK_BUILD (default research/firmware/build) and is `not done (precondition)` without it.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
FSD = ROOT / "docs/Functionality/FSD.md"


def _build() -> Path:
    b = Path(os.environ.get("ESPK_BUILD", ROOT / "research/firmware/build"))
    if not (b / "espk_research.map").is_file():
        pytest.skip("not done (precondition): no built espk_research.map")
    return b


def test_only_the_synchronous_runtime_is_compiled():
    """CON-ENG-03: no MBROLA, Klatt, speech player, sonic nor the upstream's async/fifo/event modules."""
    forbidden = {"mbrowrap", "synth_mbrola", "compilembrola", "klatt", "sPlayer", "fifo", "event",
                 "espeak_command"}
    text = (_build() / "espk_research.map").read_text(errors="replace")
    members = set(re.findall(r"libespeak-ng\.a\((\w+)\.c\.obj\)", text))
    assert {"synthesize", "wavegen", "translate"} <= members, "the engine's objects were not found in the map"
    assert not (members & forbidden), f"objects that must not be built: {sorted(members & forbidden)}"
    assert "sonic.c.obj" not in text and "sonic.o" not in text, "sonic is linked"


def test_the_engine_is_built_with_the_pinned_idf_through_the_wrapper():
    """CON-PLT-01: scripts/idf.sh pins v5.5.5 (the FSD's value) and that tree really is v5.5.5."""
    assert "v5.5.5" in (ROOT / "scripts/idf.sh").read_text()
    assert "v5.5.5" in FSD.read_text(encoding="utf-8")
    tree = Path.home() / "esp/esp-idf-v5.5.5"
    if not tree.is_dir():
        pytest.skip("not done (precondition): the pinned ESP-IDF is not installed")
    done = subprocess.run(["git", "describe", "--tags"], cwd=tree, capture_output=True, text=True)
    tag = done.stdout.strip()
    assert tag == "v5.5.5", tag


def test_the_component_manifest_declares_the_idf_and_the_four_targets():
    """CON-PLT-02."""
    m = yaml.safe_load((ROOT / "components/espeak-ng/idf_component.yml").read_text())
    assert m["dependencies"]["idf"] == ">=5.5"
    assert sorted(m["targets"]) == ["esp32", "esp32p4", "esp32s2", "esp32s3"]


def _sizes(csv: Path) -> dict[str, tuple[str, str, int]]:
    """Name -> (type, subtype, size in bytes) from an ESP-IDF partition CSV."""
    units = {"K": 1024, "M": 1024 * 1024}
    out = {}
    for line in csv.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, typ, sub, _off, size = (c.strip() for c in line.split(","))
        n = int(size[:-1], 0) * units[size[-1]] if size[-1] in units else int(size, 0)
        out[name] = (typ, sub, n)
    return out


def test_the_partition_table_is_the_one_of_the_fsd():
    """CON-PLT-05 (host half): names, types, subtypes and sizes equal the FSD table; espeak takes the rest
    of the 16 MB flash (ESP-IDF rules: 0x9000 for the first data partition, apps aligned to 64 KB)."""
    text = FSD.read_text(encoding="utf-8").split("**Tabela de partições do firmware de pesquisa**", 1)[1]
    rows = re.findall(r"^\| `(\w+)` \| (\w+) \| (`?\w+`?) \| ([^|]+) \|", text.split("\n\n")[1], flags=re.M)
    fsd = {n: (t, s.strip("`"), sz.strip()) for n, t, s, sz in rows}
    csv = _sizes(ROOT / "research/firmware/partitions.csv")
    assert set(fsd) == set(csv), (sorted(fsd), sorted(csv))
    for name, (typ, sub, size_text) in fsd.items():
        assert csv[name][:2] == (typ, sub), (name, csv[name], fsd[name])
        if name != "espeak":
            num, unit = size_text.split()
            assert csv[name][2] == int(num) * {"KB": 1024, "MB": 1024 * 1024}[unit], (name, size_text)
    off = 0x9000
    for name in ("nvs", "otadata", "phy_init"):
        off += csv[name][2]
    for name in ("ota_0", "ota_1"):
        off = (off + 0xFFFF) & ~0xFFFF
        off += csv[name][2]
    assert off + csv["espeak"][2] == 16 * 1024 * 1024, "espeak does not take the rest of the 16 MB flash"
