# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-DOC-01 (a translation says which revision of its source it translates) and FR-DOC-02 (the release
job fails when a source changed after that revision), through tools/docs/check_translations.py."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/docs/check_translations.py"


def run(root, *args):
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root), *args], capture_output=True, text=True
    )


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    """A repository with a source, its translation at the source's revision, and the table."""
    (tmp_path / "tools/docs").mkdir(parents=True)
    (tmp_path / "tools/docs/translations.yaml").write_text(
        "translations:\n  - {source: A.md, translation: A.pt-BR.md}\n"
    )
    (tmp_path / "A.md").write_text("# A\n")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.org")
    git(tmp_path, "config", "user.name", "t")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "source")
    rev = git(tmp_path, "rev-parse", "--short", "HEAD")
    (tmp_path / "A.pt-BR.md").write_text(f"<!-- source-revision: {rev} -->\n# A\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "translation")
    return tmp_path


def test_every_translation_of_the_project_carries_its_source_revision():
    """FR-DOC-01."""
    p = run(ROOT)
    assert p.returncode == 0, p.stderr


def test_a_translation_without_the_field_is_refused(repo):
    (repo / "A.pt-BR.md").write_text("# A\n")
    p = run(repo)
    assert p.returncode == 1 and "source-revision" in p.stderr


def test_a_source_changed_after_its_translation_fails_the_release_check(repo):
    """FR-DOC-02: the release check is red; the ordinary check, which only wants the field, stays green."""
    assert run(repo, "--release").returncode == 0
    (repo / "A.md").write_text("# A changed\n")
    git(repo, "commit", "-qam", "change the source")
    p = run(repo, "--release")
    assert p.returncode == 1 and "A.md changed after source-revision" in p.stderr
    assert run(repo).returncode == 0


def test_the_release_job_runs_the_check():
    """FR-DOC-02: the release workflow runs it with --release, before the board is touched."""
    text = (ROOT / ".github/workflows/release.yml").read_text()
    assert "check_translations.py --release" in text and "needs: [build, translations]" in text
