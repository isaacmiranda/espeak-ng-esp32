# SPDX-License-Identifier: GPL-3.0-or-later
"""FR-REF-02: the component's sources and configuration, built on the host, say what R1 says, say by say.
FR-SEC-02: bytes that are not valid UTF-8 neither panic nor reset the engine: under the AddressSanitizer."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ref"))
sys.path.insert(0, str(ROOT / "tests"))
import board  # noqa: E402
import r1  # noqa: E402
import r3host  # noqa: E402

# Not UTF-8, in the ways a text can fail to be: a lone continuation byte, truncated sequences, overlong forms,
# surrogates, bytes that never occur, five- and six-byte forms, a long run, and bad bytes inside valid text.
HOSTILE = {
    "continuation": b"\x80",
    "truncated2": b"\xc3",
    "truncated3": b"\xe2\x82",
    "truncated4": b"\xf0\x9f\x98",
    "overlong": b"\xc0\x80 \xe0\x80\x80 \xf0\x80\x80\x80",
    "surrogates": b"\xed\xa0\x80 \xed\xbf\xbf",
    "never": b"\xff\xfe\xfd",
    "five_six_bytes": b"\xf8\x88\x80\x80\x80 \xfc\x84\x80\x80\x80\x80",
    "above_10ffff": b"\xf4\x90\x80\x80",
    "long_run": b"\x80\xbf" * 400,
    "inside_text": b"Aten\xe7\xe3o: a bateria est\xe1 fraca.",
    "mixed": "Atenção ".encode() + b"\xff" + " está ".encode() + b"\xc3" + b"\x28",
    "ssml_and_control": b"<speak>\x01\x02\x1b[31m\xff</speak> \x7f",
}


def test_the_component_built_on_the_host_equals_r1_over_the_verification_corpus():
    """FR-REF-02: the vendored sources and the component's config.h, host-built, against R1 (the tarball
    built by the upstream's own CMake): the SHA-256 of each say's PCM, in the corpus order."""
    script = board.verify_script()
    mine = r3host.run(script)
    ref = r1.run(script)
    assert len(mine) == len(ref) >= 100
    pairs = enumerate(zip(mine, ref, strict=True))
    diffs = [(k, a["sha256"][:12], b["sha256"][:12]) for k, (a, b) in pairs if a["sha256"] != b["sha256"]]
    assert not diffs, f"{len(diffs)} says differ, first: {diffs[0]}"


@pytest.mark.parametrize("voice", ["en", "pt-br"])
@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_invalid_utf8_does_not_crash_the_engine_under_asan(name, voice):
    """FR-SEC-02: one process per input, so a failure of one says which."""
    script = f"init {voice}\nsay ".encode() + HOSTILE[name] + b"\nsay Ol\xc3\xa1, tudo bem?\n"
    p, _tmp = r3host.run_raw(script, sanitize=True)
    err = p.stderr.decode(errors="replace")
    assert "AddressSanitizer" not in err, err[:600]
    assert p.returncode >= 0 and p.returncode < 128, f"killed by a signal ({p.returncode}): {err[:300]}"
