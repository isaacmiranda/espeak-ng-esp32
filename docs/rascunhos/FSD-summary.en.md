<!-- source-revision: 3142005 -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# espeak-ng-esp32 — functional specification, summary (draft, English)

This is a summary of the Portuguese [FSD](../Functionality/FSD.md) (version 0.4.0), which is the normative text. It is a
draft for the responsible's review and is not published.

## What the project is

eSpeak NG 1.52.0 as a native ESP-IDF component, sources unmodified, for any ESP32 with PSRAM and for every language of
the upstream; and a research platform: memory, latency and coexistence with Wi-Fi/BLE/display measured on the board,
intelligibility estimated by ASR, and, in the future, a listening study approved by an ethics committee. Priority:
Brazilian Portuguese, then English. Reference hardware: Waveshare ESP32-S3-RLCD-4.2.

## Structure

- **Part A, research application and tools (L2):** a console firmware with `ESPK` markers (boot, ready, say, done with
  PCM SHA-256, cancel, volume ceiling, memory), load profiles, references and equivalence (R1 = pinned upstream on the
  host, R2 = the system package, R3 = the board), corpora, ASR estimate, listening tool, examples.
- **Part B, the component (L1):** data image and partition, language selection and capacity report, the synchronous
  core (`espk_init`, `espk_synth`, `espk_deinit`), the asynchronous layer (queue, cancel), memory modes.
- **Part C/D:** platform constraints, licences and packaging, errors, documentation in two languages.

## Key requirements (IDs are stable)

- PCM on the board equals the upstream's on the host, item by item, by SHA-256 (FR-REF-01..03); the engine keeps state
  between utterances, so equivalence is by sequence.
- Accented letters must be classified by `ucd-tools` (FR-ENG-04); an intact mode exists for study (FR-ENG-05).
- The data image has its own partition and a checksummed header (FR-DAT-*); the language set is chosen at build time and
  checked against the partition and PSRAM budget (FR-CAP-*). The image with every language does not fit the reference
  board's partition.
- Package: compiled data of every language, `phsource/`, `dictsource/` and a regeneration script that reproduces the data
  byte for byte (FR-LIC-03, FR-LIC-04).
- The development bench is silent by decision of the responsible (FR-RES-17).
- ASR numbers are estimates and always carry the caveat: *estimativa por reconhecimento automático; não é medida de
  inteligibilidade com ouvintes* (FR-ASR-05). No intelligibility result exists without the listening study.

## Status

Phase 3 (construction). See `testing/test-plan.yaml` for what is verified and `docs/Method/project/proximos-passos.md`
for what is next.
