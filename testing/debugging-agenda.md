# Agenda de depuração

O que nunca foi visto funcionando **aqui**. O `/commission` esvazia esta lista; as medições vão para a capacidade
correspondente em [`test-plan.yaml`](test-plan.yaml), não para casos de teste.

| Parte | Não comprovada porque | Comprovada por | Capacidade |
|---|---|---|---|
| Driver de bancada | só rodou contra a porta falsa | cada comando passa com a placa real | `bench-*` |
| Link udev `/dev/espk-dut` | o número de série da placa não está em `bench.yaml` | `bench discover` grava o serial; `bench udev-rule` instalado; o link aparece depois de replugar | `udev-link` |
| ModemManager | está ativo no notebook (2026-11-26) e pode abrir a porta | `systemctl is-active ModemManager` = `inactive` | `bench-discover` |
| A placa neste projeto | só foi vista com o firmware do AlertAlergo | `bench chip-info dut`: esp32-s3, 16 MB de flash, 8 MB de PSRAM, MAC registrado | `dut`, `bench-chip-info` |
| Caminho CI → gravação | o CI deste repositório nunca rodou | artefato do CI gravado com `bench flash`; `ESPK boot` com o commit do artefato | `bench-flash`, `release-verification` |
| Runner do notebook | não registrado (concessão do responsável) | uma tag dispara o job e ele termina | `release-verification` |
| Partição de dados do eSpeak | nunca gravada a partir deste repositório | `ESPK ready` no boot | `dut` |
| Saída de áudio (ES8311/I2S) | nunca acionada por este firmware | tom de teste no volume 5 e `underrun=0` | `audio-out` |
| Captura do PCM no alvo | o *seam* não existe | hash de um texto conhecido igual ao de R1 | `pcm-capture` |
| R1 no host | a ferramenta não existe | hashes reproduzem os vetores da semente (`seed/alertalergo-port/tests/host/vectors/`) | `r1-host-reference` |
| `espeak-ng` do sistema (R2) | não instalado | `espeak-ng --version` mostra 1.52.0 | `espeak-ng-system` |
