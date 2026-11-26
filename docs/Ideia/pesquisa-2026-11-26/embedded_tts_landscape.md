# Embedded / MCU text-to-speech landscape (non-eSpeak) and academic literature, focus pt-BR and accessibility (as of 2026-11-26)

Legend: **[PR]** = peer-reviewed; **[GREY]** = grey literature (README, model card, forum, blog, preprint, thesis/TCC); **[UNVERIFIED]** = seen only in a search snippet, not read in full.

## Q1. Which TTS engines run on MCUs, with languages (pt-BR?), footprint, license, quality?

### Takeaway
pt-BR offline TTS on an ESP32-class MCU is **no longer an empty niche**. The most important finding is **vtts** (Apache-2.0, 2026). It is a distilled VITS/Piper-derived neural TTS that runs on the ESP32-S3 (8 MB PSRAM) and the ESP32-P4, ships a **Brazilian Portuguese** voice (`nu-pt`, bilingual with English), and runs its text front-end on the device. The other non-eSpeak options cover no Portuguese. Espressif esp-tts is Chinese-only. The PicoTTS port covers EN/DE/FR/IT/ES. SAM is English, with a Spanish fork. Flite is essentially English. sanoTTS is English. eSpeak NG remains the only **rule-based/formant, 100+ language, GPL** engine with pt-BR; its only MCU port found (pschatzmann's) is Arduino-oriented and not a native ESP-IDF component.

### Cited Findings
**Espressif esp-tts (esp-sr)** [GREY, vendor docs]
- The official model "currently only supports Chinese", with UTF-8 input. It is concatenative and outputs mono 16-bit audio at 16 kHz. — [esp-sr TTS docs (S3)](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/speech_synthesis/readme.html); [zh_CN docs](https://docs.espressif.com/projects/esp-sr/zh_CN/latest/esp32/speech_synthesis/readme.html)

**PicoTTS (SVOX) ESP-IDF component, by jmattsson / DiUS** [GREY]
- An ESP-IDF component on the Espressif registry. The readme says Espressif offers Chinese TTS but "there has been no support for other languages". The component covers English (UK and US), German, French, Italian and Spanish, **not Portuguese**. — [Component registry](https://components.espressif.com/components/jmattsson/picotts/versions/1.1.4/readme?language=en); [DiUS/esp-picotts](https://github.com/DiUS/esp-picotts)
- Resource loading was changed to read directly from memory-mapped flash, which cut RAM from 2.5 MB to 1.1 MB. Real-time generation is possible on an otherwise idle ESP32-S3. The authors recommend an S3 with enough PSRAM and flash. — [Component registry](https://components.espressif.com/components/jmattsson/picotts/versions/1.1.4/readme?language=en); [esp32.com forum thread](https://esp32.com/viewtopic.php?p=139907)
- Another port exists by lllucius. — [lllucius/esp32_picotts](https://github.com/lllucius/esp32_picotts)

**vtts (tuanpmt), neural, includes pt-BR** [GREY: model card and repo]
- Architecture: a ~24M-parameter VITS teacher per voice, distilled into a student made of a duration model, an acoustic model with pitch and energy predictors, and a Vocos-style ConvNeXt/iSTFT decoder. The student is int8-quantized and outputs 22.05 kHz. — [HF model card](https://huggingface.co/tuanpm/vtts)
- **Brazilian Portuguese voice** `nu-pt` ("female, about 40, Brazilian Portuguese"), bilingual pt+en.
  - M model: 2.6 MB, RTF 0.57 on ESP32-S3 and 0.28 on ESP32-P4.
  - S model: 1.2 MB, RTF 0.32 on S3 and 0.19 on P4.
  - The ESP32-S3 needs 8 MB PSRAM. — [HF model card](https://huggingface.co/tuanpm/vtts)
- The front-end is rule-based, implemented in Python for training and C for the device with identical output. For Portuguese it applies spelling rules covering stress, nasal vowels and the two r sounds. Normalization, G2P, acoustic model and vocoder all run on the MCU with no network. — [HF model card](https://huggingface.co/tuanpm/vtts)
- Self-reported evaluation on 50 out-of-domain sentences:
  - Portuguese CER is 0.008, measured by transcribing with Whisper large-v3.
  - UTMOS is 2.36 for `nu-pt` M, which is low naturalness.
  - Neither is a human listening test. — [HF model card](https://huggingface.co/tuanpm/vtts)
- Licensing: code and models (v0.4.0+) are Apache-2.0. Piper/VITS-derived parts are MIT and CMUdict is BSD.
- Supported chips: ESP32-P4, ESP32-S3 and ESP32-S31.
- It requires **ESP-IDF v6.1.1**, builds through a script, and is not packaged as an ESP-IDF component.
- Repo stats: 31 stars, latest release v0.13.0. Dates were not shown on the page.
- The page asks that the audio be labelled as AI-generated. — [tuanpmt/vtts](https://github.com/tuanpmt/vtts)

**sanoTTS, neural, English only** [GREY: arXiv preprint, not peer-reviewed]
- arXiv:2608.21378, submitted 14 Jul 2026, by Ashish Thapa (Ampixa Labs).
- It is a phoneme-to-waveform model running on the ESP32-S3 at 0.22× real time and on the FPU-less ESP32-C3 at 5.72×. It has 567,008 parameters, stored as two int8 blobs totalling 679,832 bytes.
- It is distilled from Piper/VITS en_US voices.
- On unseen text it scores 2.54 SCOREQ and 2.80 UTMOS, against 4.68 and 4.42 for the teacher.
- It starts from phoneme IDs; whether a phonemizer runs on the device is not stated. — [arXiv abs](https://arxiv.org/abs/2608.21378); [PDF](https://arxiv.org/pdf/2608.21378)
- A gitee mirror exists. — [gitee sanoTTS](https://gitee.com/xia-guard/sanoTTS)
- A related hobby project, RVTTS (offline neural TTS for RISC-V MCUs), is [UNVERIFIED]. — [Hackaday.io](https://hackaday.io/project/206668-rvtts-offline-neural-tts-for-risc-v-mcus)

**SAM (Software Automatic Mouth) / ESP8266SAM** [GREY]
- A reverse-engineered port of the 1982 C64/Apple SAM. It runs fully on the device with ESP8266Audio, outputting through a DAC or direct-drive speaker, on ESP8266 and ESP32. The author calls the quality modest and recommends MP3 for a fixed vocabulary. It is English-only. — [earlephilhower/ESP8266SAM](https://github.com/earlephilhower/ESP8266SAM); [Wikipedia: SAM](https://en.wikipedia.org/wiki/Software_Automatic_Mouth)
- A **Spanish** fork exists for ESP8266, ESP32 and RP2040. No Portuguese port was found. — [ESP8266SAM_ES](https://github.com/pablomarquez76/ESP8266SAM_ES/blob/master/README.md)
- Other ports: arduino-SAM ([link](https://pschatzmann.github.io/arduino-SAM/)) and STM32SAM ([link](https://github.com/Bakisha/STM32SAM)).

**Flite (CMU)** [GREY]
- From an old README: core code about 60 KB, lexicon about 600 KB, diphone voice about 1.8 MB, runtime under 1 MB. Memory depends heavily on the chosen voice; cmu_us_kal is the smallest. — [festvox/flite](https://github.com/festvox/flite); [Arduino FLITE](https://pschatzmann.github.io/arduino-flite/doc/html/index.html)
- An ESP32 demo runs synthesis locally. No measured footprint was found for it. — [alkhimey/esp32-flite](https://www.github.com/alkhimey/esp32-flite)
- No Portuguese Flite voice was found in these sources.

**eSpeak NG on MCU (for comparison)** [GREY]
- pschatzmann's arduino-espeak-ng is an Arduino library that needs the "Huge APP" partition on ESP32. Its minimal ESP32 example uses 1,457,411 B of flash (46% of 3 MB) and 39,616 B of globals. Large buffers go on the heap and PSRAM is used automatically.
- Loading data from SD "uses excessive RAM" and only works with PSRAM, so PROGMEM is recommended.
- The license is GPL-3.0.
- The page does not mention ESP-IDF, and the README does not list which languages are bundled. — [pschatzmann/arduino-espeak-ng](https://github.com/pschatzmann/arduino-espeak-ng); [docs](https://pschatzmann.github.io/arduino-espeak-ng)
- Searching the Espressif Component Registry and GitHub found **no native ESP-IDF eSpeak NG component**. This is a negative search result, not proof of absence. — [search context: component registry results](https://components.espressif.com/components/jmattsson/picotts)
- Upstream eSpeak NG covers more than 100 languages and accents, including Portuguese (Brazil) and (Portugal). Voice quality varies greatly by language. — [espeak-ng](https://github.com/espeak-ng/espeak-ng/); [Wikipedia: eSpeak](https://en.wikipedia.org/wiki/ESpeak)

### Inferences
- Quality and resource trade-off, by engine family:
  - SAM is tiny, intelligible only in English, and robotic.
  - Formant and rule-based engines (eSpeak) are a few hundred KB to about 1.5 MB, cover many languages, and sound robotic but are robust and fast.
  - Diphone and unit-selection engines (Pico, Flite) are 1–2+ MB, more natural, and limited in languages.
  - Distilled neural engines (vtts, sanoTTS) are 0.7–2.6 MB of weights and need PSRAM. They are more natural, but their accuracy depends on a custom per-language front-end.
- vtts is the direct competitor for "offline pt-BR on ESP32-S3". It differs from an eSpeak NG ESP-IDF port in several ways:
  - License: Apache-2.0 vs GPL-3.0.
  - Platform: it requires ESP-IDF 6.1.1 and is not a component.
  - Voices: one pt voice, bilingual with English.
  - Front-end: a young pt G2P, which is untested for drug names and number normalization.
  - Validation: no human or blind-user listening test.
  - Tunability: eSpeak offers rate and pitch control, phoneme-level correction through dictionaries, and very high-speed intelligibility, which blind screen-reader users value.
- "Novelty" for an eSpeak NG ESP-IDF port must therefore be framed narrowly, as one or more of the following:
  - the first native ESP-IDF eSpeak NG component;
  - pt-BR validated for a clinical/assistive vocabulary;
  - co-existence with BLE, Wi-Fi and display in tight internal RAM;
  - documented footprint.
  It cannot be framed as "the first offline pt-BR TTS on ESP32".

### Gaps
- **Talkie (LPC, TI-99/Speak & Spell vocabularies)**: not covered by the searches. From prior knowledge [UNVERIFIED] it plays pre-encoded LPC word lists, mostly English, rather than doing TTS. Verify before citing.
- **MBROLA**: Brazilian voices br1–br4 exist and the voices carry their own (often non-commercial) licenses, per prior knowledge [UNVERIFIED]. No MCU port of MBROLA was found. Verify the voice licenses at github.com/numediart/MBROLA-voices before citing.
- **Edge Impulse / TFLite Micro TTS**: no product or example found. Edge Impulse appears focused on keyword spotting, not synthesis [UNVERIFIED negative].
- **Piper on ESP32**: no direct port found. Piper-derived distillations (vtts, sanoTTS) are the MCU route.
- The arduino-espeak-ng language set and last-update date were not visible on the page.
- vtts release dates and actual RAM/PSRAM consumption were not stated.

## Q2. Academic papers on TTS on microcontrollers / low-resource embedded devices; any with pt-BR; intelligibility evaluations of eSpeak in Portuguese?

### Takeaway
Peer-reviewed work on TTS for **microcontrollers** is old and thin: ICASSP 2004 on an 8051 core, and IEEE work on embedded unit selection for mobiles. The 2025–2026 MCU-neural work exists only as preprints and model cards (sanoTTS, vtts). **No peer-reviewed paper on TTS on an MCU in pt-BR was found.** No controlled, published intelligibility study (MOS, word recognition rate, SUS) of **eSpeak in Brazilian Portuguese** was found. Evidence on eSpeak pt quality is anecdotal.

### Cited Findings
- [PR] ICASSP 2004, "Embedded speech recognition system on 8-bit MCU core": an optimized embedded TTS and recognition system on an 8051-compatible core with about 1 KB of RAM and CVSD speech coding. [UNVERIFIED: abstract snippet only] — [ResearchGate](https://www.researchgate.net/publication/4088068_Embedded_speech_recognition_system_on_8-bit_MCU_core)
- [PR] "Embedded unit selection text-to-speech synthesis for mobile devices" (IEEE). It covers database reduction, acoustic inventory compression and runtime load minimization, with objective and subjective assessments. [UNVERIFIED: abstract snippet] — [IEEE Xplore 5174430](https://ieeexplore.ieee.org/document/5174430/)
- [GREY/uncertain venue] "Synthesized Speech using a small Microcontroller" (Bhanwrela, Khamele, ~2015) — [Semantic Scholar](https://www.semanticscholar.org/paper/Synthesized-Speech-using-a-small-Microcontroller-Bhanwrela-Khamele/c458bee3b328dea0bfc367b632bdc8df4e9aa0bf). "ARM based Text-To-Speech Synthesis" (cited as IEEE ICSIP, year unknown, venue unverified) — [Academia.edu](https://www.academia.edu/29721448/ARM_based_Text_To_Speech_Synthesis)
- [GREY: preprint] sanoTTS (2026), an MCU neural TTS evaluated with SCOREQ and UTMOS, without a controlled MOS study. Its related work does not mention SAM, eSpeak, Flite, PicoTTS or vtts. — [arXiv 2608.21378](https://arxiv.org/abs/2608.21378)
- [PR per snippet] "Compact Neural TTS Voices for Accessibility" (arXiv 2501.17332, reported as accepted at ICASSP 2025). It targets low-power devices with about 15 ms latency, not MCUs. [UNVERIFIED: snippet] — [arXiv 2501.17332](https://arxiv.org/abs/2501.17332v1); [Apple ML research](https://pr-mlr-shield-prod.apple.com/research/compact-neural-tts)
- [PR: SSW 2023 per snippet] "Lightweight End-to-end TTS for low resource on-device applications", aimed at on-device use, not MCUs. — [arXiv 2505.07701](https://arxiv.org/abs/2505.07701)
- [GREY: thesis] A TU Delft master's thesis on a hardware accelerator for real-time neural TTS. — [TU Delft repository](https://repository.tudelft.nl/record/uuid:b8d7a5f2-de3f-4664-a2a6-398dc36b5ab5)
- [GREY: preprint, 2020] TTS-Portuguese Corpus, a pt-BR dataset for neural TTS (server-class, not embedded). — [arXiv 2005.05144](https://arxiv.org/abs/2005.05144v2)
- [PR: STIL/SBC 2024] An online evaluation method using eye-tracking for pt-BR speech synthesis. [UNVERIFIED: snippet] — [ACL Anthology 2024.stil-1.18](https://aclanthology.org/2024.stil-1.18.pdf)
- [PR: STIL 2026] States that neural TTS models underperform for pt-BR. [UNVERIFIED: snippet] — [ACL Anthology 2026.stil-1.29](https://aclanthology.org/2026.stil-1.29.pdf)
- [PR: SBC STIL] AI voice cloning for pt-BR, evaluated for naturalness and intelligibility by a 4-person panel. eSpeak was not included, per the snippet. — [SOL/SBC](https://sol.sbc.org.br/index.php/stil/article/download/44625/44388/)
- [GREY: UFPB monograph, 2019] "Avaliação de sintetizadores de voz aplicados ..." is directly on-topic by title. The PDF could not be text-extracted, so whether eSpeak was among the evaluated voices is **unknown**. — [UFPB repository PDF](https://repositorio.ufpb.br/jspui/bitstream/123456789/14646/1/SFSN07062019.pdf)
- [GREY: UFRJ undergraduate monograph] A Portuguese synthesis system with word- and sentence-level articulation intelligibility tests. Intelligibility was "more than sufficient" for dialogue. It did not evaluate eSpeak. — [UFRJ Poli monograph](http://repositorio.poli.ufrj.br/monografias/monopoli10003224.pdf)
- [PR per snippet] "Avaliação de sintetizadores de voz para leitura em livros digitais" compared DOSVOX 4.3, JAWS 9.0 and Virtual Vision 2.0. [UNVERIFIED] — [ResearchGate](https://www.researchgate.net/publication/304469957_Avaliacao_de_sintetizadores_de_voz_para_leitura_em_livros_digitais)
- Anecdotal [GREY]: a 2008 Brazilian Linux comment claims eSpeak's Portuguese was weak because the developer did not speak it. — [br-linux.org](https://br-linux.org/wparchive/2008/sintetizador-de-voz-lancamento-do-gespeak-016.php). An Orca-list thread also discusses Portuguese synthesizers on GNU/Linux. — [orca-list 2017](https://lists.gnome.org/archives/orca-list/2017-September/msg00057.html)

### Inferences
- A small, well-documented intelligibility study would fill a real, citable gap. Suitable measures are word or drug-name recognition rate with SUS-style semantically unpredictable sentences, ideally with blind and low-vision listeners. It would compare eSpeak NG pt-BR on the ESP32-S3 against at least one alternative, such as vtts `nu-pt` or a recorded human voice.
- vtts's Whisper-CER metric shows that ASR-based intelligibility proxies are becoming the norm in grey literature. A human-listener evaluation would set a project apart.

### Gaps
- Google Scholar, IEEE Xplore and SBC OpenLib were not queried directly with full-text access. Coverage is limited to search-engine snippets.
- The UFPB 2019 monograph's content (whether it covers eSpeak, its method and results) is unread. The PDF is cached locally but text extraction was unavailable (no pdftotext).
- SBrT proceedings: one SBrT library PDF appeared (biblioteca.sbrt.org.br/articlefile/4464.pdf) but was not read.

## Q3. Literature on assistive devices for blind/low-vision users using embedded TTS (health/medical alerts), especially in Brazil

### Takeaway
Brazilian work on ESP32 and voice for the visually impaired consists mostly of prototypes in grey literature: canes, bus-stop aids and obstacle detectors. These typically use **cloud TTS or a phone app**, not on-MCU synthesis. No paper was found on a **health/medication-allergy alert device with offline embedded pt-BR TTS**.

### Cited Findings
- [GREY: Revista E&S, executive summary] A smart cane with ESP32-CAM that sends images to a generative AI. A phone app converts the AI's text replies to audio, so the TTS is not on the MCU. — [Revista E&S](https://revistaes.com.br/resumo-executivo/bengala-inteligente-com-esp32-cam-e-ia-para-acessibilidade-visual)
- [GREY] A low-cost ESP32 + Wi-Fi bus-stop aid with audio feedback. — [Núcleo do Conhecimento](https://www.nucleodoconhecimento.com.br/engenharia-eletronica/sistema-de-auxilio)
- [GREY] ORION, an embedded computer-vision and speech-synthesis wearable for obstacles (YOLO, MiDaS). It is not clearly MCU-based. — [ResearchGate](https://www.researchgate.net/publication/400020422_ORION_DISPOSITIVO_EMBARCADO_DE_VISAO_COMPUTACIONAL_E_SINTESE_DE_VOZ_PARA_IDENTIFICACAO_DE_OBSTACULOS_-_APLICANDO_PROCESSAMENTO_DE_IMAGENS_PARA_AUMENTAR_A_ACESSIBILIDADE_E_MOBILIDADE_SEGURA_DE_PESSOAS_)
- [GREY] An ESP32 obstacle assistant (HC-SR04 sensor, buzzer only), tested only in a simulator. — [Medium](https://medium.com/@patrick.moraes/tecnologia-para-a-inclus%C3%A3o-desenvolvimento-de-um-dispositivo-assistivo-para-pessoas-com-54e9b6fd150f)
- [GREY] XIAO ESP32S3 reading aid that uses OCR and **Google TTS (cloud)**. — [Hackster.io](https://www.hackster.io/mmbharathram/reading-aid-for-the-visually-impaired-using-xiao-esp32s3-8c5a81)
- [GREY: SEGET] Evaluation of an electronic cane as assistive technology. — [SEGET PDF](https://www.aedb.br/seget/arquivos/artigos12/6616490.pdf)
- Brazilian TTS context: DOSVOX (UFRJ/NCE) is described as the first pt-BR synthesizer, built from concatenated recorded syllables, and remains the most-used Portuguese voice among blind users despite technical limits. [Partly UNVERIFIED: snippet] — [ResearchGate: Do Braille ao Dosvox](https://www.researchgate.net/publication/257985278_Do_Braille_ao_Dosvox_-_Diferencas_nas_Vidas_dos_Cegos_Brasileiros); [DOSVOX usability (UFRJ)](https://intervox.nce.ufrj.br/~antonio2/mec_aee/usabilidade-dosvox.pdf)
- Users' view of eSpeak as "a bit robotic" but agile and intelligible at high speeds is reported in a Brazilian accessibility manual and app list [GREY]. — [Portal da Indústria manual](https://static.portaldaindustria.com.br/media/filer_public/2e/45/2e45a6b1-e6dd-439e-ba28-6ca1f4d59e65/manual_do_aluno_do_curso_de_digitavox_e_atualizacao_de_dosvox_virtual_vision_10_nvda_2016_e_jaws_17.pdf); [Acessibilidade em Foco](https://www.acessibilidadeemfoco.com/aplicativos/android/sintetizadores.html)

### Inferences
- A medical alert device for blind and low-vision patients, such as allergy wristbands, that speaks pt-BR **fully offline on an MCU** appears unreported in the literature found. It could be positioned as an applied contribution, for example a short paper at SBC venues (STIL, SBCAS, WebMedia/IHC accessibility tracks) or SBrT.
- Cloud TTS dominates hobby and student assistive prototypes. Offline operation, which needs no connectivity and keeps patient data on the device, is a defensible differentiator.

### Gaps
- PubMed, SciELO and RESNA/ASSETS were not searched for talking medical devices, such as talking glucometers and pill bottles. These are a known commercial category, but no citations were gathered here.
- No search was made for regulatory or clinical-alarm literature (IEC 60601-1-8) on voice alarms.

## Q4. Is there a known gap: offline pt-BR TTS on a cheap MCU?

### Takeaway
**Partially closed as of 2026.** vtts (Apache-2.0) already provides an offline pt-BR neural voice on the ESP32-S3 and P4, and pschatzmann's Arduino eSpeak NG presumably can include pt-BR data. Several gaps remain open:
- a **native, maintained ESP-IDF eSpeak NG component**, with pt-BR validated;
- a documented footprint under real co-existence with BLE, Wi-Fi and display;
- **any peer-reviewed intelligibility evaluation** of embedded pt-BR TTS, eSpeak or neural, especially with blind or low-vision listeners and domain vocabulary such as drug names;
- an MCU without PSRAM: vtts needs 8 MB PSRAM on the S3.

### Cited Findings
- vtts offers a pt-BR voice on ESP32-S3 (8 MB PSRAM) and P4 with an on-device front-end. Its evaluation is ASR-CER and UTMOS only. — [HF model card](https://huggingface.co/tuanpm/vtts); [GitHub](https://github.com/tuanpmt/vtts)
- Espressif's own TTS is Chinese-only. — [esp-sr docs](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/speech_synthesis/readme.html)
- The PicoTTS ESP-IDF component has no Portuguese. — [Component registry](https://components.espressif.com/components/jmattsson/picotts/versions/1.1.4/readme?language=en)
- The eSpeak NG MCU port found is Arduino-oriented. Native ESP-IDF support is not stated. — [arduino-espeak-ng](https://github.com/pschatzmann/arduino-espeak-ng)
- sanoTTS (MCU neural) is English only. — [arXiv 2608.21378](https://arxiv.org/abs/2608.21378)
- A local research-adjacent note: the AlertAlergo V3 project already vendors eSpeak NG 1.52.0 in ESP-IDF on the ESP32-S3. Per the project's own notes, it runs alongside SoftAP, BLE and LCD, with min heap 39,828 B and the eSpeak `.bss` (~90 KB) in internal RAM. — project `CLAUDE.md` (internal, not a public source)

### Inferences
- A claim of novelty that holds up: "first open, native ESP-IDF component of eSpeak NG (GPL-3.0) with pt-BR, integrated in a safety-relevant assistive device. It co-exists with BLE scanning, Wi-Fi and display on an ESP32-S3, with a documented memory budget, and has a pt-BR clinical-vocabulary evaluation (if one is done)."
- A claim to avoid: "first offline pt-BR TTS on ESP32" or "no pt-BR TTS exists for MCUs". vtts refutes both.
- Value relative to vtts:
  - eSpeak is deterministic and rule-based.
  - Drug names can be fixed in a dictionary, with no retraining.
  - It handles arbitrary rate (useful for experienced screen-reader users) and many languages.
  - It has a longer track record among blind users through NVDA and Orca.
  - On the downside, its GPL license constrains closed-source adopters, and its naturalness is lower.

### Gaps
- Whether anyone published an ESP-IDF eSpeak NG port only on GitHub (with no registry entry) is not fully excluded. A direct GitHub code search ("espeak" + "idf_component_register") was not run.
- No measured head-to-head comparison of eSpeak NG pt-BR and vtts `nu-pt` exists, in intelligibility, latency, flash or RAM.
