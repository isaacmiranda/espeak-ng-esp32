# Portão: AI harnessed (fecha a Fase 1)

**Exclusão permanente:** a evidência é só o que está commitado no repositório, o CI e o que a bancada responde agora. Nunca memória do assistente, transcrições, `docs/Ideia/` nem o relato de quem fez o trabalho.

## Requisitos

| # | Deve ser verdade | Onde olhar | Evidência |
|---|---|---|---|
| 1 | Plano com capacidades declaradas | `testing/test-plan.yaml` | `capabilities` com `bench-discover`, `bench-chip-info`, `bench-flash`, `bench-reset`, `bench-telemetry`, `bench-command`, `bench-wait-event`, `udev-link`, `dut`, `release-verification`; nenhuma `yes` (a placa não foi tocada) |
| 2 | Jornada semeada | idem | `JRN-01` a `JRN-06`, `shape: workflow`, `verifies` com IDs que existem na FSD |
| 3 | Agenda de depuração | `testing/debugging-agenda.md` | cada linha com "não comprovada porque" e "comprovada por" |
| 4 | Padrão de testes único | `docs/Method/standards/testing.md` | seção "Preparação, limpeza e evidência" (P1–P3) |
| 5 | Driver com testes na porta falsa | `tools/bench/` | `pytest -q tools/bench` verde; um arquivo de teste por comando de `bancada.md` |
| 6 | Comandos citados = comandos do driver | `docs/`, `.claude/`, `CLAUDE.md` × `python -m bench --help` | as duas listas iguais (fora `bench.yaml`) |
| 7 | Esqueleto de firmware sem módulo extra | `research/firmware/` | só `main.c` com o marcador `ESPK boot`; nenhum componente que a FSD não peça |
| 8 | CI rodou verde uma vez | `.github/workflows/ci.yml` | `gh run list -w ci -L 1` com `success` |
| 9 | Release com verificação na bancada | `.github/workflows/release.yml` | job `release-verify` em `[self-hosted, bench-notebook]` antes de `publish` |
| 10 | Runner instalado; registro como concessão | `tools/bench/runner/` | `install.sh` com SHA-256; `register.sh` efêmero, por repositório |

## Checagens mecânicas

```bash
.venv/bin/pytest -q tools/bench
.venv/bin/ruff check tools conftest.py
.venv/bin/reuse lint
diff <(.venv/bin/python -m bench --help | grep -oE '^    [a-z-]+' | tr -d ' ' | sort -u) \
     <(grep -rhoE '`bench [a-z][a-z-]*|python -m bench [a-z][a-z-]*' docs .claude CLAUDE.md | grep -oE '[a-z][a-z-]*$' | sort -u)
gh run list -w ci -L 1 --json conclusion -q '.[0].conclusion'          # success
grep -c 'id: JRN-' testing/test-plan.yaml                               # 6
```

## Julgamento

- Abra uma sessão `/build` só com o repositório: ela diz em que fase está e qual o próximo ato sem perguntar nada?
  Cite a frase dela.

## Armadilhas

- Capacidade com `available: yes` ou `observed:` que só a placa daria: a Fase 2 foi feita sem o portão dela.
- Teste do host que afirma comportamento do produto em vez de provar que o nível roda.
- Firmware consertado medindo o hardware em vez de emendar a FSD.

**Veredito:** `OPEN`, ou `SHUT` com cada achado: o requisito, onde procurou, o que achou. O verificador não corrige nada.
