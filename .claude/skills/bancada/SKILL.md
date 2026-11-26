---
name: bancada
description: >
  Drive and debug the project's bench: one Waveshare ESP32-S3-RLCD-4.2 on the
  USB port of the bench notebook, the `python -m bench` driver, `bench.yaml`
  roles, the udev link, flashing, resetting, telemetry and waiting for events.
  Use when a task touches the physical board, the driver in `tools/bench/`, a
  board that does not enumerate, flashing, "run it on the board", "play it on
  the speaker", the bench CI runner, or volume/hearing safety on the bench.
---

# Bancada — the bench, in one place

The facts of the equipment live in `docs/Method/project/bancada.md`; this
skill carries the **judgement**: the order to act in, and symptom → first
suspect → how to confirm. It does not repeat the command table.

## Status first

The bench starts `available: unproven` and flips only in `/commission`. A task
that needs the board while it is `unproven` is **Phase 2 work**: say so, and
start with `python -m bench discover` and `pytest tools/bench -q`. A bench
notebook without the board is `not done`, never `failed`.

**The board is shared** with the AlertAlergo project on the same notebook.
Before flashing, read what is on it (`bench chip-info dut` and the boot banner);
after a session, say in the evidence which firmware was left on the board.

## Order of action on the board

1. `bench discover` — the `dut` role exists and matches `bench.yaml`. If not,
   nothing else is worth running.
2. **Volume before any sound:** automated tests run at the bench volume ceiling
   (`bancada.md`). Only a listening session raises it, with people present.
3. `bench flash dut <artifact>` — the artifact is the CI's (or a local build
   with the CI's pinned versions); offsets come from `flash_args`, including
   the eSpeak data partition image.
4. Start the listener **before** the reset: `bench wait-event dut "<marker>"
   --timeout <s>` with the `reset` fired after it opens.
5. Read the telemetry (`bench telemetry dut`); one process per port.

## Symptom → first suspect → confirm

| Symptom | First suspect | Confirm |
|---|---|---|
| role missing in `discover` | charge-only cable, or the notebook's xHCI reset | `lsusb` (`303a:1001`); replug; `ls /dev/espk-*` |
| port busy / garbage on serial | a second reader (another project's capture), or ModemManager | `fuser /dev/espk-dut`; `systemctl status ModemManager` |
| flash "succeeds" but the board does not boot (`invalid magic byte`) | offsets guessed instead of read from `flash_args` | compare with the build's `flash_args`; re-flash from them |
| speech silent, tones fine | eSpeak data partition missing, stale or from another build | boot marker for the data check; re-flash the data image from the same build |
| board boots someone else's firmware | the shared board was left with AlertAlergo firmware | boot banner; flash this project's artifact |
| speech starts late or the watchdog fires | synthesis task starved or not yielding | the speech done marker with timing; `heap_min` |
| internal RAM exhausted at boot or under Wi-Fi/BLE | eSpeak's fixed `.bss` (~90 KB) | `idf.py size-components`; compare with the budget in the FSD |
| marker never seen | listener opened after the reset (late, not absent) | re-run with the listener first |
| device path changed after a reset | native-USB re-enumeration | rely on `/dev/espk-dut`, never `ttyACM*` |

## A driver gap is a decision, not a workaround

Needing a hand-opened serial terminal, a one-off script, or SSH to *do*
something means the driver lacks a capability or the firmware lacks a seam.
Decide it in `/harness`: add the command to `tools/bench/` with the test that
proves it. Never leave the workaround in a doc.

## Hard limits

- Never commit `test-results/` with listener data that identifies a person;
  listening-study data follows the study protocol, not this skill.
- Never claim a listening result the protocol did not produce: automated
  checks (PCM identity, phonemes) are not intelligibility.
- Registering the self-hosted runner is the user's grant, not yours.
