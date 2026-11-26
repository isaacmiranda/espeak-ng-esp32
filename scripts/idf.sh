#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Runs a command with the ESP-IDF pinned by the FSD (CON-PLT-01: v5.5.5) in a clean
# environment, independent of any other ESP-IDF loaded by ~/.bashrc.
#   scripts/idf.sh idf.py -C research/firmware build
set -euo pipefail
IDF_DIR="${IDF_DIR:-$HOME/esp/esp-idf-v5.5.5}"
exec env -i HOME="$HOME" USER="${USER:-dev}" TERM="${TERM:-dumb}" LANG="${LANG:-C.UTF-8}" \
  PATH=/usr/local/bin:/usr/bin:/bin bash -c '
    . "$0/export.sh" >/dev/null
    # export.sh exits 0 even when activation fails (e.g. an esptool outside
    # the IDF range): without idf.py on PATH there is no environment; fail loudly.
    command -v idf.py >/dev/null || { echo "FATAL: ESP-IDF activation failed in $0 (run: . $0/export.sh)" >&2; exit 1; }
    exec "$@"' "$IDF_DIR" "$@"
