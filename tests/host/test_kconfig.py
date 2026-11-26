# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-CFG-01: every option of the FSD's configuration catalogue (section 19) exists in the component's Kconfig
with the catalogue's default; the Kconfig has no option the catalogue does not list."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FSD = ROOT / "docs/Functionality/FSD.md"
KCONFIG = ROOT / "components/espeak-ng/Kconfig"


def _norm(v: str) -> str:
    v = v.strip().strip("`").strip('"')
    low = v.lower()
    if low.startswith("desligado"):
        return "n"
    if low.startswith("ligado"):
        return "y"
    if low == "sem afinidade":
        return "-1"
    return re.sub(r"\s+", "", v)  # 2 048 -> 2048


def _catalogue() -> dict[str, str]:
    text = FSD.read_text(encoding="utf-8")
    section = text.split("## 19. Catálogo de configuração", 1)[1].split("- **FR-CFG-01**", 1)[0]
    rows = re.findall(r"^\| `CONFIG_(ESPK_\w+)` \| ([^|]+?) \|", section, flags=re.M)
    return {name: _norm(default) for name, default in rows}


def _kconfig() -> dict[str, str]:
    out = {}
    for block in re.split(r"^\s*config ", KCONFIG.read_text(), flags=re.M)[1:]:
        name = block.split()[0]
        m = re.search(r"^\s*default\s+(.+)$", block, flags=re.M)
        out[name] = _norm(m.group(1)) if m else ""
    return out


def test_the_kconfig_has_every_catalogue_option_with_its_default():
    cat, kc = _catalogue(), _kconfig()
    assert len(cat) >= 17, f"the catalogue was not read: {cat}"
    missing = sorted(set(cat) - set(kc))
    assert not missing, f"options of the catalogue absent from the Kconfig: {missing}"
    wrong = {k: (cat[k], kc[k]) for k in cat if k in kc and cat[k] != kc[k]}
    assert not wrong, f"defaults differ (catalogue, Kconfig): {wrong}"


def test_the_kconfig_has_no_option_outside_the_catalogue():
    extra = sorted(set(_kconfig()) - set(_catalogue()))
    assert not extra, f"options not in the catalogue (add them to FSD section 19): {extra}"
