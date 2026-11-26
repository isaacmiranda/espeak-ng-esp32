# Decisões abertas e valores propostos

Cada item nomeia o requisito que bloqueia. O item sai daqui quando a FSD absorver a decisão.

## Decisões abertas

| ID | Decisão | Bloqueia | Como se resolve |
|---|---|---|---|
| OD-01 | Resultado da F2: a divergência por acento (#1611) se confirma no alvo? Há divergência por ponto flutuante? | FR-ENG-04, FR-ENG-05, FR-UPS-01, FR-REF-04, padrão de `CONFIG_ESPK_UCD_WRAP` | experimento da F2 (R3 × R1); emenda da FSD |
| OD-02 | O Registro aceita o pacote com os dados de todos os idiomas mais `phsource/` e `dictsource/`? A documentação não publica limite; o `espeak-ng-data` completo tem ≈ 24 MB instalado. | FR-REL-01, FR-REL-03, FR-LIC-03 | upload de teste ao *staging* (FR-REL-03). Alternativa, se recusado: pacote base (`en`, `pt`) mais pacotes de idioma — exige emenda |
| OD-03 | Licença das Harvard sentences (IEEE 1969) permite redistribuir no repositório? | FR-COR-05 | conferência da licença; sem confirmação, só as frases imprevisíveis geradas |
| OD-04 | Transporte de OTA do firmware de pesquisa (as partições `ota_0`/`ota_1` existem). | nenhum requisito ainda; abre um FR futuro | decisão do responsável quando o OTA entrar no escopo |

## Valores propostos pelo assistente, à espera de aceite

Marcados `proposto` na FSD. Aceitar um valor é trocar a marca por `[user]`.

| Requisito | Valor proposto |
|---|---|
| §2.2, CON-PLT-03 | versão 6.x do build de compatibilidade: a última 6.x estável na data do `/harness` |
| CON-PLT-02 | `targets`: esp32, esp32s2, esp32s3, esp32p4 |
| FR-RES-10, FR-SYN-03, FR-ASY-03, §15.2, §28.1 | cancelamento em ≤ 100 ms |
| FR-RES-16, FR-SYN-09, `CONFIG_ESPK_MAX_TEXT_LEN` | texto de até 1 024 bytes |
| FR-COR-03 | corpus automático: numerais, `2026-11-26`, `14:30` |
| FR-COR-04 | 200 palavras, 50 frases imprevisíveis, 30 frases do dia a dia |
| FR-ASR-01 | modelo Whisper `small` multilíngue |
| FR-CAP-08, `CONFIG_ESPK_CAPACITY_WARN_PCT` | aviso a 90 % |
| `CONFIG_ESPK_PSRAM_BUDGET_KB` | 2 048 |
| FR-SYN-11, NFR-SYN-04 | tolerância de heap de 1 KB |
| FR-ASY-01 | `espk_say()` volta em ≤ 5 ms |
| FR-ASY-04, `CONFIG_ESPK_QUEUE_LEN` | fila de 4 |
| FR-ASY-06 | pilha mínima de 49 152 B |
| §15.2 | `espk_deinit` em ≤ 100 ms |
| FR-MEM-04 | tolerância de 5 % no pico de PSRAM |
| `CONFIG_ESPK_TASK_PRIORITY`, `CONFIG_ESPK_TASK_CORE` | prioridade 5, sem afinidade |
| Apêndice B | base de erro própria `0x7E00` |
