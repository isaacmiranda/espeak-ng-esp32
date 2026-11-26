# Prior art: eSpeak / eSpeak NG ports to microcontrollers (as of 2026-11-26)

Metadata (stars, last push, open issues) was read from the GitHub API on 2026-11-26. Notes marked "local copy" come from the clones in this repo's `reference/` folder (BackgroundAudio at `e5d6008`, 2026-10-08; arduino-espeak-ng at `3b01622`, 2026-10-13).

## Which ports exist? (inventory)

### Takeaway
Five published MCU ports/adaptations of eSpeak NG were found. Two are mature Arduino libraries: pschatzmann/arduino-espeak-ng (ESP32/RP2350) and earlephilhower/BackgroundAudio (RP2040/RP2350/ESP32). The others are a Teensy 4 derivative of the pschatzmann port, a brand-new native ESP-IDF port with pt-PT data (dfxpto-cyber, created 2026-11-25), and a subset port inside a retro-computer project on the RP2350. All of them are GPL-3.0. Every port uses eSpeak NG 1.52.x or a later upstream commit, and every one keeps the data in flash (C arrays or a raw flash partition), not on a filesystem.

### Cited Findings

**1. pschatzmann/arduino-espeak-ng**: https://github.com/pschatzmann/arduino-espeak-ng
- Author: Phil Schatzmann ("I converted eSpeak NG to an Arduino Library"). The license is GPL-3.0, with Apache-2.0, BSD-2 and UCD files also in the tree. It has 54 stars and 11 forks, 0 open issues (37 issues in total, all closed), and its last push was 2026-10-13. — [GitHub repo](https://github.com/pschatzmann/arduino-espeak-ng); GitHub API
- Version: upstream eSpeak NG 1.52.0. An issue reporter writes "espeak-ng Arduino library 1.52.0", and issue #31 "Version 1.52" (2026-07) tracked the upgrade. — [issue #37](https://github.com/pschatzmann/arduino-espeak-ng/issues/37), [issue #31](https://github.com/pschatzmann/arduino-espeak-ng/issues/31)
- Targets and framework: the README documents ESP32 and RP2350 (PSRAM via the arduino-pico core). Users report running it on the ESP32-C6, ESP32-S3 and ESP32-S2. It also has a CMake desktop build. It depends on `arduino-posix-fs` for file access and `arduino-audio-tools` for output. — [README](https://github.com/pschatzmann/arduino-espeak-ng), [issue #36](https://github.com/pschatzmann/arduino-espeak-ng/issues/36), [issue #8](https://github.com/pschatzmann/arduino-espeak-ng/issues/8)
- Data storage: the data ships as header files in `src/data`, one `*_dict.h` per language. "The recommended way is to load the data from PROGMEM." Loading from an SD card "uses excessive RAM" and needs PSRAM. A virtual POSIX filesystem (`/mem/data`) maps the PROGMEM arrays to file names. — [README](https://github.com/pschatzmann/arduino-espeak-ng), [issue #37](https://github.com/pschatzmann/arduino-espeak-ng/issues/37)
- Footprint (ESP32, minimum configuration, Huge APP partition): 1,457,411 bytes of flash (46%) and 39,616 bytes of globals (12%). An `ESPEAK_HEAP_HACK` option moves large buffers to the heap, and `setUsePSRAM(false)` avoids PSRAM latency. — [README](https://github.com/pschatzmann/arduino-espeak-ng). A search snippet of an older README gives "52% program / 36% dynamic", so the numbers have changed over versions. — [pschatzmann.github.io](https://pschatzmann.github.io/arduino-espeak-ng)
- Languages: "more than 100 languages and accents". Local copy: `src/data/pt_dict.h` exists (418 KB of C source).
- Known limitations and bugs, all now closed:
  - #3/#2: the broken `iswalpha()` in the ESP32 toolchain made accented and umlaut characters non-alphabetic; fixed by switching to `ucd_isalpha()`.
  - #7: `.dram0.bss` overflowed by about 13 KB when WiFi was added on a classic ESP32. The maintainer's advice was "If you must use Wifi, why don't you just do TTS via Wifi as well?"
  - #28: `espeak.end()` hit an assert in `heap_caps_free`.
  - #35: changing the voice at runtime crashed on the ESP32-C6.
  - #36: on the ESP32-S3 N16R8 the PROGMEM-to-file mapping returned garbage file names (a fix was made in arduino-posix-fs, but the reporter still saw the error afterwards).
  - #37: on the ESP32-S3 with core 3.3.12, "test"/"five" were spoken as "letter FB06/FB02" because the `.replace` table was located by absolute-address alignment.
  - #33: an assert in `MakePhonemeList`.
  - #34: Vietnamese words were cut off.
  - [issues list](https://github.com/pschatzmann/arduino-espeak-ng/issues?q=is%3Aissue)

**2. earlephilhower/BackgroundAudio**, `src/libespeak-ng`: https://github.com/earlephilhower/BackgroundAudio
- Author: Earle F. Philhower III. The license is GPL-3.0 ("ESpeak-NG is GPL3 licensed"). It has 156 stars, 12 forks and 4 open issues, and its last push was 2026-10-08. — [README](https://github.com/earlephilhower/BackgroundAudio); GitHub API
- The eSpeak NG support arrived in PR/commit #36 "Add ESpeak-NG based background speech generation" on 2025-01-26. Follow-ups #43 "No KLATT in Espeak, remove source" and #44 "auto-include dictionary" are dated 2025-01-29. — GitHub API (commits/issues of the repo)
- Version: local copy, `src/libespeak-ng/config.h` contains `#define PACKAGE_VERSION "1.52.0"`.
- Targets and framework: an Arduino library for the RP2040 and RP2350 (arduino-pico) and the ESP32 (arduino-esp32 3.x I2S API). It is published in the PlatformIO registry as `earlephilhower/BackgroundAudio` 1.4.4 (2025-10-29). — [README](https://github.com/earlephilhower/BackgroundAudio), [PlatformIO API search "espeak"](https://api.registry.platformio.org/v3/search?query=espeak)
- Data storage: per-language dictionaries are C headers in `src/libespeak-ng/dict/` and voices in `voice/*.h` (local copy; `pt_dict.h` is 471 KB of source). Synthesis is interrupt-driven, generates one frame per cycle and cannot read LittleFS or SD at interrupt time. — local copy README/LANGUAGES.md; [README](https://github.com/earlephilhower/BackgroundAudio)
- pt-BR: LANGUAGES.md lists "Portuguese (Brazil) `#include <libespeak-ng/voice/pt_br.h>` `setVoice(voice_pt_br)`" and "Portuguese (Portugal) `voice_pt`". — local copy `reference/BackgroundAudio/LANGUAGES.md:106-107`
- RAM/flash footprint: not documented. Klatt synthesis was removed (#43).

**3. vindar/espeak-ng_T4** (Teensy 4.0/4.1, Cortex-M7): https://github.com/vindar/espeak-ng_T4
- It is "based on the Arduino eSpeak NG port for ESP32" by pschatzmann. The license is GPL-3.0. It has 5 stars and 2 forks; it was created 2025-05-22 and last pushed 2025-05-31, so it is effectively dormant.
- Voices and dictionaries are "compiled directly into the binary" with no filesystem. Runtime RAM is about 150 kB (in DMAMEM, or EXTMEM/PSRAM). Flash is about 1 MB with English, plus "a few hundred kilobytes" per extra language. It works with the Teensy Audio library. MBROLA is not implemented. — [README](https://github.com/vindar/espeak-ng_T4)

**4. dfxpto-cyber/eSpeak-NG-.-Esp32** (native ESP-IDF, pt-PT): https://github.com/dfxpto-cyber/eSpeak-NG-.-Esp32
- Author: Domingos Guedes Ferreira ("com a ajuda do Claude (Anthropic) para debug de erros"). The license is GPL-3.0-or-later. It was created 2026-11-25 with a single commit, "versão 1.0.0", and has 0 stars. It is very new and unvetted. — [README](https://github.com/dfxpto-cyber/eSpeak-NG-.-Esp32); GitHub API
- Version: pinned to upstream commit `688cb603` (in `UPSTREAM_COMMIT`), a merge on espeak-ng master dated 2026-11-08, which is post-1.52.0. — GitHub API
- Framework and targets: ESP-IDF 5.4 ("deve funcionar com 5.2+"), ESP32-S3 with at least 4 MB of flash, tested on the M5Stack CoreS3 and in QEMU. PSRAM is optional. It came out of the CSD-AP project, an assistive device for blind users.
- Structure: three IDF components, `espeak-ng` (patched by `tools/espeak/patch_espeak.py` to read from memory-mapped flash), `espeak_pack` and `espeak_tts` (a task, `espeak_tts_speak()`, and a PCM sink callback with resampling).
- Data storage: a prebuilt pack, `data/espeak-pt.bin` (about 810 KB: roa/pt plus 33 variants), is written to a raw data partition named `espeak` (at least 1 MB) with `esptool_py_flash_to_partition`, then read directly from mapped flash ("sem ocupar RAM"). It includes tools to rebuild the pack and add languages (`make_espeak_pack.py --extra`).
- Footprint: about 560 KB of app flash plus 810 KB of data. Without PSRAM it needs about 150 KB of static RAM and a 32 KB stack. With `CONFIG_SPIRAM_ALLOW_BSS_SEG_EXTERNAL_MEMORY`, the bss and the stack move to PSRAM. In that case the sink must not write to flash (NVS/FAT) from the eSpeak task.
- Languages: European Portuguese only, out of the box. It also documents a fix for accented letters ("A biblioteca de C do ESP-IDF não as reconhece") and Portuguese reading of numbers, dates and times.
- It is not in the Espressif Component Registry; it is copied via `EXTRA_COMPONENT_DIRS`.

**5. ccdavis/retro_pc_project** (RP2350, partial): https://github.com/ccdavis/retro_pc_project
- `05_accessible_speech_retro_pc/third_party/espk/` holds "a subset of eSpeak NG" plus derived `ESPK.DAT` data and a fixed-point port of klatt 3.04 `parwave.c`. These run on Core 1 of the RP2350-Zero as a speech synthesizer and screen reader. The license is GPL-3.0. The README says it is "a fully AI written project". It has 0 stars and was created 2026-11-08. — [README](https://github.com/ccdavis/retro_pc_project)

**Related but not MCU ports:**
- [eugenehp/espeak-ng-rs](https://github.com/eugenehp/espeak-ng-rs) is a pure-Rust port that is bit-identical against the C oracle. It has 27 stars and was pushed 2026-11-25. It is GPL-3.0-or-later per the README badge. No MCU or `no_std` claim was found in the README.
- [Hackster "Stack-chan minimal voice in English"](https://www.hackster.io/uta-aoya/stack-chan-minimal-voice-in-english-c00769) is a user project on the M5 AtomS3R that adapted the pschatzmann library to use PSRAM plus PROGMEM. The write-up reports compatibility issues with M5Speaker (search snippet; not fetched in full).
- Non-eSpeak MCU TTS, for context: [DiUS/esp-picotts](https://github.com/DiUS/esp-picotts) is an ESP-IDF component in the registry as `jmattsson/picotts` 1.1.4 ([registry](https://components.espressif.com/components/jmattsson/picotts)); it has 35 stars and was pushed 2026-11-10. Others are [alkhimey/esp32-flite](https://github.com/alkhimey/esp32-flite) (Flite, ESP-IDF 3.2.2) and `earlephilhower/ESP8266SAM` (SAM).

### Inferences
- The lineage is: upstream → pschatzmann (2022) → vindar (Teensy). BackgroundAudio (2025) is an independent conversion to C arrays. dfxpto-cyber (2026-11) uses a different design: a raw flash partition plus mmap instead of compiled-in arrays. That design is closer to what a native ESP-IDF product would want, because the data can be updated without relinking.
- The ESP32 `iswalpha()` defect is the recurring porting pitfall for accented languages (pschatzmann #3, upstream #1611, dfxpto README). Any pt-BR port must handle it.

### Gaps
- No RAM/flash numbers for BackgroundAudio's eSpeak path.
- I found no STM32, nRF or Zephyr port of eSpeak NG. GitHub repository searches for "espeak zephyr / stm32 / nrf52 / rp2040 / esp-idf" returned only desktop wrappers. GitHub code search (not run) might find unpublished ones.
- I could not verify any port in Arduino Library Manager listings.
- The pschatzmann.ch blog posts (2022, voice setting and PSRAM; 2021, "text-to-speach in arduino conclusions") are referenced in issue #7 and on Hackster but were not fetched.

## Is there an ESP-IDF-native eSpeak NG component? Any in the Espressif registry or PlatformIO?

### Takeaway
No eSpeak NG component is in the Espressif Component Registry; a search for "espeak" returns "Components not found". The only native ESP-IDF port found is dfxpto-cyber/eSpeak-NG-.-Esp32, which is GitHub-only and one day old. In the PlatformIO registry, only BackgroundAudio, an Arduino-framework library that embeds eSpeak NG, matches "espeak".

### Cited Findings
- The Espressif registry search for "espeak" returns "Components not found." — [components.espressif.com/components?q=espeak](https://components.espressif.com/components?q=espeak)
- The only on-device TTS in the registry is PicoTTS (`jmattsson/picotts`), which recommends an "ESP32-S3 with sufficient PSRAM and flash". — [registry](https://components.espressif.com/components/jmattsson/picotts/versions/1.1.4/readme)
- The PlatformIO API search "espeak" returns 2 results, `earlephilhower/BackgroundAudio` 1.4.4 and `earlephilhower/ESP8266SAM` 1.1.0 (SAM, not eSpeak). pschatzmann/arduino-espeak-ng is not in the PlatformIO registry, although issue #1 shows people compiling it under PlatformIO from git. — [PlatformIO API](https://api.registry.platformio.org/v3/search?query=espeak), [issue #1](https://github.com/pschatzmann/arduino-espeak-ng/issues/1)
- The native ESP-IDF port dfxpto-cyber/eSpeak-NG-.-Esp32 is described above (section 1, item 4).
- This project (AlertAlergo V3) vendors eSpeak NG 1.52.0 as an ESP-IDF component, per CLAUDE.md. It is not published.

### Inferences
- Publishing a clean ESP-IDF component, for example one with a data partition and a pt-BR pack, would be the first such entry in the Espressif registry.

### Gaps
- The registry search was read from the web UI, not the API. It could miss a component whose name lacks "espeak" (for example "tts"); one known example is picotts.

## Does upstream espeak-ng support MCUs? Issues/PRs?

### Takeaway
Upstream has no official embedded or MCU support. The latest release is 1.52.0 (2024-12-12), and master is active (pushed 2026-11-19). Only two upstream threads touch MCUs: #918 asks how to shrink the library for embedded use, and #1611 asks to use UCD IsAlpha because of the ESP32 toolchain.

### Cited Findings
- Releases: 1.52.0 (2024-12-12), 1.51 (2022-04-02), 1.50 (2019-12-02). The repo has 7,062 stars and 672 open issues/PRs, and was last pushed 2026-11-19. — [espeak-ng/espeak-ng](https://github.com/espeak-ng/espeak-ng); GitHub API
- #918, "How to make espeak-ng even more lightweight (for embedded application)" (2021-04, closed). The author targets less than 500 KB of ROM. Stripping `libespeak-ng.so` took it from 1.56 MB to 512 KB, and the author asks how to remove languages. No maintainer answer was given. A 2023 commenter compiling under VC6 asks the same thing. — [issue #918](https://github.com/espeak-ng/espeak-ng/issues/918)
- #1611, "Use UCD functionality in common.c for IsAlpha()" (2022-12, still open). It cites the Arduino port: "The ESP32 toolchain appears to have a broken implementation of iswalpha()… multibyte characters not to be recognized as alphabetic". The only reply (jaacoppi) was "Probably it's just historical technical debt." — [issue #1611](https://github.com/espeak-ng/espeak-ng/issues/1611)
- Upstream issue searches for "microcontroller", "rp2040", "stm32" and "arduino" returned nothing else relevant. — GitHub search API (repo:espeak-ng/espeak-ng)
- Recent upstream security fixes in `readclause.c` (#2647, a global buffer overflow in the embedded-command 'B' handler, open 2026-11-06; PR #2556 bounding buf writes, closed 2026-09-18) postdate 1.52.0. Ports pinned to 1.52.0 (pschatzmann, BackgroundAudio, this project) would not include them. — [#2647](https://github.com/espeak-ng/espeak-ng/issues/2647), [#2556](https://github.com/espeak-ng/espeak-ng/pull/2556)

### Inferences
- Every MCU port carries patches out of tree: the data-as-arrays loader, the isalpha fix, and PSRAM/bss relocation. Updating to a newer upstream means re-applying them. dfxpto keeps its patch as a script (`patch_espeak.py`), which makes this easier.

### Gaps
- I did not check whether #2647 affects ports that never pass embedded commands. Needs code review.

## Does any port document pt-BR use and intelligibility?

### Takeaway
Not really. BackgroundAudio ships a `voice_pt_br` header, and arduino-espeak-ng ships `pt_dict`, but neither documents testing in Portuguese. The only Portuguese-focused port (dfxpto-cyber) is pt-PT and claims correct accents, numbers and dates. I found no intelligibility evaluation of eSpeak on an MCU, in any language.

### Cited Findings
- BackgroundAudio: "Portuguese (Brazil) … `setVoice(voice_pt_br)`". — local copy `reference/BackgroundAudio/LANGUAGES.md:106`; [repo](https://github.com/earlephilhower/BackgroundAudio)
- dfxpto-cyber: "Síntese de voz em português europeu"; the voice is `roa/pt` with 33 variants; it claims "Letras acentuadas pronunciadas correctamente" after an `iswalpha` fix. It was tested only on the M5Stack CoreS3 and in QEMU. — [README](https://github.com/dfxpto-cyber/eSpeak-NG-.-Esp32)
- pschatzmann issues show that accented and ligature input is fragile on ESP32: umlauts (#2), "st"/"ff"/"fi" ligatures (#6, #37), and a case where English was forced as the language (#23). — [issues](https://github.com/pschatzmann/arduino-espeak-ng/issues?q=is%3Aissue)

### Inferences
- Upstream pt-BR (`roa/pt-BR`) uses the same `pt_dict` as pt-PT. So the dfxpto pack would likely need only the `lang/roa/pt-BR` voice file added through `--extra`. This is unverified.

### Gaps
- No published listening test, word error rate or MOS for eSpeak NG pt-BR on any MCU. No academic paper on eSpeak on MCUs was found; Google Scholar was not queried directly.

## Blog posts, forums, papers

### Takeaway
There is little community material. The relevant items are the pschatzmann blog (referenced, not fetched), a Hackster Stack-chan project, and an Elektor note about ESP32 speech memory limits. Searches returned no relevant esp32.com, Hackaday or Reddit threads.

### Cited Findings
- pschatzmann blog posts are referenced from issue #7: "esp32-and-psram" (2022-05-30) and "text-to-speach-in-arduino-conclusions" (2021-06-23). — [issue #7](https://github.com/pschatzmann/arduino-espeak-ng/issues/7)
- [Hackster: Stack-chan minimal voice in English](https://www.hackster.io/uta-aoya/stack-chan-minimal-voice-in-english-c00769) uses arduino-espeak-ng on the AtomS3R with PSRAM and PROGMEM (search snippet).
- [Elektor Labs: ESP-32 speech function](https://www.elektormagazine.com/labs/esp-32-speech-function) says that, because of the ESP32's limited memory, only short 3–4-word sentences can be spoken continuously (search snippet). It is unclear whether it uses eSpeak.

### Gaps
- Hackaday.io, esp32.com and Reddit were not searched with site-specific queries. The single general query surfaced nothing from them.
