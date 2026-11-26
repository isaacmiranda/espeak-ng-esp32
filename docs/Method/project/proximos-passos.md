# Próximos passos (retomada de sessão)

Documento de **retomada**: onde o trabalho está e o que fazer a seguir, para uma sessão nova começar sem perguntar.
A posição **derivada** (testes, requisitos, portões) está em [`testing/test-plan.yaml`](../../../testing/test-plan.yaml) e
na [FSD](../../Functionality/FSD.md); este arquivo só aponta e lista o que o plano não diz. **Quem encerra uma sessão
atualiza este arquivo.** Última atualização: 2026-11-26, commit `9946bf8`.

## Como abrir a sessão

1. Leia `CLAUDE.md` e [`AI-Workflow.md`](../AI-Workflow.md).
2. Abra a sessão dizendo onde o projeto está (skill `/build`, §0): Fase 3, **onda 1** (só testes `standard` e
   funcionalidades; deviation e negative ficam travados).
3. Confira a árvore: `git status`, `git log --oneline -5`, `gh run list -w ci -L 1` (o último CI verde foi `9946bf8`).
4. A placa está no notebook com o firmware de pesquisa (build local de `6951a9e`). Antes de gravar outra coisa, leia o
   que está nela (`python -m bench wait-event dut '^ESPK boot' --timeout 15 --reset`); ela é compartilhada com o
   AlertAlergo V3.

## Onde estamos

- **Portões abertos:** Load defined, AI harnessed, DUT ready (veredito `OPEN` em `testing/test-plan.yaml` → `gates`).
  Os de Ready for shipment e Shipped esperam o fim da onda.
- **Testes:** 21 de 23 declarados `successful` no commit `6951a9e` (jornada 1, 2, 4 e 5 verdes). Faltam **JRN-03**
  (áudio pelo alto-falante) e **JRN-06** (cancelar no meio da fala).
- **Prova central já feita (F2):** a placa produz o mesmo PCM que o upstream no host, bit a bit, em 100 de 100 itens do
  corpus de verificação, depois de redirecionar as `isw*` para o `ucd-tools` (FR-ENG-04). Sem o redirecionamento, a
  placa soletra as letras acentuadas (#1611).
- **Capacidades ainda `unproven`:** `audio-out` (ES8311/I2S) e `release-verification` (o runner).

## Próximos atos, em ordem

1. **FR-ENG-05, modo "intacto".** Build com `CONFIG_ESPK_UCD_WRAP=n` (`-D` no `sdkconfig` ou
   `sdkconfig.defaults` de uma variante): deve compilar e funcionar. Teste primeiro (`xfail` enquanto não existe):
   `nm` do ELF sem `__wrap_isw*` e, na placa, a divergência de R1 **só** nos itens acentuados (o
   `tests/target/test_equivalence.py` já grava `test-results/equivalence-report.json`). Entra no plano como `TC-ENG-05`.
2. **Áudio pelo ES8311 (JRN-03, capacidade `audio-out`).** Portar `seed/alertalergo-port/firmware/components/l1_audio/`
   (`audio_es8311.c`: I2C `0x18`, I2S 0, `esp_codec_dev`) para o firmware de pesquisa, adaptado ao PCM a 22 050 Hz mono,
   e escrever o comando `say` sem `--mute`, `volume`, `listen open|close` (FR-RES-04, 07, 08, 09, 12). **Faz som na
   placa:** volume padrão 5, teto de bancada 10 (o driver recusa mais, `bancada.md`); alguém presente, sem alto-falante
   junto ao ouvido. Escrever o `JRN-03` antes do código.
3. **Cancelar (JRN-06) e a camada assíncrona (§15, FR-RES-10 e 11, FR-ASY-*).** Tarefa de síntese com fila, pilha de
   64 KB na PSRAM, `espk_say`/`espk_cancel`, eventos START/DONE/CANCELLED. A tabela de estados da §15.2 é testável no host
   como função pura. O R1 precisa passar a repetir o cancelamento no mesmo bloco (passo novo no roteiro de `pcm_script.c`).
4. **Comandos que faltam no console:** `rate`, `info`, `mem`, `load` (FR-RES-06, 13, 14; `load` é v0.2).
5. **Parte B restante:** `espk_deinit`, `espk_set_rate`, relatório de capacidade e falhas de build (§13), `Kconfig`
   completo (§19), erros do Apêndice B, FR-DAT-01 a 06 com partição trocada ou corrompida (precisa de gravação de imagem
   ruim: `bench flash` de uma imagem com CRC errado e depois regravar o artefato).
6. **R2 como ferramenta (FR-REF-05 a 07).** Hoje só houve uma comparação exploratória (CLI do Ubuntu = CLI do R1, bit a
   bit). Falta `tools/ref/r2.py`: API × API e CLI × CLI, todos os idiomas, relatório com a versão do pacote.
7. **Corpora e ASR (FR-COR-03 a 07, FR-ASR-*).** Corpus automático para todos os idiomas, lista de frequência Leipzig
   (CC BY 4.0, versão fixada por SHA-256), frases imprevisíveis geradas por semente, `whisper.cpp` no CI.
8. **Empacotamento e publicação (F4):** dados de todos os idiomas gerados pelo CI (fora do git), `phsource/` e
   `dictsource/`, `idf_component.yml`, README e traduções (`source-revision`), `AI-USE.md`, exemplo `hello` e
   `waveshare-s3-rlcd`. **Upload de teste ao *staging* do Registro antes de tudo** (OD-02: o `espeak-ng-data` completo
   tem ≈ 24 MB instalado e o Registro não publica limite).

A v0.2 (convivência, os dois modos de `.bss`, comparação de portes, ferramenta guiada de escuta) só abre depois do
portão da v0.1.

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
