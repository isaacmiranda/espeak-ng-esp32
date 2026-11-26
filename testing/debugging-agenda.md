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
| Saída de áudio (ES8311/I2S) | o caminho de áudio entra com o firmware de pesquisa completo | tom de teste no volume 5 e `underrun=0` | `audio-out` |
| Runner e release na bancada | o registro é concessão do responsável; a primeira tag só faz sentido com `tests/bench/` escrito | uma tag roda o `release-verify` até o fim | `release-verification` |

## Resolvidos (2026-11-26)

Driver de bancada com a placa real (sete comandos), a placa neste projeto (`chip-info`), caminho CI → gravação
(run 45859053285), link udev `/dev/espk-dut`, ModemManager desligado, `espeak-ng` 1.52.0 do sistema, partição de dados (`ESPK ready`), captura do PCM no alvo
(hash igual ao R1 na mesma sequência), R1 no host. As observações
estão nas capacidades.
