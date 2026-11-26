# espeak-ng-esp32

Componente livre e de uso geral: **eSpeak NG 1.52 como componente ESP-IDF nativo**, para todos os idiomas do upstream
e qualquer ESP32 com PSRAM, com as fontes do upstream intactas e o PCM provado igual ao do upstream. Também é plataforma
de pesquisa: medido no aparelho (memória, latência, convivência com Wi-Fi/BLE/tela), com inteligibilidade estimada por
ASR e, no futuro, um estudo com ouvintes aprovado pelo CEP. Prioridade: pt-BR, depois en. Hardware de referência:
**Waveshare ESP32-S3-RLCD-4.2** (a mesma placa do AlertAlergo V3). O ponto de partida é o porte feito no AlertAlergo V3 (`seed/alertalergo-port/`).

Este arquivo só configura o assistente e aponta. As regras estão no Método: **leia `docs/Method/AI-Workflow.md` antes
de qualquer mudança.**

## Fases e portões

| Fase | Skill | Portão |
|---|---|---|
| 0 · Definição | `/grill-me`, `/define` | **Load defined**: todo Must/Should com contrato de verificação; três planos existem |
| 1 · Harness | `/harness` | **AI harnessed**: uma sessão `/build` abre, diz onde está e age sem perguntar |
| 2 · Comissionamento | `/commission` | **DUT ready**: bancada comissionada, DUT verificada, caminho de gravação provado |
| 3 · Construção | `/build` | **Ready for shipment**: requisitos atendidos, jornada verde, reconcile vazio |
| Liberação | tag (ato do responsável) | **Shipped**: versão publicada e jornada verde nos bytes publicados |

Estado atual: **Fase 1 (harness)**: FSD aprovada (`docs/Functionality/FSD.md`), plano em `testing/test-plan.yaml`,
agenda em `testing/debugging-agenda.md`, portões em `testing/gates/`. Próximo passo depois do portão "AI harnessed":
`/commission`. O que está em `seed/` é evidência,
não produto.

## A bancada

O notebook de desenvolvimento (físico, Ubuntu) com a placa direto na USB. Driver `python -m bench`, papel `dut` em
`bench.yaml`, link `/dev/espk-dut`, testes com placa só com `pytest --run-bench`. Tudo em
`docs/Method/project/bancada.md`. A bancada começa `available: unproven`. **A placa é compartilhada com o AlertAlergo
V3** (`~/projetos/alertalergo-v3-firmware`): antes de gravar, veja o que está nela; ao sair, registre o que ficou.

## Skills próprias

`bancada` (placa e driver), `esp-idf` (build, memória, dados do eSpeak). As skills de fase são porte do upstream:
`.claude/skills/UPSTREAM.md`.

## Ambiente

- Notebook limitado (≈ 3,4 GB de RAM, HDD 5400 rpm): todo build com `nice -n 15 ionice -c 2 -n 7` e no máximo 2 jobs;
  um processo pesado por vez; builds longos em segundo plano. ESP-IDF sempre por `scripts/idf.sh` (versão fixada).
- Buscas ignoram `build*/`, `.git/`, `managed_components/`.
- O pip do sistema é bloqueado (PEP 668): use um `venv`.

## Regras do projeto

- **Idiomas:** código, identificadores, mensagens de commit, README e documentação para contribuidores em **inglês**;
  FSD, protocolo do estudo e material dos ouvintes em **pt-BR**; os documentos públicos existem nos dois idiomas
  (política exata: pauta do `/define`). Respostas ao responsável em pt-BR.
- **Licença:** GPL-3.0-or-later (o eSpeak NG é GPL). Código de terceiros só com licença compatível e origem registrada
  (`REUSE.toml`). As fontes do eSpeak NG ficam **sem alteração**; correção vai primeiro ao upstream.
- **Estudo com pessoas:** nenhum dado de ouvinte identificável entra no git. Coleta com participantes só depois da
  aprovação do protocolo pelo comitê de ética (CEP / Plataforma Brasil) — decisão e escopo na FSD.
- **Nunca afirmar** "primeiro TTS pt-BR offline no ESP32" nem resultado de inteligibilidade sem o estudo
  (`docs/Ideia/pesquisa-2026-11-26/relatorio.md`).
- **Git:** identidade `Isaac Miranda <19537105+isaacmiranda@users.noreply.github.com>`, commits com `-s` (DCO),
  imperativo curto em inglês com o requisito, ex.: `Add data partition reader (FR-DAT-01)`. Não rodar `git push` sem
  pedido explícito; não reescrever histórico enviado.
