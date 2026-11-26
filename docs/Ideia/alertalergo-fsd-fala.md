# Trechos do FSD do AlertAlergo V3 sobre a fala

Extraídos de `alertalergo-v3-firmware` `docs/Functionality/FSD.md` no commit `19787f2` (FSD 1.10.x), sem
alteração. São **evidência** para o `/define` deste repositório, não requisitos dele: cada item só vale aqui se a
FSD da pesquisa o absorver.

## Restrições e não funcionais (linhas 236–237, 265, 281–286)

| CON-SW-03 | Must | A pilha BLE é o **NimBLE**, nos papéis *observer* e *central*. O Bluedroid não é ligado. | [user] Q2 |
| CON-SW-04 | Must | A biblioteca gráfica é o **LVGL 9**, com framebuffer de cor **I1 (1 bpp)**. | [user] Q8 |
| CON-SW-05 | Must | A síntese de fala é o **eSpeak NG** com a voz formante pt-BR. | [user] Q15/Q4 |
| CON-SW-06 | Must | O firmware é distribuído sob **GPL-3.0-or-later**. O código-fonte completo correspondente a cada release está disponível a quem recebe o aparelho. | [user] Q15 |
| NFR-SW-02 | Must | Os dados de idioma do eSpeak NG (pt / pt_br, ≈ 735 KB) ficam na partição `espeak` e não no app. | [user] seed 04 §5 |
| CON-SW-03 | `sdkconfig` de release | NimBLE ligado; Bluedroid desligado | Bluedroid | host (CI) |
| CON-SW-04 | `sdkconfig` / lock | LVGL 9.x; cor 1 bpp | LVGL 8 | host (CI) |
| CON-SW-05 | SBOM | eSpeak NG 1.52.0 | outro motor | host (CI) |
| CON-SW-06 | release | `LICENSE` GPL-3.0-or-later e FR-3P-01 | release sem fonte | manual |
| CON-SW-07 | build de teste, `status` | núcleo e prioridade das tarefas BLE e fala conforme a restrição | fala no núcleo 0 | target |
| CON-SW-08 | `partitions.csv` × tabela; `esptool read-flash` da tabela no DUT | idênticos | divergência | host (CI) · target |
| NFR-SW-01 | build com app > 0x400000 (teste do *script*) | build falha | build verde | host (CI) |
| NFR-SW-02 | ELF de release | sem os dados `phondata`/dicionário (tamanho e símbolos) | dados no app | host (CI) |

## §3.3 Fase 3 — Fala


- **Escopo:** §18 (fala), §29 eSpeak NG.
- **Entregas:**
  - a fala dos eventos de §11;
  - os requisitos de latência e CPU;
  - o teste manual de inteligibilidade.
- **Saída:** os requisitos de §18 verdes; as jornadas J1–J7 continuam verdes
  com a fala ligada.
- **Depende de:** Fase 2.


## OD-19

| OD-19 | Inteligibilidade da fala para o público com cegueira ou baixa visão: velocidade, pausas e tom do eSpeak (hoje padrão: 175 palavras/min, sem pausas extras) e, se a escuta mostrar que não basta, trechos gravados de fármacos no aparelho. Kit de escuta A–D com os 20 fármacos entregue em 2026-11-11; a fala continua sintetizada localmente (FR-SPK-01) | FR-SPK-01/07, NFR-SPK-01 | Escolher a configuração (provável C: 130 palavras/min com pausas) e aprovar FR-SPK-08 com ela como parâmetro `(assumed)`; avaliação de NFR-SPK-01 no aparelho |

## 18. Áudio e fala

### 18.1 Saída de áudio

| ID | Pri | Requisito | Fonte |
|---|---|---|---|
| FR-AUD-01 | Must | O áudio sai pelo ES8311 via I²S (§2.2.2), com o amplificador habilitado pelo GPIO46 só enquanto há reprodução. | [vendor] · [user] revisão 2026-11-07 |
| FR-AUD-02 | Must | Os tons `alert`, `beep`, `low_battery`, `success` e `error` são distintos entre si em frequência ou padrão e duram ≤ 1 s cada. | [user] Q4 · revisão 2026-11-07 |
| FR-AUD-03 | Must | O volume (0–100, §31) é aplicado a tons e fala. | [code] |
| FR-AUD-04 | Must | Cada reprodução emite `AUDIO play clip=<id> reason=<evento> vol=<v>` no início e `AUDIO done clip=<id> ms=<duração>` no fim. | [user] Q14 · revisão 2026-11-08 (`vol`, `ms`: os contratos de FR-AUD-02/03 já os liam) |
| NFR-AUD-01 | Must | Com volume 70, o tom `alert` é audível a 1 m num ambiente de enfermaria, segundo 2 avaliadores. | [user] Q4 (manual) |

### 18.2 Fala

| ID | Pri | Requisito | Fonte |
|---|---|---|---|
| FR-SPK-01 | Must | A fala é sintetizada no aparelho pelo eSpeak NG, com a voz pt-BR e os textos de §11.2. | [user] Q4/Q15 |
| FR-SPK-02 | Must | Uma fala emite `SPEECH start id=<n> chars=<c>` ao começar o áudio e `SPEECH done id=<n> ms=<t>`, `SPEECH abort id=<n>` ou `SPEECH fail id=<n> err=<e>` ao terminar. `chars` é o número de caracteres (code points) do texto falado. | [user] seed 04 §6 · revisão 2026-11-08 (`chars`) |
| FR-SPK-03 | Must | A síntese nunca dispara o watchdog de tarefa. | [user] seed 04 §4 |
| FR-SPK-04 | Must | Para o mesmo texto e os mesmos parâmetros, o PCM gerado é idêntico (hash) entre execuções, no host e no alvo. | [user] seed 04 §6 |
| FR-SPK-05 | Must | Uma síntese que não produz áudio em 3 s é abortada com `SPEECH fail err=timeout`. | [user] revisão 2026-11-07 |
| FR-SPK-06 | Must | Durante a fala, a heap interna livre fica ≥ 32 KB. | [user] revisão 2026-11-07 (assumed) — medir no commissioning |
| FR-SPK-07 | Should | Um dicionário de exceções `pt_extra` corrige a pronúncia dos fármacos da lista de referência clínica. | [user] seed 04 §4 |
| NFR-SPK-01 | Should | Numa lista de 20 fármacos de referência, cada um de 2 avaliadores da enfermagem identifica corretamente ≥ 18. | [user] seed 04 §6 · revisão 2026-11-07 |

### 18.3 Contratos

| ID | Pré-condição · estímulo | Observação esperada | Não pode acontecer | Tier |
|---|---|---|---|---|
| FR-AUD-01 | sem reprodução / durante | GPIO46 baixo / alto (marcador `AUDIO pa=`) | PA ligado em repouso | target |
| FR-AUD-02 | cada tom | duração em `AUDIO done` ≤ 1 s; espectros distintos (gravação manual) | tons iguais | target · manual |
| FR-AUD-03 | volume 0 | `AUDIO play` com `vol=0`; silêncio audível | som com volume 0 | target · manual |
| FR-AUD-04 | cada evento | par start/done | done sem start | target |
| NFR-AUD-01 | enfermaria, 1 m | 2 «audível» | — | manual |
| FR-SPK-01 | `patient_new` | `SPEECH start chars=` = tamanho do texto esperado | texto diferente | target |
| FR-SPK-02 | fala completa, interrompida, falha | os 3 marcadores finais | fala sem marcador final | target |
| FR-SPK-03 | 50 falas seguidas | nenhum `task_wdt` | reinício | target |
| FR-SPK-04 | 10 textos fixos | hashes iguais entre 3 execuções e iguais aos de referência | divergência | host |
| FR-SPK-05 | `speech fault stall` | `SPEECH fail err=timeout` em 3 s ±0,5 s | travamento | target |
| FR-SPK-06 | fala mais longa possível | `SPEECH done heap_min=` ≥ 32768 | — | target |
| FR-SPK-07 | lista de referência | WAVs aprovados por escuta humana | — | manual |
| NFR-SPK-01 | 20 fármacos | ≥ 18 corretos por avaliador | — | manual |

---


## FR-PLT-06 (partição espeak)

| FR-PLT-06 | Must | A partição `espeak` começa com um cabeçalho com versão de formato, tamanho e CRC32 dos dados. Com o cabeçalho ou o CRC inválido, a fala fica desligada, o app emite `SPEECH ready=0 reason=<bad_magic/bad_version/bad_crc>` e os tons continuam. O CRC é conferido a cada boot, sem atrasar o splash (FR-DSP-03). | [derived] NFR-SW-02 · regra 11 · [user] revisão 2026-11-07 |
| FR-PLT-06 | partição `espeak` com CRC corrompido | `SPEECH ready=0 reason=bad_crc`; tons presentes | reinício; fala tentada | target |

## 29. Componentes de terceiros

### 29.1 Inventário

| Componente | Origem | Versão | Licença | Usado em |
|---|---|---|---|---|
| ESP-IDF (FreeRTOS, NVS, esp_wifi, esp_http_server, esp_http_client, esp-tls, bootloader) | Espressif | v5.5.5 (CON-SW-01) | Apache-2.0 | todo o firmware |
| NimBLE (dentro do ESP-IDF) | Apache Mynewt | a do ESP-IDF v5.5.5 | Apache-2.0 | §15, §16 |
| LVGL | Component Manager | 9.x, travada em `dependencies.lock` | MIT | §12, §17 |
| `esp_codec_dev` | Component Manager | travada em `dependencies.lock` | Apache-2.0 | §18 |
| BSP Waveshare (`port_bsp`, display ST7305, ADC) | `reference/ESP32-S3-RLCD-4.2/examples/factory/components/port_bsp/` | commit registrado em `components/<nome>/` | Apache-2.0 | §17, §21 |
| eSpeak NG | upstream 1.52.0, porte próprio como componente ESP-IDF | 1.52.0 | GPL-3.0-or-later | §18.2 |
| Montserrat (fonte) | Julieta Ulanovsky et al., a cópia do LVGL; subconjunto 0x20–0xFF gerado com `lv_font_conv` | a do LVGL travado | OFL-1.1 | §12 (FR-UI-11) |
| Ícones FontAwesome Free (bateria, alto-falante) | os símbolos `LV_SYMBOL_*` do LVGL | a do LVGL travado | ícones CC-BY-4.0, fonte OFL-1.1 | §12 |

### 29.2 Requisitos

| ID | Pri | Requisito | Fonte |
|---|---|---|---|
| CON-3P-01 | Must | Só os componentes de §29.1 entram no firmware. Um componente novo entra por emenda deste capítulo, com origem, versão e licença. | [user] regra 15 |
| CON-3P-02 | Must | Toda licença de §29.1 é compatível com a distribuição do firmware sob GPL-3.0-or-later (CON-SW-06). As fontes (OFL-1.1, CC-BY-4.0) são dados empacotados com o programa, como a OFL permite, e levam aviso e licença em `LICENSES/`. | [user] Q15 · [derived] · revisão 2026-11-08 |
| FR-3P-01 | Must | Cada release publica, junto com o binário, o código-fonte completo correspondente e os textos das licenças de §29.1. | [derived] CON-SW-06 |
| FR-3P-02 | Must | `GET /api/status` informa, no campo `source_url`, a URL do código-fonte da versão em execução. O manual traz a mesma URL e a oferta do código-fonte. | [derived] CON-SW-06 · [user] revisão 2026-11-07 |

| ID | Pré-condição · estímulo | Observação esperada | Não pode acontecer | Tier |
|---|---|---|---|---|
| CON-3P-01 | build de release | lista de componentes do build (`idf.py show-components` / SBOM) ⊆ §29.1 | componente fora da lista | host (CI) |
| CON-3P-02 | SBOM do build | licenças ∈ {Apache-2.0, MIT, GPL-3.0-or-later, OFL-1.1 e CC-BY-4.0 só para fontes} | licença incompatível; OFL ou CC-BY fora de fonte | host (CI) |
| FR-3P-01 | release publicada | arquivo de fonte + `LICENSES/` presentes nos artefatos | binário sem fonte | manual |

## Configuração e marcadores

| `speech_rate_wpm` | inteiro | 175 | 80–260 (limites do eSpeak NG; padrão = `SPK_RATE_WPM`) | operacional | próxima fala | pedido do responsável 2026-11-16 · OD-19 |
| `SPEECH` | `start id chars`; `done id ms heap_min`; `abort id`; `fail id err`; `ready=<0/1> reason` | FR-SPK-02, FR-PLT-06 |
