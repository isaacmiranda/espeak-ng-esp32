# Publication and contribution paths for an ESP-IDF eSpeak NG (pt-BR) component

Research date: 2026-11-26. Some pages (gnu.org, sciencedirect.com) could not be fetched in this session; items that rest on them are marked **[unverified this session]**.

## 1. Community distribution: Espressif Component Registry, PlatformIO, upstream espeak-ng

### Takeaway
The ESP Component Registry already hosts GPL-3.0 components and has no GPL-specific prohibition. The only hard upload requirement is a `version`; it also needs an SPDX `license` or a LICENSE file. No eSpeak NG component was found on the registry (PicoTTS is listed), so an `espeak-ng` ESP-IDF component would fill a gap. Upstream espeak-ng is active, with pt maintenance ongoing in 2026, and it accepts PRs. Engine PRs must be single-problem, tested and non-trivial. Language changes go through the language maintainer.

### Cited Findings
**ESP Component Registry / idf_component.yml**
- `version` is required for upload (set it in the manifest, as a git tag, or with `compote component upload --version`). `description`, `url` and `repository` are recommended and trigger a warning when missing. `repository` must be a valid git remote URL — [IDF Component Manager manifest reference](https://docs.espressif.com/projects/idf-component-manager/en/latest/reference/manifest_file.html)
- License: there must be either a `license` field or a `LICENSE`/`LICENSE.txt` file. `license` must be a valid SPDX identifier. If neither yields a type, the registry shows "Custom" — [manifest reference](https://docs.espressif.com/projects/idf-component-manager/en/latest/reference/manifest_file.html)
- `files` include/exclude filters. The default exclusions cover `build/**`, `managed_components/**`, `sdkconfig`, `dependencies.lock` and `.git/**`. The filters also apply to `examples/`, which is auto-discovered. `targets` is optional (omit it if all targets are supported). An `idf` dependency can pin a compatible ESP-IDF range. `path`/`git` dependencies are **not** allowed on upload — [manifest reference](https://docs.espressif.com/projects/idf-component-manager/en/latest/reference/manifest_file.html)
- Terms of Use: the uploader declares they created the content or hold legal authorization for it. Rights stay with the uploader or original copyright holder, who bears sole liability. Other users get rights "according to the license they select". No GPL-specific rule was found — [Registry Terms of Use](https://components.espressif.com/pages/terms) (seen via search snippet)
- GPL components already exist on the registry, e.g. `mrwheel/ota_upload` (GPL-3.0-or-later) and `slint/slint` (GPL-3.0-only among its options) — [ota_upload license](https://components.espressif.com/components/mrwheel/ota_upload/versions/1.0.0/license), [slint license](https://components.espressif.com/components/slint/slint/versions/1.2.2/license)
- Publishing authenticates with GitHub accounts and namespaces — [How to authenticate for publishing](https://docs.espressif.com/projects/idf-component-manager/en/latest/publish/how_to_authenticate.html)
- Adjacent registry TTS: `jmattsson/picotts` (PicoTTS engine) — [registry page](https://components.espressif.com/components/jmattsson/picotts/versions/1.1.3/examples). Search found no eSpeak NG component (the search was not exhaustive; confirm at components.espressif.com with `?q=espeak`).

**Prior embedded port (comparison baseline)**
- `pschatzmann/arduino-espeak-ng` (GPL-3.0, last push 2026-10-13, 54 stars). It loads data from PROGMEM, because SD loading "is using an excessive amount of RAM". Reported footprint on `esp32:esp32:esp32` (Huge APP): sketch 1,457,411 B flash and 39,616 B globals. It has PSRAM allocation via `heap_caps_malloc()` with fallback to internal RAM — [README via GitHub API](https://github.com/pschatzmann/arduino-espeak-ng)
- That port's author opened upstream issue #1611: the ESP32 toolchain's `iswalpha()` fails on multibyte characters, and `ucd_isalpha()` works. A maintainer replied it is "probably just historical technical debt". The issue is still open, which makes it a concrete upstreamable fix that matters for pt-BR accented letters — [espeak-ng#1611](https://github.com/espeak-ng/espeak-ng/issues/1611)

**PlatformIO Registry**
- Publish with `pio pkg publish`. The manifest is `library.json` (highly recommended). `license` takes an optional SPDX ID or expression. The version must be bumped on every republish. Run `pio pkg pack` to validate first. `pio pkg unpublish` removes a release — [Creating Library](https://docs.platformio.org/en/latest/librarymanager/creating.html), [pio pkg publish](https://docs.platformio.org/en/latest/core/userguide/pkg/cmd_publish.html)
- ESP-IDF libraries declare `"frameworks": ["espidf"]` and `"platforms": "esp32"`. This comes from a community example, not official docs — [community thread](https://community.platformio.org/t/publishing-a-new-library/16212)

**Upstream espeak-ng**
- The repo is active: last push 2026-11-19, 7,062 stars, 672 open issues and PRs, license GPL-3.0. The latest tagged release is still **1.52.0 (2024-12-12)**. `ChangeLog.md` already has a 1.53.0 section (unreleased as of this date), which lists "pt (Portuguese) -- Fabio Lima" under updated languages and fuzzing-driven memory-safety fixes — [GitHub API: repo/releases](https://github.com/espeak-ng/espeak-ng/releases), [ChangeLog.md](https://github.com/espeak-ng/espeak-ng/blob/master/ChangeLog.md)
- Contribution rules (docs/contributing.md):
  - Fork, run `ctest --test-dir build --output-on-failure`, then open a PR.
  - Each PR solves a single problem.
  - New functionality needs new automated tests.
  - "There shouldn't be trivial changes only like code indentation, fixed typos".
  - For an existing language, ask its maintainer (listed in `espeak-ng-data/lang`) to review.
  - Core changes should follow the roadmap wiki.
  - The project is volunteer-run, and reaction time is "one, two weeks".
  - Changes can also go by email to the groups.io list.

  [docs/contributing.md](https://github.com/espeak-ng/espeak-ng/blob/master/docs/contributing.md)
- The build is CMake, with options `-DUSE_MBROLA=OFF`, `-DUSE_KLATT=ON`, `-DUSE_LIBSONIC=OFF` and `-DUSE_LIBPCAUDIO=OFF`. Pronunciation tests use `test_phon <lang> <expected_phonemes> <text>` in `tests/*.test`. Dictionaries live in `dictsource/<lang>_rules` and `_list`. Upstream also ships an `AGENTS.md` for coding agents — [AGENTS.md](https://github.com/espeak-ng/espeak-ng/blob/master/AGENTS.md)
- The repo already has non-desktop ports in-tree (`android/`, `emscripten/`), so a precedent exists for platform directories. There is no ESP-IDF or MCU directory — [repo root listing](https://github.com/espeak-ng/espeak-ng)
- Open embedded-related issue: #2013, "option to build without git 'module'… on embedded systems with a small footprint" — [espeak-ng#2013](https://github.com/espeak-ng/espeak-ng/issues/2013). Searches for "microcontroller", "memory footprint" and "static allocation" returned no issues.
- pt-BR activity:
  - #2531 (closed 2026-11-07): an NVDA user reported a regression in the pt-BR "r" and intonation after Fabio Lima's update. The maintainer opened PR #2429 and adjusted the weak /r/ — [espeak-ng#2531](https://github.com/espeak-ng/espeak-ng/issues/2531)
  - #1054, "Brazilian Portuguese MBrola rules need adjustments" (open) — [espeak-ng#1054](https://github.com/espeak-ng/espeak-ng/issues/1054)
  - #2248, "pt-br not supported by the espeak backend" (open) — [espeak-ng#2248](https://github.com/espeak-ng/espeak-ng/issues/2248)
- The voice file `espeak-ng-data/lang/roa/pt-BR` sets `language pt-br`, `dictrules 2` and a `stressLength` row — [pt-BR voice file](https://github.com/espeak-ng/espeak-ng/blob/master/espeak-ng-data/lang/roa/pt-BR)

### Inferences
- The most realistic community path is to **publish the component on the ESP Component Registry** (namespace = GitHub user/org) under `license: "GPL-3.0-or-later"`. Pin `idf: ">=5.5"`, declare `targets: [esp32s3]` (or test the others), and provide `examples/` with a minimal "say a phrase" app. Optionally mirror it as a PlatformIO `library.json` with `frameworks: espidf`.
- The component should stay **separate from the clinical firmware**, i.e. it should not contain drug tables or patient logic. That way it is generic, reusable and registry-appropriate.
- Upstream contributions with the best odds, smallest first:
  - (a) the `ucd_isalpha` fix for #1611, with a test;
  - (b) pt-BR dictionary exceptions (`dictsource/pt_list`) for drug names, each covered by `test_phon` cases, coordinated with the pt maintainer (Fabio Lima) given the 2026 regression controversy;
  - (c) optional CMake switches that reduce footprint (e.g. compile a single language or drop SSML/klatt). These are likely harder: they touch core code and need maintainer buy-in per the roadmap rule.
  - A whole ESP-IDF port directory upstream is less likely to be accepted than a separate component that consumes upstream as a git submodule or vendored release.
- Track upstream 1.53 when it is released. The vendored 1.52.0 predates fuzzing-driven memory-safety fixes, which matters for a medical device.

### Gaps
- The full Registry Terms of Use prohibited-content list was not read. There is also no explicit statement that GPL is welcome, though precedent suggests it is accepted.
- No confirmation that no eSpeak component exists on the registry (the search was not exhaustive).
- PR #2429's merge state and the exact maintainer of `pt` / `pt-BR` (the `maintainer` line in the lang file) were not checked.
- Whether upstream would accept footprint-reduction build options is untested; no prior issue or PR was found.

## 2. Academic venues and their requirements

### Takeaway
JOSS is the cleanest fit for the reusable component (free, short paper). Under its 2026 rules it requires at least 6 months of public history, demonstrated research impact, and an AI-usage disclosure. AI-generated codebases alone do not count as scholarly contribution, which is directly relevant to this project. SoftwareX is the Elsevier alternative, open access with an APC of about USD 760–970. For the device and evaluation, Brazilian venues fit best: SBCAS (health), SBESC (embedded; English full papers go to IEEE Xplore, 6 pages) and IHC (accessibility). These need novelty plus evaluation.

### Cited Findings
**JOSS**
- Scope is research software with an "obvious" research application and clear research impact. The paper must not focus on new research results. The software must be feature-complete, documented, tested and packaged to community standards. Out of scope: minor utilities, thin API clients, single-function packages. Contributions to existing integrated libraries are welcome — [JOSS submitting (latest)](https://joss.readthedocs.io/en/latest/submitting.html)
- Pre-review gates: projects that were private need **≥ 6 months of public development history** with releases, issues and PRs. Commits concentrated in a short window are a negative signal. Failing a gate means desk rejection, possibly a "not yet" with resubmission after ≥ 6 months — [JOSS submitting](https://joss.readthedocs.io/en/latest/submitting.html)
- License must be OSI-approved. The repo must be public with an open issue tracker. `paper.md` holds summary, authors, affiliations and references — [JOSS submitting](https://joss.readthedocs.io/en/latest/submitting.html)
- AI policy: generative AI is permitted but must be disclosed (tools, versions, where it was used, and confirmation that humans made the core design decisions). Incomplete disclosure can lead to desk rejection or retraction — [JOSS submitting](https://joss.readthedocs.io/en/latest/submitting.html)
- The old effort proxy was about 3 months of individual work as a minimum. Submissions under 1000 LOC were flagged and under 300 LOC desk-rejected — [pre-2026 review criteria](https://joss.readthedocs.io/en/pre-2026-submission/review_criteria.html), [Minimum publishable unit (2020)](https://blog.joss.theoj.org/2020/07/minimum-publishable-unit)
- The January 2026 post says the 3-month benchmark "could be matched in three days, or even three hours" with generative AI. JOSS is shifting to evidence of research impact, intellectual contribution, scholarly significance and open-source practice. "Generating extensive codebases through AI prompts alone does not necessarily constitute the scholarly contribution" — [JOSS blog, Jan 2026](https://blog.joss.theoj.org/2026/01/preparing-joss-for-a-generative-ai-future), [latest review criteria](https://joss.readthedocs.io/en/latest/review_criteria.html)

**SoftwareX (Elsevier)**
- Open access. The APC is listed as USD 760 with a waiver policy on DOAJ and aggregators; one listing gives USD 970 — [DOAJ](https://doaj.org/toc/aebea1c2d72c41cfae9da55edb18f140), [Editage](https://www.editage.com/research-solutions/journal/softwarex/19571)
- Code must be freely available. Accepted code is archived on the journal's GitHub. The Original Software Publication uses a dedicated template with a code-metadata table (version, repository link, versioning system, languages and tools) — [software-update template v6, Mar 2026](https://legacyfileshare.elsevier.com/promis_misc/softwarex-software-update-template.docx)
- **[unverified this session]** The Guide for Authors could not be fetched (HTTP 403), so the word limit (commonly cited as about 3000 words) and current APC need confirming at https://www.sciencedirect.com/science/journal/23527110/publish/guide-for-authors

**HardwareX** (only if the whole device is opened)
- It covers free and open-source scientific hardware. Designs must be under an open-hardware license with editable design files in an approved repository, and all software used to operate the hardware must be included — [HardwareX template 2021](https://zenodo.org/records/5078227/files/HardwareXTemplate_20210707.pdf), [Wikipedia](https://en.wikipedia.org/wiki/HardwareX)
- Our device runs on a commercial Waveshare board. A HardwareX paper would need the bracelet and enclosure design as open hardware, so it is a weaker fit.

**SBESC (SBC CE-ESC)**
- Topics include real-time and run-time support, design methodologies and tools, IoT, embedded AI, and "embedded systems for healthcare". Assistive tech is not listed explicitly.
- Format: IEEE two-column, full papers ≤ 6 pages, in English, Portuguese or Spanish. English full papers go to IEEE Xplore (CPS); pt/es papers and work in progress go to SBC OpenLib (SOL). All papers get a DOI. Best papers are invited to journals.
- 2026 dates: final deadline around Aug 2, symposium Nov 24–27, 2026 in Salvador.

  [SBESC 2026 CFP](https://sbesc.lisha.ufsc.br/sbesc2026/Call+for+Papers)
- Best-paper special issues of SBESC 2025 appear in JBCS — [JBCS SBESC 2025](https://journals-sol.sbc.org.br/index.php/jbcs/sbesc-2025)

**SBCAS (SBC CE-CAS)**
- 2026 (XXVI edition) ran June 1–4 in Ouro Preto, so the next opportunity is SBCAS 2027 (CFP not found).
- Main track: 373 submissions, 107 full papers and 39 works in progress. Acceptance was 35.1% for full papers and 57.4% for work in progress. Review is double-blind, in Portuguese or English, published on SOL. There is also an extended-proceedings volume with the undergraduate research contest (CTIC).

  [SBCAS on SOL](https://sol.sbc.org.br/index.php/sbcas/index), [Anais estendidos](https://sol.sbc.org.br/index.php/sbcas_estendido/issue/view/1716)

**Other Brazilian venues (not researched in depth)**
- IHC (accessibility), WSCAD, SBrT and Revista Brasileira de Computação Aplicada were not checked this session. **[unverified]**
- CSBC 2026 satellite-events call — [SBC PDF](https://www.sbc.org.br/wp-content/uploads/2025/10/Chamada-de-Eventos-Satelite-do-CSBC-2026.pdf)

### Inferences
- **JOSS timing risk:** if the component repo goes public now, the earliest JOSS submission is about mid-2027. The heavy AI assistance in this project must be disclosed. The paper should emphasize *human* design decisions: the pt-BR drug-name lexicon, the memory-placement strategy (PSRAM vs internal RAM), and real-time constraints alongside a safety-critical display path.
- JOSS's "research software" bar is a risk for a product component. The research angle could be framing it as a platform for on-device TTS intelligibility and accessibility research in low-resource languages and dialects on MCUs.
- **SBESC** suits a systems paper: footprint, real-time factor, coexistence with BLE and Wi-Fi, and heap minimum. **SBCAS** suits the clinical and assistive device paper plus a listener evaluation. **IHC** suits a study with blind and low-vision users. SoftwareX is a fallback if JOSS screening fails, but it costs an APC.
- A plausible sequence: registry release → SBESC 2027 systems paper (English, IEEE Xplore) → SBCAS 2027 with user evaluation → JOSS once there are 6 months of history.

### Gaps
- The SBCAS 2027 and SBESC 2027 calls, and SBCAS page limits, were not found.
- The IHC, WSCAD, SBrT and RBCA requirements were not researched.
- The IEEE assistive-technology conferences named in the brief were not researched.
- SoftwareX word limit and current APC are unverified (403).

## 3. Evaluation that would make it publishable

### Takeaway
A credible evaluation combines objective systems metrics with perceptual intelligibility tests:
- systems metrics: flash, internal RAM and PSRAM, heap minimum, real-time factor, latency to first audio, CPU share, compared with other ports;
- perceptual tests: word or sentence recognition with semantically unpredictable sentences plus a domain list of drug names, scored as word error rate, plus MOS.

A study with blind and low-vision listeners in Brazil needs CEP approval via Plataforma Brasil.

### Cited Findings
- **SUS rationale:** semantically unpredictable sentences stop listeners from guessing unclear words from context. A Latin-square design spreads each listener's bias across voices — [Columbia intelligibility testing notes](https://www.cs.columbia.edu/~ecooper/tts/intelligibility.html)
- **Scoring:** "sentences-correct" is adequate when only rank order matters, and full SUS response analysis is labor-intensive — [Bunnell, SSW 2007](https://www.isca-archive.org/ssw_2007/bunnell07_ssw.html)
- **Limits of WER/MOS:** they focus on low-level accuracy and miss whether key information gets across. SP-MCQA (2025) proposes question-answering about key information — [arXiv 2510.26190](https://arxiv.org/html/2510.26190v1). This is relevant: the clinically key information here is the drug name.
- **ITU standards:** ITU-T P.85 (1994) was designed for overall quality of synthetic speech but "has not been widely accepted". P.800 is the general MOS/ACR recommendation — [Sityaev et al., Interspeech 2006](https://www.isca-archive.org/interspeech_2006/sityaev06_interspeech.pdf)
- **Baseline footprint** of a competing port: arduino-espeak-ng on ESP32 uses 1.46 MB flash and 39.6 KB globals — [arduino-espeak-ng README](https://github.com/pschatzmann/arduino-espeak-ng)
- **This project's own known figures** (internal, from `CLAUDE.md`; not yet a measured benchmark):
  - eSpeak NG 1.52.0 is vendored.
  - eSpeak's `.bss` is about 90 KB in internal RAM.
  - Each synthesizing task needs about 40 KB of stack, in PSRAM.
  - `heap_min` was 39,828 B with SoftAP + BLE + speech active.

  Source: [project CLAUDE.md](/home/dev/projetos/alertalergo-v3-firmware/CLAUDE.md)
- **Ethics (Brazil):**
  - Research with human participants is submitted through Plataforma Brasil to the CEP/CONEP system — [gov.br: submeter na Plataforma Brasil](https://www.gov.br/pt-br/servicos/submeter-na-plataforma-brasil-de-projetos-de-pesquisa-envolvendo-seres-humanos-para-avaliacao-etica)
  - Res. CNS 510/2016 covers human and social sciences research with data obtained directly from participants. Art. 1 sole paragraph lists cases not registered or evaluated by CEP/CONEP. Waiving informed consent (TCLE) must be justified and requested from CEP. Items VII–X of Res. 466/2012 apply where relevant — [Res. 510/2016 (FURB copy)](https://www.furb.br/web/upl/arquivos/201702061757160.CNS_5102016.pdf)
  - Ofício Circular 17/2022/CONEP gives guidance on Art. 1 of Res. 510 (content not accessed) — [Res. 510 search context](https://www.gov.br/conselho-nacional-de-saude/pt-br/camaras-tecnicas-e-comissoes/conep/plataforma-brasil)

### Inferences
- **Systems benchmark set** (repeatable, scripted, from the CI artifact):
  - flash and partition use, `.dram0.bss`, `.iram0.text`, PSRAM use;
  - `heap_min` during synthesis with radios on;
  - real-time factor (synthesis time ÷ audio duration) for fixed pt-BR phrases;
  - time from request to first audio sample;
  - worst-case jitter on the display path, to show that speech never delays the screen (project rule 11);
  - comparison against arduino-espeak-ng on the same S3 and against desktop eSpeak NG output (bit-exact or phoneme-exact check via `espeak-ng -x`).
- **Perceptual set:**
  - pt-BR SUS lists;
  - a 20-drug reference list (the project already has `testing/manual/spk-reference-drugs.md`) scored as drug-name recognition accuracy, i.e. the clinically relevant metric;
  - MOS following ITU-T P.800 ACR;
  - speech-rate conditions (`speech_rate_wpm`);
  - playback through the device speaker at realistic ambient noise;
  - listeners: sighted vs blind or low-vision, ideally recruited via an institution for the blind.
- Any study with blind or low-vision participants, or with clinicians, should go through CEP. It is human-participant research and the population may be considered vulnerable. Plan months for approval. Res. 466/2012 is likely the governing frame for a health-device study, and 510/2016 for purely perceptual or HCI questionnaires. Confirm with the institution's CEP.
- SUS is ambiguous here (System Usability Scale vs Semantically Unpredictable Sentences). The System Usability Scale suits a usability study of the device. Semantically Unpredictable Sentences suit intelligibility testing.

### Gaps
- No source was found on TTS intelligibility methodology with blind listeners specifically, nor on any existing pt-BR SUS corpus.
- ITU-T P.800 text was not fetched. Neither was the content of Ofício Circular 17/2022, nor the exact Art. 1 exemption list of Res. 510.
- No published footprint or RTF benchmarks for eSpeak NG on ESP32-S3 were found beyond the Arduino README numbers.

## 4. GPL-3.0 implications and good practices

### Takeaway
eSpeak NG is GPL-3.0 (upstream repo license, project rule CON-SW-06 = GPL-3.0-or-later). Statically linking it into the firmware makes the whole distributed firmware a combined work under GPLv3. Distributing devices means supplying Corresponding Source and, for "User Products", the Installation Information. REUSE 3.3 plus SPDX headers and `REUSE.toml` for vendored trees is the recommended provenance practice. Apache-2.0 BSP code is GPLv3-compatible.

### Cited Findings
- **License facts:**
  - The upstream repo license is GPL-3.0 — [GitHub API](https://github.com/espeak-ng/espeak-ng)
  - Upstream also ships `COPYING.APACHE`, `COPYING.BSD2` and `COPYING.UCD` for bundled parts, which must be carried into the component's license inventory — [repo root](https://github.com/espeak-ng/espeak-ng)
- **REUSE 3.3** (2024-11-14):
  - Put each license text in `LICENSES/<SPDX-ID>.txt`, with no unused licenses.
  - Every file carries `SPDX-FileCopyrightText` and `SPDX-License-Identifier`.
  - Use `REUSE.toml` (`version = 1`, `[[annotations]]` with `path`, `precedence`) for bulk or vendored directories.
  - Use `.license` sidecars for binaries such as compiled `espeak-ng-data`.
  - DEP5 is deprecated.

  [REUSE spec 3.3](https://reuse.software/spec-3.3/)
- **The following GPL points rest on the license text and FAQ but could not be fetched this session** (gnu.org timed out) **[unverified this session — confirm at https://www.gnu.org/licenses/gpl-3.0.html and https://www.gnu.org/licenses/gpl-faq.html]**:
  - The FAQ (GPLStaticVsDynamic) says linking a GPL library, statically or dynamically, makes a combined work that must be released under the GPL as a whole.
  - GPLv3 §6 allows object code to be conveyed with the Corresponding Source on a medium, with a written offer valid ≥ 3 years, or by offering equivalent access from a network server.
  - GPLv3 §6 "Installation Information" (anti-tivoization) applies to "User Products", defined as consumer products, using a test of typical or common use of that class of product. Equipment sold only to hospitals may not be a "consumer product", but this is a legal-interpretation question.
  - The FSF license list states that Apache-2.0 is compatible with GPLv3 (not GPLv2).

### Inferences
- **Obligations when shipping devices:** ship (or offer) the exact source of each firmware image. That includes build scripts, `sdkconfig`, `dependencies.lock` and the compiled-data generation scripts needed to reproduce the binary. Tagged releases with CI artifacts plus a source tarball per release are the easiest way to satisfy this.
- **Secure boot and flash encryption:** if these are ever enabled (cf. SEC-NVS-01, eFuse key), GPLv3 Installation Information may require giving users of a "User Product" the means to install modified firmware. Evaluate this before burning eFuses.
- **The logo** (`assets/logo/`, not GPL per the project) is a separate non-code asset. Keep it clearly marked (`LicenseRef-…`) and outside the component.
- **Patient data:** GPL does not require publishing it, and the component should contain no such data anyway.
- **Recommended tooling:**
  - run `reuse lint` in CI;
  - add an SPDX SBOM per release;
  - record upstream commit or tag and local patches (a `PATCHES.md` or patch series) in the component;
  - list `COPYING.*` third-party notices in the registry package.

### Gaps
- The GPL FAQ and GPLv3 text were not retrieved in-session.
- Whether a hospital-only medical device is a "User Product" needs legal advice; no source was consulted.
- `reuse lint` was not confirmed from the spec page (it lives in the REUSE tool docs).

## 5. Possible upstream contributions

### Takeaway
The highest-value, most-acceptable upstream contributions are:
- the multibyte `iswalpha` fix for ESP32 toolchains (#1611);
- pt-BR exception-list entries for drug names, with `test_phon` tests, coordinated with the active pt maintainer;
- reproducible bug reports for any crash or overflow found on the MCU.

Footprint-reduction build options are possible but need maintainer agreement.

### Cited Findings
- #1611: `iswalpha()` is broken for multibyte characters on the ESP32 toolchain, and `ucd_isalpha()` works. The issue is open — [espeak-ng#1611](https://github.com/espeak-ng/espeak-ng/issues/1611)
- Language contributions:
  - edit `dictsource/<lang>_rules` / `_list`;
  - test with `test_phon`;
  - reviewed by the language maintainer;
  - PRs must not be trivial-only.

  [contributing.md](https://github.com/espeak-ng/espeak-ng/blob/master/docs/contributing.md), [AGENTS.md](https://github.com/espeak-ng/espeak-ng/blob/master/AGENTS.md)
- pt was updated by Fabio Lima for 1.53.0. Blind NVDA users actively review pt-BR changes, e.g. #2531 on the /r/ regression, fixed with audio samples — [ChangeLog](https://github.com/espeak-ng/espeak-ng/blob/master/ChangeLog.md), [#2531](https://github.com/espeak-ng/espeak-ng/issues/2531)
- Upstream is actively merging fuzzing-driven memory-safety fixes (1.53.0), and a global buffer overflow in ReadClause was opened on 2026-11-21 — [ChangeLog](https://github.com/espeak-ng/espeak-ng/blob/master/ChangeLog.md), [#2647](https://github.com/espeak-ng/espeak-ng/issues/2647)

### Inferences
- **Drug names:** many INN-derived names (e.g. "sulfametoxazol", "amoxicilina") follow regular pt spelling rules. Add exceptions only where eSpeak mispronounces them, and prove each case with `espeak-ng -xq -v pt-br`. A curated pt-BR medical lexicon with tests would be a distinct, citable contribution, and could also be a JOSS or SBCAS talking point.
- Run upstream's test suite (`ctest`) on the host build of the vendored version, so that local patches are proven not to regress phoneme output before proposing them.
- Offer the blind-user listening results back to the pt maintainers. This aligns with the community's existing review practice in #2531.

### Gaps
- No check of whether drug names are already handled in `pt_list`.
- No upstream maintainer statement on accepting MCU build options. Ask on the groups.io list or in a discussion before investing.
