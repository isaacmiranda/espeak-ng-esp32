#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Regenerates the compiled eSpeak NG data of this package from its own sources (FSD FR-LIC-04, FR-DAT-08).
# Runs on the host with an espeak-ng 1.52.0 command line; the layout is the package's:
#   phsource/  dictsource/  data-src/  espeak-ng-data/ (the compiled data shipped)
#
#   regen-data.sh --check               compile into a temporary directory and compare, byte for byte, with espeak-ng-data/
#   regen-data.sh --out DIR             compile into DIR (a fresh espeak-ng-data tree)
#   --listx FILE                        add an integrator's <lang>_listx file to that language's dictionary (repeatable)
#   --langs "pt en"                     compile only these dictionaries (default: every <lang>_dict of espeak-ng-data/)
#   ESPEAK_NG=<binary>                  the command line to use (default: espeak-ng in PATH)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="${ESPEAK_NG:-espeak-ng}"
mode="" out="" langs="" listx=()
while [ $# -gt 0 ]; do
  case "$1" in
    --check) mode=check ;;
    --out) out="$2"; mode=out; shift ;;
    --listx) listx+=("$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"); shift ;;
    --langs) langs="$2"; shift ;;
    *) echo "usage: regen-data.sh (--check | --out DIR) [--listx FILE]... [--langs \"a b\"]" >&2; exit 2 ;;
  esac
  shift
done
[ -n "$mode" ] || { echo "FATAL: say --check or --out DIR" >&2; exit 2; }
ver=$("$BIN" --version | sed -n 's/^eSpeak NG text-to-speech: \([0-9.]*\).*/\1/p')
[ "$ver" = "1.52.0" ] || { echo "FATAL: $BIN is eSpeak NG '$ver', this package needs 1.52.0" >&2; exit 1; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
root="$work/root"
mkdir -p "$root/espeak-ng-data/voices"
cp -r "$HERE/data-src/lang" "$root/espeak-ng-data/"
cp -r "$HERE/data-src/voices/!v" "$root/espeak-ng-data/voices/"
cp -r "$HERE/phsource" "$root/phsource"
export ESPEAK_DATA_PATH="$root"
( cd "$root/phsource" && "$BIN" --compile-intonations && "$BIN" --compile-phonemes ) > /dev/null
if [ -z "$langs" ]; then
  langs=$(cd "$HERE/espeak-ng-data" && ls | sed -n 's/_dict$//p' | tr '\n' ' ')
fi
for l in $langs; do
  d="$work/dict-$l"
  mkdir "$d"
  cp "$HERE/dictsource/${l}_rules" "$HERE/dictsource/${l}_list" "$d/"
  if [ -f "$HERE/dictsource/extra/${l}_listx" ]; then cp "$HERE/dictsource/extra/${l}_listx" "$d/"
  elif [ -f "$HERE/dictsource/${l}_listx" ]; then cp "$HERE/dictsource/${l}_listx" "$d/"; fi
  [ -f "$HERE/dictsource/${l}_emoji" ] && cp "$HERE/dictsource/${l}_emoji" "$d/"
  for x in "${listx[@]}"; do
    [ "$(basename "$x")" = "${l}_listx" ] && cp "$x" "$d/${l}_listx"
  done
  ( cd "$d" && "$BIN" --compile="$l" ) > /dev/null 2>&1 || { echo "FATAL: compiling $l failed" >&2; exit 1; }
done
if [ "$mode" = out ]; then
  mkdir -p "$out"
  cp -r "$root/espeak-ng-data/." "$out/"
  echo "regenerated into $out"
  exit 0
fi
bad=0
for f in intonations phondata phondata-manifest phonindex phontab $(for l in $langs; do echo "${l}_dict"; done); do
  if ! cmp -s "$root/espeak-ng-data/$f" "$HERE/espeak-ng-data/$f"; then echo "DIFFERS: $f" >&2; bad=1; fi
done
[ $bad = 0 ] && echo "ok: the regenerated data equals the package's"
exit $bad
