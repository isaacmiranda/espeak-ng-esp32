#!/usr/bin/env bash
# Roda um comando com o ESP-IDF fixado pelo FSD (CON-SW-01: v5.5.5), num ambiente
# limpo — independe de outro ESP-IDF carregado pelo ~/.bashrc.
#   scripts/idf.sh idf.py -C firmware build
set -euo pipefail
IDF_DIR="${IDF_DIR:-$HOME/esp/esp-idf-v5.5.5}"
exec env -i HOME="$HOME" USER="${USER:-dev}" TERM="${TERM:-dumb}" LANG="${LANG:-C.UTF-8}" \
  PATH=/usr/local/bin:/usr/bin:/bin bash -c '
    . "$0/export.sh" >/dev/null
    # o export.sh sai com 0 mesmo quando a ativação falha (ex.: esptool fora
    # da faixa do IDF): sem idf.py no PATH, o ambiente não existe — falhe alto.
    command -v idf.py >/dev/null || { echo "FATAL: ativação do ESP-IDF falhou em $0 (rode: . $0/export.sh)" >&2; exit 1; }
    exec "$@"' "$IDF_DIR" "$@"
