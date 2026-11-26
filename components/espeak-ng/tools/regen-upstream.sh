#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Regenerates components/espeak-ng/upstream/ from the pinned eSpeak NG tarball
# (FSD CON-ENG-01, CON-ENG-02). The SHA-256 is checked before anything is extracted;
# running it again must leave `git diff` empty. All libespeak-ng sources are kept as
# shipped; which of them are compiled (the synchronous runtime only, CON-ENG-03) is the
# component's CMakeLists.txt.
#
#   components/espeak-ng/tools/regen-upstream.sh
#   ESPK_TARBALL=<file>  use this tarball instead of the cached download
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=upstream.env
. "$HERE/upstream.env"
DST="$(cd "$HERE/.." && pwd)/upstream"
CACHE="${ESPK_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/espk}"
tgz="${ESPK_TARBALL:-$CACHE/espeak-ng-$ESPEAK_VER.tar.gz}"

if [ ! -f "$tgz" ]; then
  mkdir -p "$(dirname "$tgz")"
  curl -sSLf -o "$tgz.part" "$ESPEAK_URL" && mv "$tgz.part" "$tgz"
fi
got=$(sha256sum "$tgz" | cut -d' ' -f1)
if [ "$got" != "$ESPEAK_SHA256" ]; then
  echo "FATAL: sha256 of $tgz is $got, expected $ESPEAK_SHA256; nothing extracted" >&2
  exit 1
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
tar -xzf "$tgz" -C "$work"
SRC="$work/espeak-ng-$ESPEAK_VER"
stage="$work/upstream"
mkdir -p "$stage/src/libespeak-ng" "$stage/src/include/espeak-ng" \
         "$stage/src/ucd-tools/src/include/ucd"
cp "$SRC"/COPYING "$SRC"/COPYING.APACHE "$SRC"/COPYING.BSD2 "$SRC"/COPYING.UCD "$stage/"
cp "$SRC"/src/libespeak-ng/*.c "$SRC"/src/libespeak-ng/*.h "$stage/src/libespeak-ng/"
cp "$SRC"/src/include/espeak-ng/*.h "$stage/src/include/espeak-ng/"
cp "$SRC"/src/ucd-tools/src/*.c "$stage/src/ucd-tools/src/"
cp "$SRC"/src/ucd-tools/src/include/ucd/*.h "$stage/src/ucd-tools/src/include/ucd/"
[ -f "$SRC/src/ucd-tools/COPYING" ] && cp "$SRC/src/ucd-tools/COPYING" "$stage/src/ucd-tools/"
# files keep the tarball's bytes; timestamps are irrelevant to git
rm -rf "$DST"
mv "$stage" "$DST"
echo "upstream $ESPEAK_VER: $(find "$DST" -type f | wc -l) files in $DST"
