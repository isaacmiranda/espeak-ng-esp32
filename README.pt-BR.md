# espeak-ng-esp32

*[English](README.md)*

**eSpeak NG como componente ESP-IDF nativo para o ESP32-S3, com fala em português do Brasil — e um estudo de quanto
ela é inteligível para ouvintes reais.**

> **Situação: Fase 0 (definição).** Ainda não há especificação e nada aqui é uma versão publicada. O código em
> [`seed/alertalergo-port/`](seed/alertalergo-port/) é o porte que funciona e de onde o projeto parte (roda hoje na
> placa de referência dentro do firmware AlertAlergo V3); ele vira componente reutilizável à medida que a
> especificação é escrita. Contribuições são bem-vindas — veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Por quê

- Vários projetos já rodam o eSpeak NG em microcontroladores (bibliotecas Arduino para ESP32/RP2040 e um porte
  ESP-IDF recente), mas **não há componente do eSpeak NG no Registro de Componentes da Espressif** nem relato
  publicado e medido dele rodando junto com Wi-Fi, BLE e tela.
- **Não há estudo publicado de escuta de síntese de fala embarcada em português do Brasil** — nem com ouvintes que
  enxergam, nem com ouvintes cegos ou de baixa visão, nem com nomes de fármacos. Verificação automática não é
  inteligibilidade.

O levantamento que sustenta essas afirmações está em
[`docs/Ideia/pesquisa-2026-11-26/`](docs/Ideia/pesquisa-2026-11-26/).

## O que o porte de partida faz

- eSpeak NG **1.52.0, fontes sem alteração**, compilado como componente ESP-IDF (só o motor síncrono).
- Dados de voz e dicionário (~736 KB, pt / pt-BR) numa **partição própria da flash**, com cabeçalho e CRC, vistos pelo
  código de arquivos do upstream (sem alteração) por um VFS somente leitura.
- Tarefa de síntese com pilha na PSRAM, cancelamento e fatiamento que não dispara o watchdog; áudio para o codec
  ES8311 por I2S.
- Build no PC das mesmas fontes: PCM **idêntico byte a byte** ao do upstream para textos fixos, e fonemas fixados.
- Medido na placa de referência com BLE, SoftAP e tela ligados: heap interna mínima durante a fala 39 828 B; o eSpeak
  ocupa ~90 KB fixos de RAM interna.

## Hardware de referência

Waveshare ESP32-S3-RLCD-4.2 — ESP32-S3, 16 MB de flash, PSRAM, codec ES8311, alto-falante, LCD reflexivo.

## Licença

GPL-3.0-or-later ([LICENSE](LICENSE)), porque o eSpeak NG é GPL-3.0-or-later. Partes de terceiros mantêm as próprias
licenças (Apache-2.0, BSD-2-Clause, Unicode), listadas em [`REUSE.toml`](REUSE.toml) e [`LICENSES/`](LICENSES/).

## Como o repositório é construído

O desenvolvimento segue o método [Embedded-AI-Harness](https://github.com/SensorsIot/Embedded-AI-Harness) com um
assistente de IA: especificação primeiro ([`docs/Functionality/`](docs/Functionality/)), teste antes do código,
evidência de hardware a partir do artefato do CI. As decisões humanas ficam registradas na especificação; o uso de IA
é declarado aqui e nos commits. Comece por [`docs/00-Overview.md`](docs/00-Overview.md).

## Citação

Veja [CITATION.cff](CITATION.cff).
