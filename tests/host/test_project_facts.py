# SPDX-License-Identifier: GPL-3.0-or-later
"""Facts about the repository that the FSD turns into requirements.

Licences (CON-LIC-01, 02, 05), the package (FR-REL-02, FR-REL-04), pinned tools (CON-BLD-01), the CI
workflows (FR-BLD-02, FR-BLD-03) and what no document may claim (FR-DOC-03)."""

import json
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
COMP = ROOT / "components/espeak-ng"
REUSE = ROOT / ".venv/bin/reuse"
GPL_COMPATIBLE = {
    "GPL-3.0-or-later",
    "GPL-3.0-only",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "MIT",
    "ISC",
    "LGPL-3.0-or-later",
    "CC0-1.0",
    "0BSD",
}


def _reuse_json():
    exe = str(REUSE) if REUSE.exists() else "reuse"
    p = subprocess.run([exe, "lint", "--json"], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout)


def test_reuse_lint_passes_and_every_own_file_is_gpl():
    """CON-LIC-01: `reuse lint` is green (third-party files through REUSE.toml) and the
    project's own sources carry GPL-3.0-or-later."""
    rc, d = _reuse_json()
    assert rc == 0 and d["summary"]["compliant"] and not d["non_compliant"]["missing_licensing_info"]
    own = [
        f for f in d["files"] if f["path"].startswith(("components/espeak-ng/src/", "tests/", "tools/ref/"))
    ]
    assert own
    wrong = [f["path"] for f in own if [x["value"] for x in f["spdx_expressions"]] != ["GPL-3.0-or-later"]]
    assert not wrong, f"own files not GPL-3.0-or-later: {wrong[:5]}"


def test_the_package_carries_the_licences():
    """CON-LIC-02: LICENSE (GPL-3.0) and the upstream's COPYING, COPYING.APACHE, COPYING.BSD2, COPYING.UCD."""
    assert (
        "GNU GENERAL PUBLIC LICENSE" in (COMP / "LICENSE").read_text()
        and "Version 3" in (COMP / "LICENSE").read_text()
    )
    for name in ("COPYING", "COPYING.APACHE", "COPYING.BSD2", "COPYING.UCD"):
        assert (COMP / "upstream" / name).is_file(), name


def test_every_file_of_the_package_is_gpl_compatible_and_there_is_no_logo():
    """CON-LIC-05: nothing in the package folder under a licence the GPL cannot take, and no logo."""
    _rc, d = _reuse_json()
    bad = {}
    for f in d["files"]:
        if f["path"].startswith("components/espeak-ng/"):
            lic = {x["value"] for x in f["spdx_expressions"]}
            flat = {t for e in lic for t in re.split(r"\s+(?:AND|OR|WITH)\s+|[()]", e) if t.strip()}
            if flat - GPL_COMPATIBLE - {""}:
                bad[f["path"]] = sorted(flat - GPL_COMPATIBLE)
    assert not bad, f"licences outside the compatible set: {dict(list(bad.items())[:5])}"
    logos = [p for p in COMP.rglob("*") if "logo" in p.name.lower()]
    assert not logos, f"a logo is in the package: {logos}"


def test_the_component_version_is_its_own_semver_and_the_upstream_is_in_origin():
    """FR-REL-02: 0.1.0 as its own SemVer; the upstream's version in ORIGIN.md and the manifest."""
    m = yaml.safe_load((COMP / "idf_component.yml").read_text())
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(m["version"])), m["version"]
    assert str(m["version"]) == "0.1.0"
    upstream = dict(
        line.split("=", 1)
        for line in (COMP / "tools/upstream.env").read_text().splitlines()
        if "=" in line and not line.startswith("#")
    )["ESPEAK_VER"]
    assert upstream in (COMP / "ORIGIN.md").read_text()
    assert upstream.rsplit(".", 1)[0] in m["description"] or "1.52" in m["description"]


def test_the_package_folder_has_no_research_seed_bench_or_docs():
    """FR-REL-04: the package is the folder components/espeak-ng/, and none of those is inside it."""
    inside = {p.name for p in COMP.rglob("*") if p.is_dir()} | {p.name for p in COMP.iterdir()}
    assert not ({"research", "seed", "bench", "docs"} & inside), sorted(
        {"research", "seed", "bench", "docs"} & inside
    )


def test_every_tool_the_ci_and_the_notebook_install_has_an_exact_version():
    """CON-BLD-01: requirements with ==, the pinned ESP-IDF, the pinned upstream, a locked dependency
    set, and no unpinned installs in the workflows. (whisper.cpp and its model are not installed yet.)"""
    for line in (ROOT / "requirements.txt").read_text().splitlines():
        if line.strip() and not line.startswith(("#", "-e")):
            assert "==" in line, f"unpinned requirement: {line}"
    assert "v5.5.5" in (ROOT / "scripts/idf.sh").read_text()
    env = (COMP / "tools/upstream.env").read_text()
    assert re.search(r"ESPEAK_SHA256=[0-9a-f]{64}", env)
    assert (ROOT / "research/firmware/dependencies.lock").is_file()
    for wf in (ROOT / ".github/workflows").glob("*.yml"):
        text = wf.read_text()
        assert "apt-get install" not in text, f"{wf.name}: an apt install has no exact version"
        for m in re.finditer(r"pip install (?!-q )(?:-r \S+|(\S+))", text):
            assert m.group(1) is None or "==" in m.group(1), f"{wf.name}: {m.group(0)}"
        assert not re.search(r"container: \S+:(latest|\S*[a-z]$)", text), (
            f"{wf.name}: a container without a version"
        )


def _workflow(name):
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def test_the_hosted_ci_runs_on_every_push_with_lint_licences_host_tests_and_the_build():
    """FR-BLD-02 (what exists: lint, reuse lint, host and driver tests, the firmware build; the examples'
    builds of FSD 18 are the next test)."""
    ci = _workflow("ci.yml")
    assert "push" in ci[True] and ci[True]["push"]["branches"] == ["**"]
    steps = " ".join(str(s.get("run", "")) for j in ci["jobs"].values() for s in j["steps"])
    for needed in ("ruff check", "reuse lint", "pytest -q tools/bench tests/host", "idf.py"):
        assert needed in steps, f"the CI does not run {needed!r}"


def test_the_hosted_ci_builds_the_examples_for_each_chip():
    """FR-BLD-02 (the builds of FSD 18) and FR-EXM-02: hello for esp32, esp32s2, esp32s3 and esp32p4, and the
    waveshare example, in the pinned ESP-IDF container, from the compiled data the host job publishes."""
    jobs = _workflow("ci.yml")["jobs"]
    ex = jobs["examples"]
    assert sorted(ex["strategy"]["matrix"]["chip"]) == ["esp32", "esp32p4", "esp32s2", "esp32s3"]
    assert ex["container"] == "espressif/idf:v5.5.5"
    text = json.dumps(ex["steps"])
    assert "examples/hello" in text and "IDF_TARGET=${{ matrix.chip }}" in text and "ESPK_DATA_DIR" in text
    assert "examples/waveshare-s3-rlcd" in json.dumps(jobs["example-waveshare"]["steps"])
    assert any("espeak-data" in json.dumps(s) for s in jobs["host"]["steps"]), (
        "the host does not publish the data"
    )


def test_board_tests_run_only_from_a_tag_on_the_notebook_runner_with_the_tags_artifact():
    """FR-BLD-03."""
    rel = _workflow("release.yml")
    assert list(rel[True]) == ["push"] and set(rel[True]["push"]) == {"tags"}
    job = rel["jobs"]["release-verify"]
    assert job["runs-on"] == ["self-hosted", "bench-notebook"]
    text = json.dumps(job)
    assert "--run-bench" in text and "ESPK_ARTIFACT" in text and "download-artifact" in text
    for name in ("ci.yml",):
        assert "--run-bench" not in (ROOT / ".github/workflows" / name).read_text()


MARKERS = re.compile(r"nunca|never|avoid|cannot|deve afirmar|nenhum documento|refut|não|must not", re.I)
CLAIMS = [
    re.compile(r"primeiro\s+TTS\s+pt-?BR\s+offline", re.I),
    re.compile(r"first\s+offline\s+pt-?BR\s+TTS", re.I),
    re.compile(r"intelligibility\s+(?:of|was|is|reached)\s+\d+\s*%", re.I),
    re.compile(r"inteligibilidade\s+(?:de|foi|é|chegou a)\s+\d+\s*%", re.I),
]


def test_no_document_claims_the_first_offline_ptbr_tts_or_a_listener_result():
    """FR-DOC-03: such a phrase may appear only to forbid it."""
    hits = []
    for md in ROOT.rglob("*.md"):
        rel = md.relative_to(ROOT).as_posix()
        if rel.startswith(("seed/", ".claude/", ".venv/", "test-results/")):
            continue
        for n, line in enumerate(md.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if any(c.search(line) for c in CLAIMS) and not MARKERS.search(line):
                hits.append(f"{rel}:{n}: {line.strip()[:100]}")
    assert not hits, "claims without a prohibition around them:\n" + "\n".join(hits)


def test_ai_use_exists_in_english_and_portuguese_and_names_the_human_decisions():
    """FR-AIU-01."""
    en = (ROOT / "AI-USE.md").read_text(encoding="utf-8")
    pt = (ROOT / "AI-USE.pt-BR.md").read_text(encoding="utf-8")
    assert "What only a person decides" in en and "O que só uma pessoa decide" in pt
    for text in (en, pt):
        assert "tag" in text.lower() and "CEP" in text and len(text.splitlines()) > 20
