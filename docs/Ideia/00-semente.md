# Semente da ideia

Registro do pedido do responsável (2026-11-26), base da Fase 0. Não é requisito: o `/grill-me` e o `/define`
transformam isto em FSD.

## O pedido

> Mover o estudo, e o que for necessário do repositório do AlertAlergo V3, para um repositório novo, voltado para o
> desenvolvimento desta pesquisa. A princípio o responsável será o testador principal e pedirá auxílio aos bolsistas
> para os testes de ouvintes. O repositório deve ser público, de código livre, aberto a contribuições. O hardware é o
> mesmo do AlertAlergo. O workflow de IA começa do zero, apenas com a semente da ideia, e a FSD da pesquisa deve ser
> definida — aproveitando tudo referente ao porte que já foi feito.

## Decisões já tomadas (2026-11-26)

| Tema | Decisão |
|---|---|
| Nome | `espeak-ng-esp32` (GitHub `isaacmiranda/espeak-ng-esp32`) |
| Publicação | público desde o 1º commit, com `LICENSE` e REUSE corretos (o relógio de 6 meses do JOSS começa) |
| Idiomas | código e README em inglês; FSD, protocolo e material de ouvintes em pt-BR; tudo nos dois idiomas |
| Bancada | o mesmo notebook físico do AlertAlergo, a mesma placa (compartilhada) |
| Licença | GPL-3.0-or-later (imposta pelo eSpeak NG) |

## A pergunta de pesquisa (rascunho para o grill)

1. **Engenharia:** um componente ESP-IDF nativo do eSpeak NG, com as fontes do upstream intocadas e os dados numa
   partição, cabe e convive com Wi-Fi, BLE e tela num ESP32-S3 — com quanto de memória, flash, latência e fator de tempo
   real, e com que garantia de equivalência ao upstream?
2. **Percepção:** quão inteligível é essa fala em pt-BR — frases, palavras e nomes de fármacos — para ouvintes que
   enxergam e, depois, para ouvintes cegos ou de baixa visão? Que parâmetros (velocidade, pausas, dicionário) melhoram
   o resultado?
3. **Comunidade:** o que volta para o upstream (correções, entradas de dicionário pt-BR) e para o Registro de
   Componentes da Espressif.

## Material de partida

- [`pesquisa-2026-11-26/relatorio.md`](pesquisa-2026-11-26/relatorio.md) — estado da arte, lacunas, caminhos de
  publicação e plano de ação; as notas de cada frente estão ao lado.
- [`origem-do-porte.md`](origem-do-porte.md) — o que veio do AlertAlergo e de onde.
- [`alertalergo-fsd-fala.md`](alertalergo-fsd-fala.md) — requisitos de fala do AlertAlergo (evidência).
- [`spk-reference-drugs.md`](spk-reference-drugs.md) — lista de 20 fármacos de referência do AlertAlergo.
- [`achados-pre-define.md`](achados-pre-define.md) — pauta do grill.
