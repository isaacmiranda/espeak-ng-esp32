# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-ENG-04: the ucd-tools functions the wrap installs agree with the desktop libc.

The board's libc (newlib, C locale) knows no letter beyond ASCII (#1611). The wrap sends the
engine's isw*/tow* calls to ucd-tools, so R3 = R1 holds only where ucd-tools and the desktop libc
agree. They agree on Latin, Greek, Cyrillic and Latin Extended Additional (U+0000-U+052F,
U+1E00-U+1EFF) except, at most, for the code points below, which the FSD lists as known differences
(the desktop libc's Unicode tables move with its version: a newer glibc differs on more of them,
an older one on fewer; the CI runner and the bench notebook differ).
"""

import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UCD = ROOT / "components/espeak-ng/upstream/src/ucd-tools/src"

KNOWN = {
    "alpha": {*range(0x363, 0x370)},
    "alnum": {0xB2, 0xB3, 0xB9, 0xBC, 0xBD, 0xBE, *range(0x363, 0x370)},
    "lower": {0x295},
    "punct": {0xA0, 0xAD, 0xB2, 0xB3, 0xB9, 0xBC, 0xBD, 0xBE, *range(0x363, 0x370)},
    "space": {0x85},
}


def test_ucd_tools_agree_with_the_desktop_libc_except_the_listed_code_points(tmp_path):
    exe = tmp_path / "ucd_agree"
    srcs = [UCD / f"{n}.c" for n in ("case", "categories", "ctype", "proplist", "scripts", "tostring")]
    subprocess.run(["cc", "-O1", "-I", str(UCD / "include"), str(ROOT / "tests/host/ucd_agree.c"),
                    *map(str, srcs), "-o", str(exe)], check=True)
    out = subprocess.run([str(exe)], capture_output=True, text=True, check=True).stdout
    got = defaultdict(set)
    for line in out.splitlines():
        name, cp = line.split()
        got[name].add(int(cp[2:], 16))
    # an older or newer libc may agree on more; none may disagree anywhere else
    unexpected = {k: sorted(v - KNOWN.get(k, set())) for k, v in got.items() if v - KNOWN.get(k, set())}
    assert not unexpected, f"differences outside the listed code points: {unexpected}"
