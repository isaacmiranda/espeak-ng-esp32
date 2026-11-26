# Propostas para o `/harness`

O resto da pauta pré-`/define` foi absorvido pela [FSD](../Functionality/FSD.md) e por
[`open-issues.md`](../Functionality/open-issues.md). Ficam aqui só as propostas para as duas perguntas que o
`/harness` faz no fim da Fase 1. Todo valor é proposta até o responsável aceitar. O arquivo sai quando o `/harness`
as absorver.

## Agenda de depuração

| Parte | Não comprovada porque | Comprovada por |
|---|---|---|
| Bancada (driver, link udev, `bench.yaml`) | não existe ainda | testes do driver na porta falsa + `bench discover` encontra `dut` |
| A placa neste projeto | só foi vista com o firmware do AlertAlergo | `bench chip-info dut` (S3, 16 MB de flash, 8 MB de PSRAM, MAC) e o boot do firmware de pesquisa |
| Caminho CI → gravação | o CI deste repositório não existe | artefato do CI gravado com `bench flash` e `ESPK boot` com o commit visto |
| Partição de dados do eSpeak | nunca gravada a partir deste repositório | `ESPK ready` (CRC válido) no boot |
| Saída de áudio (ES8311/I2S) | idem | tom de teste no volume 5 + `ESPK done underrun=0` |
| Captura do PCM no alvo | o *seam* não existe | hash do PCM de um texto conhecido igual ao de R1 |
| `espeak-ng` do sistema (R2) | não instalado no notebook | `espeak-ng --version` mostra 1.52.0 |

## Jornada (FSD §28.1)

1. Gravar o artefato do CI → `ESPK boot` com o commit da tag.
2. `ESPK ready`.
3. `say` de um item do corpus de verificação pt-BR → `ESPK start` e `ESPK done underrun=0`.
4. Hash do item igual ao de R1.
5. `voice en` e `say` → hash igual ao de R1.
6. `cancel` no meio de uma fala longa → `ESPK cancelled`.
