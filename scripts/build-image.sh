#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Builds the research firmware's data image from the R1 build of the pinned upstream.
#   scripts/build-image.sh <out.img> [voices, default pt-br,en]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3}"
data=$("$PY" -c "import sys; sys.path.insert(0, '$ROOT/tools/ref'); import r1; print(r1.build(r1.upstream()) / 'espeak-ng-data')")
"$PY" "$ROOT/components/espeak-ng/tools/gen_image.py" --data "$data" --voices "${2:-pt-br,en}" --out "$1"
