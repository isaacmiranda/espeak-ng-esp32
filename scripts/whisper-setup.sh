#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Builds the pinned whisper.cpp (CLI only) and fetches the pinned `small` multilingual model into the cache
# (FSD FR-ASR-01). The model's SHA-256 is checked before it is used; a mismatch deletes it and fails.
#   scripts/whisper-setup.sh        prints the two paths: whisper-cli and the model
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=../tools/asr/pins.env
. "$ROOT/tools/asr/pins.env"
CACHE="${ESPK_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/espk}/whisper"
mkdir -p "$CACHE"
src="$CACHE/whisper.cpp-$WHISPER_TAG"
if [ ! -d "$src" ]; then
  git clone -q --depth 1 --branch "$WHISPER_TAG" "$WHISPER_URL" "$src.part" && mv "$src.part" "$src"
fi
bin="$src/build/bin/whisper-cli"
if [ ! -x "$bin" ]; then
  nice -n 15 ionice -c 2 -n 7 cmake -S "$src" -B "$src/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_SERVER=OFF -DGGML_NATIVE=OFF -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_F16C=OFF -DGGML_BMI2=OFF >&2
  nice -n 15 ionice -c 2 -n 7 cmake --build "$src/build" -j2 --target whisper-cli >&2
fi
model="$CACHE/$MODEL_NAME"
if [ ! -f "$model" ]; then
  curl -sSLf -o "$model.part" "$MODEL_URL" && mv "$model.part" "$model"
fi
got=$(sha256sum "$model" | cut -d' ' -f1)
if [ "$got" != "$MODEL_SHA256" ]; then
  rm -f "$model"
  echo "FATAL: sha256 of the model is $got, expected $MODEL_SHA256; the file was removed" >&2
  exit 1
fi
echo "$bin"
echo "$model"
