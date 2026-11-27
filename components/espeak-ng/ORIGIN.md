<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# Origin of the engine

This component packages **eSpeak NG** as an ESP-IDF component. The engine is not ours.

| | |
|---|---|
| Upstream | https://github.com/espeak-ng/espeak-ng |
| Version | **1.52.0** |
| Tarball | `https://github.com/espeak-ng/espeak-ng/archive/refs/tags/1.52.0.tar.gz` |
| SHA-256 | `bb4338102ff3b49a81423da8a1a158b420124b055b60fa76cfb4b18677130a23` |
| Licence | GPL-3.0-or-later, with the parts under `upstream/COPYING.APACHE`, `COPYING.BSD2`, `COPYING.UCD` |

The sources under `upstream/` are the tarball's, **unmodified** (the regeneration script, run again, leaves no
`git diff`). Where the engine needed help on the ESP32 the component works around it at link time
(`src/espk_wrap.c`, `linker.lf`), never by editing the upstream.

The version of this component follows its own SemVer, starting at 0.1.0 (see `idf_component.yml`); the upstream
version above is the one it packages.

## Upstream contribution

The ESP32 libc knows no letter beyond ASCII, so the engine spells accented text letter by letter
(upstream issue espeak-ng#1611). The component redirects the engine's `isw*` calls to the upstream's own
`ucd-tools`. A pull request to `espeak-ng/espeak-ng` that makes the engine use `ucd-tools` for these
classifications is **not open yet**; its link goes here when it is.
