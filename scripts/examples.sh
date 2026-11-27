#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Builds the examples (FSD 18), one at a time, low priority and two jobs; for the ones that run on the reference
# board it packs the artifact, flashes it and runs its test.
#   scripts/examples.sh hello:esp32 hello:esp32s2 hello:esp32s3 hello:esp32p4 waveshare-s3-rlcd:esp32s3
#   (default: all of those)   Needs the compiled upstream data (ESPK_DATA_DIR, default: the R1 build in the cache).
set -euo pipefail
cd "$(dirname "$0")/.."
data=${ESPK_DATA_DIR:-$(python3 -c "import sys; sys.path.insert(0, 'tools/ref'); import r1; print(r1.build(r1.upstream()) / 'espeak-ng-data')")}
specs=("$@"); [ ${#specs[@]} -gt 0 ] || specs=(hello:esp32 hello:esp32s2 hello:esp32s3 hello:esp32p4 waveshare-s3-rlcd:esp32s3)
for spec in "${specs[@]}"; do
  ex=${spec%%:*}; chip=${spec##*:}
  b="build-$chip"
  echo "== $ex on $chip: build"
  (cd "examples/$ex" && nice -n 15 ionice -c 2 -n 7 ../../scripts/idf.sh env ESPK_DATA_DIR="$data" \
     idf.py -B "$b" -G Ninja -D "IDF_TARGET=$chip" -D "SDKCONFIG=$b/sdkconfig" build -- -j2 > "/tmp/example-$ex-$chip.log" 2>&1) \
     || { echo "build of $ex on $chip failed, see /tmp/example-$ex-$chip.log" >&2; exit 1; }
  echo "== $ex on $chip: built"
  if [ "$chip" = esp32s3 ]; then
    rm -rf "/tmp/fw-$ex"
    scripts/idf.sh env scripts/package-artifact.sh "examples/$ex/$b" "/tmp/fw-$ex" > /dev/null
    echo "== $ex on $chip: test"
    env "ESPK_EXAMPLE_ARTIFACT=/tmp/fw-$ex" ESPK_EXAMPLE="$ex" \
      nice -n 15 ionice -c 2 -n 7 .venv/bin/pytest tests/target/test_examples.py --run-bench -q
  fi
done
