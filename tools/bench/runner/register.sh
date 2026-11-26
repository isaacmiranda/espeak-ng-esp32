#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Registers the bench-notebook runner for THIS repository and serves jobs in a loop.
#
# What registering means: GitHub may then send workflow code from this repository to
# this notebook, and that code drives the board on its USB port. Only the release
# workflow targets these labels, and it runs only on tag pushes. Run this only with
# the owner's explicit yes.
#
# Ephemeral: each registration serves one job and is removed; the loop re-registers.
set -euo pipefail
REPO=isaacmiranda/espeak-ng-esp32
DIR="${RUNNER_DIR:-$HOME/actions-runner/espeak-ng-esp32}"
cd "$DIR"
while true; do
  token=$(gh api -X POST "repos/$REPO/actions/runners/registration-token" --jq .token)
  ./config.sh --unattended --ephemeral --replace \
    --url "https://github.com/$REPO" --token "$token" \
    --name "bench-notebook-$(hostname)" --labels bench-notebook
  nice -n 10 ./run.sh || true
  sleep 5
done
