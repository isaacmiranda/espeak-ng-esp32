# SPDX-License-Identifier: GPL-3.0-or-later
"""The system eSpeak NG's synchronous API, driven through ctypes (R2, FSD 7): the steps of pcm_script.c.

    r2_api.py <espeak-ng-data dir> <voice> <out dir>      texts on stdin, one per line

`init en`, `voice <voice>`, then one `say` per line; the PCM of the k-th say goes to <out dir>/<k>.pcm.
Prints the library's sample rate. Exit 0 when every step answered ENS_OK.
"""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

ENOUTPUT_MODE_SYNCHRONOUS = 1
POS_CHARACTER = 1
ESPEAK_CHARS_UTF8 = 1
CALLBACK = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)


def main(argv: list[str]) -> int:
    data, voice, out = argv[0], argv[1], Path(argv[2])
    lib = ctypes.CDLL("libespeak-ng.so.1")
    lib.espeak_ng_InitializePath(data.encode())
    if (
        lib.espeak_ng_Initialize(None) != 0
        or lib.espeak_ng_InitializeOutput(ENOUTPUT_MODE_SYNCHRONOUS, 0, None) != 0
    ):
        return 3
    chunks: list[bytes] = []

    def on_pcm(wav, n, _ev):
        if wav and n > 0:
            chunks.append(ctypes.string_at(wav, n * 2))
        return 0

    cb = CALLBACK(on_pcm)  # kept alive for the whole run
    lib.espeak_SetSynthCallback(cb)
    for name in ("en", voice):
        if lib.espeak_ng_SetVoiceByName(name.encode()) != 0:
            return 4
    out.mkdir(parents=True, exist_ok=True)
    for k, text in enumerate(sys.stdin.read().splitlines()):
        chunks.clear()
        raw = text.encode()
        lib.espeak_ng_Synthesize(raw, len(raw) + 1, 0, POS_CHARACTER, 0, ESPEAK_CHARS_UTF8, None, None)
        lib.espeak_ng_Synchronize()
        (out / f"{k:04d}.pcm").write_bytes(b"".join(chunks))
    print(f"rate={lib.espeak_ng_GetSampleRate()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
