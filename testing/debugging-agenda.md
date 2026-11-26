# Agenda de depuração

O que nunca foi visto funcionando **aqui**. O `/commission` esvazia esta lista; as medições vão para a capacidade
correspondente em [`test-plan.yaml`](test-plan.yaml), não para casos de teste.

## Abertos

Nenhum do lado da bancada.

## Movidos para a Fase 3, onda 1 (bring-up antes da jornada)

Dependem do componente, que o `/build` constrói; até lá não há código que os exercite. As capacidades seguem
`unproven`, e os `JRN-*` que precisam delas ficam bloqueados por cálculo.

| Parte | Por que espera | Comprovada por | Capacidade |
|---|---|---|---|
| Partição de dados do eSpeak | a imagem e o leitor são da Parte B da FSD | `ESPK ready` no boot | `dut` (dados) |
| Saída de áudio (ES8311/I2S) | o caminho de áudio entra com o firmware de pesquisa completo | tom de teste no volume 5 e `underrun=0` | `audio-out` |
| Captura do PCM no alvo | o *seam* é o callback do componente | hash de um texto conhecido igual ao de R1 | `pcm-capture` |
| R1 no host | a ferramenta é da F1 do `/build` | hashes reproduzem os vetores da semente | `r1-host-reference` |
| Runner e release na bancada | o registro é concessão do responsável; a primeira tag só faz sentido com `tests/bench/` escrito | uma tag roda o `release-verify` até o fim | `release-verification` |

## Resolvidos (2026-11-26)

Driver de bancada com a placa real (sete comandos), a placa neste projeto (`chip-info`), caminho CI → gravação
(run 45859053285), link udev `/dev/espk-dut`, ModemManager desligado, `espeak-ng` 1.52.0 do sistema. As observações
estão nas capacidades.
