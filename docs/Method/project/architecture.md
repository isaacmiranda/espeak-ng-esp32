# Arquitetura (COMO)

O comportamento observável está na [FSD](../../Functionality/FSD.md) (§2.4). Aqui está só o que não sobreviveria a
uma reescrita.

## Camadas, com fronteira por posse

| Camada | Conteúdo | Posse | Muda quando |
|---|---|---|---|
| **L0 motor e plataforma** | eSpeak NG do tarball fixado, sem alteração (só o runtime síncrono); ESP-IDF | upstream (espeak-ng, Espressif) | a versão fixada sobe |
| **L1 componente** | imagem de dados com cabeçalho e CRC, VFS somente leitura, seleção de idiomas e relatório de capacidade, núcleo síncrono, camada assíncrona, colocação de memória | este repositório; é o que vai ao Registro | o ESP-IDF ou o contrato da API muda |
| **L2 aplicação de pesquisa e ferramentas** | firmware de pesquisa (console, marcadores, perfis de carga, escuta), exemplos, R1/R2, corpora, ASR, driver de bancada | este repositório | o estudo ou a bancada muda |

Regra de dependência: L2 → L1 → L0. A L1 não conhece a placa: o PCM sai por callback. Nada deste repositório edita as
fontes de L0. O que precisar mudar no comportamento do motor sem editar a fonte é feito pelo caminho de inclusão (o `include/compat` do upstream) ou no
linker (fragmento de colocação), e a correção de verdade vai ao upstream.

## Seams que dão os níveis baratos

| Seam | Permite | Nível |
|---|---|---|
| fonte de dados (partição no alvo, diretório no host) | as mesmas fontes rodam no PC com os mesmos dados | host |
| callback de PCM | hash do PCM no host e no alvo, sem microfone | host, target |
| marcadores com tempo | latência, RTF e intervalo entre quadros sem cronômetro manual | target, bench |
| ponto de falha no firmware de teste | PSRAM ocupada, dados corrompidos, cancelamento | target |
| lógica de estados da camada assíncrona como função pura | cobrir cada par estado × evento no host | host |

## Organização de pastas

```
components/espeak-ng/       O PRODUTO (vai ao Registro)
  upstream/                 fontes 1.52.0 intactas, geradas pelo script com SHA-256
  data/ phsource/ dictsource/  gerados pelo CI ao empacotar (fora do git)
  src/ include/             camada própria (VFS, partição, API síncrona e assíncrona)
  tools/                    gerador da imagem, relatório de capacidade, script de regeneração
  Kconfig CMakeLists.txt idf_component.yml LICENSE COPYING* README.md ORIGIN.md
examples/hello/             genérico, sem áudio; teste de fumaça de todos os chips
examples/waveshare-s3-rlcd/ ES8311 da placa de referência
research/firmware/          firmware de pesquisa (console, perfis, captura, escuta)
research/study/             corpora de escuta, gerador de amostras e de ordem, material
tools/bench/                driver: python -m bench <comando>
tools/ref/                  R1 (upstream no host) e R2 (espeak-ng do sistema)
tools/asr/                  ASR do CI
tests/host/ tests/target/ tests/bench/
testing/                    test-plan.yaml, debugging-agenda.md, gates/ (do /harness)
scripts/idf.sh              ESP-IDF fixado, ambiente limpo
seed/alertalergo-port/      evidência de partida; sai quando o código a absorver
```

**O que o git guarda e o que o CI gera.** O git guarda as fontes C do upstream em `upstream/` (regeneradas por
`tools/regen-upstream.sh`, `git diff` vazio). Os dados compilados de todos os idiomas, o `phsource/` e o `dictsource/`
não são commitados: o CI os gera do mesmo tarball ao empacotar o componente, e o pacote publicado os leva (FSD
FR-LIC-03, FR-LIC-04). O R1 compila o upstream no cache do host (`~/.cache/espk/`), nunca no repositório.

Cada componente da §2.4 é um módulo próprio. O núcleo puro de cada interface (leitor da imagem, cálculo de
capacidade, transições de estado, parser do console) é uma função livre testável no host.
