# espeak-ng-esp32

*[Português](README.pt-BR.md)*

**eSpeak NG as a native ESP-IDF component for the ESP32-S3, with Brazilian Portuguese speech — and a study of how
intelligible it is to real listeners.**

> **Status: Phase 0 (definition).** There is no specification yet and nothing here is a release. The code under
> [`seed/alertalergo-port/`](seed/alertalergo-port/) is the working port this project starts from (it runs today on
> the reference board inside the AlertAlergo V3 firmware); it becomes a reusable component as the specification is
> written. Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Why

- Several projects already run eSpeak NG on microcontrollers (Arduino libraries for ESP32/RP2040, one recent ESP-IDF
  port), but there is **no eSpeak NG component in the Espressif Component Registry** and no published, measured
  account of running it next to Wi-Fi, BLE and a display.
- There is **no published listening study of embedded text-to-speech in Brazilian Portuguese** — not with sighted
  listeners, not with blind or low-vision listeners, not for drug names. Automated checks are not intelligibility.

The survey behind these claims is in [`docs/Ideia/pesquisa-2026-11-26/`](docs/Ideia/pesquisa-2026-11-26/) (pt-BR).

## What the starting port does

- eSpeak NG **1.52.0, sources unmodified**, built as an ESP-IDF component (synchronous engine only).
- Voice and dictionary data (~736 KB, pt / pt-BR) in **their own flash partition**, with a checksummed header,
  exposed to the unmodified upstream file code through a small read-only VFS.
- Synthesis task with its stack in PSRAM, cancellation, watchdog-safe chunking; audio to the ES8311 codec over I2S.
- Host build of the same sources: PCM output **byte-identical** to upstream for fixed texts, and pinned phonemes.
- Measured on the reference board with BLE, SoftAP and the display active: minimum free internal heap during speech
  39 828 B; eSpeak keeps ~90 KB of fixed internal RAM.

## Reference hardware

[Waveshare ESP32-S3-RLCD-4.2](https://www.waveshare.com/) — ESP32-S3, 16 MB flash, PSRAM, ES8311 codec, speaker,
reflective LCD.

## License

GPL-3.0-or-later ([LICENSE](LICENSE)), because eSpeak NG is GPL-3.0-or-later. Third-party parts keep their own
licenses (Apache-2.0, BSD-2-Clause, Unicode), listed in [`REUSE.toml`](REUSE.toml) and [`LICENSES/`](LICENSES/).

## How this repository is built

Development follows the [Embedded-AI-Harness](https://github.com/SensorsIot/Embedded-AI-Harness) method with an AI
assistant: specification first ([`docs/Functionality/`](docs/Functionality/)), tests before code, hardware evidence
from CI artifacts. Human decisions are recorded in the specification; AI use is disclosed here and in commits.
Start at [`docs/00-Overview.md`](docs/00-Overview.md).

## Citation

See [CITATION.cff](CITATION.cff).
