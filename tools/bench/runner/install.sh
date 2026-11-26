#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Installs the GitHub Actions runner on the bench notebook (no registration).
# Registration is the owner's grant: tools/bench/runner/register.sh.
set -euo pipefail
VER=2.338.2
SHA=baebf204307bac6193480852732f0aba2ae97b6c5597c244f4d5558390147c40
DIR="${RUNNER_DIR:-$HOME/actions-runner/espeak-ng-esp32}"
mkdir -p "$DIR"
cd "$DIR"
tgz="actions-runner-linux-x64-$VER.tar.gz"
[ -f "$tgz" ] || curl -sSLf -o "$tgz" "https://github.com/actions/runner/releases/download/v$VER/$tgz"
echo "$SHA  $tgz" | sha256sum -c --quiet
[ -x ./config.sh ] || nice -n 15 tar xzf "$tgz"
echo "runner $VER installed in $DIR (not registered)"
