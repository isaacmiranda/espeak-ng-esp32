# Convenções (COMO)

## Linguagens e nomes

- Firmware e componente: C (ESP-IDF). Ferramentas, testes e análise: Python 3.
- Código, API, símbolos, commits e README em inglês; FSD, protocolo do estudo e material de ouvintes em pt-BR.
- Prefixo da API pública do componente: `espk_`; tag de log do componente: `espk`; marcadores do firmware de pesquisa:
  `ESPK <evento> chave=valor …` (FSD FR-LOG-01).
- Marcadores de log observáveis por teste: `TAG event key=value …` numa linha, estáveis entre versões.
- Todo arquivo próprio leva cabeçalho SPDX (`GPL-3.0-or-later`); terceiros constam de `REUSE.toml`.

## Versões fixadas

Tudo o que o CI e o notebook instalam tem versão exata: ESP-IDF **v5.5.5** (FSD §2.2), eSpeak NG **1.52.0** pelo tarball com SHA-256 fixado, `dependencies.lock` versionado
(não `managed_components/`), `requirements.txt` com `==`. Atualizar versão é mudança própria, com a suíte verde antes e
depois.

## Comandos de verificação (proposta; o `/harness` fixa)

| Comando | Faz | Portão de CI |
|---|---|---|
| `scripts/host-tests.sh` | nível host: PCM e fonemas contra o upstream, montador da imagem | sim |
| `pytest -q tests/host tools/bench` | testes Python do host e do driver (porta serial falsa) | sim |
| `ruff check tools tests` | lint do Python | sim |
| `reuse lint` | licenças e SPDX | sim |
| `scripts/idf.sh nice -n 15 ionice -c 2 -n 7 idf.py -C firmware -B build build -- -j2` | firmware de pesquisa | sim |
| `pytest -q tests/target tests/bench --run-bench` | níveis com placa; exige o notebook com a placa | só na tag, no runner do notebook |

"Convenção" quer dizer que a pessoa roda; "portão" quer dizer que o CI bloqueia. O repositório é público: o runner
hospedado do GitHub Actions é gratuito para os níveis sem placa.

## Commits

Curtos, em inglês, no imperativo, assinados (`-s`, DCO), com o id do requisito. Identidade do projeto
(`19537105+isaacmiranda@users.noreply.github.com`), nunca o e-mail pessoal. Não reescrever histórico enviado. Nunca
commitar `test-results/` com dado de participante, artefato de build ou segredo.

## Skills de fase

`.claude/skills/{grill-me,define,harness,commission,build}` são porte do upstream. Toda mudança nelas entra também em
`.claude/skills/UPSTREAM.md`.
