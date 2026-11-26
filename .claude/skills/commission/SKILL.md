---
name: commission
description: >
  Phase 2 of AI Closed-Loop Programming — Commissioning: prove the project's
  OWN never-seen-working parts — the bench (USB link, udev links, the
  `tools/bench/` driver), the boards, the wiring and the peers — so that a
  failing test means the code and not the setup. Use this skill when the user
  mentions commissioning, bring-up, a new board or peer, wiring or polarity
  doubts, a board that does not enumerate, or wants to burn down the debugging
  agenda. Exit gate: DUT ready.
---

# Commission — Phase 2 door

A door into the Method skill: **the driver, the chain, and the dispatch map
live in `../build/SKILL.md`** — read that first. This door exists so the phase
can be entered by its own name; the phase itself is always derived from state.
If the debugging agenda is already burned down, say so and continue as
`/build` — typing the "wrong" door costs nothing.

## The bench is this project's equipment

The bench — USB link, udev links, `tools/bench/`, `bench.yaml` — is built
and maintained in this repository, so nothing about it is taken on faith. It
starts `available: unproven` (`../../../docs/Method/project/bancada.md`) and
becomes `available` only when each driver command has passed its own test and
the roles in `bench.yaml` match what `bench discover` finds. The host toolchain
(compiler, ESP-IDF, pytest) is the only thing taken at face value, the way a
project takes gcc.

**When a red is not the product's fault, say whose it is.** A failing bench
test is first a suspect about the driver, the cable, the USB link or the
board; exonerate those with evidence (the driver's own test, a loopback, the
udev link) before touching the product. A bench fault is fixed in
`tools/bench/` with the test that proves it.

## What commissioning is

The debugging agenda (`../build/references/test-design.md` §5, first question)
lists every part that has never been observed doing its job *here* — whatever
its reputation elsewhere:

- the bench: USB link, udev links, each driver command
- the DUT board — this unit, this role, first flash, first boot
- project peers (none today) and wiring: the speaker on the board connector,
  USB power, the reference listening setup (headphones or room position)
- the project firmware's first contact with each path it uses (flash data
  partition, PSRAM, I2S/codec)

Until each is seen working, a failing test measures the environment.

- Work the agenda top-down; each item names *what proves it*.
- **Agenda items are debugging work, not test cases** — they never enter the
  plan. The separator: does it discharge a requirement, or interrogate the
  setup? Setup measurements go on the **capability**, with their consequence
  ("two bursts in six arrive clean → assert across several cycles").
- The `unproven` capability state covers **the bench and all project-side
  equipment**.
- The bring-up work that *is* a test case (it discharges a requirement about
  the device) is `standard` in kind, ordered ahead of the journey.
- The bench notebook and the boards are not always connected or powered. A missing board
  or a failing driver is an unmet precondition — `not done` with the reason,
  never `failed`.
- **The operator's hands are for physical acts — plug, wire, power, swap.
  Observations belong to instruments.** Never design a step where a human
  reads a measurement by eye. If no instrument can make the observation, that
  is a new driver capability or a firmware seam, decided in `/harness`.
- **Hearing safety first.** Automated speech and tone tests run at the bench
  volume ceiling (`bancada.md`); only a listening session raises it, with
  people present. Never hold the speaker at an ear at test volume.

## The worked shape — one board on the bench notebook

1. **Commission the bench.** Board enumerated on USB; `/dev/<prj>-<role>` links
   present; `python -m bench discover` lists every role in `bench.yaml`;
   each driver command passes its own test (`pytest tools/bench`). Record the
   bench notebook, driver version and date as dated observations. Tests select by role,
   never by device path or machine address.
2. **Find the DUT and verify it is what the project expects** —
   `bench chip-info dut`: chip type and revision, flash size, MAC against the
   FSD's unit. Mismatch = stop: wrong board on the role.
3. **Project peers** (`peer-a`, …): present and answering one basic command;
   record the role.
4. **Prove the forward path with a trivial known-good program** — CI
   compiles it, the artifact is flashed with `bench flash dut <artifact>`, and
   its output is observed. **Print alternating `ON` / `OFF` plus a heartbeat on
   serial rather than blinking an LED**: no GPIO need be wired, and the bench
   observes it directly with `bench wait-event`. One pass proves the whole
   pipeline — toolchain, artifact flow, flash, boot, observation — with code
   that cannot itself be the problem.

Nothing else. Items 1–3 are minutes; item 4 is one CI cycle.

### Running the four checks

```bash
# 1 · bench: USB link, links, driver
python -m bench discover                 # every role of bench.yaml, with serial number
pytest tools/bench -q                    # the driver's own tests (no boards needed)

# 2 · DUT: the right board, on the right role
python -m bench chip-info dut            # chip, revision, flash size, MAC
# Compare with the unit the FSD records. A mismatch stops the phase.
# Native-USB ESP32-S3 boards enumerate with the same VID:PID, so the role is
# tied to the serial number in bench.yaml, never to the VID:PID alone; verify
# the MAC, which is per-board.

# 3 · project peers, if any: present, and answering one basic command
python -m bench command peer-a "ping"    # whatever the firmware's console defines

# 4 · forward path: CI artifact → flash → observed marker
gh run download <run-id> -D fw           # the same bytes CI built
python -m bench flash dut fw/<artifact>  # offsets come from the build's flash_args
python -m bench wait-event dut "<marker>" --timeout 30
```

**Take the flash offsets from the build, never from memory.** An ESP-IDF build
ships `flash_args` beside the images with the authoritative offsets; they move
whenever the partition table changes. Guessing produces a *successful* flash
with a hash-verified write and a device that then reports `invalid magic byte`
and refuses to boot. The driver reads `flash_args`; the flash succeeding is not
evidence that it landed where the partition table expects.

**Wait for the pattern with the listener started before the reset**, or match
a periodic marker instead: a boot banner has already scrolled past by the time
a listener opened afterwards, so a missed match may mean *late*, not *absent*.
A heartbeat line (`alive 1`, `alive 2`, …) is observable at any moment, which
is why item 4's program prints one. Only one process may hold a serial port: a
second reader makes both read garbage.

## Exit

### Deliverables — what Phase 2 hands to Phase 3

All of it lives in `testing/test-plan.yaml` as dated observations; none of it
is prose in a document nobody reads again.

| Deliverable | Content |
|---|---|
| **Bench record** | bench notebook, driver version, date; every driver capability `available`, each with the test that proved it; `bench.yaml` roles equal to `bench discover` |
| **DUT record** | role, chip type and revision, flash size, MAC — the unit this project is verified against, matching the FSD |
| **Peer records** | each project peer: what it is, its role, the command it answered |
| **Forward-path evidence** | the CI run id, the artifact, the flash offsets used (from `flash_args`), and the marker observed |
| **Capability updates** | every `unproven` resolved to `yes` or `no`; each `no` carries its consequence, each `yes` its observation |
| **Agenda** | empty |

### The gate

**Run the four checks in a fresh checker** with this project's gate file
(`../build/references/gate-checks.md`) — the session that flashed the board is
the one most likely to read a half-observed marker as proof.

**The gate loops, it does not wave through.** A failed check sends the work
back to the act that owns it — a driver command whose test fails, a DUT that
is not the expected unit, a peer that will not answer, a forward path that does
not reach its marker — and the whole check runs again. Wave 1 does not start on
a partial commissioning.

**DUT ready** — derived, never declared: the bench commissioned, the DUT
connected and verified as the unit the FSD names, the project's peers
answering, and the forward path proven to deliver code to it. From here
`/build` runs the journey tests as the gate and the loop proper begins. For a
project with no new hardware and no peers beyond the bench, this phase is
minutes, not days.
