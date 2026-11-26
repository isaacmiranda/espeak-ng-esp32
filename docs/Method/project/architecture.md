# Arquitetura (COMO)

Proposta de partida, a confirmar no `/define`. O comportamento observável está na FSD; aqui está só o que não
sobreviveria a uma reescrita.

## Camadas, com fronteira por posse

| Camada | Conteúdo | Posse | Muda quando |
|---|---|---|---|
| **L0 motor** | eSpeak NG do tarball fixado, sem alteração (só o motor síncrono compilado); dados compilados pelo `espeak-ng` do mesmo tarball | upstream (espeak-ng) | a versão fixada sobe |
| **L1 componente** | Adaptação ao ESP-IDF: `CMakeLists`/`config.h`, imagem de dados com cabeçalho e CRC numa partição, VFS somente leitura, tarefa de síntese (pilha na PSRAM, cancelamento, fatias), interface de saída de áudio | este repositório; é o que vai ao Registro de Componentes | o ESP-IDF ou o contrato da API muda |
| **L2 aplicação de pesquisa** | Firmware de medição e de sessão de escuta: console de teste, telemetria, saída de áudio pela placa de referência (ES8311/I2S), cargas de convivência (Wi-Fi/BLE/tela); ferramentas do PC (`tools/bench/`, montagem do material de escuta, análise) | este repositório | o estudo ou a bancada muda |

Regra de dependência: L2 → L1 → L0. L1 não conhece a placa: a saída de áudio é uma interface que a L2 implementa. Nada
deste repositório edita as fontes de L0.

## Seams que dão os níveis baratos

| Seam | Permite | Nível |
|---|---|---|
| fonte de dados (partição no alvo, diretório no host) | as mesmas fontes rodam no PC com os mesmos dados | host |
| interface de saída de áudio | capturar o PCM no host e, no alvo, o PCM entregue ao I2S | host, target |
| tempo como parâmetro / marcadores com tempo | medir latência e fator de tempo real sem cronômetro manual | target |
| ponto de falha no firmware de teste | falta de memória, dados corrompidos, cancelamento | target |

## Organização de pastas (proposta)

```
components/espeak-ng/       L0 + L1: upstream/ intocado, config/, data/ gerado, CMakeLists, idf_component.yml
components/<l1 adaptação>/  se o /define separar VFS e tarefa de síntese do pacote do motor
examples/                   exemplo mínimo para o Registro de Componentes
firmware/                   L2: aplicação de pesquisa para a placa de referência
tools/bench/                driver de bancada: python -m bench <comando>
tools/listening/            material e coleta do estudo (sem dado de participante)
tests/host/ tests/target/ tests/bench/
testing/                    test-plan.yaml, debugging-agenda.md, gates/ (gerados pelo /harness)
seed/alertalergo-port/      evidência de partida; sai quando a FSD e o código a absorverem
```
