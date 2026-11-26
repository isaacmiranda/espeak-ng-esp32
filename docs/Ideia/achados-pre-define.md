# Achados antes do `/define`

Pauta para o `/grill-me` e o `/define`. Todo valor sugerido aqui é `proposed-by-skill` até o responsável aceitar. O
arquivo é temporário: cada item sai quando a FSD o absorve.

Fontes: [`pesquisa-2026-11-26/`](pesquisa-2026-11-26/) (relatório e notas), [`origem-do-porte.md`](origem-do-porte.md),
[`alertalergo-fsd-fala.md`](alertalergo-fsd-fala.md).

## 1. O que ainda não é falseável

| Item da semente | Problema | O que fixar |
|---|---|---|
| "inteligível" | sem método, população nem limiar | método (frases semanticamente imprevisíveis, reconhecimento de palavras, fármacos; nota P.800), nº de ouvintes, critério de acerto, limiar ou só relato |
| "convive com Wi-Fi, BLE e tela" | sem carga definida nem critério | qual carga (SoftAP? scan BLE contínuo? tela atualizando?), e o critério (heap mínima ≥ X, nenhuma perda de áudio, latência ≤ Y) |
| "componente reutilizável" | sem contrato | API pública, o que é configurável (rótulo/subtipo da partição, ponto de montagem, idiomas, pilha, buffer), exemplo mínimo |
| "equivalente ao upstream" | só provado no host | PCM idêntico **no alvo** (hash do PCM entregue ao I2S) para o mesmo conjunto de textos |
| "contribuições ao upstream" | sem escopo | quais: correção da issue #1611, entradas `pt_list` de fármacos com `test_phon`, opções de memória |

## 2. Números que o build vai ler e a semente não declara

| Número | Hoje (porte de partida) | Decidir |
|---|---|---|
| Versão do ESP-IDF | v5.5.5 | manter (compatível com o AlertAlergo) ou seguir a 6.x (o `vtts` exige 6.1.1) |
| Versão do eSpeak NG | 1.52.0 (tarball) | 1.52.0 ou um commit posterior com as correções de fuzzing (PR #2556; issue #2647 aberta) |
| Idiomas nos dados | só pt / pt-BR | só pt-BR na pesquisa; o componente aceita qualquer idioma (lista configurável) |
| Partição de dados | 1 MiB, subtipo 0x40, rótulo `espeak`; imagem 735 910 B (70 %) | tamanho, rótulo e subtipo padrão do componente |
| Onde os dados vivem em uso | copiados para a PSRAM (~736 KB) | manter, ou ler direto da flash mapeada (como o porte `dfxpto-cyber`) — medir os dois |
| `.bss` interna do eSpeak | ~90 KB | opção para mandar à PSRAM (no AlertAlergo era proibido por `SPIRAM_IGNORE_NOTFOUND`; aqui pode ser permitido) |
| Pilha da tarefa de síntese | 64 KB na PSRAM, ~39 KB usados | padrão e mínimo |
| Taxa de amostragem | 22 050 Hz (inferida, não registrada) | registrar no marcador e na FSD |
| Voz | pt-BR, 175 ppm, pitch 50 | parâmetros do estudo (velocidades a testar) |
| Teto de volume de bancada | volume 5 nos testes do AlertAlergo | valor do teto e o volume das sessões de escuta |
| Tabela de partições da placa | a do AlertAlergo (16 MB, OTA, `assets`) | a do firmware de pesquisa (sem OTA? sem `assets`?) |

## 3. Conflitos e lacunas técnicas

1. **Acentos no alvo (issue #1611, hipótese).** No toolchain do ESP32, `iswalpha()` não reconhece letras acentuadas. O
   porte não altera as fontes e o teste de PCM só roda no host; o AlertAlergo passa por isso porque os textos chegam sem
   acento. Texto com acento ("Atenção") pode sair diferente na placa. **Primeiro experimento:** hash do PCM no alvo vs.
   host para textos acentuados. Se confirmar, é a primeira contribuição ao upstream (`ucd_isalpha()`).
2. **GPL completa.** `LICENSE` e REUSE entram no 1º commit deste repositório. Falta decidir como a "fonte correspondente"
   dos dados compilados é entregue: o `gen-espeak.sh` baixa o tarball (reprodutível), mas uma release precisa levar o
   tarball ou `phsource/`+`dictsource/` junto.
3. **Medidas que não existem:** fator de tempo real, tempo até a 1ª amostra, PSRAM usada, tempo de carga dos dados no
   boot, consumo de corrente durante a fala. Só há a estimativa "síntese < metade do tempo real".
4. **Dicionário de fármacos.** `pt_listx` cobre 8 nomes da lista antiga; a lista de 2026-11-16 do AlertAlergo não foi
   conferida (hidroclorotiazida, glibenclamida…). No estudo, a lista de fármacos precisa ser fixada antes da coleta, e
   decidir se o dicionário é parte do componente, do exemplo ou contribuição ao `pt_list` do upstream.
5. **Separar do produto.** O que ainda está acoplado: tarefa/fila/cancelamento no `main.c`; `/es`, rótulo, "AAES" e 1 MiB
   fixos no código e nas flags; o script só copia pt. Tudo isso vira configuração do componente.
6. **Outros portes.** `dfxpto-cyber/eSpeak-NG-.-Esp32` (ESP-IDF, S3, pt-PT, dados na flash, criado em 2026-11-25) é o
   mais próximo; `arduino-espeak-ng` e `BackgroundAudio` são as linhas de base Arduino; `vtts` é o rival neural com
   pt-BR. Decidir: contatar o autor do `dfxpto` antes de publicar no Registro? Quais entram na comparação (mesma placa,
   mesmos textos)?
7. **Estudo com pessoas.** Ouvintes = responsável + bolsistas. Mesmo com a equipe, se o dado for publicado, o protocolo
   provavelmente precisa do CEP (Res. CNS 466/2012 ou 510/2016) — **confirmar com o CEP da instituição**. Separar:
   piloto interno (ajuste do protocolo, sem publicação) × coleta do estudo (após aprovação). Ouvintes cegos ou de baixa
   visão: fase posterior, com parceria a definir.
8. **Bilinguismo.** "Tudo nos dois idiomas": decidir qual é a fonte (pt-BR) e quando a tradução acompanha (a cada
   portão? a cada release?), e se a FSD inteira ou só um resumo vai para o inglês.
9. **Placa compartilhada.** Toda sessão regrava; a evidência registra o firmware deixado. A placa com firmware do
   AlertAlergo fala sozinha perto de pulseiras: medições de áudio exigem regravar antes.
10. **Uso de IA e JOSS.** O JOSS pede 6 meses de histórico público e declaração do uso de IA, e diz que gerar código por
    prompts "não constitui necessariamente" a contribuição acadêmica: as decisões humanas (protocolo, escolhas de
    projeto) precisam ficar visíveis na FSD e nos commits.

## 4. Propostas para as duas perguntas do `/harness`

### Agenda de depuração

| Parte | Não comprovada porque | Comprovada por |
|---|---|---|
| Bancada (driver, link udev, `bench.yaml`) | não existe ainda | testes do driver na porta falsa + `bench discover` encontra `dut` |
| A placa neste projeto | só foi vista com o firmware do AlertAlergo | `bench chip-info dut` (S3, 16 MB, PSRAM, MAC) e o boot do firmware de pesquisa |
| Caminho CI → gravação | o CI deste repositório não existe | artefato do CI gravado com `bench flash` e o marcador de boot visto |
| Partição de dados do eSpeak | nunca gravada a partir deste repositório | marcador de dados válidos (CRC) no boot |
| Saída de áudio (ES8311/I2S) | idem | tom de teste no volume de bancada + marcador de fim |
| Captura do PCM no alvo | *seam* não existe | hash do PCM de um texto conhecido igual ao do host |

### Jornada (uma execução comum, ponta a ponta)

1. Gravar o artefato do CI (app + dados) → marcador de boot com a versão.
2. Dados do eSpeak válidos → `SPEECH ready=1`.
3. `bench command dut "speech say <texto de referência>"` → `SPEECH start` e `SPEECH done` com duração e `heap_min`.
4. Hash do PCM do texto de referência igual ao do host.
5. Repetir com carga de convivência ligada → mesmos marcadores, heap mínima acima do limiar da FSD.

## 5. Calendário que restringe decisões (do relatório)

- JOSS: a partir de ~jun./2027 (6 meses de repositório público).
- SBESC 2027 (artigo de sistemas, 6 páginas IEEE) e SBCAS 2027/2028 (estudo com ouvintes): chamadas ainda não
  publicadas — conferir.
- CEP: meses entre submissão e aprovação; submeter cedo se o estudo entra num artigo de 2027.
