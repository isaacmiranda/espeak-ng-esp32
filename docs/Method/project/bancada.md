# A bancada (COMO)

A bancada é o notebook de desenvolvimento (físico, Ubuntu, ≈ 3,4 GB de RAM, HDD) com uma **Waveshare
ESP32-S3-RLCD-4.2** ligada direto na USB (USB-Serial/JTAG nativo do ESP32-S3, `303a:1001`). Não há bancada de
terceiros: o equipamento é deste projeto, o driver mora em `tools/bench/` e é comissionado no `/commission`.

**Status: `available: unproven`.** Vira `available` quando cada comando do driver passou no seu próprio teste, o link
udev está presente e o papel de [`bench.yaml`](../../../bench.yaml) bate com o que `bench discover` encontra. Antes
disso, nada que dependa de placa é `failed`: é `not done`.

**A placa é compartilhada** com o AlertAlergo V3, que usa o mesmo notebook. Cada sessão grava o próprio artefato antes
de testar e registra, na evidência, o firmware que deixou na placa.

## O contrato

- **Driver:** `tools/bench/`, chamado como `python -m bench <comando>`. É escrito no `/harness`, com testes próprios.
- **Papel:** `dut` (a placa de referência), com link udev estável `/dev/espk-dut` amarrado ao número de série.
- **Mapa de papéis:** [`bench.yaml`](../../../bench.yaml), versionado: papel → VID:PID, número de série, chip esperado.
  `/dev/ttyACM*` nunca entra em arquivo versionado. Os testes escolhem a placa pelo papel.
- **Opt-in:** `pytest --run-bench` liga os testes que precisam de placa. Sem a opção, eles são pulados, nunca falham.

### Os comandos e o teste que prova cada um

Todos os testes do driver rodam sem placa, contra uma porta serial falsa (`tools/bench/tests/`), e depois passam pelo
`/commission` com a placa real.

| Comando | O que faz | Teste que o prova (sem placa) | Prova com placa (`/commission`) |
|---|---|---|---|
| `discover` | lista os papéis de `bench.yaml` com o número de série encontrado; falha se faltar papel obrigatório | `test_discover.py`: dispositivos falsos faltando, sobrando e duplicados | `dut` encontrado pelo número de série |
| `chip-info <papel>` | chip, revisão, tamanho de flash, PSRAM e MAC | `test_chip_info.py`: respostas gravadas do esptool | chip, flash e MAC iguais à unidade da FSD |
| `flash <papel> <artefato>` | grava as imagens (app e dados do eSpeak) nos offsets lidos do `flash_args` do build; recusa artefato sem `flash_args` | `test_flash.py`: offsets vêm do arquivo; recusa offset ausente | o marcador do firmware conhecido aparece |
| `reset <papel>` | reinicia pela sequência do USB nativo | `test_reset.py`: a sequência esperada | contador de boot avança na telemetria |
| `telemetry <papel>` | lê os marcadores do produto, um por linha, carimba o horário do PC | `test_telemetry.py`: linhas boas, truncadas e intercaladas | marcadores de boot e de fala lidos |
| `command <papel> <cmd>` | envia uma linha ao console de teste e devolve a resposta | `test_command.py`: eco, tempo esgotado, resposta parcial | o firmware responde ao comando básico |
| `wait-event <papel> <padrão> --timeout <s>` | espera um padrão; abre o ouvinte **antes** de agir; prazo esgotado = `not done` | `test_wait_event.py`: padrão antes, depois e nunca | o marcador de boot é visto depois de um `reset` |
| `udev-rule` | imprime a regra udev de cada papel a partir do serial de `bench.yaml`; recusa papel sem serial | `test_udev_and_config.py`: sem serial recusa; regra amarra link ao serial | o link `/dev/espk-dut` aparece depois de instalar a regra e replugar |

Um único processo segura a porta serial. Nada de terminal aberto à mão.

## Preparação do notebook

1. **Grupo `dialout`** para o usuário que roda o driver.
2. **ModemManager desligado** (`systemctl disable --now ModemManager`).
3. **Regra udev** que cria `/dev/espk-dut` a partir do número de série: depois do `bench discover` gravar o serial em
   `bench.yaml`, `python -m bench udev-rule | sudo tee /etc/udev/rules.d/99-espk.rules` e
   `sudo udevadm control --reload && sudo udevadm trigger`. Pode conviver com o link do AlertAlergo para a mesma placa.
4. **ESP-IDF v5.5.5** em `~/esp/esp-idf-v5.5.5`, sempre por `scripts/idf.sh` (ambiente limpo).
5. **Ambiente Python:** `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` (versões exatas; o driver
   entra como pacote editável).
6. **Recursos:** todo build com `nice -n 15 ionice -c 2 -n 7` e no máximo 2 jobs; um processo pesado por vez.
7. **Rede:** o único Wi-Fi do notebook é o seu uplink: não reconfigurar. Carga de Wi-Fi da placa (SoftAP) não depende do
   notebook entrar na rede dela.
8. **`espeak-ng` do sistema** (referência R2 da FSD): `sudo apt install espeak-ng`.

## CI

- **Runner hospedado (GitHub Actions, gratuito em repositório público):** lint, `reuse lint`, nível host, testes do
  driver (porta falsa) e build do firmware, a cada push.
- **Runner auto-hospedado no notebook:** só em tag. Grava o **artefato do CI** com `bench flash` e roda a jornada
  (`pytest --run-bench`). Jornada vermelha não publica. Etiquetas `[self-hosted, bench-notebook]`, registro efêmero,
  disparado só por tag, com aprovação para contribuição externa (repositório público: código de terceiros nunca roda
  no notebook sem aprovação).
- **Registrar o runner é uma concessão do responsável.** `tools/bench/runner/install.sh` instala (versão e SHA-256
  fixados); `tools/bench/runner/register.sh` registra por repositório, efêmero, em laço, com o rótulo `bench-notebook`,
  e só roda com o "sim" do responsável.

## Riscos físicos

1. **Volume de bancada:** teste automático com som roda no teto de volume **10** (de 0 a 100), com padrão **5** no boot
   (FSD FR-RES-07, FR-RES-08); só uma sessão de escuta aberta (`listen open`) sobe o volume, com pessoas presentes. Nunca encostar o alto-falante no ouvido.
2. **Sessão de escuta** registra posição do ouvinte, volume e ruído de fundo na evidência; o estudo com o CEP fixa esses
   valores no protocolo antes da coleta.

## Armadilhas conhecidas (herdadas do porte de partida)

- **USB nativo do ESP32-S3 reenumera ao reiniciar**; por isso o link udev. O reset de USB do notebook reinicia o xHCI
  inteiro (webcam, Bluetooth e a placa por ~2 s).
- **Gravar com sucesso não prova que gravou no lugar certo:** os offsets vêm do `flash_args`, inclusive o da partição
  de dados do eSpeak.
- **Banner de boot já passou** quando o ouvinte abre depois do reset: abra o ouvinte antes.
- **Escrita na USB-Serial/JTAG maior que o buffer de TX falha inteira**: o console fatia a saída.
- **Placa com firmware do AlertAlergo**: lê pulseiras BLE e fala sozinha quando há pulseira por perto; regrave antes de
  qualquer medição.
- **Abrir a porta pode reiniciar a placa.** O cdc-acm do Linux sobe DTR e RTS juntos ao abrir; baixar o DTR antes do RTS
  passa pelo estado de reset do USB-Serial/JTAG (RTS alto com DTR baixo). O driver baixa o RTS primeiro
  (`tools/bench/bench/ports.py`, teste `test_open_never_passes_through_the_reset_state`). Um reset no meio de um teste é
  suspeita de bancada antes de ser defeito do produto.
