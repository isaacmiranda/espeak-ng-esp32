# Local analysis of the eSpeak NG port in AlertAlergo V3 (ESP-IDF v5.5.5, ESP32-S3)

Scope: read-only analysis of the repository `/home/dev/projetos/alertalergo-v3-firmware` at HEAD `19787f2` (2026-11-26). Sources are repository paths (relative to the repo root) and commit hashes; "map" figures come from `build-release/alertalergo.map` / `alertalergo.elf` built 2026-11-16 (eSpeak sources and `l1_speech` unchanged since 2026-11-16, per git log). No file was modified, the board was not touched, no patient data was copied (the only names in test vectors are fictitious).

Short characterisation: the "port" is **upstream eSpeak NG 1.52.0, unmodified, compiled as an ESP-IDF component** (sync runtime only), plus a **small original glue layer** (~300 lines of C + a 70-line Python image builder) that (a) stores the compiled pt-BR data in a dedicated flash partition with a custom CRC-checked container and (b) exposes it to the unmodified upstream file I/O through a read-only ESP-IDF VFS mounted at `/es`. Around it the product adds a PSRAM-stacked synthesis task, a PCM buffer, audio post-processing to an ES8311 codec, a pt-BR drug-name exception dictionary, and a verification harness (bit-exact PCM hashes vs. upstream on the host, phoneme pins for drug names, on-target heap/watchdog tests).

---

## 1. eSpeak NG version, license, modifications and GPL compliance

### Takeaway
Upstream eSpeak NG tag 1.52.0 is vendored byte-for-byte (sources unmodified, tarball SHA-256 pinned, reproducible regeneration script); everything project-specific lives outside `upstream/`. GPL-3.0-or-later is declared for the whole firmware, but two compliance items are promised in docs and not yet implemented: the release bundle does not include the upstream tarball (the "corresponding source" of the compiled data), and the repo has no top-level `LICENSE`/`COPYING` file. No release tag exists yet.

### Cited Findings
- Origin `https://github.com/espeak-ng/espeak-ng`, tag `1.52.0`, tarball SHA-256 `bb4338102ff3b49a81423da8a1a158b420124b055b60fa76cfb4b18677130a23`; license GPL-3.0-or-later with parts under Apache-2.0, BSD-2 and the Unicode license (`upstream/COPYING*`); "Alterações: nenhuma nas fontes (`upstream/`); `config/config.h` e `CMakeLists.txt` são deste projeto"; "rodar de novo dá `git diff` vazio" — [ORIGIN.md](firmware/components/third_party/espeak-ng/ORIGIN.md)
- `scripts/gen-espeak.sh` downloads the tarball, verifies SHA-256, copies `src/libespeak-ng/*.c,*.h`, `src/include/espeak-ng/*.h`, `src/ucd-tools/src/*` and the four COPYING files unchanged; then builds upstream on the host (`-DUSE_MBROLA=OFF -DUSE_LIBSONIC=OFF -DUSE_LIBPCAUDIO=OFF -DUSE_ASYNC=OFF -DUSE_KLATT=OFF -DUSE_SPEECHPLAYER=OFF`) and uses upstream's own `espeak-ng --compile` to produce the data — [scripts/gen-espeak.sh](scripts/gen-espeak.sh)
- Vendored tree: 81 files under `upstream/` (66 in `src/libespeak-ng`, 3 public headers, 7 ucd-tools), ~2.1 MB on disk — local `find`/`du` on `firmware/components/third_party/espeak-ng/upstream`
- Only the synchronous runtime is compiled (27 libespeak-ng `.c` + 6 ucd-tools `.c`); MBROLA, Klatt, speech-player, sonic and async are "arquivos presentes, não compilados"; compiled with `-w -fwrapv -fno-exceptions` ("avisos não viram erro (não editamos as fontes)") and `PATH_ESPEAK_DATA="/es"` — [CMakeLists.txt](firmware/components/third_party/espeak-ng/CMakeLists.txt)
- Project `config.h` (replacing upstream's CMake-generated one) sets `USE_ASYNC/KLATT/LIBPCAUDIO/LIBSONIC/MBROLA/SPEECHPLAYER = 0`, `PACKAGE_VERSION "1.52.0"` — [config/config.h](firmware/components/third_party/espeak-ng/config/config.h)
- Commit introducing the vendoring: "copies the library sources unmodified, compiles the pt-BR data with upstream's own tool (735 518 bytes, NFR-SW-02) … A second clean run gives identical data" (96 files, 52 390 insertions) — commit `712a96b` (2026-11-08)
- Data modifications are confined to the dictionary build input: `pt_listx` is copied into upstream `dictsource/` before compiling, so the shipped `pt_dict` differs from stock upstream; the voice file can receive extra lines from `voice_pt_br_extra` (currently empty, so `lang/pt-br` equals upstream `lang/roa/pt-BR`) — [gen-espeak.sh](scripts/gen-espeak.sh), [voice_pt_br_extra](firmware/components/third_party/espeak-ng/voice_pt_br_extra)
- FSD: CON-SW-05 "A síntese de fala é o eSpeak NG com a voz formante pt-BR"; CON-SW-06 "O firmware é distribuído sob GPL-3.0-or-later. O código-fonte completo correspondente a cada release está disponível a quem recebe o aparelho"; §29.1 lists "eSpeak NG | upstream 1.52.0, porte próprio como componente ESP-IDF | 1.52.0 | GPL-3.0-or-later"; FR-3P-01 (release publishes full source + license texts), FR-3P-02 (`GET /api/status` exposes `source_url`) — [docs/Functionality/FSD.md](docs/Functionality/FSD.md) (lines ~236–237, 1914–1941)
<!-- REUSE-IgnoreStart -->
- All project-original speech files carry `SPDX-License-Identifier: GPL-3.0-or-later` — [l1_speech.h](firmware/components/l1_speech/include/l1_speech.h), [espeak_part.c](firmware/components/l1_speech/espeak_part.c), [pt_listx](firmware/components/third_party/espeak-ng/pt_listx)
<!-- REUSE-IgnoreEnd -->
- ORIGIN.md states "A release (FR-3P-01) leva o tarball upstream junto com o código deste repositório", but `scripts/release-assemble.sh` only copies `espeak.bin` and produces `git archive … HEAD` (the repo, which contains the unmodified C sources, compiled data and `pt_listx`, but not upstream `phsource/`/`dictsource/`); no reference to the upstream tarball in `release-assemble.sh`, `release.sh` or `release-verify.sh` — [scripts/release-assemble.sh](scripts/release-assemble.sh) (lines 14–16), grep for `1.52|espeak-ng|upstream` returned nothing
- No top-level `LICENSE` or `COPYING` in the repo; `LICENSES/` only holds font/icon licenses (CC-BY-4.0, FontAwesome, OFL-1.1) and a README stating the firmware is GPL-3.0-or-later — local `ls`; [LICENSES/README.md](LICENSES/README.md). The FSD verification row for CON-SW-06 expects "`LICENSE` GPL-3.0-or-later e FR-3P-01" — [FSD.md](docs/Functionality/FSD.md) line ~282
- `git tag` is empty: no release has been published yet — local `git tag`

### Inferences
- Because sources are pristine and regeneration is scripted with a pinned hash, the port's provenance is unusually auditable; a diff against upstream 1.52.0 should be empty for `upstream/`.
- GPL "Corresponding Source" for the compiled data arguably requires `phsource/` + `dictsource/` (or a written offer/pinned URL). The pinned URL + SHA in `gen-espeak.sh` partly covers this, but the ORIGIN.md promise (tarball in the release) is not yet implemented; a top-level `LICENSE` (GPL-3.0 text) is also missing. Both should be fixed before publishing.

### Gaps
- Did not diff `upstream/` against a freshly downloaded 1.52.0 tarball (no network fetch performed); the "unmodified" claim rests on ORIGIN.md, the script, and the commit message.
- Whether the omitted upstream files (e.g. `fifo.c`, `event.c`, `klatt.c`, `mbrowrap.c`, `sPlayer.c`) are all present in `upstream/` was not enumerated individually; the script copies `*.c` wholesale, so they should be.

---

## 2. Architecture of the port (what is original)

### Takeaway
The original contribution is the storage/integration layer: a custom "AAES" partition image with CRC32, a minimal read-only ESP-IDF VFS that lets the unmodified upstream `fopen`/`fread` path load data from memory-mapped flash, a synchronous callback-based C API, and an RTOS integration (PSRAM-stacked task, timeout, cancel, watchdog-safe yielding). Reference ports instead convert data to C arrays and patch upstream sources.

### Cited Findings
- Partition table: `espeak, data, 0x40, 0x830000, 0x100000` (1 MiB custom data subtype 0x40) alongside two 4 MiB OTA app slots and a 6.8 MiB `assets` LittleFS — [firmware/partitions.csv](firmware/partitions.csv)
- Image format v1 (little-endian): `"AAES"` magic, `format u32 = 1`, `size u32`, `crc32 u32` (zlib CRC-32 of the body), `count u32`, table of `{name[32], offset u32, len u32}`, files 4-byte aligned, deterministic ordering by sorted path; fails if image > 0x100000 — [scripts/gen-espeak-image.py](scripts/gen-espeak-image.py)
- `espeak_part_mount()` finds the partition, `esp_partition_mmap`s the whole 1 MiB, checks magic/version/CRC (`esp_rom_crc32_le`) and table coherence, then registers a read-only VFS (`open/read/lseek/close/fstat/stat`, max 4 fds, directory emulation by path prefix) — [espeak_part.c](firmware/components/l1_speech/espeak_part.c) (165 lines)
- Upstream data loading still goes through `ReadPhFile` → `malloc(length)` for `phontab`, `phonindex`, `phondata`, `intonations`, so data is copied from mmapped flash into heap (PSRAM, since blocks exceed `SPIRAM_MALLOC_ALWAYSINTERNAL`) — [synthdata.c](firmware/components/third_party/espeak-ng/upstream/src/libespeak-ng/synthdata.c) lines 66–125; comment in [espeak_part.c](firmware/components/l1_speech/espeak_part.c) header
- API: `spk_hw_init(const char **reason)` (mount + `espeak_ng_InitializePath("/es")`, `espeak_ng_Initialize`, `InitializeOutput(ENOUTPUT_MODE_SYNCHRONOUS)`, `SetVoiceByFile("/es/lang/pt-br")`); `spk_hw_synth(utf8, cb, ctx)` streams 16-bit mono PCM via callback, callback returning false aborts (`ESP_ERR_NOT_FINISHED`); `spk_hw_rate()`; `spk_hw_set_rate(wpm)`. Failure reasons: `bad_magic, bad_version, bad_crc, no_partition, init` — [l1_speech.h](firmware/components/l1_speech/include/l1_speech.h), [speech_synth.c](firmware/components/l1_speech/speech_synth.c) (70 lines)
- Voice file stored as lowercase `lang/pt-br` because "`espeak_ng_SetVoiceByFile` converte o caminho para minúsculas" (and limits it to 60 bytes) — [ORIGIN.md](firmware/components/third_party/espeak-ng/ORIGIN.md), [speech_synth.c](firmware/components/l1_speech/speech_synth.c)
- FR-PLT-06: invalid header/CRC disables speech, emits `SPEECH ready=0 reason=<…>`, tones keep working; CRC checked every boot after the splash — [FSD.md](docs/Functionality/FSD.md) line ~1892; NFR-SW-02: data (≈735 KB) in the `espeak` partition, not in the app — FSD line ~265
- Commit `e1976d1`: "l1_speech checks it after the splash and serves it read-only at /es, so the upstream file I/O runs unchanged. A low-priority task synthesises into a PSRAM buffer, yielding on every chunk, and the audio task plays it after the tone" — commit `e1976d1` (2026-11-08)
- Reference port BackgroundAudio (Earle Philhower, v1.4.4, eSpeak NG 1.52.0): data embedded as C arrays (`dict/pt_dict.h`: `const unsigned char __espeakng_dict[]`, `phoneme/phondata.h` etc.), one header per language/voice, interrupt-driven playback, Arduino class API; upstream `.c` files contain Arduino/PROGMEM references in at least 10 files (common, espeak_api, langopts, error, intonation, phoneme, soundicon, synthdata, tr_languages, encoding) — [reference/BackgroundAudio/src/BackgroundAudioSpeech.h](reference/BackgroundAudio/src/BackgroundAudioSpeech.h), [library.properties](reference/BackgroundAudio/library.properties), grep on `reference/BackgroundAudio/src/libespeak-ng/*.c`
- Reference port arduino-espeak-ng (Phil Schatzmann, version 1.52.0): "recommended way is to load the data from PROGMEM" (data also available as headers); `ESPEAK_HEAP_HACK` moves big global arrays (phoneme list, wavegen queue, phoneme tables) to the heap; central allocator `mem_alloc.h` routes to PSRAM via `heap_caps_malloc`; depends on arduino-posix-fs and arduino-audio-tools; reported footprint on ESP32: sketch 1 457 411 B flash, 39 616 B globals — [reference/arduino-espeak-ng/README.md](reference/arduino-espeak-ng/README.md), [library.properties](reference/arduino-espeak-ng/library.properties)

### Inferences
- Distinctive vs. the two reference ports: (1) native ESP-IDF component (CMake, no Arduino core), (2) zero source patches — integration by VFS rather than by `#ifdef ARDUINO`/PROGMEM edits, which keeps upstream upgrades a script re-run, (3) data in a separately flashable, integrity-checked partition (independent of app OTA slots; app stays smaller), (4) a deterministic test harness proving bit-exact PCM vs upstream.
- Trade-off of the zero-patch choice: upstream's large static arrays stay in internal `.bss` (~90 KB, see §3), something arduino-espeak-ng solves with its heap hack; and data is copied into PSRAM at init instead of being read in place from flash (XIP), costing ~0.7 MB PSRAM.

### Gaps
- No measurement of init time (mount + CRC over ~736 KB + data copy) was found in the repo.

---

## 3. Footprint (flash, internal RAM, PSRAM, stack) and timing

### Takeaway
eSpeak NG code+rodata ≈ 249 KB in app flash; data image 735 910 B in its own 1 MiB partition; **≈ 89.8 KB of fixed internal `.bss`** (dominant constraint); task stack 64 KB in PSRAM (measured ~39 KB used); PSRAM also holds the ~736 KB data copy and a 12-s PCM buffer. Minimum internal free heap during speech measured at 39 828 B with SoftAP+BLE+LVGL active (requirement ≥ 32 768). Real-time factor/synthesis latency was not measured directly; only "speech starts ≤ 1.5 s after the tone" is tested.

### Cited Findings
- Linker map (release build) attributed to `libespeak-ng.a`: `.flash.text` 139 164 B, `.flash.rodata` 109 746 B, `.dram0.bss` 89 783 B, `.dram0.data` 224 B; `libl1_speech.a`: text 362 B, rodata 25 B, bss 10 B — parsed from `build-release/alertalergo.map` (2026-11-16) with a scratch script
- Largest internal `.bss` symbols from eSpeak (ELF `nm`): `phoneme_list` 0x7d20 = 32 032 B; `echo_buf` 0x2af8 = 11 000 B; `frame_pool` 0x2a80 = 10 880 B; `ph_list2` 0x1f40 = 8 000 B; `phoneme_tab_list` 0x19c8 = 6 600 B; `hspect` 3 200 B; `wcmdq` 2 720 B — `build-release/alertalergo.elf`; sizes come from upstream constants such as `N_PHONEME_LIST 1000`, `N_WCMDQ 170` — [synthesize.h](firmware/components/third_party/espeak-ng/upstream/src/libespeak-ng/synthesize.h)
- Data: `phondata` 554 740 B, `pt_dict` 76 518 B, `phontab` 58 652 B, `phonindex` 43 316 B, `intonations` 2 312 B, `lang/pt-br` 109 B (total 735 518 B with SHA-256 list in `data.sha256`); packed image `espeak.bin` = 735 910 B (~70 % of the 1 MiB partition) — local `ls`; [data.sha256](firmware/components/third_party/espeak-ng/data.sha256); `build-ci/local-60b6894/firmware-release-*/coldflash/espeak.bin`
- Stack: `#define SPK_STACK 65536 /* medido: ~39 KB na fala de paciente */`, created with `xTaskCreateWithCaps(..., MALLOC_CAP_SPIRAM)`, priority 2; comment "A pilha do eSpeak é funda (o upstream sugere 80 KB)"; PCM buffer `SPK_MAX_S 12` seconds × sample rate × 2 B in PSRAM — [firmware/main/main.c](firmware/main/main.c) lines ~417–600
- Board findings in `e1976d1`: "eSpeak needs about 39 KB of stack (12 KB corrupted the NimBLE queue and tripped the interrupt watchdog), so its task stack lives in PSRAM; and its 90 KB of fixed .bss left 21 KB of internal heap, below the 32 KB of FR-SPK-06. LVGL now uses the libc malloc instead of its 64 KB static pool, which gives heap_min about 49 KB during speech" — commit `e1976d1`
- `.bss` cannot be moved to PSRAM: "Moving eSpeak .bss to PSRAM is impossible with SPIRAM_IGNORE_NOTFOUND (FR-PLT-02)" (incompatible with `SPIRAM_ALLOW_BSS_SEG_EXTERNAL_MEMORY`), so other subsystems were pushed out of internal RAM: BLE controller in flash, FreeRTOS/ringbuf functions out of IRAM, NimBLE pools in PSRAM, Wi-Fi 4 static RX buffers; `.iram0.text` 118 → 86 KB; TC-SPK-25 heap_min 39 828 — commit `1a194eb`; [sdkconfig.defaults](firmware/sdkconfig.defaults) (lines 15–17, 23–25, 36–54)
- Further RAM pressure fixes motivated by FR-SPK-06: `1a96e31` (free ~30 KB: Wi-Fi/lwIP buffers try PSRAM, no AMPDU, no Wi-Fi IRAM opt), `286a657` (console stack/line buffer to PSRAM; heap_min had dropped to 31 632 on `319d430`), `CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC=y` "para a heap interna livre ficar ≥ 32 KB durante a fala" — commits `1a96e31`, `286a657`; [sdkconfig.defaults](firmware/sdkconfig.defaults)
- Measured on target (`SPEECH done … heap_min=` is minimum internal free heap since boot): `ms=2557 heap_min=39828` for the 35-char battery phrase with SoftAP+BLE (dut-86b38a1); `ms≈5038–5051 heap_min=75212` for 50 consecutive 56-char patient phrases (target-ci-b228a76, no Wi-Fi) — grep of `test-results/dut-86b38a1*`, `test-results/target-ci-b228a76*`
- `ms=` is the audio playback duration (from codec open to close, including 60 ms lead silence and ~90 ms tail), not synthesis time — [main.c](firmware/main/main.c) `audio_task`
- Synthesis runs fully before playback ("enche um buffer na PSRAM; a tarefa de áudio o toca depois do tom"), one utterance at a time; callback yields with `vTaskDelay(1)` per chunk (FR-SPK-03 watchdog); 3 s no-audio timeout (FR-SPK-05) — [main.c](firmware/main/main.c)
- TC-SPK-23 asserts speech starts 0–1.5 s after the low-battery tone (`assert 0 < dt <= 1.5`) and passed at `b228a76` — [tests/target/test_speech.py](tests/target/test_speech.py) line 76; [testing/test-plan.yaml](testing/test-plan.yaml) TC-SPK-23
- Sample rate: whatever `espeak_ng_GetSampleRate()` returns; upstream wavegen presets are "for 22050 Hz sample rate"; tones use `AUD_HW_RATE 16000`; the codec is reopened at the speech rate per playback — [speech_synth.c](firmware/components/l1_speech/speech_synth.c), [wavegen.c](firmware/components/third_party/espeak-ng/upstream/src/libespeak-ng/wavegen.c) line 206, [l1_audio.h](firmware/components/l1_audio/include/l1_audio.h)

### Inferences
- PSRAM budget attributable to speech ≈ 736 KB (data copies) + 64 KB (stack) + ~529 KB (12 s × 22 050 Hz × 2 B buffer, if the rate is 22 050) ≈ 1.3 MB of octal PSRAM (board PSRAM size not checked in this analysis). The 22 050 figure is inferred from upstream defaults, not from a log in the repo.
- Real-time factor: a 56-char utterance plays ~5.0 s and speech start is ≤ 1.5 s after the tone (the tone itself lasts ≤ 1 s, FR-AUD-02), so full-utterance synthesis of ~5 s audio completes in well under ~2.5 s, i.e. RTF roughly < 0.5 on the ESP32-S3 at default clocks with PSRAM data — a loose upper bound, not a measurement.
- The 90 KB internal `.bss` is the single most important portability limitation for a standalone component; an optional patch (à la `ESPEAK_HEAP_HACK`) or a build that permits `.bss` in PSRAM would be the obvious improvement, at the cost of the "unmodified upstream" property.

### Gaps
- No direct synthesis-time or RTF log (e.g. a `SPEECH synth ms=` marker) exists; no CPU-load figure; no init-time figure.
- Exact runtime sample rate not found in logs (only inferred from upstream code).
- Actual PSRAM consumption was not measured in the repo.

---

## 4. Languages, pt-BR specifics, and drug-name pronunciation

### Takeaway
Only Portuguese is shipped (pt dictionary + `pt-BR` voice; formant synthesis, default parameters 175 wpm, pitch 50, no word gap). The project adds `pt_listx`, a small exception dictionary that fixes stress/hiatus for drug names spoken without accents (the codec stores uppercase, accent-free fields), and text normalisation (lowercase to avoid spelling-out as acronyms, `-` → space). Intelligibility with clinical evaluators (NFR-SPK-01) and the voice-parameter decision (OD-19) are still open; the reference drug list was replaced by the owner on 2026-11-16, after `pt_listx` was built for the previous list.

### Cited Findings
- Data contains only `pt_dict` and `lang/pt-br` (plus the language-independent phoneme files) — [data.sha256](firmware/components/third_party/espeak-ng/data.sha256)
- `pt_listx` entries: `cefalexina $3`, `nimesulida $3`, `morfina $1`, `carbamazepina $4`, `codeina k,ode'in&`, `lidocaina l,idoka'in&`, `acido 'asidw`, `acetilsalicilico ,asetS,iUsalis'ilikU`; rationale: "O aparelho fala o campo sem acento (FR-SLOT-01), então a sílaba tônica e os hiatos que o acento marcaria vêm daqui" — [pt_listx](firmware/components/third_party/espeak-ng/pt_listx)
- Commit: "Without it eSpeak stressed cefalexina, nimesulida, morfina, carbamazepina and acetilsalicilico on the wrong syllable and read codeina/lidocaina with a diphthong … TC-SPK-05 pins the phonemes of all 20 reference drugs" — commit `1fcf544` (2026-11-11)
- TC-SPK-05 (host): the 20 drug names produce the phonemes pinned in `vectors/speech/drug_phonemes.inc` (e.g. `{"dipirona", "dZ,ipi*'on&"}`, `{"codeina", "k,ode'in&"}`); "sem pt_listx 9 deles saem errados"; status successful at `688b44f` — [testing/test-plan.yaml](testing/test-plan.yaml), [tests/host/vectors/speech/drug_phonemes.inc](tests/host/vectors/speech/drug_phonemes.inc), [tests/host/speech_phonemes.c](tests/host/speech_phonemes.c)
- The current reference list "fornecida pelo responsável em 2026-11-16 (substitui a proposta do assistente de 2026-11-08)" has different drugs (losartana potássica, metformina, hidroclorotiazida, sinvastatina, omeprazol, …, loratadina); procedure: generate WAVs on the host, listen, add failures to `pt_extra`, then NFR-SPK-01 with 2 nursing evaluators ≥ 18/20 — [testing/manual/spk-reference-drugs.md](testing/manual/spk-reference-drugs.md)
- Voice parameters centralised in `speech_params.h` (`SPK_RATE_WPM 175`, `SPK_PITCH 50`, `SPK_WORDGAP 0`, "os padrões do eSpeak"), shared by device and host PCM tool so hashes match; rate configurable at runtime 80–260 wpm via `speech_rate_wpm` (FR-CFG-07) — [speech_params.h](firmware/components/l1_speech/include/speech_params.h), [FSD.md](docs/Functionality/FSD.md) line ~1983, commit `03c0b38`
- OD-19 (open): intelligibility for blind/low-vision users — rate, pauses, pitch; listening kit A–D with 20 drugs delivered 2026-11-11; "provável C: 130 palavras/min com pausas"; possible recorded drug clips if insufficient — [FSD.md](docs/Functionality/FSD.md) line ~465
- Text normalisation: "Para a fala viram minúsculas com espaços — em maiúsculas o eSpeak pode soletrar a palavra como sigla"; spoken templates e.g. «Atenção. Paciente, ‹nome›. Alergia a, a, b e c.», «Alergia a látex.» — [l2_speech.h](firmware/components/l2_speech/include/l2_speech.h), [speech_text.c](firmware/components/l2_speech/speech_text.c)
- Risk R6 "Pronúncia ruim de fármacos | alta" mitigated by screen-as-source-of-truth and `pt_extra` (FR-SPK-07) — [FSD.md](docs/Functionality/FSD.md) line ~424
- Audio post-processing for speech: +4 dB gain with a soft knee above 24 000 (eSpeak "peaks near full scale but its RMS sits around -21 dBFS"), 60 ms lead silence and 10 ms fade-in to remove an onset click — commit `134dcef`; [l2_audio/audio.c](firmware/components/l2_audio/audio.c) `aud_speech_sample`

### Inferences
- `pt_listx` covers the earlier (assistant-proposed) list; the owner's 2026-11-16 list shares only some names (acido acetilsalicilico, dipirona, paracetamol, ibuprofeno, amoxicilina), so new drug names (e.g. hidroclorotiazida, glibenclamida, besilato de anlodipino) are not pinned by TC-SPK-05 and have not been checked. This is an observation from comparing the two files.
- The "accent-free input → stress dictionary" problem is a reusable, publishable insight for pt-BR TTS on constrained devices where data is stored in ASCII.

### Gaps
- No result of human listening (NFR-SPK-01) found; FR-SPK-07 manual contract ("WAVs aprovados por escuta humana") not recorded as done.
- No pronunciation fixes for the 2026-11-16 list were found.

---

## 5. Coupling to the AlertAlergo product (what to separate for a standalone component)

### Takeaway
The engine-plus-storage layer (`third_party/espeak-ng` + `l1_speech` + `gen-espeak.sh` + `gen-espeak-image.py`) is already nearly product-independent (~300 lines of glue). Product coupling sits in: the task/buffer/timeout/cancel logic in `firmware/main/main.c`, the ES8311 audio path, product texts/markers in `l2_speech`, the drug dictionary, FSD requirement IDs in comments, and some hard-coded constants.

### Cited Findings
- `l1_speech` depends only on `esp_common`, `espeak-ng`, `esp_partition`, `vfs`, `esp_rom`, `esp_timer` — [l1_speech/CMakeLists.txt](firmware/components/l1_speech/CMakeLists.txt)
- Hard-coded in the glue: partition label `"espeak"` and subtype `0x40`, mount point `/es`, voice `/es/lang/pt-br`, `MAX_FD 4`, magic `"AAES"` ("AlertAlergo eSpeak"), `PART_SIZE = 0x100000` in the image builder; global callback state (single instance, not re-entrant) — [espeak_part.c](firmware/components/l1_speech/espeak_part.c), [speech_synth.c](firmware/components/l1_speech/speech_synth.c), [gen-espeak-image.py](scripts/gen-espeak-image.py)
- `PATH_ESPEAK_DATA="/es"` is baked into the eSpeak component's compile definitions — [third_party/espeak-ng/CMakeLists.txt](firmware/components/third_party/espeak-ng/CMakeLists.txt)
- RTOS integration (PSRAM stack task, 12-s PSRAM buffer, 3 s timeout, cancel on "silence" gesture, `SPEECH start/done/abort/fail` markers, tone-then-speech sequencing) lives in the app's `main.c`, not in a reusable component — [firmware/main/main.c](firmware/main/main.c) lines ~405–620
- Product-specific: `l2_speech` (alert texts, `alr_event_t`, `texts_pt_br.h`), `pt_listx`, `speech_params.h` comments referencing OD-19/FSD, `gen-espeak.sh` also generates the project's PCM reference hashes into `tests/host/vectors/speech/` — [l2_speech.h](firmware/components/l2_speech/include/l2_speech.h), [gen-espeak.sh](scripts/gen-espeak.sh)
- `gen-espeak.sh` uses `${TMPDIR:-/tmp}` and is pt-only (copies only `pt_dict` and `lang/roa/pt-BR`) — [gen-espeak.sh](scripts/gen-espeak.sh)
- sdkconfig choices needed by the port are mixed with product settings (PSRAM octal, `LV_USE_CLIB_MALLOC`, BT/Wi-Fi IRAM moves) — [sdkconfig.defaults](firmware/sdkconfig.defaults)

### Inferences
- To publish as a standalone ESP-IDF component (e.g. on the Espressif Component Registry): parameterise language list/voice, partition label/subtype, mount point (also in `PATH_ESPEAK_DATA`), image-size limit; move the generic task/streaming wrapper (queue, PSRAM stack, timeout, cancel, yield) from `main.c` into the component behind Kconfig; add an `idf_component.yml`, a top-level GPL-3.0 `LICENSE`, an example app with `esp_codec_dev`/I2S; possibly a partition-image CMake target (`esptool`/`parttool` flashing). Product texts, `pt_listx` and markers stay in the product (or `pt_listx` becomes an optional "medical pt-BR" extension).
- Optional Kconfig knob for moving `.bss` to PSRAM (when `SPIRAM_IGNORE_NOTFOUND` is off) or a heap-allocation patch would broaden applicability.

### Gaps
- No existing `idf_component.yml` for the eSpeak component; no example project; license metadata for registry not prepared.

---

## 6. Test evidence available

### Takeaway
There is a layered, automated test harness: host tests prove bit-exact PCM equality with the upstream build and pin drug-name phonemes; target tests on the real board cover boot integrity check, markers, tone→speech latency, 50-utterance soak without watchdog, and internal-heap floor with Wi-Fi SoftAP + BLE + LVGL. Human intelligibility tests are pending.

### Cited Findings
- TC-SPK-04 (host): 10 fixed texts synthesised 3× with the vendored sources; SHA-256 equal to each other and to `pcm.sha256` generated from the upstream 1.52.0 build by `gen-espeak.sh`; successful at `688b44f` (evidence `test-results/host-688b44f/`) — [testing/test-plan.yaml](testing/test-plan.yaml), [tests/host/check_speech_pcm.py](tests/host/check_speech_pcm.py), [tests/host/speech_pcm.c](tests/host/speech_pcm.c), [vectors/speech/texts.txt](tests/host/vectors/speech/texts.txt)
- TC-SPK-05 (host): drug phonemes pinned; successful at `688b44f` — test-plan.yaml
- TC-SPK-11 (host, spoken text per event): status "not done"; TC-SPK-12 (marker format): successful — test-plan.yaml
- TC-SPK-21 (`SPEECH ready=1` after splash), TC-SPK-22 (`speech say` start/done, ms 300–5000), TC-SPK-23 (speech ≤ 1.5 s after tone), TC-SPK-24 (50 utterances, no `task_wdt`, heap_min ≥ 32768): successful on target at `b228a76` (2026-11-12), evidence `test-results/target-ci-b228a76/` — test-plan.yaml
- TC-SPK-25 (5 utterances with SoftAP+BLE+LVGL, heap_min ≥ 32768): successful at `86b38a1` (2026-11-16), evidence `test-results/dut-86b38a1/`, measured 39 828 — test-plan.yaml; grep of results
- FR-PLT-06 contract: corrupted CRC → `SPEECH ready=0 reason=bad_crc`, tones present (target tier) — [FSD.md](docs/Functionality/FSD.md) line ~1905
- FR-SPK-04 requires identical PCM "no host e no alvo"; the implemented test (TC-SPK-04) is host-only — FSD line ~1310; test-plan.yaml
- Firmware build is reproducible from CI artifacts (`build-ci/local-<sha>/`), including `coldflash/espeak.bin` for test/release/demo variants — local listing of `build-ci/local-60b6894/`
- Later target runs (60b6894) report 49 green and 2 environmental failures including speech duration, attributed to real bracelets on air, not to the speech engine — [CLAUDE.md](CLAUDE.md) «Atualização 2026-11-19»

### Inferences
- The bit-exact host-vs-upstream PCM test is a strong, citable correctness argument for "unmodified port"; extending it to the target (dump PCM hash over serial) would close FR-SPK-04 fully and would be an academically interesting result (cross-architecture determinism of a formant synthesiser, Xtensa vs x86-64).
- Engineering narrative usable for a paper/report: integrating a desktop-class TTS (~90 KB static RAM, ~39 KB stack) alongside BLE + Wi-Fi SoftAP + LVGL on a 512 KB-SRAM MCU, with documented RAM-budget fixes and a measured 39 828 B internal-heap floor.

### Gaps
- No PCM hash comparison on target; no RTF/CPU measurement; no human listening results (NFR-SPK-01, FR-SPK-07); TC-SPK-11 not done; no FR-PLT-06 corruption test result located in `test-results/` during this analysis (not searched exhaustively).
