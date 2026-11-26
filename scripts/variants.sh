#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Builds, packs, flashes and tests the research firmware's configuration variants, one at a time
# (heavy: each is a full build; low priority, two jobs). The variants prove what a normal build cannot:
#   intact    CONFIG_ESPK_UCD_WRAP off            FR-ENG-05      tests/target/test_intact.py
#   sync      CONFIG_ESPK_ASYNC off               FR-ASY-08      tests/target/test_async_off.py
#   nolabel   a partition label the table lacks   FR-DAT-02      tests/target/test_variants.py
#   nosubtype the right label, another subtype    FR-DAT-01      tests/target/test_variants.py
#   nopsram   built without PSRAM                 FR-MEM-01      tests/target/test_variants.py
#   mount     another VFS mount point             FR-CFG-02      tests/target/test_variants.py
#   scripts/variants.sh [name...]      (default: all). Needs /tmp/espeak.img (scripts/build-image.sh) and a board.
set -euo pipefail
cd "$(dirname "$0")/.."
img=${ESPK_IMAGE:-/tmp/espeak.img}
[ -f "$img" ] || { echo "no data image at $img: run scripts/build-image.sh $img" >&2; exit 1; }
names=("$@"); [ ${#names[@]} -gt 0 ] || names=(intact sync nolabel nosubtype nopsram mount)
declare -A test_file=([intact]=test_intact [sync]=test_async_off [nolabel]=test_variants [nosubtype]=test_variants [nopsram]=test_variants [mount]=test_variants)
for n in "${names[@]}"; do
  b=research/firmware/build-$n
  echo "== $n: build"
  (cd research/firmware && nice -n 15 ionice -c 2 -n 7 ../../scripts/idf.sh env ESPK_IMAGE="$img" \
     idf.py -B "build-$n" -G Ninja -D "SDKCONFIG=build-$n/sdkconfig" \
     "-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.$n.defaults" build -- -j2 > "/tmp/variant-$n.log" 2>&1) \
     || { echo "build of $n failed, see /tmp/variant-$n.log" >&2; exit 1; }
  rm -rf "/tmp/fw-$n"
  scripts/idf.sh env scripts/package-artifact.sh "$b" "/tmp/fw-$n" > /dev/null
  echo "== $n: test"
  upper=$(echo "$n" | tr a-z A-Z)
  env "ESPK_${upper}_BUILD=$b" ESPK_ARTIFACT="/tmp/fw-$n" \
    nice -n 15 ionice -c 2 -n 7 .venv/bin/pytest "tests/target/${test_file[$n]}.py" --run-bench -q
done
