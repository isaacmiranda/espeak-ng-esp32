# Próximos passos (retomada de sessão)

Documento de **retomada**: onde o trabalho está e o que fazer a seguir, para uma sessão nova começar sem perguntar.
A posição **derivada** (testes, requisitos, portões) está em [`testing/test-plan.yaml`](../../../testing/test-plan.yaml) e
na [FSD](../../Functionality/FSD.md); este arquivo só aponta e lista o que o plano não diz. **Quem encerra uma sessão
atualiza este arquivo.** Última atualização: 2026-11-26, após FR-ENG-05.

## Como abrir a sessão

1. Leia `CLAUDE.md` e [`AI-Workflow.md`](../AI-Workflow.md).
2. Abra a sessão dizendo onde o projeto está (skill `/build`, §0): Fase 3, **onda 1** (só testes `standard` e
   funcionalidades; deviation e negative ficam travados).
3. Confira a árvore: `git status`, `git log --oneline -5`, `gh run list -w ci -L 1` (o último CI verde conhecido foi `9946bf8`).
4. A placa está no notebook com o firmware de pesquisa normal (build local de `6951a9e`, regravado depois da variante intacta; agora o de `174a978`, com áudio). Antes de gravar outra coisa, leia o
   que está nela (`python -m bench wait-event dut '^ESPK boot' --timeout 15 --reset`); ela é compartilhada com o
   AlertAlergo V3.

## Onde estamos

- **Portões abertos:** Load defined, AI harnessed, DUT ready (veredito `OPEN` em `testing/test-plan.yaml` → `gates`).
  Os de Ready for shipment e Shipped esperam o fim da onda.
- **Testes:** 45 de 46 declarados `successful`; 1 `failed` (TC-SYN-11-heap, vazamento do upstream). Camada assíncrona (FR-ASY-01..09) e núcleo (FR-SYN-*) cobertos; faltam os grupos de "Próximos atos".
- **Prova central já feita (F2):** a placa produz o mesmo PCM que o upstream no host, bit a bit, em 100 de 100 itens do
  corpus de verificação, depois de redirecionar as `isw*` para o `ucd-tools` (FR-ENG-04). Sem o redirecionamento, a
  placa soletra as letras acentuadas (#1611).
- **FR-ENG-05 (modo intacto) feito:** variante `research/firmware/sdkconfig.intact.defaults` (`-B build-intact -D SDKCONFIG=build-intact/sdkconfig "-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.intact.defaults"`); ELF sem `__wrap_isw*`; na placa a divergência de R1 começa no primeiro item acentuado e **se espalha** (100 de 100 itens divergem, inclusive inglês depois do primeiro acento, pelo estado do motor); inglês sem acento desde um reset é igual a R1.
- **Volume (FR-RES-07, 08, 09):** `volume` sem argumento responde `ESPK volume ok=<n>`, argumento ruim `err=range`, `listen close` volta ao padrão 5 (propostas minhas, ainda sem aceite). O guarda do driver barra `volume` > 10 antes da placa; o teste de 11 é do host.
- **Cancelar (JRN-06) verde** (`a55a70d`): `cancel` no meio de uma fala de 985 bytes → `ESPK cancelled id=<n> cancel_ms=5`; `cancel_ms` é proposta minha (medida no chip, da chamada ao evento). Os pedidos tirados da fila também recebem `cancelled` (para o dono liberar o contexto); um `say` durante `CANCELLING` fala logo depois do `CANCELLED` (a tabela não diz; proposta).\n- **`.bss` do motor na PSRAM (FR-MEM-02, `CONFIG_ESPK_BSS_IN_PSRAM`, padrão ligado):** fragmento `components/espeak-ng/linker.lf` (precisa de `LDFRAGMENTS` no CMake); a RAM interna livre depois do boot subiu de 250 KB para 341 KB. O teste do host lê o ELF (`ESPK_BUILD` aponta outro diretório de build).
- **Variantes de build (`scripts/variants.sh [nome...]`, um build completo cada, ~10 min):** `intact`, `sync`, `nolabel`, `nosubtype`, `nopsram`, cada uma com o seu teste (`ESPK_<NOME>_BUILD`). Provam FR-ENG-05, FR-ASY-08, FR-DAT-01/02 e FR-MEM-01. Depois de rodar variantes, a placa fica com a última: regrave o artefato normal. Um build sem PSRAM não linka `esp_psram`: o componente trata como "sem PSRAM".
- **Marcadores e comandos de pesquisa novos (propostas minhas):** `ESPK queued id= queue_us=` (resposta do `say`), `synth <texto>` → `ESPK sync sha256=` (caminho síncrono), `taskinfo` → `stack= psram= hwm=` ou `task=none`, `cancel` → `ESPK cancel err=` só em erro. Variantes de build: `sdkconfig.intact.defaults`, `sdkconfig.sync.defaults` (`-B build-intact` / `-B build-sync`, mesmo formato do intacto).
- **JRN-03 verde** (`174a978`): `say` sem `--mute` por `research/firmware/components/audio_es8311` (I2C SDA 13/SCL 14, ES8311 0x18), `start` antes de `done`, `underrun` por estimativa (escrita que chega com o alto-falante já seco). Volume 5 é inaudível; a escuta do responsável (30 não, 70 sim, baixa) provou o caminho: `audio-out: yes`. A placa tem o firmware de `174a978`.
- **Capacidades ainda `unproven`:** `release-verification` (o runner).

## Próximos atos, em ordem

O levantamento de lacunas é gerado, não escrito à mão: requisitos Must/Should da v0.1 da FSD cujo id não aparece em
nenhum `verifies:` de `testing/test-plan.yaml` (na sessão de 2026-11-26 eram ~70 depois do núcleo e da camada assíncrona).
Em ordem de dependência:

1. **Escuta e nível de saída.** Registrar posição e ruído da escuta de 2026-11-26 (o responsável ouviu a fala em 70, baixa;
   em 30 não ouviu). O PCM do eSpeak não tem ganho e o AlertAlergo subiu +4 dB com compressão suave; um ganho só pode entrar
   depois do hash (R3 = R1 exige o PCM intacto). Proposta minha, sem requisito. Falta a metade de FR-RES-07/09 na placa com
   `--listening` (`volume 60` aceito dentro da sessão, recusado depois).
2. **Cancelamento no R1** (`tools/ref/pcm_script.c`: repetir o cancelamento no mesmo bloco) para comparar com R1 o hash do
   `say` depois de cancelar (FR-SYN-03, FR-ASY-03; hoje só se prova que o núcleo continua falando).
3. **Parte B restante:** FR-DAT-01 a 06 com partição trocada ou corrompida (precisa de `bench flash` de imagem ruim e depois
   regravar o artefato), FR-MEM-01/02/04, relatório de capacidade e falhas de build (§13, FR-CAP), `Kconfig` completo
   (§19, FR-CFG), erros do Apêndice B (FR-ERR), FR-LOG, FR-SEC, NFR-SYN (RTF, primeira amostra, watchdog, 50 sínteses).
4. **R2 como ferramenta (FR-REF-05 a 07).** Hoje só houve uma comparação exploratória (CLI do Ubuntu = CLI do R1, bit a
   bit). Falta `tools/ref/r2.py`: API × API e CLI × CLI, todos os idiomas, relatório com a versão do pacote.
5. **Corpora e ASR (FR-COR-03 a 07, FR-ASR-*).** Corpus automático para todos os idiomas, lista de frequência Leipzig
   (CC BY 4.0, versão fixada por SHA-256), frases imprevisíveis geradas por semente, `whisper.cpp` no CI.
6. **Empacotamento e publicação (F4):** dados de todos os idiomas gerados pelo CI (fora do git), `phsource/` e
   `dictsource/`, `idf_component.yml`, README e traduções (`source-revision`), `AI-USE.md`, exemplo `hello` e
   `waveshare-s3-rlcd`. **Upload de teste ao *staging* do Registro antes de tudo** (OD-02: o `espeak-ng-data` completo
   tem ≈ 24 MB instalado e o Registro não publica limite).

A v0.2 (convivência, os dois modos de `.bss`, comparação de portes, ferramenta guiada de escuta) só abre depois do
portão da v0.1.

## Pedido de aceite ao responsável (um só, reunido)

Valores e comportamentos que **eu propus** (não estão na FSD; entram como requisito só com o aceite dele):
- marcadores e comandos de pesquisa na forma atual do console: `ESPK queued id= queue_us=`, `cancel_ms=` em `cancelled`,
  `taskinfo`, `init`/`deinit`/`cut`/`synth`/`mem`/`info`/`rate`; `volume` sem argumento responde o valor atual, argumento
  ruim dá `err=range`, `listen close` volta ao 5; pedidos tirados da fila também recebem `cancelled`; um `say` durante
  `CANCELLING` fala depois do `CANCELLED`; `SAY_TOO_BIG` dá `INVALID_SIZE` em todo estado vivo; o `underrun` é estimado
  (escrita que chega com o alto-falante já seco).
- **FR-SYN-11 (decisão):** o upstream vaza 1 344 B por ciclo `espk_deinit`/`espk_init` (`DoVoiceChange` não é liberado por
  `espeak_ng_Terminate`). Opções: (a) afrouxar a tolerância de 1 KB para o vazamento medido e registrar a limitação,
  (b) levar a correção ao upstream (a regra do projeto) e manter o xfail até ela entrar, (c) as duas. Recomendo (c).
- **Armadilha nova (já aplicada):** `esp_partition_mmap`/`munmap` afirmam que a pilha de quem chama está na RAM interna;
  o componente mantém o mapeamento entre `deinit` e `init` e nunca desmapeia.

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
cd research/firmware && ../../scripts/idf.sh env ESPK_IMAGE=/tmp/espeak.img \
    idf.py -B build -G Ninja build -- -j2                     # sem sdkconfig velho: apague research/firmware/sdkconfig ao mudar defaults
scripts/package-artifact.sh research/firmware/build /tmp/fw   # artefato: flash_args + imagens + manifest.yaml
ESPK_ARTIFACT=/tmp/fw .venv/bin/pytest tests/target tests/bench --run-bench -q   # ~3 min, na placa
gh run download <run-id> -n espk-research-firmware -D /tmp/ci-fw   # os bytes que o CI construiu
```

O build do firmware exige `ESPK_IMAGE`. O cache do R1 fica em `~/.cache/espk/` (nunca no repositório).
`test-results/` está no `.gitignore`: a evidência que conta é o `observed:`/`result:` do plano e a resposta da bancada.

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
- **Placa compartilhada:** o firmware do AlertAlergo fala sozinho perto das pulseiras; regrave antes de medir e
  registre o firmware encontrado e o deixado em `testing/test-plan.yaml` → `dut.observed`.
- **Marcador de boot já passou** quando o ouvinte abre depois do reset: abra o ouvinte antes (`wait-event --reset`).
- **Dado gerado fora do git:** os dados compilados de todos os idiomas, `phsource/` e `dictsource/` não são commitados.

## Convenções de condução

Respostas em pt-BR; commits em inglês, imperativo, `-s`, com o ID do requisito; a cada passo, a posição, o próximo ato e,
quando houver decisão do responsável, uma recomendação. Valores novos propostos pelo assistente entram como proposta e
só viram requisito com o aceite dele. Fonte do upstream nunca é editada.
