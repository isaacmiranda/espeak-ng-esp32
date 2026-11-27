# Próximos passos (retomada de sessão)

Documento de **retomada**: onde o trabalho está e o que fazer a seguir, para uma sessão nova começar sem perguntar.
A posição **derivada** (testes, requisitos, portões) está em [`testing/test-plan.yaml`](../../../testing/test-plan.yaml) e
na [FSD](../../Functionality/FSD.md); este arquivo só aponta e lista o que o plano não diz. **Quem encerra uma sessão
atualiza este arquivo.** Última atualização: 2026-11-27, ao fim da fila da madrugada (itens 0–7 feitos).

## Como abrir a sessão

1. Leia `CLAUDE.md`, [`AI-Workflow.md`](../AI-Workflow.md) e **O que a madrugada fez** abaixo. A fila da madrugada acabou;
   o que sobra depende do responsável (seção "Ações que são do responsável") ou é do passo "Depois da fila".
2. Posição: Fase 3, **onda 1** (só testes `standard`; `deviation` e `negative` já escritos ficam, mas não escreva novos).
3. **A placa é muda (decisão dele, 2026-11-27).** `bench.yaml` tem `audio.bench_sound: forbidden`; o driver recusa `say` sem
   `--mute`, `play` e a gravação de `espk_waveshare`. Não contorne, não edite para `allowed`. Use `--mute`, `pcm`, `synth`.
4. Confira a árvore: `git status`, `git log --oneline -5`. **Nenhum `git push` foi feito** (≈ 80 commits locais): só ele
   manda. Leia o que está na placa antes de gravar (`python -m bench wait-event dut '^ESPK boot' --timeout 15 --reset`):
   deve ser o firmware de pesquisa (`espk_research`); ela é compartilhada com o AlertAlergo V3.
5. Builds de exemplos e ESP-IDF 6.1.1 já rodaram (ver abaixo); `/tmp` é tmpfs de 512 MB e enche: testes pesados usam
   `~/.cache/espk/tmp`.

## Onde estamos

- **Portões abertos:** Load defined, AI harnessed, DUT ready (veredito `OPEN` em `testing/test-plan.yaml` → `gates`).
  Os de Ready for shipment e Shipped esperam o fim da onda.
- **Testes:** 126 de 128 declarados `successful` (o resto: TC-SYN-11-heap `failed` por vazamento do upstream; TC-EXM-03 que espera a placa não muda; antes: e o que
  ainda não rodou). Suítes: `pytest -q tools/bench tests/host` (≈ 170, 3 min) e `pytest tests/target tests/bench --run-bench` (≈ 8 min).
- **Prova central já feita (F2):** a placa produz o mesmo PCM que o upstream no host, bit a bit, em 100 de 100 itens do
  corpus de verificação, depois de redirecionar as `isw*` para o `ucd-tools` (FR-ENG-04). Sem o redirecionamento, a
  placa soletra as letras acentuadas (#1611).
- **FR-ENG-05 (modo intacto) feito:** variante `research/firmware/sdkconfig.intact.defaults` (`-B build-intact -D SDKCONFIG=build-intact/sdkconfig "-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.intact.defaults"`); ELF sem `__wrap_isw*`; na placa a divergência de R1 começa no primeiro item acentuado e **se espalha** (100 de 100 itens divergem, inclusive inglês depois do primeiro acento, pelo estado do motor); inglês sem acento desde um reset é igual a R1.
- **Volume (FR-RES-07, 08, 09):** `volume` sem argumento responde `ESPK volume ok=<n>`, argumento ruim `err=range`, `listen close` volta ao padrão 5 (propostas minhas, ainda sem aceite). O guarda do driver barra `volume` > 10 antes da placa; o teste de 11 é do host.
- **Cancelar (JRN-06) verde** (`a55a70d`): `cancel` no meio de uma fala de 985 bytes → `ESPK cancelled id=<n> cancel_ms=5`; `cancel_ms` é proposta minha (medida no chip, da chamada ao evento). Os pedidos tirados da fila também recebem `cancelled` (para o dono liberar o contexto); um `say` durante `CANCELLING` fala logo depois do `CANCELLED` (a tabela não diz; proposta).\n- **`.bss` do motor na PSRAM (FR-MEM-02, `CONFIG_ESPK_BSS_IN_PSRAM`, padrão ligado):** fragmento `components/espeak-ng/linker.lf` (precisa de `LDFRAGMENTS` no CMake); a RAM interna livre depois do boot subiu de 250 KB para 341 KB. O teste do host lê o ELF (`ESPK_BUILD` aponta outro diretório de build).
- **Variantes de build (`scripts/variants.sh [nome...]`, um build completo cada, ~10 min):** `intact`, `sync`, `nolabel`, `nosubtype`, `nopsram`, cada uma com o seu teste (`ESPK_<NOME>_BUILD`). Provam FR-ENG-05, FR-ASY-08, FR-DAT-01/02 e FR-MEM-01. Depois de rodar variantes, a placa fica com a última: regrave o artefato normal. Um build sem PSRAM não linka `esp_psram`: o componente trata como "sem PSRAM".
- **Capacidade (FR-CAP-01..10):** `components/espeak-ng/tools/capacity.py` valida idiomas, voz inicial, tamanho da imagem × partição, orçamento de PSRAM e o aviso de 90 %, e emite o relatório; o CMake do componente a roda no configure (com `ESPK_DATA_DIR`), grava `build/espeak.img` e `build/espk_capacity.json` e passa o pico ao `espk_init` (`ESPK_PSRAM_PEAK_BYTES`). A RAM estática interna vem do `.map` (`--map`); o relatório pós-link ainda não é automático. Medido: imagem `pt-br en` = 904 477 B, pico 827 224 B, RAM estática interna do componente 482 B.
- **Achados da capacidade para o responsável:** (1) a imagem de **todos** os idiomas tem 18,3 MB e **não cabe** na partição `espeak` de 9,9 MB do §2.2; (2) o upstream 1.52.0 lista as vozes `xex`, `fo` e `kaa` sem dicionário compilado nos próprios dados, e o `--all` as deixa de fora com aviso.
- **R2 (`tools/ref/r2.py`, FR-REF-05..07):** compara o `espeak-ng` 1.52.0+dfsg-5build1 do sistema com o R1; API e CLI (PCM e fonemas). Em 141 vozes pela API: 45 divergências, todas de `fo`, `kaa`, `xex` (o R1 não tem o dicionário dessas três; o pacote do Ubuntu compila) e atribuídas em `tools/ref/r2-causes.tsv`. A passagem `--all --cli` (uns 8 mil processos) não foi rodada aqui, e **o passo no CI hospedado não foi ligado**: precisa do pacote do sistema com versão exata no runner (decisão do responsável, abaixo).
- **Marcadores e comandos de pesquisa novos (propostas minhas):** `ESPK queued id= queue_us=` (resposta do `say`), `synth <texto>` → `ESPK sync sha256=` (caminho síncrono), `taskinfo` → `stack= psram= hwm=` ou `task=none`, `cancel` → `ESPK cancel err=` só em erro. Variantes de build: `sdkconfig.intact.defaults`, `sdkconfig.sync.defaults` (`-B build-intact` / `-B build-sync`, mesmo formato do intacto).
- **JRN-03 verde** (`174a978`): `say` sem `--mute` por `research/firmware/components/audio_es8311` (I2C SDA 13/SCL 14, ES8311 0x18), `start` antes de `done`, `underrun` por estimativa (escrita que chega com o alto-falante já seco). Volume 5 é inaudível; a escuta do responsável (30 não, 70 sim, baixa) provou o caminho: `audio-out: yes`. A placa tem o firmware de `174a978`.
- **Capacidades ainda `unproven`:** `release-verification` (o runner).

## Decisões tomadas pelo responsável (2026-11-27)

Ele aceitou todas as sugestões. Viram trabalho abaixo; a FSD ainda **não** as absorve (primeiro item da fila).

1. **Lista pt-BR (FR-COR-04):** `por_news_2022_10K` do Leipzig (CC BY 4.0, SHA-256 fixado), rotulada "português (Leipzig), não
   específica de pt-BR"; emenda da FSD.
2. **ESP-IDF 6.x do CI (CON-PLT-03):** `v6.1.1`.
3. **R2 no CI (FR-REF-07):** job em contêiner com a release do Ubuntu que traz o `espeak-ng` 1.52.0 (a do notebook é Ubuntu
   26.04), versão do pacote fixada.
4. **Testes `negative`/`deviation` escritos antes da hora:** mantidos, reclassificados no plano.
5. **FR-SYN-11:** tolerância afrouxada para o vazamento medido (1 348 B por ciclo) **e** correção preparada para o upstream.
6. **Todos os idiomas não cabem** (18,3 MB de imagem; o russo pede 9,2 MB de PSRAM): documentar no README, sem mudar o §2.2.
7. **Propostas minhas aceitas** (viram requisito): marcadores e comandos de pesquisa (`queued id= queue_us=`, `cancel_ms=` em
   `cancelled`, `taskinfo`, `init`/`deinit`/`cut`/`synth`/`mem`/`info`/`rate`/`pcm`/`audio`/`play`/`hog`/`vfs`), `volume` sem
   argumento responde o valor, argumento ruim `err=range`, `listen close` volta ao 5, pedidos tirados da fila recebem
   `cancelled`, um `say` durante `CANCELLING` fala depois do `CANCELLED`, `SAY_TOO_BIG` dá `INVALID_SIZE` em todo estado vivo,
   `underrun` estimado, NFR-SYN-04 lido como "a heap livre não encolhe mais de 1 KB e é constante a partir da 2ª síntese",
   `espk_synth` exige ≥ 48 KB de pilha (os exemplos usam `espk_say`), a bancada muda.
8. **Textos públicos:** eu atualizo o README (tabelas de chips e de capacidade); ele revisa tudo de manhã. `AI-USE.md` e
   `ORIGIN.md` também esperam a revisão dele.
9. **Rascunhos (nunca enviados):** patch do PR do upstream, mensagem ao `dfxpto-cyber`, `FSD-summary.en.md`.

## O que a madrugada fez (2026-11-27, commits `3142005`…`d99ae14` e seguintes)

- **0 · exemplos:** `hello` compila para esp32, esp32s2, esp32p4 e esp32s3; o da Waveshare compila (teste da placa pulado
  pelo guarda mudo). `TC-BLD-02-examples` declara também o FR-EXM-02.
- **1 · FSD 0.4.0:** FR-RES-17..20 e as decisões; plano reconciliado.
- **2 · README** (en e pt-BR): status da Fase 3, tabela por chip, bloco de capacidade gerado
  (`tools/docs/capacity_table.py`), testes `test_readme.py`. O `source-revision` da tradução é o commit do README.
- **3 · pacote:** `scripts/package-component.sh` (pasta com dados, `phsource/`, `dictsource/`, licenças) e
  `regen-data.sh` (`--check`, `--out`, `--listx`, `--langs`; `ESPEAK_NG=` o binário 1.52.0). `tests/host/test_package.py`.
- **4 · corpus pt-BR e ASR:** `tools/corpus/leipzig.py` (SHA-256 fixado), `wordlist-pt-br.tsv`, `tests/corpus/listen/pt-br.tsv`
  (200 + 50 + 30); corrigi o gênero do substantivo em `sus.py`. ASR: `tools/asr/pins.env` (whisper.cpp `v1.9.6`, modelo
  `small`), `scripts/whisper-setup.sh` (sem AVX, o notebook só tem SSE4.2), `tools/asr/report.py`. Uma execução real de 3
  itens saiu idêntica duas vezes, mas custou 19 min por 6 clipes: **o relatório completo é do CI da tag**.
- **5 · ESP-IDF 6.1.1:** instalado em `~/esp/esp-idf-v6.1.1`; `hello` compila para esp32s3 (4 min 50 s; build em
  `examples/hello/build-idf6`, ignorado). CI: job `hello-idf6` (`espressif/idf:v6.1.1`).
- **6 · R2 no CI:** job `r2` em `ubuntu:26.04` com `espeak-ng` 1.52.0+dfsg-5build1 fixado; o teste de "sem apt sem versão"
  agora só admite apt nesse contêiner e com os pacotes espeak fixados (as ferramentas de build são as da release).
- **7 · rascunhos:** `docs/rascunhos/` (nunca enviados). **Achado:** o build CMake do upstream já usa o shim
  `src/include/compat/wctype.h` (isw* → ucd-tools); o componente não põe esse diretório no include, daí o wrap.
  Ver `upstream-1611.md`.
- **Suítes ao fim:** `pytest tools/bench tests/host` 187 verdes; `tests/target tests/bench --run-bench` com o artefato
  `4d4b2fa` na placa: 41 passam, 15 pulados, 1 xfail (o vazamento do FR-SYN-11).

## Depois da fila (o que um próximo passo pode fazer sozinho)

1. **Experimento do `compat`** (ver `docs/rascunhos/upstream-1611.md`): `PRIV_INCLUDE_DIRS` com
   `upstream/src/include/compat` no lugar do wrap; build, PCM da placa × R1 (silencioso), modo intacto. Se igual, emenda da
   FSD (FR-ENG-04, FR-UPS-01) e o wrap sai. É decisão de projeto: mostre ao responsável antes de remover o wrap.
2. **TC-EXM-03** (exemplo da Waveshare fala): precisa da placa não muda; espera o responsável.
3. **Onda 1 fechada?** Lacunas da v0.1 sem teste: só FR-REL-01, FR-REL-03, FR-REL-05, FR-UPS-01 (atos dele). Rode o script
   de lacunas abaixo.
4. **Relatório ASR completo e R2 `--all --cli`:** só no CI (rodar com a tag).
5. **README e AI-USE.md/ORIGIN.md:** ele revisa de manhã; atualizar `AI-USE.md`/`ORIGIN.md` com o que a madrugada fez
   (ASR, corpus Leipzig CC BY, achado do `compat`) ainda não foi feito.

## Ações que são do responsável (peça, não faça)

- **`git push`:** só quando ele pedir; até agora ele autorizou caso a caso.
- **Registrar o runner** (`tools/bench/runner/register.sh`, instalado em `~/actions-runner/espeak-ng-esp32`, não
  registrado): antes da primeira tag. O `release.yml` já passa `ESPK_ARTIFACT` ao `tests/bench --run-bench -k jrn`; o
  notebook precisa de `cmake`, `ninja` e `cc` para o R1.
- **Tag de release:** ato dele; o laço nunca cria tag.
- **Texto do contato com o `dfxpto-cyber`** (FR-REL-05) e **texto do PR da #1611** (FR-UPS-01): redigir e mostrar a ele
  antes de qualquer envio; o PR e a issue são públicos.
- **`sudo`:** qualquer ajuste de sistema (já feitos: regra udev, ModemManager desligado, `espeak-ng` instalado).
- **Decisão aberta:** OD-02 (`docs/Functionality/open-issues.md`), resolvida pelo upload de teste.

## Comandos de trabalho

Do diretório do repositório, com o `venv` (`.venv/`, `requirements.txt`) e sempre em baixa prioridade
(`nice -n 15 ionice -c 2 -n 7`, no máximo 2 jobs; um processo pesado por vez; builds longos em segundo plano):

```bash
.venv/bin/pytest -q tools/bench tests/host                    # host + driver na porta falsa (~10 s; 1º R1 compila o upstream, minutos)
.venv/bin/ruff check components tools tests conftest.py ; .venv/bin/reuse lint
scripts/build-image.sh /tmp/espeak.img                        # imagem de dados (pt-br, en) a partir do R1
cd research/firmware && ../../scripts/idf.sh env ESPK_DATA_DIR=~/.cache/espk/r1-1.52.0-bb4338102ff3/espeak-ng-data \
    idf.py -B build -G Ninja build -- -j2                     # sem sdkconfig velho: apague research/firmware/sdkconfig ao mudar defaults
scripts/package-artifact.sh research/firmware/build /tmp/fw   # artefato: flash_args + imagens + manifest.yaml
ESPK_ARTIFACT=/tmp/fw .venv/bin/pytest tests/target tests/bench --run-bench -q   # ~3 min, na placa
gh run download <run-id> -n espk-research-firmware -D /tmp/ci-fw   # os bytes que o CI construiu
```

O build do firmware exige `ESPK_DATA_DIR` (o `espeak-ng-data` compilado do R1: o componente escolhe os idiomas de `CONFIG_ESPK_LANGUAGES`, monta a imagem e roda as verificações de capacidade, `tools/capacity.py`) **ou** `ESPK_IMAGE` (uma imagem pronta: é o caminho do CI e das variantes de `scripts/variants.sh`, que não podem falhar no build). O cache do R1 fica em `~/.cache/espk/` (nunca no repositório).
`test-results/` está no `.gitignore`: a evidência que conta é o `observed:`/`result:` do plano e a resposta da bancada.

### Levantamento de lacunas (gerado, não escrito à mão)

```bash
.venv/bin/python - <<'PY'
import re, yaml
fsd = open('docs/Functionality/FSD.md').read()
reqs = re.findall(r'^- \*\*((?:FR|NFR|CON)-[A-Z]+-\d+)\*\* \[(Must|Should|Could)[^\]]*?· (v0\.1|v0\.2|futuro)\]', fsd, flags=re.M)
ver = {v for t in yaml.safe_load(open('testing/test-plan.yaml'))['tests'] for v in t.get('verifies', [])}
print(sorted(r for r, _p, v in reqs if v == 'v0.1' and r not in ver))
PY
```

## Armadilhas já pagas

- **Abrir a porta serial reiniciava a placa** (DTR baixado antes do RTS). Corrigido em `tools/bench/bench/ports.py`;
  um reset no meio de um teste é suspeita de bancada antes de ser defeito do produto.
- **O motor guarda estado entre sínteses:** o PCM de um texto depende do que foi falado antes. Nunca compare o hash de
  um item sozinho: compare a fala k com a fala k de R1 executando o mesmo roteiro (FSD §7).
- **O console perdia bytes de linhas longas** (anel de 256 B); o anel agora é de 4 096 B e `ESPK done` traz `bytes=`.
  Um teste com texto longo deve conferir `bytes`.
- **A libc de desktop muda com a versão:** o glibc do runner do GitHub concorda com o `ucd-tools` em mais pontos de
  código que o do notebook. Testes contra a libc aceitam subconjunto da lista de diferenças conhecidas.
- **`--wrap` vale para o link da aplicação inteira**, não só para o motor (documentar no README do componente).
- **`pkill -f` derruba o próprio shell** (a linha de comando contém o padrão): mate por PID. Um `until grep -q DONE arquivo`
  pode ler um `DONE` de uma execução anterior: confira também que os processos terminaram.
- **`espk_synth` na pilha da tarefa principal estoura** (o motor pede ≥ 48 KB): em `app_main` use `espk_say`.
- **`esp_partition_munmap`/`mmap` afirmam que a pilha de quem chama está na RAM interna:** o componente mantém o mapeamento.
- **Marcador sem `=`** (`ESPK taskinfo none`) não é lido pelo driver: use `chave=valor`.
- **Placa compartilhada:** o firmware do AlertAlergo fala sozinho perto das pulseiras; regrave antes de medir e
  registre o firmware encontrado e o deixado em `testing/test-plan.yaml` → `dut.observed`.
- **Marcador de boot já passou** quando o ouvinte abre depois do reset: abra o ouvinte antes (`wait-event --reset`).
- **Dado gerado fora do git:** os dados compilados de todos os idiomas, `phsource/` e `dictsource/` não são commitados.

## Convenções de condução

Respostas em pt-BR; commits em inglês, imperativo, `-s`, com o ID do requisito; a cada passo, a posição, o próximo ato e,
quando houver decisão do responsável, uma recomendação. Valores novos propostos pelo assistente entram como proposta e
só viram requisito com o aceite dele. Fonte do upstream nunca é editada.
