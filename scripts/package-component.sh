#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Assembles the component package folder (FSD FR-LIC-03, CON-LIC-02, CON-LIC-05): the component, the compiled data of
# every language, phsource/ and dictsource/ of the same tarball, and the regeneration script. Never committed.
#   scripts/package-component.sh <out-dir>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3}"
out="${1:?usage: package-component.sh <out-dir>}"
[ ! -e "$out" ] || [ -z "$(ls -A "$out")" ] || { echo "FATAL: $out is not empty" >&2; exit 1; }
eval "$("$PY" - <<PYEOF
import sys
sys.path.insert(0, "$ROOT/tools/ref")
import r1
up = r1.upstream()
src = r1.cache_dir() / f"src-{up['ESPEAK_VER']}" / f"espeak-ng-{up['ESPEAK_VER']}"
print(f'src="{src}"; data="{r1.build(up) / "espeak-ng-data"}"')
PYEOF
)"
mkdir -p "$out"
tar -C "$ROOT/components/espeak-ng" --exclude=__pycache__ --exclude=tools/regen-data.sh -cf - . | tar -C "$out" -xf -
cp "$ROOT/components/espeak-ng/tools/regen-data.sh" "$out/regen-data.sh"
cp "$ROOT/LICENSE" "$out/LICENSE"
for f in COPYING COPYING.APACHE COPYING.BSD2 COPYING.UCD; do cp "$src/$f" "$out/$f"; done
cp -r "$data" "$out/espeak-ng-data"
cp -r "$src/phsource" "$out/phsource"
cp -r "$src/dictsource" "$out/dictsource"
mkdir -p "$out/data-src"
cp -r "$src/espeak-ng-data/lang" "$out/data-src/lang"
mkdir -p "$out/data-src/voices"
cp -r "$src/espeak-ng-data/voices/!v" "$out/data-src/voices/!v"
echo "package assembled in $out"
