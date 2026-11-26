---
name: esp-idf
description: >
  Build, size and lint the ESP-IDF firmware and the host-built eSpeak NG on the
  bench notebook: pinned ESP-IDF version, clean environment wrapper, low-priority
  two-job builds, sdkconfig and partition rules, component layout, memory budget
  checks. Use for "build", "idf.py", "sdkconfig", "partition", "menuconfig",
  "size", "component", "eSpeak data image", or a build that runs out of memory.
---

# ESP-IDF on the bench notebook

The pinned version and the command list live in
`docs/Method/project/conventions.md`; this skill carries the judgement.

## Environment

- Always run through `scripts/idf.sh <command>`: it opens a clean shell with the
  pinned ESP-IDF, independent of whatever `~/.bashrc` loads. If `idf.py` is
  missing after activation, the environment does not exist — fail loudly.
- The notebook has ~3.4 GB of RAM and a 5400 rpm HDD. **Every** build is
  `nice -n 15 ionice -c 2 -n 7`, at most two jobs
  (`idf.py ... build -- -j2` or `IDF_PY_BUILD_JOBS=2`). One heavy process at a
  time; long builds run in the background.
- Searches skip `build*/`, `.git/` and `managed_components/`.

## Rules learned on this port (carry them)

- Changing `sdkconfig.defaults` means deleting the build directory's
  `sdkconfig`; otherwise the old values win silently.
- eSpeak NG keeps ~90 KB of fixed `.bss` in internal RAM. Check
  `.dram0.bss` / `.iram0.text` of the ELF (`idf.py size-components`) after any
  new module; a large static belongs in PSRAM (`EXT_RAM_BSS_ATTR`), never in
  internal `.bss`.
- A task that synthesises speech needs ~40 KB of stack; put it in PSRAM
  (`xTaskCreateWithCaps(..., MALLOC_CAP_SPIRAM)`).
- eSpeak lower-cases the voice path and limits it to 60 bytes: keep the data
  mount short (`/es`).
- The eSpeak data is not in the app: it is an image built from the same
  sources and flashed to its own partition. A build that changes the data
  without re-flashing the image is a stale-data bug, not a speech bug.
- The upstream sources stay unmodified; project code lives beside them. A
  needed change to upstream goes upstream first (and is tracked as a patch
  with its reason until it lands).

## Host build

The same eSpeak sources compile on the host (CMake) for the `host` tier: PCM
and phoneme checks run there in milliseconds. Host and target must use the same
sources and the same compiled data; a difference is a defect in the build, not
an acceptable drift.
