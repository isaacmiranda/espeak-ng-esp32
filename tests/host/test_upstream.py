# SPDX-License-Identifier: GPL-3.0-or-later
"""CON-ENG-01, CON-ENG-02: the upstream sources come only from the pinned tarball, untouched."""

import hashlib
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGEN = ROOT / "components/espeak-ng/tools/regen-upstream.sh"
UPSTREAM = ROOT / "components/espeak-ng/upstream"



def tree_digest(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in path.rglob("*") if p.is_file()):
        h.update(str(f.relative_to(path)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def test_wrong_tarball_is_refused_before_extraction(tmp_path):
    before = tree_digest(UPSTREAM) if UPSTREAM.exists() else None
    fake = tmp_path / "espeak-ng-1.52.0.tar.gz"
    fake.write_bytes(b"not the upstream tarball")
    env = {**os.environ, "ESPK_TARBALL": str(fake)}
    p = subprocess.run([str(REGEN)], env=env, capture_output=True, text=True)
    assert p.returncode != 0
    assert "sha256" in (p.stdout + p.stderr).lower()
    after = tree_digest(UPSTREAM) if UPSTREAM.exists() else None
    assert after == before, "upstream/ changed after a refused tarball"


def test_regeneration_is_idempotent():
    p = subprocess.run([str(REGEN)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    diff = subprocess.run(["git", "status", "--porcelain", "--", str(UPSTREAM)],
                          cwd=ROOT, capture_output=True, text=True)
    assert diff.stdout == "", f"regeneration changed upstream/:\n{diff.stdout}"
