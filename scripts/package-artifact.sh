#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Packs a firmware build into the CI artifact (FSD FR-BLD-04): every file named by
# flash_args at its relative path, flash_args itself and a manifest.
#   scripts/package-artifact.sh <build-dir> <out-dir>
set -euo pipefail
build=$1 out=$2
[ -f "$build/flash_args" ] || { echo "no flash_args in $build" >&2; exit 1; }
mkdir -p "$out"
head -n 1 "$build/flash_args" > "$out/flash_args"
tail -n +2 "$build/flash_args" | while read -r off path; do
  [ -n "$path" ] || continue
  src="$build/$path"
  # a file outside the build dir (the data image) comes inside the artifact by its name
  case "$path" in /*|*..*) path=$(basename "$path") ;; esac
  mkdir -p "$out/$(dirname "$path")"
  cp "$src" "$out/$path"
  echo "$off $path" >> "$out/flash_args"
done
{
  echo "commit: $(git rev-parse HEAD)"
  echo "ref: ${GITHUB_REF:-local}"
  echo "idf: $(idf.py --version 2>/dev/null | tr -d '\n' || echo unknown)"
  echo "built: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "files:"
  (cd "$out" && find . -type f ! -name manifest.yaml | sort | xargs sha256sum | awk '{print "  \"" $2 "\": " $1}')
} > "$out/manifest.yaml"
echo "artifact in $out"
