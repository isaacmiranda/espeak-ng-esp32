# Padrão — Testes

Teste faz parte do contrato de construção. Toda regra de comportamento da FSD é verificável, e toda mudança traz o teste
que a prova.

## Níveis

Use o nível mais barato que pode pegar a falha. A "lei de posição": um comportamento é testado **no nível mais baixo
onde o defeito que ele pega pode se manifestar**. O nível mora no **teste**, nunca na coluna do requisito nem no id.

| Nível | Roda em | Velocidade | Pega |
|---|---|---|---|
| **host** | PC: as mesmas fontes do eSpeak NG compiladas com CMake; `pytest` | ms a s, a cada commit | PCM idêntico ao upstream, fonemas fixados, montador da imagem de dados, texto → normalização, contratos de build (tamanho, símbolos). |
| **target** | A placa (`bench flash` + `bench wait-event`) | segundos, antes do merge | Leitura da partição, PSRAM, pilha, watchdog, tempo até o 1º áudio, fator de tempo real, heap mínima, PCM no aparelho igual ao do host. |
| **bench** | A placa com carga de convivência (Wi-Fi, BLE, tela) e captura de áudio, se a FSD pedir | minutos, antes da liberação | Ponta a ponta: fala sob carga de rádio e tela, sequências longas, reinício no meio da fala. |
| **listening** | Pessoas ouvindo a placa, sob o protocolo do estudo | sessões agendadas | Só o que um ouvinte decide: reconhecimento de palavras e de fármacos, nota de qualidade. |

Não há nível `sim`: o produto é um dispositivo só.

### O nível `listening` é outro tipo de evidência

Nos outros níveis, **observação é de instrumento**: nenhum passo depende de uma pessoa ler um valor a olho. No
`listening`, a percepção humana **é** a medida, por desenho. Por isso:

- o protocolo (material, ordem, número de ouvintes, critério de acerto, análise) está fixado **antes** da coleta e mora
  na FSD (o quê) e no manual (como aplicar); mudar o protocolo depois de começar a coleta invalida a coleta;
- o áudio tocado é o do **artefato do CI** de um commit registrado, no volume e na posição fixados;
- a resposta do ouvinte é registrada por ferramenta (formulário ou arquivo estruturado), nunca resumida de memória;
- com participantes de fora da equipe, só depois da aprovação do protocolo pelo CEP; dado identificável nunca entra no
  git (fica fora do repositório, com o identificador pseudônimo);
- um teste automático (PCM, fonema) **nunca** substitui um resultado de `listening`, e vice-versa.

## Regras

- **Toda regra Must/Should tem caso de teste.** Regra sem caso aparece como lacuna.
- **Toda mudança traz o seu teste.** Defeito escreve o teste de regressão **primeiro**, e ele falha antes da correção.
- **Os casos remetem a ids de requisito**; a cobertura é **gerada**, nunca mantida à mão.
- **Máquinas de estado são cobertas por transição**, não por estado.
- **Falha esperada para o ausente.** O caso especificado e ainda não construído é `xfail` com a pré-condição declarada.
- **Bancada fora do ar é `not done`, nunca `failed`.** Notebook sem a placa, placa com o firmware de outro projeto não
  regravado, ou driver falhando é pré-condição não atendida.
- **Nada de previsão.** Um teste que você tem certeza que vai falhar continua `not done` até rodar.
- **Referência externa, não autorreferência.** O PCM e os fonemas do porte são comparados com o eSpeak NG do upstream
  compilado no host a partir do mesmo tarball, nunca só com o que o próprio porte produziu antes.
- **A suíte está verde antes do commit.**
- **Volume de bancada.** Teste automático com som roda no teto de volume de [`../project/bancada.md`](../project/bancada.md).

## Controlabilidade na bancada (sem instrumentos de laboratório)

| Falha ou estado | Como se provoca | Instrumento |
|---|---|---|
| Dados da partição ausentes ou corrompidos | gravar imagem com CRC errado ou apagar a partição (`bench flash`) | driver |
| Falta de memória | *seam* de alocação no firmware de teste | firmware |
| Carga de rádio (Wi-Fi/BLE) | firmware de teste liga SoftAP/scan BLE por comando | `bench command` |
| Cancelamento no meio da fala | `bench command` em instante medido pela telemetria | driver |
| Reinício no meio da fala | `bench reset dut` | driver |
| Texto patológico (longo, acentuado, comandos embutidos) | `bench command` com o texto | driver |
| Qualidade percebida | **não instrumentável**: só `listening` | pessoas, sob protocolo |
| Áudio no ar (o que sai do alto-falante) | **não instrumentável** sem microfone de medição; o PCM entregue ao I2S é observável por *seam* | firmware (*seam*) |

## Segurança

Entrada externa da biblioteca é o texto. Casos de segurança: texto longo, caracteres inválidos em UTF-8, comandos
embutidos do eSpeak (SSML/«\x01») — ancorados em CWE (estouro de buffer: CWE-120/787) e nas correções de fuzzing do
upstream posteriores à 1.52.0.
