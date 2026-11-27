# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-LIC-03 (the package holds the compiled data, the sources and the script), CON-LIC-02, CON-LIC-05,
FR-LIC-04 (the regeneration from the package's own sources gives the package's data byte for byte) and
FR-DAT-08 (an integrator's *_listx reaches the dictionary of its language)."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ref"))
import r1  # noqa: E402

NICE = ["nice", "-n", "15", "ionice", "-c", "2", "-n", "7"]


@pytest.fixture(scope="module")
def r1_bin():
    return r1.build(r1.upstream()) / "src/espeak-ng"


@pytest.fixture(scope="module")
def scratch():
    """A directory on the disk, not the tmpfs /tmp (the package is about 75 MB)."""
    base = r1.cache_dir() / "tmp"
    base.mkdir(parents=True, exist_ok=True)
    d = Path(tempfile.mkdtemp(dir=base))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def package(scratch, r1_bin):
    out = scratch / "espeak-ng"
    subprocess.run(
        [*NICE, str(ROOT / "scripts/package-component.sh"), str(out)], check=True, capture_output=True
    )
    return out


def regen(package, r1_bin, *args):
    env = {"PATH": "/usr/bin:/bin", "ESPEAK_NG": str(r1_bin), "TMPDIR": str(package.parent)}
    return subprocess.run(
        [*NICE, str(package / "regen-data.sh"), *args], env=env, capture_output=True, text=True
    )


def test_the_package_has_the_data_the_sources_the_script_and_the_licences(package):
    for name in (
        "CMakeLists.txt",
        "idf_component.yml",
        "regen-data.sh",
        "LICENSE",
        "COPYING",
        "COPYING.APACHE",
        "COPYING.BSD2",
        "COPYING.UCD",
    ):
        assert (package / name).is_file(), name
    data = {p.name for p in (package / "espeak-ng-data").iterdir()}
    assert {"phondata", "phontab", "phonindex", "intonations", "pt_dict", "en_dict", "ru_dict"} <= data
    assert (package / "phsource/phonemes").is_file() and (package / "dictsource/pt_rules").is_file()
    assert not list(package.rglob("__pycache__"))
    assert not list(package.rglob("*.svg")) and not list(package.rglob("*.png")), (
        "a logo is outside the package"
    )


def test_regeneration_from_the_package_sources_reproduces_the_data_byte_for_byte(package, r1_bin):
    r = regen(package, r1_bin, "--check")
    assert r.returncode == 0, r.stderr
    assert "ok" in r.stdout


def test_an_extra_listx_reaches_the_dictionary_of_its_language(package, r1_bin, scratch):
    listx = scratch / "pt_listx"
    listx.write_text("zzqxword  zz'Qx@\n")
    out = scratch / "data"
    r = regen(package, r1_bin, "--out", str(out), "--langs", "pt", "--listx", str(listx))
    assert r.returncode == 0, r.stderr
    assert (package / "espeak-ng-data/pt_dict").read_bytes() != (out / "pt_dict").read_bytes()
    # the data path of the binary is a tree whose pt_dict is the regenerated one
    shadow = scratch / "shadow/espeak-ng-data"
    shadow.mkdir(parents=True)
    for item in (package / "espeak-ng-data").iterdir():
        (shadow / item.name).symlink_to(item)
    (shadow / "pt_dict").unlink()
    (shadow / "pt_dict").symlink_to(out / "pt_dict")
    run = lambda data: subprocess.run(  # noqa: E731
        [str(r1_bin), "-q", "-x", "-v", "pt", "zzqxword"],
        env={"ESPEAK_DATA_PATH": str(data)},
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert run(shadow.parent) != run(package), "the extra entry did not change the phonemes of the word"
