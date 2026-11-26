# espeak-ng-esp32 — Especificação Funcional (FSD)

```yaml
document_status: approved
fsd_version: 0.2.0
repository: https://github.com/isaacmiranda/espeak-ng-esp32
baseline_commit: fc1d08a
applicable_firmware_version: nenhuma (antes da Fase 3)
author: Isaac Miranda (responsável); redação assistida por IA (AI-USE.md)
reviewers: Isaac Miranda
approval_status: approved (Isaac Miranda, 2026-11-26)
created: 2026-11-26
last_updated: 2026-11-26
change_history:
  - 0.1.0 (2026-11-26): primeira versão, a partir de docs/Ideia/ e do /grill-me de 2026-11-26; valores propostos aceitos pelo responsável no mesmo dia
  - 0.1.1 (2026-11-26): FR-RES-15 e FR-RES-16 usam `ESPK error code=…`, no formato do FR-LOG-01 (achado do /commission)
  - 0.2.0 (2026-11-26): ferramenta guiada de escuta (FR-LST-07 a FR-LST-19, NFR-LST-01), pedido do responsável;
    cada item tocado uma única vez, sem repetição (decisão do responsável)
superseded_requirements: []
open_decisions: ver open-issues.md (cada item nomeia o requisito que bloqueia)
related_test_baseline: testing/test-plan.yaml (criado no /harness)
```

**Como ler.** A FSD diz **o que precisa ser verdade**. Cada requisito tem um ID estável, uma prioridade (**Must**,
**Should**, **May**), uma origem e um marco:
- **Origem:** `[user]` é uma decisão do responsável, inclusive valores propostos pelo assistente e aceitos no grill.
  `[derived]` é consequência de outro requisito aprovado. `[seed:alertalergo]` vem do porte de partida.
  `[pack:esp32]` veio do pacote de domínio e foi aceito. `[lit:<fonte>]` vem da literatura.
- **Situação:** o sufixo **`· proposto`** marca um valor sugerido pelo assistente que ainda espera o aceite do
  responsável. Os demais requisitos estão aprovados.
- **Marco:** v0.1, v0.2 ou futuro (§3).

Cada Must e Should carrega um **contrato de verificação**: em tabela compacta, ou em YAML completo quando um sistema
quebrado poderia passar por engano. A coluna "Não pode acontecer" é obrigatória. Os níveis de teste (`host`, `target`,
`bench`, `listening`, `other`) estão no [padrão de testes](../Method/standards/testing.md). `other` cobre a revisão
humana de um ato fora do código.

---

## 1. Visão geral

### 1.1 Propósito

O projeto entrega o **eSpeak NG 1.52.0 como componente nativo de ESP-IDF**, de **uso geral** e livre. Ele segue a
filosofia do próprio eSpeak: serve a qualquer aplicação, em qualquer idioma que o upstream suporte, e roda em qualquer
chip da família ESP32 que tenha PSRAM. O integrador escolhe os idiomas, e o build diz se a escolha cabe na
plataforma. As fontes do upstream não são alteradas, e o PCM produzido é provado igual ao do upstream.

O repositório também é uma **plataforma de pesquisa**. Ele mede o componente no aparelho (memória, latência, tempo
real, convivência com Wi-Fi, BLE e tela) e estima a inteligibilidade da fala por reconhecimento automático. O estudo
com ouvintes é preparado desde já e acontece depois, com aprovação do CEP.

### 1.2 Usuários

| Quem | O que precisa |
|---|---|
| **Integrador** (qualquer desenvolvedor ESP-IDF, de qualquer país) | adicionar a fala a um projeto, escolher idiomas, saber antes de gravar se cabe |
| **Equipe de pesquisa** (responsável e bolsistas) | medições reprodutíveis a partir do artefato do CI; escuta interna para ajustar a fala |
| **Contribuidor** (inclusive estrangeiro) | entender o contrato, rodar os testes, propor idiomas e chips |
| **Upstream** (eSpeak NG, Registro de Componentes da Espressif) | correções com teste; um pacote que cumpre as regras do Registro |
| **Futuro estudo com pessoas** (baixa visão, baixa audição) | instrumento de escuta pronto e protocolo aprovado pelo CEP |

### 1.3 Prioridades

1. A **biblioteca de fala** (o componente) é o centro. Seus portões bloqueiam a release.
2. Wi-Fi, BLE e tela são acessórios do firmware de pesquisa. Servem aos estudos da equipe e não bloqueiam a v0.1.
3. Idiomas: **pt-BR** primeiro, foco da pesquisa e verificado no alvo; **en** em segundo, também verificado no alvo.
   Os demais idiomas são cobertos pelo que a automação alcança e pelo que contribuidores trouxerem.

### 1.4 Fora do escopo

- Alterar as fontes do eSpeak NG. Correções vão ao upstream (§17).
- Driver de áudio no componente: o PCM sai por callback, e o I2S e o codec são do integrador.
- Normalização de texto específica de produto, como passar para minúsculas ou expandir siglas de domínio.
- Dicionário de fármacos e qualquer vocabulário clínico. A lista herdada do AlertAlergo não é referência deste
  projeto.
- Chips sem PSRAM (ESP32-C2, C3, C6, H2).
- MBROLA, Klatt, sonic e o modo assíncrono do upstream. Só o motor síncrono é compilado.
- Reamostragem no componente.
- Atualização da partição de dados por OTA (futuro; o formato da imagem já leva versão e CRC).
- Mecanismo de transporte de OTA do firmware de pesquisa. As partições existem, e o transporte é uma decisão aberta.
- Estudo com participantes de fora da equipe antes da aprovação do protocolo pelo CEP.
- Publicar taxas de acerto ou notas de qualidade vindas de ouvintes humanos antes desse estudo.
- Comparação com o `vtts`, a não ser por emenda; tráfego Wi-Fi com cliente (`iperf`); medida de corrente.
- Pacote de domínio ESP32, biblioteca **NVS**: recusada, porque o componente não usa NVS.

### 1.5 Fluxo principal

```
texto UTF-8 ──► espk_synth() / espk_say() ──► motor eSpeak NG (fontes intactas)
                                                 │ lê dados por fopen/fread
                                                 ▼
                     VFS somente leitura /espeak ◄── partição "espeak" (imagem com cabeçalho e CRC)
                                                 │
                     PCM 16 bits mono 22 050 Hz ◄┘ ──► callback do integrador ──► I2S/codec (fora do componente)
```

---

## 2. Arquitetura

### 2.1 Arquitetura lógica

| Subsistema | Papel |
|---|---|
| **Componente `espeak-ng`** | motor intacto, imagem de dados, VFS, API síncrona e camada assíncrona, gerador de imagem e relatório de capacidade |
| **Exemplos** | `hello` (sem áudio, qualquer chip) e `waveshare-s3-rlcd` (ES8311) |
| **Firmware de pesquisa** | console de teste, marcadores, captura de PCM, perfis de carga, sessão de escuta |
| **Ferramentas do PC** | referências R1 e R2, corpora, ASR, driver de bancada `python -m bench` |
| **CI** | runner hospedado (host, builds, ASR, pacote) e runner do notebook (só em tag, níveis com placa) |

### 2.2 Plataforma

Estes números são lidos pelo build. Cada um é uma restrição.

| Item | Valor | Origem |
|---|---|---|
| Placa de referência | Waveshare ESP32-S3-RLCD-4.2 | [user] |
| Chip | ESP32-S3 | [user] |
| Flash da placa de referência | 16 MB | [seed:alertalergo] (confirmação por `bench chip-info` no `/commission`) |
| PSRAM da placa de referência | 8 MB (assumed: módulo N16R8; confirmação por `bench chip-info`) | [seed:alertalergo] |
| Codec de áudio | ES8311 por I2S | [seed:alertalergo] |
| ESP-IDF do firmware de pesquisa e dos exemplos | v5.5.5 | [user] |
| ESP-IDF declarado pelo componente | `>=5.5` | [user] |
| ESP-IDF verificado só por build | uma versão 6.x fixada no CI (a última 6.x estável na data do `/harness`) | [user] |
| eSpeak NG | 1.52.0, tarball com SHA-256 `bb4338102ff3b49a81423da8a1a158b420124b055b60fa76cfb4b18677130a23` | [user] [seed:alertalergo] |
| Taxa de amostragem esperada | 22 050 Hz | [user] |
| Tamanho do `espeak-ng-data` completo | ≈ 24 MB instalado (pacote Ubuntu `espeak-ng-data` 1.52.0); o valor exato da nossa imagem é medido pelo gerador | [derived] |

**Tabela de partições do firmware de pesquisa** (flash de 16 MB), [user]:

| Nome | Tipo | Subtipo | Tamanho |
|---|---|---|---|
| `nvs` | data | nvs | 24 KB |
| `otadata` | data | ota | 8 KB |
| `phy_init` | data | phy | 4 KB |
| `ota_0` | app | ota_0 | 3 MB |
| `ota_1` | app | ota_1 | 3 MB |
| `espeak` | data | `0x40` | o restante da flash (≈ 9,9 MB) |

Os deslocamentos são os que o `gen_esp32part.py` calcula a partir dessa ordem, com alinhamento de 64 KB nas
partições `app`. A imagem com todos os idiomas não cabe na placa de referência. A placa verifica subconjuntos, e o
host verifica todos os idiomas (§7).

### 2.3 Arquitetura de software

- **Motor:** só o runtime síncrono do eSpeak NG, chamado de dentro do componente.
- **Dados:** uma imagem com cabeçalho, tabela de arquivos e CRC32 numa partição. Um VFS somente leitura, montado em
  `/espeak`, deixa o `fopen` e o `fread` do upstream lerem a flash mapeada. O upstream copia os arquivos com `malloc`
  (`synthdata.c:92`, `dictionary.c:231`), e essa cópia vai para a PSRAM.
- **Tarefa:** a camada assíncrona tem uma tarefa FreeRTOS própria, com pilha configurável e permitida na PSRAM, e uma
  fila de pedidos.
- **Boot:** a aplicação chama `espk_init()`. O componente monta os dados, valida o CRC e a versão, inicializa o motor
  e seleciona a voz inicial.
- **Persistência:** nenhuma. O componente não escreve na flash.

### 2.4 Camadas

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ L2  Aplicação de pesquisa e ferramentas                                       │
│     firmware de pesquisa · perfis de carga · exemplos · R1/R2 · corpora · ASR │
├───────────────────────────────────────────────────────────────────────────────┤
│ L1  Componente espeak-ng (posse deste repositório; vai ao Registro)           │
│     imagem/partição/VFS · idiomas e capacidade · núcleo síncrono ·            │
│     camada assíncrona · colocação de memória                                  │
├───────────────────────────────────────────────────────────────────────────────┤
│ L0  Fundação (usada e configurada, não escrita aqui)                          │
│     motor eSpeak NG 1.52.0 intacto · ESP-IDF (partições, VFS, PSRAM, FreeRTOS)│
└───────────────────────────────────────────────────────────────────────────────┘
```

Dependência em sentido único: L2 → L1 → L0. A L1 não conhece placa nem codec: o PCM sai por callback. A organização
de pastas que espelha as camadas está no Método ([`architecture.md`](../Method/project/architecture.md)).

---

## 3. Fases e marcos

O calendário conta a partir de 2026-11-26 [user]. Cada fase só começa com o que as anteriores entregaram.

### 3.1 Fase F1 — Fundação

- **Escopo:** reprodução do motor e da referência R1 no host; firmware de pesquisa mínimo, derivado da semente, com
  console, marcadores e hash de PCM; bancada comissionada.
- **Entregas:** script de regeneração do upstream (§17); R1 no host (§7); firmware mínimo que fala e emite
  `ESPK done … sha256=` (§5); driver e bancada (Fases 1–2 do método).
- **Saída:** `bench flash` grava o artefato do CI; `ESPK boot` e `ESPK ready` aparecem; um texto de referência dá
  `ESPK done` com hash.
- **Depende de:** nada.
- **Alvo:** dez./2026.

### 3.2 Fase F2 — Equivalência no alvo

- **Escopo:** o primeiro experimento. Compara R3 com R1 sobre o corpus de verificação pt-BR e en, e decide o wrap
  da #1611 (§17).
- **Entregas:** relatório de equivalência; FR-ENG-04 e FR-ENG-05 decididos; corpus de verificação (§8).
- **Saída:** FR-REF-03 verde para pt-BR e en, com ou sem wrap, conforme o resultado registrado.
- **Depende de:** F1 (firmware com hash, R1).

### 3.3 Fase F3 — Componente

- **Escopo:** extração do componente genérico.
- **Entregas:** a Parte B inteira; o exemplo `hello`; R2 (§7); o firmware de pesquisa completo (§5) sobre o
  componente.
- **Saída:** os requisitos da Parte B, de §5 e de §7 com marco v0.1 verdes; o firmware de pesquisa usa o componente.
- **Depende de:** F2 (decisão do wrap; corpus).

### 3.4 Fase F4 — Release v0.1.0

- **Escopo:** publicação.
- **Entregas:** exemplo `waveshare-s3-rlcd`; corpus de escuta (§8); instrumento de escuta (§10); ASR no CI (§9); documentação nos dois idiomas (§26); pacote no Registro
  (§25); contato com o `dfxpto` (§25); PR da #1611, se aplicável (§17); `AI-USE.md`.
- **Saída:** todo requisito Must e Should com marco v0.1 verde; jornada verde nos bytes publicados.
- **Depende de:** F3.
- **Alvo:** jan.–fev./2027.

### 3.5 Fase F5 — v0.2.0

- **Escopo:** pesquisa de engenharia.
- **Entregas:** perfis de convivência e seus portões (§6); medidas nos dois modos de `.bss` (§16); comparação com
  outros portes (§7); escuta interna com a ferramenta guiada (§10); entradas candidatas ao `pt_list` do upstream (§25).
- **Saída:** requisitos com marco v0.2 verdes.
- **Depende de:** F4.
- **Alvo:** 1º semestre de 2027.

### 3.6 Futuro

- Estudo com pessoas de baixa visão e de baixa audição, com protocolo aprovado pelo CEP. É aberto por emenda.
- Ligação da ferramenta de escuta com a placa pela rede local (FR-LST-19, OD-05).
- Migração para o eSpeak NG 1.53 quando ela sair (FR-ENG-06).
- OTA da partição de dados; transporte de OTA do firmware de pesquisa.
- Publicações: SBESC 2027, quando sair a chamada; JOSS a partir de ~2027-05-26, seis meses depois do primeiro commit
  público (`6b98659`).

---

## 4. Riscos, premissas e dependências

### 4.1 Riscos

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| `iswalpha` da newlib não reconhece letras acentuadas (#1611): o PCM no alvo diverge do host | alta | alto | F2 primeiro; wrap no link (FR-ENG-04); PR upstream (FR-UPS-01) |
| `libm` da newlib e da glibc divergem em ponto flutuante (`wavegen.c`, `setlengths.c`) | média | alto | F2 investiga; emenda decide tolerância medida ou correção (FR-REF-04) |
| RTF passa de 0,5 com a `.bss` na PSRAM | média | médio | medir os dois modos (FR-MEM-03); emenda do limiar ou do padrão |
| Pacote do Registro grande demais com todos os idiomas e as fontes | média | médio | upload de teste no *staging* (OD-02); alternativa: pacote base mais pacotes de idioma |
| Pacote Debian (`+dfsg`, patches) diverge do tarball | média | baixo | R2 registra a causa, sem falhar o build (FR-REF-06) |
| Defeitos de memória do upstream (#2647) com texto hostil | média | alto | perfil de segurança (§22); limite de tamanho do texto; seguir a 1.53 |
| ASR erra pt-BR por limitação do modelo, não da fala | alta | médio | ASR só como estimativa relativa (por velocidade e por condição), nunca como inteligibilidade; ressalva escrita (FR-ASR-05) |
| Placa compartilhada com firmware do AlertAlergo, que fala sozinho | alta | médio | regravar antes de medir; registrar o firmware encontrado e o deixado (§27) |
| Notebook de 3,4 GB e HDD lento | alta | médio | builds com prioridade baixa e 2 jobs; ASR só no CI |
| Fragmentação com o `dfxpto` | média | baixo | contato antes da publicação (FR-REL-05) |

### 4.2 Premissas

- O módulo da placa de referência tem 8 MB de PSRAM (assumed, confirmado no `/commission`).
- O pacote `espeak-ng` do Ubuntu 26.04 é 1.52.0 (`1.52.0+dfsg-5build1`), conferido em 2026-11-26.
- O runner hospedado do GitHub Actions é gratuito para repositório público e tem memória para rodar o ASR.

### 4.3 Dependências externas

- Tarball do eSpeak NG 1.52.0 no GitHub (SHA-256 fixado).
- Leipzig Corpora Collection, lista de frequência pt-BR, CC BY 4.0 [user].
- `whisper.cpp` e um modelo Whisper multilíngue, ambos com versão e hash fixados (§9).
- ESP Component Registry, que aceita pacotes GPL [lit:relatorio-2026-11-26].

---

# Parte A — Aplicação de pesquisa e ferramentas (L2)

## 5. Firmware de pesquisa: console e telemetria

### 5.1 Propósito

É a aplicação da placa de referência que deixa o driver de bancada medir o componente: recebe comandos por uma linha
de console na USB-Serial/JTAG e emite marcadores de uma linha. Toda medição de placa passa por aqui.

### 5.2 Requisitos

- **FR-RES-01** [Must · user · v0.1] No boot, o firmware deve emitir uma linha
  `ESPK boot fw=<versão> commit=<sha curto> idf=<versão> espeak=<versão> rate=<Hz> bss=<internal|psram> langs=<lista> init_ms=<n>`.
- **FR-RES-02** [Must · derived · v0.1] Com dados válidos, o firmware deve emitir `ESPK ready` depois de
  `ESPK boot` e antes de aceitar qualquer comando de fala.
- **FR-RES-03** [Must · user · v0.1] O comando `say <texto>` deve sintetizar o texto e emitir
  `ESPK done id=<n> samples=<n> synth_ms=<n> first_ms=<n> audio_ms=<n> heap_min=<B> sha256=<hex>`, em que `sha256` é
  o SHA-256 dos bytes PCM entregues pelo callback, em ordem.
- **FR-RES-04** [Must · derived · v0.1] O comando `say` deve aceitar a opção `--mute`. Com ela, o PCM é só
  calculado e resumido no hash, sem ir ao I2S. O hash é igual com e sem `--mute`.
- **FR-RES-05** [Must · user · v0.1] O comando `voice <nome>` deve trocar a voz e responder `ESPK voice ok=<nome>`. Um
  nome ausente da imagem deve responder `ESPK voice err=not_found`.
- **FR-RES-06** [Must · user · v0.1] O comando `rate <ppm>` deve ajustar a velocidade e responder `ESPK rate ok=<ppm>`.
- **FR-RES-07** [Must · user · v0.1] O comando `volume <0–100>` deve recusar valores acima de **10** com
  `ESPK volume err=ceiling` quando não houver sessão de escuta aberta.
- **FR-RES-08** [Must · user · v0.1] O volume padrão depois do boot deve ser **5**.
- **FR-RES-09** [Must · user · v0.1] O comando `listen open <volume>` deve abrir uma sessão de escuta e permitir
  volumes de 0 a 100 até `listen close` ou o próximo reinício.
- **FR-RES-10** [Must · user · v0.1] O comando `cancel` deve cancelar a fala em curso e esvaziar a fila. O firmware
  responde `ESPK cancelled id=<n>` para a fala interrompida.
- **FR-RES-11** [Must · derived · v0.1] Com a camada assíncrona, o comando `say` deve responder `ESPK start id=<n>`
  antes de `ESPK done`, e o console continua aceitando `cancel` durante a fala.
- **FR-RES-12** [Must · user · v0.1] O firmware deve contar os *underruns* do I2S durante cada fala e incluí-los em
  `ESPK done … underrun=<n>`.
- **FR-RES-13** [Must · derived · v0.1] O comando `info` deve responder uma linha com as versões, a taxa de
  amostragem, o tamanho e o CRC da imagem, os idiomas presentes e a voz atual.
- **FR-RES-14** [Must · derived · v0.1] O comando `mem` deve responder a heap interna livre, a mínima desde o boot,
  a PSRAM livre e a mínima desde o boot, em bytes.
- **FR-RES-15** [Must · user · v0.1] Uma linha de comando desconhecida deve receber `ESPK error code=unknown_command`, sem
  efeito na fala em curso.
- **FR-RES-16** [Should · user · v0.1] O firmware deve aceitar textos de até 1 024 bytes por `say` e responder
  `ESPK error code=too_long` acima disso (1 024).

### 5.3 Contratos

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-RES-01 | artefato do CI gravado · `bench reset` | linha `ESPK boot` com todos os campos; `commit` = commit do artefato | campo ausente; commit de outro build | target |
| FR-RES-02 | idem | `ESPK ready` depois de `ESPK boot`; `say` antes de `ready` recusado | `ready` com dados corrompidos | target |
| FR-RES-03 | `ready` · `say` com texto do corpus | `ESPK done` com os campos; `samples` > 0 | `sha256` calculado sobre buffer que não é o entregue ao callback | target |
| FR-RES-04 | `ready` · `say --mute T` e `say T` | hashes iguais; nada no I2S com `--mute` | hashes diferentes | target |
| FR-RES-05 | imagem com `pt` e `en` · `voice en`, `voice xx` | `ok=en`; `err=not_found` | travamento; voz anterior perdida após o erro | target |
| FR-RES-06 | `ready` · `rate 220` e `say` | `ok=220`; `audio_ms` menor que a 175 ppm para o mesmo texto | `rate` ignorado | target |
| FR-RES-07 | sem sessão · `volume 11` | `err=ceiling`; volume inalterado | volume aplicado | host (parser) · target |
| FR-RES-08 | boot | `info` mostra volume 5 | outro valor | target |
| FR-RES-09 | `listen open 60` · `volume 60` · `listen close` · `volume 60` | aceito dentro da sessão; recusado depois | sessão sobrevivendo ao reinício | target |
| FR-RES-10 | fala longa em curso e mais duas na fila · `cancel` | `ESPK cancelled` em ≤ 100 ms; a fila não fala | as falas da fila tocam | target |
| FR-RES-11 | `say` longo | `start` antes de `done`; `cancel` aceito no meio | console bloqueado durante a fala | target |
| FR-RES-12 | `say` | campo `underrun` presente | campo ausente | target |
| FR-RES-13 | `ready` · `info` | campos completos e coerentes com `ESPK boot` | divergência com o boot | target |
| FR-RES-14 | `mem` | quatro números em bytes | campos ausentes | target |
| FR-RES-15 | `xyzzy` | `ESPK error code=unknown_command`; a fala em curso continua | reinício; cancelamento | host (parser) · target |
| FR-RES-16 | `say` com 1 024 e com 1 025 bytes | o primeiro fala; o segundo recebe `ESPK error code=too_long` | estouro; reinício | target |

## 6. Perfis de carga e convivência

### 6.1 Propósito

Mede o componente com rádios e tela ligados. É o material do artigo de sistemas. **Não bloqueia a v0.1 do
componente** [user].

### 6.2 Perfis [user]

| Perfil | Carga |
|---|---|
| `idle` | só a fala |
| `wifi` | SoftAP no ar e varredura de Wi-Fi a cada 2 s |
| `ble` | advertising mais varredura BLE contínua (NimBLE) |
| `display` | tela redesenhada pelo LVGL a 10 quadros/s |
| `all` | `wifi` + `ble` + `display` |

### 6.3 Requisitos

- **FR-LOAD-01** [Must · user · v0.2] O comando `load <perfil>` deve ligar o perfil e responder
  `ESPK load ok=<perfil>`. O perfil vale até o próximo `load` ou o próximo reinício.
- **NFR-LOAD-01** [Must · user · v0.2] No perfil `all`, durante a fala do corpus de verificação pt-BR, a heap interna
  mínima (`heap_min`) deve ficar em ≥ 24 576 B.
- **NFR-LOAD-02** [Must · user · v0.2] Em cada perfil, a fala do corpus de verificação pt-BR deve terminar com
  `underrun=0` em todas as falas.
- **NFR-LOAD-03** [Must · user · v0.2] No perfil `all`, o RTF (`synth_ms` / `audio_ms`) de cada fala do corpus de
  verificação pt-BR a 175 ppm deve ser ≤ 0,5.
- **NFR-LOAD-04** [Must · user · v0.2] No perfil `all`, o tempo até a primeira amostra (`first_ms`) deve ser
  ≤ 300 ms para cada frase do corpus de verificação pt-BR com até 20 palavras.
- **NFR-LOAD-05** [Must · user · v0.2] No perfil `display`, nenhum intervalo entre quadros deve passar de 200 ms
  durante a fala. O firmware emite `ESPK display frame_gap_max_ms=<n>` ao fim de cada fala.
- **NFR-LOAD-06** [Must · user · v0.2] No perfil `all`, 50 falas seguidas do corpus devem terminar sem reinício e sem
  disparo do watchdog.

### 6.4 Contratos

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-LOAD-01 | `ready` · `load all` | `ok=all`; SoftAP visível; varredura BLE ativa | perfil aplicado parcialmente sem erro | bench |
| NFR-LOAD-01 | `load all` · corpus pt-BR | menor `heap_min` ≥ 24 576 B | qualquer fala abaixo; reinício | bench |
| NFR-LOAD-02 | cada perfil · corpus pt-BR | `underrun=0` em todas | qualquer *underrun* | bench |
| NFR-LOAD-03 | `load all` · corpus pt-BR a 175 ppm | RTF ≤ 0,5 em cada fala | média escondendo uma fala acima | bench |
| NFR-LOAD-04 | `load all` · frases ≤ 20 palavras | `first_ms` ≤ 300 em cada uma | medir a partir do fim da síntese | bench |
| NFR-LOAD-05 | `load display` · corpus | `frame_gap_max_ms` ≤ 200 | linha ausente; tela congelada | bench |
| NFR-LOAD-06 | `load all` · 50 falas | 50 `done`; contador de boot inalterado | reinício; `cancelled` espúrio; watchdog | bench |

## 7. Referências e equivalência

### 7.1 Propósito

Prova que o porte não altera o motor. Há três referências [user]:

| Ref. | Fonte | Critério |
|---|---|---|
| **R1** | upstream 1.52.0 compilado no host a partir do mesmo tarball pelo script deste repositório | bit a bit; portão |
| **R2** | `espeak-ng` do sistema (pacote do Ubuntu), `espeak-ng --stdout` e `espeak-ng -x -q` | bit a bit esperado; divergência analisada e registrada, sem falhar o build |
| **R3** | PCM entregue pelo callback na placa | bit a bit contra R1; portão |

### 7.2 Requisitos

- **FR-REF-01** [Must · user · v0.1] A ferramenta R1 deve produzir, para cada item de um corpus e cada idioma, o
  SHA-256 do PCM e a transcrição fonêmica (`-x`) do upstream compilado no host.
- **FR-REF-02** [Must · user · v0.1] Com o componente compilado no host (mesmas fontes, mesmos dados, mesma
  configuração de voz), o SHA-256 do PCM de cada item do corpus de verificação deve ser igual ao de R1.
- **FR-REF-03** [Must · user · v0.1] Na placa, o SHA-256 do PCM (R3) de cada item do corpus de verificação pt-BR e en
  deve ser igual ao de R1.
- **FR-REF-04** [Must · user · v0.1] Uma divergência entre R3 e R1 que não seja explicada pelo defeito da #1611 deve
  ser registrada com o item, o primeiro índice de amostra divergente, a diferença máxima por amostra e a SNR, e deve
  bloquear a release até uma emenda desta FSD decidir o critério.
- **FR-REF-05** [Must · user · v0.1] A ferramenta R2 deve comparar, para cada idioma da imagem, a transcrição
  fonêmica e o SHA-256 do PCM de R1 com os do `espeak-ng` do sistema, e registrar a versão do pacote do sistema no
  relatório.
- **FR-REF-06** [Must · user · v0.1] Uma divergência em R2 deve gerar uma linha no relatório com o idioma, o item, o
  tipo (fonemas, PCM ou ambos), a diferença máxima por amostra, a SNR e a causa atribuída, sem falhar o build.
- **FR-REF-07** [Must · user · v0.1] R1 e R2 devem rodar para **todos** os idiomas do upstream, com o corpus
  automático de §8 (FR-COR-03), no CI hospedado.
- **FR-REF-08** [Should · user · v0.2] O relatório de comparação de portes deve medir, na placa de referência e com o
  corpus de verificação pt-BR: este componente, o `dfxpto-cyber/eSpeak-NG-.-Esp32` e o `arduino-espeak-ng`. As
  medidas são flash, `.bss`, pico de PSRAM, RTF, primeira amostra e igualdade do hash com R1.

### 7.3 Contratos

```yaml
id: FR-REF-03
verification:
  preconditions:
    - Artefato do CI gravado com imagem contendo pt e en; ESPK ready.
    - Hashes R1 do mesmo commit disponíveis (artefato do CI).
  stimulus:
    - Para cada item do corpus de verificação pt-BR e en: voice <idioma>; say --mute <item>.
  expected_observations:
    - sha256 de cada ESPK done igual ao hash R1 do mesmo item.
  timing: nenhum
  tolerance: nenhuma (bit a bit)
  prohibited_outcomes:
    - Hashes R1 gerados pelo próprio firmware ou copiados de uma execução anterior do alvo.
    - Itens pulados por erro ou tempo esgotado contados como iguais.
    - Comparar só os itens sem acento.
  tier: target
  evidence:
    - Tabela item × (hash R1, hash R3, igual?) em test-results/<run-id>/.
    - Linha ESPK boot (commit, bss, langs).
  cleanup:
    - voice e rate de volta ao padrão.
```

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-REF-01 | tarball verificado · corpus | um hash e uma transcrição por item × idioma | tarball sem conferência do SHA-256 | host |
| FR-REF-02 | componente e R1 compilados no host · corpus de verificação | hashes iguais | comparar o componente consigo mesmo | host |
| FR-REF-04 | divergência injetada (item com PCM alterado no teste da ferramenta) | linha com índice, diferença e SNR; status de bloqueio | divergência só no log, sem bloquear | host |
| FR-REF-05 | `espeak-ng` do sistema instalado · todos os idiomas | relatório com versão do pacote e comparação por item | pacote ausente tratado como igual | host |
| FR-REF-06 | divergência conhecida (pacote com patch) | linha com causa; build verde | build vermelho; divergência omitida | host |
| FR-REF-07 | CI · todos os idiomas | relatório cobre cada idioma do upstream | idioma omitido sem registro | host |
| FR-REF-08 | os três portes gravados em sequência | tabela com as seis medidas por porte | medidas de portes em placas ou corpora diferentes | bench |

## 8. Corpora

### 8.1 Requisitos

- **FR-COR-01** [Must · user · v0.1] O corpus de verificação deve ter, para pt-BR e para en, cerca de 50 itens. Eles
  cobrem: todas as letras acentuadas e o `ç`, em maiúsculas e minúsculas; números; horas; datas; valores monetários
  (R$ no pt-BR, US$ no en); pontuação e interrogação; siglas e abreviações; um texto de mais de 500 caracteres.
- **FR-COR-02** [Must · derived · v0.1] Cada item do corpus de verificação pt-BR que tem acento deve ter um item par
  sem acento, para medir as duas condições.
- **FR-COR-03** [Must · user · v0.1] O corpus automático, usado em todos os idiomas, deve ser gerado sem texto em
  idioma natural: os numerais `0 1 2 3 4 5 6 7 8 9 10 100 1000`, a data `2026-11-26` e a hora `14:30`.
- **FR-COR-04** [Must · user · v0.1] O corpus de escuta pt-BR deve conter: as 200 palavras mais frequentes da lista
  Leipzig pt-BR (CC BY 4.0), excluídas as palavras de uma letra (200); 50 frases semanticamente
  imprevisíveis geradas por modelos gramaticais a partir dessas palavras, pelo método de Benoît et al. (1996)
  (50); e 30 frases do dia a dia de aparelho com fala (30).
- **FR-COR-05** [Should · user · v0.1] O corpus de escuta en deve conter frases semanticamente imprevisíveis geradas
  pelo mesmo método e as Harvard sentences, se a licença for confirmada (OD-03).
- **FR-COR-06** [Must · user · v0.1] Todo arquivo de corpus deve ter licença registrada no `REUSE.toml`. Material
  protegido sem permissão registrada (LSP, Alcaim et al.) não entra no repositório.
- **FR-COR-07** [Must · derived · v0.1] O gerador de frases imprevisíveis deve ser determinístico: a mesma semente e a
  mesma lista de palavras produzem o mesmo arquivo, byte a byte.

### 8.2 Contratos

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-COR-01 | arquivo do corpus · verificador de cobertura | cada categoria presente; 45 a 55 itens | categoria faltando | host |
| FR-COR-02 | corpus pt-BR | cada item acentuado tem o par sem acento | par ausente | host |
| FR-COR-03 | gerador · cada idioma | os três itens por idioma | texto em idioma natural | host |
| FR-COR-04 | lista Leipzig com SHA-256 fixado | 200 palavras, 50 frases, 30 frases | lista sem hash fixado | host |
| FR-COR-05 | idem en | frases geradas presentes; Harvard só com OD-03 resolvida | Harvard sem licença confirmada | host |
| FR-COR-06 | `reuse lint` | sem erro | arquivo de corpus sem licença | host |
| FR-COR-07 | gerar duas vezes com a mesma semente | arquivos idênticos | diferença | host |

## 9. Inteligibilidade estimada por ASR

### 9.1 Propósito

Dá um número reprodutível e publicável sem pessoas. **Não substitui ouvinte**, e a FSD não chama esse número de
inteligibilidade [user].

### 9.2 Requisitos

- **FR-ASR-01** [Must · user · v0.1] A cada tag de release, o CI deve sintetizar o corpus de escuta pt-BR e en no host
  (R1), em 140, 175 e 220 ppm, e transcrever cada amostra com `whisper.cpp`, com a versão e o SHA-256 do modelo
  fixados (modelo `small` multilíngue).
- **FR-ASR-02** [Must · user · v0.1] O relatório deve dar CER e WER por idioma × velocidade × tipo de corpus, e, no
  pt-BR, também por condição (com e sem acento).
- **FR-ASR-03** [Must · derived · v0.1] O relatório deve registrar a versão do `whisper.cpp`, o hash do modelo, o
  commit do componente e a normalização de texto aplicada antes do cálculo de CER e WER.
- **FR-ASR-04** [Must · derived · v0.1] Com as mesmas entradas, duas execuções devem produzir o mesmo relatório.
- **FR-ASR-05** [Must · user · v0.1] Todo documento que publica número do ASR deve trazer a ressalva: "estimativa por
  reconhecimento automático; não é medida de inteligibilidade com ouvintes".
- **FR-ASR-06** [Should · user · v0.1] O relatório deve rodar também para outros idiomas da imagem que o modelo
  Whisper suporta, com o corpus automático (FR-COR-03).

### 9.3 Contratos

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-ASR-01 | tag no CI | transcrição por amostra × velocidade | modelo baixado sem conferência do hash | host |
| FR-ASR-02 | transcrições | tabela com as quatro dimensões | célula vazia sem motivo registrado | host |
| FR-ASR-03 | relatório | campos de versão, hash, commit e normalização | campo ausente | host |
| FR-ASR-04 | rodar duas vezes | relatórios iguais | diferença sem mudança de entrada | host |
| FR-ASR-05 | README, relatórios e artigos | ressalva junto do número | número sem ressalva; a palavra "inteligível" aplicada ao número | other |
| FR-ASR-06 | idiomas suportados pelo modelo | linhas por idioma | idioma suportado omitido sem registro | host |

## 10. Escuta interna e instrumento de escuta

### 10.1 Propósito

A equipe ouve para **ajustar** a fala: dicionário, velocidade e pausas. Os resultados **não são publicados como
medida**. O instrumento serve depois ao estudo com o CEP [user].

### 10.2 Requisitos

- **FR-LST-01** [Must · user · v0.1] O gerador de amostras deve produzir, a partir do artefato do CI, os arquivos WAV
  do corpus de escuta em cada velocidade. O nome de cada arquivo é pseudoaleatório, e o mapa nome → item fica num
  arquivo separado.
- **FR-LST-02** [Must · user · v0.1] O gerador de ordem deve produzir listas em quadrado latino por condição de
  velocidade, a partir de uma semente registrada.
- **FR-LST-03** [Must · user · v0.1] Na placa, o comando `play <id>` deve falar o item do corpus de escuta pelo
  alto-falante, no volume da sessão aberta, e emitir `ESPK done` com o hash.
- **FR-LST-04** [Must · user · v0.1] As respostas da escuta interna devem ser registradas por ferramenta, num arquivo
  estruturado com código de ouvinte pseudônimo. A chave de pseudônimos fica fora do repositório.
- **FR-LST-05** [Must · user · v0.2] Cada ajuste de engenharia motivado pela escuta interna deve citar, no commit, a
  sessão e o item.
- **FR-LST-06** [Must · user · futuro] A coleta com participantes de fora da equipe só pode começar com o número do
  CAAE do protocolo aprovado registrado na FSD.

#### Ferramenta guiada de escuta

Uma aplicação web local, servida pelo computador ligado à placa e aberta no navegador, sem acesso à internet. Ela
conduz o ouvinte do começo ao fim, comanda a placa e registra as respostas. Na v0.2 a ligação com a placa é por cabo,
pelo driver de bancada; a ligação por rede é um requisito futuro (FR-LST-19) [user].

- **FR-LST-07** [Must · user · v0.2] A ferramenta deve rodar como servidor local (`127.0.0.1`) aberto no navegador,
  sem requisição a endereço fora do computador.
- **FR-LST-08** [Must · user · v0.2] Antes do primeiro item, a ferramenta deve mostrar a tela de abertura com o texto
  de instruções da versão do protocolo em uso, a duração estimada da sessão e as recomendações de ambiente, e só deve
  avançar depois que o ouvinte confirmar que leu.
- **FR-LST-09** [Must · derived · v0.2] A duração estimada deve ser a soma das durações dos itens da sessão mais 8 s
  por item para a resposta, arredondada para o minuto acima.
- **FR-LST-10** [Must · user · v0.2] Antes do primeiro item, a ferramenta deve tocar uma frase de ajuste, que não
  pertence ao corpus, e deixar o ouvinte ajustar o volume dentro da sessão de escuta aberta. O volume final fica
  registrado e não muda até o fim da sessão.
- **FR-LST-11** [Must · user · v0.2] Para cada item, a ferramenta deve comandar a placa (`play <id>`) e habilitar o
  campo de resposta só depois do `ESPK done` desse item.
- **FR-LST-12** [Must · user · v0.2] A tela deve mostrar o progresso como "item k de N" e o tempo restante estimado.
- **FR-LST-13** [Must · user · v0.2] Para palavras e frases imprevisíveis, a resposta deve ser uma transcrição livre.
  Para frases do dia a dia, a resposta deve ser a nota ACR de 1 a 5 com os rótulos da ITU-T P.800 em pt-BR
  ("Excelente", "Boa", "Razoável", "Pobre", "Ruim") e a pergunta "Você entendeu a informação principal?" (sim/não).
- **FR-LST-14** [Must · user · v0.2] Durante a sessão, a tela não deve mostrar o texto esperado, a condição do item
  (velocidade, com ou sem acento), se a resposta está certa, nem qualquer resultado parcial.
- **FR-LST-15** [Must · user · v0.2] Cada item deve ser tocado uma única vez. A ferramenta não deve oferecer
  repetição.
- **FR-LST-16** [Must · user · v0.2] Cada resposta deve ser gravada em disco no momento da confirmação. Uma sessão
  interrompida (navegador fechado, placa desligada, queda de energia) deve retomar no primeiro item sem resposta.
- **FR-LST-17** [Must · user · v0.2] O registro da sessão deve ser um arquivo JSON com: código pseudônimo do ouvinte,
  versão do protocolo, commit do artefato da placa, volume, semente e ordem dos itens, e, por item, a resposta, o
  tempo de resposta em ms e o horário. Ele não deve conter nome nem outro dado identificável.
- **FR-LST-18** [Must · user · v0.2] O comando de consolidação deve juntar os registros de sessão numa tabela CSV, com
  uma linha por ouvinte × item, e recusar juntar sessões de versões de protocolo diferentes.
- **NFR-LST-01** [Must · user · v0.2] As telas da ferramenta devem atender aos critérios de nível AA da WCAG 2.2
  (contraste, operação só por teclado, nomes acessíveis para leitor de tela, zoom de 200 % sem perda de conteúdo).
- **FR-LST-19** [May · user · futuro] A ferramenta deve poder comandar a placa pela rede local. O transporte e a
  segurança dessa ligação são a decisão aberta OD-05.

### 10.3 Contratos

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-LST-01 | artefato do CI · gerador | um WAV por item × velocidade; mapa separado | nome do arquivo revelando o item | host |
| FR-LST-02 | semente fixa | listas iguais em duas execuções; cada item uma vez por lista | repetição; lista dependente do relógio | host |
| FR-LST-03 | `listen open 40` · `play 12` | fala do item 12; hash igual ao WAV do host | tocar fora de sessão acima do teto | target |
| FR-LST-04 | sessão de teste | arquivo com código pseudônimo | nome ou dado identificável no git | host |
| FR-LST-05 | commit de ajuste | referência à sessão e ao item | ajuste sem rastro | other |
| FR-LST-06 | antes do CAAE | ferramenta de coleta recusa modo "estudo" sem CAAE configurado | coleta com terceiros sem CAAE | host |
| FR-LST-07 | ferramenta iniciada · captura de rede do processo | só conexões a `127.0.0.1` e à porta da placa | requisição externa (fonte, script, telemetria) | host |
| FR-LST-08 | sessão nova · tentar avançar sem confirmar | instruções da versão do protocolo, duração e recomendações; avanço bloqueado | primeiro item tocado antes da confirmação | host |
| FR-LST-09 | sessão de 10 itens com durações conhecidas | duração = Σ durações + 80 s, arredondada para cima | estimativa fixa no texto | host |
| FR-LST-10 | tela de ajuste · mudar volume · iniciar · tentar mudar de novo | frase de ajuste fora do corpus; volume registrado; mudança recusada depois do início | item do corpus usado no ajuste | host · target |
| FR-LST-11 | placa simulada que atrasa o `ESPK done` | campo de resposta desabilitado até o `done` | resposta aceita antes do fim do áudio | host · target |
| FR-LST-12 | item 3 de 10 | "item 3 de 10" e tempo restante | progresso ausente | host |
| FR-LST-13 | um item de cada tipo | campo livre; escala com os cinco rótulos e a pergunta sim/não | rótulos diferentes dos fixados | host |
| FR-LST-14 | sessão inteira · varrer o HTML de cada tela | nenhum texto esperado, condição, acerto ou parcial | qualquer um deles no HTML, inclusive oculto | host |
| FR-LST-15 | sessão inteira · varrer as telas e a API local · tentar `play` do mesmo item duas vezes | nenhum controle de repetição; segundo `play` do item recusado | item tocado mais de uma vez | host |
| FR-LST-16 | matar o processo depois do item 5 · reabrir | retoma no item 6; respostas 1–5 intactas | resposta perdida; item repetido | host |
| FR-LST-17 | sessão concluída | JSON com todos os campos | nome, e-mail ou outro identificador no arquivo | host |
| FR-LST-18 | três sessões, uma de outra versão | CSV das duas compatíveis; recusa explícita da terceira | mistura de versões | host |
| NFR-LST-01 | cada tela · verificador automático de acessibilidade (axe-core) e revisão por teclado | nenhuma violação AA | tela só operável com mouse | host · other |

## 11. Exemplos

### 11.1 Requisitos

- **FR-EXM-01** [Must · user · v0.1] O exemplo `hello` deve iniciar o componente, sintetizar uma frase na voz padrão e
  registrar no log a taxa de amostragem, a duração e o SHA-256 do PCM, sem saída de áudio.
- **FR-EXM-02** [Must · user · v0.1] O exemplo `hello` deve compilar no CI para cada chip de FR-PLT-02.
- **FR-EXM-03** [Must · user · v0.1] O exemplo `waveshare-s3-rlcd` deve falar uma frase em pt-BR pelo ES8311 da placa
  de referência, no volume 5.
- **FR-EXM-04** [Should · user · v0.1] O exemplo `waveshare-s3-rlcd` deve mostrar como reamostrar o PCM para a taxa
  do codec quando ela for diferente de 22 050 Hz.

### 11.2 Contratos

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-EXM-01 | `hello` gravado na placa de referência | log com taxa, duração e hash; hash = R1 | PCM vazio | target |
| FR-EXM-02 | CI | build verde por chip | chip pulado sem registro | host |
| FR-EXM-03 | exemplo gravado | `ESPK done underrun=0` | volume acima do teto | target |
| FR-EXM-04 | build do exemplo | caminho de reamostragem compilado e coberto por teste no host | reamostragem dentro do componente | host |

---

# Parte B — Componente `espeak-ng` (L1)

## 12. Imagem de dados e partição

### 12.1 Propósito

Leva os dados compilados do eSpeak NG para uma partição, valida a integridade e entrega os arquivos ao motor por um
VFS somente leitura, sem patch no upstream.

### 12.2 Formato da imagem

O cabeçalho, em little-endian, é normativo. Os detalhes estão no Apêndice A.

| Campo | Tamanho | Conteúdo |
|---|---|---|
| `magic` | 4 B | `ESPK` |
| `format_version` | 2 B | 1 |
| `flags` | 2 B | reservado, 0 |
| `espeak_version` | 16 B | string terminada em zero, ex. `1.52.0` |
| `file_count` | 4 B | número de entradas |
| `payload_size` | 4 B | bytes depois da tabela |
| `crc32` | 4 B | CRC-32 (IEEE 802.3) da tabela e do payload |
| tabela | `file_count` × 72 B | nome (64 B, terminado em zero, caminho relativo), deslocamento (4 B), tamanho (4 B) |

### 12.3 Requisitos

- **FR-DAT-01** [Must · user · v0.1] `espk_init()` deve localizar a partição pelo rótulo e pelo subtipo configurados
  (padrão `espeak`, `0x40`).
- **FR-DAT-02** [Must · derived · v0.1] Sem a partição, `espk_init()` deve devolver `ESP_ERR_NOT_FOUND` e deixar o
  componente no estado `UNINIT`.
- **FR-DAT-03** [Must · seed:alertalergo · v0.1] Com `magic` diferente de `ESPK` ou CRC32 divergente,
  `espk_init()` deve devolver `ESP_ERR_INVALID_CRC` e não chamar o motor.
- **FR-DAT-04** [Must · derived · v0.1] Com `espeak_version` diferente da versão do motor compilado, `espk_init()` deve
  devolver `ESP_ERR_INVALID_VERSION`.
- **FR-DAT-05** [Must · user · v0.1] Com a imagem válida, o VFS deve ficar montado no ponto configurado (padrão
  `/espeak`) e servir `open`, `read`, `lseek`, `fstat` e `close` de cada arquivo da tabela, somente leitura.
- **FR-DAT-06** [Must · derived · v0.1] Uma escrita ou criação no VFS deve falhar com `EROFS`.
- **FR-DAT-07** [Must · derived · v0.1] O gerador da imagem (host) deve produzir a mesma imagem, byte a byte, a partir
  dos mesmos dados e da mesma lista de idiomas.
- **FR-DAT-08** [Must · user · v0.1] O gerador deve aceitar arquivos `*_listx` extras do integrador e incluí-los na
  compilação do dicionário do idioma correspondente pelo caminho de regeneração no host (FR-LIC-04).

### 12.4 Contratos

```yaml
id: FR-DAT-03
verification:
  preconditions:
    - Firmware com o componente; imagem válida gerada.
  stimulus:
    - Gravar uma imagem com um byte do payload invertido.
    - Reiniciar e chamar espk_init().
    - Repetir com magic alterado.
  expected_observations:
    - espk_init() devolve ESP_ERR_INVALID_CRC nos dois casos.
    - Log do componente com o CRC esperado e o calculado.
    - espk_synth() seguinte devolve ESP_ERR_INVALID_STATE.
  timing: nenhum
  tolerance: nenhuma
  prohibited_outcomes:
    - O motor é inicializado com dados corrompidos.
    - Reinício, pânico ou watchdog.
    - Fala de qualquer som.
  tier: target
  evidence:
    - Log do boot; código de retorno no marcador ESPK error.
  cleanup:
    - Regravar a imagem válida.
```

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-DAT-01 | rótulo e subtipo configurados para outro par · `espk_init` | encontra a partição do par configurado | rótulo fixo no código | target |
| FR-DAT-02 | tabela de partições sem `espeak` | `ESP_ERR_NOT_FOUND`; estado `UNINIT` | pânico | target |
| FR-DAT-04 | imagem com `espeak_version` `1.51.0` | `ESP_ERR_INVALID_VERSION` | init com sucesso | host (leitor) · target |
| FR-DAT-05 | imagem válida | `fopen("/espeak/phontab")` lê os mesmos bytes do arquivo de origem | arquivo truncado | host (leitor) · target |
| FR-DAT-06 | `fopen(..., "w")` | falha com `EROFS` | escrita aceita | target |
| FR-DAT-07 | gerar duas vezes | imagens idênticas | carimbo de hora na imagem | host |
| FR-DAT-08 | `pt_listx` com uma entrada · regeneração | a palavra sai com os fonemas da entrada (`-x`) | `listx` ignorado em silêncio | host |

## 13. Seleção de idiomas e relatório de capacidade

### 13.1 Requisitos

- **FR-CAP-01** [Must · user · v0.1] O `menuconfig` deve oferecer a lista de idiomas da imagem como texto
  (`CONFIG_ESPK_LANGUAGES`, ex. `en pt`) e a opção "todos os idiomas" (`CONFIG_ESPK_LANGUAGES_ALL`).
- **FR-CAP-02** [Must · derived · v0.1] Um nome de idioma que não existe no upstream deve fazer o build falhar, com a
  mensagem que lista os nomes válidos.
- **FR-CAP-03** [Must · user · v0.1] O idioma padrão da lista deve ser `en`.
- **FR-CAP-04** [Must · user · v0.1] O idioma inicial (`CONFIG_ESPK_DEFAULT_VOICE`) deve pertencer à lista. Se não
  pertencer, o build falha.
- **FR-CAP-05** [Must · user · v0.1] O build deve emitir um relatório de capacidade com: tamanho da imagem e da
  partição; pico estimado de PSRAM (arquivos comuns mais o maior dicionário escolhido); RAM interna estática do
  componente; pilha da tarefa e onde ela fica.
- **FR-CAP-06** [Must · user · v0.1] Se a imagem for maior que a partição da tabela de partições do projeto, o build
  deve falhar.
- **FR-CAP-07** [Must · user · v0.1] Se o pico estimado de PSRAM passar do orçamento configurado
  (`CONFIG_ESPK_PSRAM_BUDGET_KB`), o build deve falhar.
- **FR-CAP-08** [Must · user · v0.1] Se a imagem ou o pico de PSRAM passar de 90 % do limite, o build deve emitir um
  aviso e seguir (90 %).
- **FR-CAP-09** [Must · user · v0.1] Os tamanhos do relatório devem ser calculados a partir dos arquivos compilados no
  próprio build, não de uma tabela mantida à mão.
- **FR-CAP-10** [Must · derived · v0.1] Em uso, `espk_init()` deve conferir a PSRAM livre antes de carregar os dados e
  devolver `ESP_ERR_NO_MEM` se ela for menor que o pico do relatório.
- **FR-CAP-11** [Must · user · v0.1] O README do componente deve publicar o tamanho da imagem com todos os idiomas e o
  pico de PSRAM correspondente, tirados do relatório do CI.

### 13.2 Contratos

```yaml
id: FR-CAP-06
verification:
  preconditions:
    - Projeto de teste com partição espeak de 1 MiB.
  stimulus:
    - Build com CONFIG_ESPK_LANGUAGES_ALL=y.
  expected_observations:
    - O build falha.
    - A mensagem mostra o tamanho da imagem, o da partição e a diferença.
  timing: nenhum
  tolerance: nenhuma
  prohibited_outcomes:
    - O build termina com sucesso e a imagem é truncada.
    - A falha só aparece na gravação ou no boot.
  tier: host
  evidence:
    - Saída do build no CI.
  cleanup: nenhum
```

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-CAP-01 | `menuconfig` | as duas opções presentes | lista fixa no código | host |
| FR-CAP-02 | `CONFIG_ESPK_LANGUAGES="pt xx"` | build falha com a lista de nomes válidos | idioma ignorado em silêncio | host |
| FR-CAP-03 | projeto novo | imagem só com `en` | outro padrão | host |
| FR-CAP-04 | lista `en`, voz inicial `pt` | build falha | falha só em uso | host |
| FR-CAP-05 | build | relatório com os quatro itens | item ausente | host |
| FR-CAP-07 | orçamento de 512 KB · lista `en pt` | build falha | sucesso | host |
| FR-CAP-08 | partição com 91 % de uso | aviso; build verde | falha; silêncio | host |
| FR-CAP-09 | mudar um dicionário | o relatório acompanha o novo tamanho | número de tabela fixa | host |
| FR-CAP-10 | PSRAM ocupada por *seam* de teste | `ESP_ERR_NO_MEM`; estado `UNINIT` | pânico no `malloc` do upstream | target |
| FR-CAP-11 | release | números no README iguais aos do relatório do CI da tag | número escrito à mão | host |

## 14. Núcleo síncrono

### 14.1 API (normativa no comportamento; os nomes vêm do Método)

| Função | Comportamento |
|---|---|
| `espk_init(const espk_config_t *)` | monta os dados, valida, inicializa o motor e a voz inicial |
| `espk_deinit(void)` | libera o motor e desmonta o VFS |
| `espk_sample_rate(void)` | taxa devolvida pelo motor |
| `espk_set_voice(const char *)` | troca de voz entre as da imagem |
| `espk_list_voices(...)` | as vozes presentes na imagem |
| `espk_set_rate(int ppm)` · `espk_set_pitch(int)` | parâmetros do upstream |
| `espk_synth(const char *utf8, espk_pcm_cb_t cb, void *ctx)` | sintetiza e chama `cb` com blocos de PCM; `cb` devolve `false` para cancelar |

### 14.2 Requisitos

- **FR-SYN-01** [Must · user · v0.1] `espk_synth()` deve entregar o PCM em 16 bits com sinal, mono, na taxa
  devolvida por `espk_sample_rate()`, sem reamostragem.
- **FR-SYN-02** [Must · user · v0.1] `espk_sample_rate()` deve devolver 22 050 depois de `espk_init()` com sucesso.
- **FR-SYN-03** [Must · user · v0.1] Quando o callback devolve `false`, `espk_synth()` deve parar e devolver
  `ESPK_ERR_CANCELLED` sem chamar o callback de novo.
- **FR-SYN-04** [Must · user · v0.1] Uma segunda chamada a `espk_init()` sem `espk_deinit()` deve devolver
  `ESP_ERR_INVALID_STATE` sem alterar o estado.
- **FR-SYN-05** [Must · derived · v0.1] `espk_synth()` antes de `espk_init()` deve devolver `ESP_ERR_INVALID_STATE`.
- **FR-SYN-06** [Must · user · v0.1] `espk_set_voice()` com uma voz ausente da imagem deve devolver
  `ESP_ERR_NOT_FOUND` e manter a voz anterior.
- **FR-SYN-07** [Must · user · v0.1] Sem configuração explícita, a velocidade deve ser 175 ppm e o pitch 50, os
  padrões do upstream.
- **FR-SYN-08** [Must · derived · v0.1] `espk_set_rate()` fora do intervalo do upstream (80 a 450 ppm) deve devolver
  `ESP_ERR_INVALID_ARG` sem mudar a velocidade.
- **FR-SYN-09** [Must · user · v0.1] Um texto maior que `CONFIG_ESPK_MAX_TEXT_LEN` (padrão 1 024 bytes)
  deve ser recusado com `ESP_ERR_INVALID_SIZE`.
- **FR-SYN-10** [Must · derived · v0.1] Uma chamada a `espk_synth()` de outra tarefa enquanto uma síntese está em
  curso deve devolver `ESP_ERR_INVALID_STATE`.
- **FR-SYN-11** [Must · derived · v0.1] `espk_deinit()` seguido de `espk_init()` deve deixar o componente pronto, com
  a mesma heap livre de antes, numa tolerância de 1 KB.
- **NFR-SYN-01** [Must · user · v0.1] Na placa de referência, sem carga (`idle`), com a `.bss` no modo padrão, o RTF
  de cada item do corpus de verificação pt-BR a 175 ppm deve ser ≤ 0,5.
- **NFR-SYN-02** [Must · user · v0.1] Nas mesmas condições, o tempo do pedido até o primeiro callback deve ser
  ≤ 300 ms para cada frase de até 20 palavras.
- **NFR-SYN-03** [Must · pack:esp32 · v0.1] A síntese do texto de mais de 500 caracteres do corpus não deve disparar o
  task watchdog com o tempo padrão do ESP-IDF (5 s).
- **NFR-SYN-04** [Must · user · v0.1] 50 sínteses seguidas do corpus de verificação pt-BR, em `idle`, devem terminar
  sem reinício, sem watchdog e com a heap interna livre final a até 1 KB da inicial.

### 14.3 Contratos

```yaml
id: FR-SYN-03
verification:
  preconditions:
    - Componente iniciado; texto longo do corpus.
  stimulus:
    - Callback de teste devolve false no terceiro bloco.
  expected_observations:
    - espk_synth() devolve ESPK_ERR_CANCELLED.
    - O callback foi chamado exatamente 3 vezes.
    - Uma espk_synth() seguinte com outro texto dá o hash R1 desse texto.
  timing: o retorno ocorre em até 100 ms depois do callback que devolveu false
  tolerance: nenhuma
  prohibited_outcomes:
    - Callback chamado depois de devolver false.
    - A síntese seguinte sai alterada pelo cancelamento (estado residual).
    - Vazamento de heap maior que 1 KB por ciclo em 20 ciclos.
  tier: host · target
  evidence:
    - Contagem de chamadas; hashes; heap antes e depois.
  cleanup: nenhum
```

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-SYN-01 | síntese | blocos `int16_t`, mono | estéreo; outra taxa | host · target |
| FR-SYN-02 | init | 22 050 | valor fixo no código sem vir do motor | target |
| FR-SYN-04 | init duas vezes | `ESP_ERR_INVALID_STATE`; síntese continua funcionando | segunda inicialização do motor | host · target |
| FR-SYN-05 | sem init · synth | `ESP_ERR_INVALID_STATE` | pânico | host |
| FR-SYN-06 | `set_voice("xx")` · synth | erro; síntese na voz anterior (hash R1 da voz anterior) | voz indefinida | host · target |
| FR-SYN-07 | init sem config de voz | hash = R1 com 175 ppm e pitch 50 | outros padrões | host |
| FR-SYN-08 | `set_rate(79)`, `set_rate(451)` | `ESP_ERR_INVALID_ARG`; velocidade inalterada | valor aplicado ou recortado em silêncio | host |
| FR-SYN-09 | texto de 1 025 bytes | `ESP_ERR_INVALID_SIZE`; nada sintetizado | truncar em silêncio | host |
| FR-SYN-10 | duas tarefas chamando ao mesmo tempo | a segunda recebe `ESP_ERR_INVALID_STATE` | PCM misturado; corrupção | target |
| FR-SYN-11 | 20 ciclos init/deinit | heap livre estável em ± 1 KB | vazamento crescente | target |
| NFR-SYN-01 | `idle` · corpus pt-BR | RTF ≤ 0,5 por item | média escondendo item acima | target |
| NFR-SYN-02 | `idle` · frases ≤ 20 palavras | ≤ 300 ms por item | medir a partir do fim da síntese | target |
| NFR-SYN-03 | texto > 500 caracteres | sem aviso do TWDT | desligar o TWDT para passar | target |
| NFR-SYN-04 | 50 sínteses | 50 sucessos; heap final ± 1 KB | reinício; vazamento | target |

## 15. Camada assíncrona

### 15.1 Propósito

Uma tarefa de síntese com fila, opcional (`CONFIG_ESPK_ASYNC`, ligada por padrão). O PCM continua saindo por
callback, chamado de dentro da tarefa.

### 15.2 Modelo de estados

Estados: `UNINIT`, `IDLE`, `SPEAKING`, `CANCELLING`.

| De | Evento | Guarda | Para | Ação | Limite |
|---|---|---|---|---|---|
| `UNINIT` | `espk_init` ok | — | `IDLE` | cria tarefa e fila | — |
| `UNINIT` | `espk_init` falha | — | `UNINIT` | devolve o erro | — |
| `UNINIT` | `say`, `cancel` | — | `UNINIT` | `ESP_ERR_INVALID_STATE` | — |
| `IDLE` | `say` | fila com vaga | `SPEAKING` | enfileira; evento `START` | — |
| `IDLE` | `say` | texto grande demais | `IDLE` | `ESP_ERR_INVALID_SIZE` | — |
| `IDLE` | `cancel` | — | `IDLE` | sem efeito; `ESP_OK` | — |
| `IDLE` | `espk_deinit` | — | `UNINIT` | encerra tarefa | ≤ 100 ms |
| `SPEAKING` | `say` | fila com vaga | `SPEAKING` | enfileira | — |
| `SPEAKING` | `say` | fila cheia | `SPEAKING` | `ESP_ERR_NO_MEM`; nada muda | — |
| `SPEAKING` | fim do texto | fila vazia | `IDLE` | evento `DONE` | — |
| `SPEAKING` | fim do texto | fila com item | `SPEAKING` | evento `DONE`; evento `START` do próximo | — |
| `SPEAKING` | `cancel` | — | `CANCELLING` | pede parada; esvazia a fila | — |
| `SPEAKING` | erro do motor | — | `IDLE` | evento `ERROR`; esvazia a fila | — |
| `SPEAKING` | `espk_deinit` | — | `CANCELLING` → `UNINIT` | cancela, encerra | ≤ 100 ms |
| `CANCELLING` | síntese parou | — | `IDLE` | evento `CANCELLED` | ≤ 100 ms do `cancel` |
| `CANCELLING` | `say` | — | `CANCELLING` | enfileira para depois do `CANCELLED` | — |
| `CANCELLING` | `cancel` | — | `CANCELLING` | ignorado; `ESP_OK` | — |

### 15.3 Requisitos

- **FR-ASY-01** [Must · user · v0.1] `espk_say()` deve enfileirar o texto e voltar sem esperar a síntese, em até 5 ms
 .
- **FR-ASY-02** [Must · user · v0.1] A camada deve emitir, pelo callback de eventos, `START`, `DONE`, `CANCELLED` e
  `ERROR`, cada um com o id do pedido. O `DONE` traz o número de amostras, `synth_ms` e `first_ms`.
- **FR-ASY-03** [Must · user · v0.1] `espk_cancel()` deve levar ao evento `CANCELLED` do pedido em curso em até
  100 ms e descartar os pedidos da fila.
- **FR-ASY-04** [Must · derived · v0.1] Com a fila cheia (`CONFIG_ESPK_QUEUE_LEN`, padrão 4),
  `espk_say()` deve devolver `ESP_ERR_NO_MEM` sem alterar a fila.
- **FR-ASY-05** [Must · user · v0.1] A pilha da tarefa deve ter o tamanho de `CONFIG_ESPK_TASK_STACK` (padrão
  65 536 B [seed:alertalergo]) e ficar na PSRAM quando `CONFIG_ESPK_TASK_STACK_PSRAM` estiver ligado (padrão ligado).
- **FR-ASY-06** [Must · derived · v0.1] O build deve falhar com `CONFIG_ESPK_TASK_STACK` abaixo de 49 152 B
  (o uso medido na semente, ~39 KB, mais 25 %).
- **FR-ASY-07** [Must · derived · v0.1] O PCM entregue pela camada assíncrona deve ser igual, bit a bit, ao do núcleo
  síncrono para o mesmo texto e a mesma voz.
- **FR-ASY-08** [Must · derived · v0.1] Com `CONFIG_ESPK_ASYNC` desligado, `espk_say()` e `espk_cancel()` devem
  devolver `ESP_ERR_NOT_SUPPORTED`, e nenhuma tarefa deve ser criada.
- **FR-ASY-09** [Must · derived · v0.1] Cada par (estado × evento) da tabela 15.2 deve produzir o estado, a ação e o
  código de retorno da tabela.

### 15.4 Contratos

```yaml
id: FR-ASY-03
verification:
  preconditions:
    - Camada assíncrona ligada; fala longa em curso; dois pedidos na fila.
  stimulus:
    - espk_cancel() no meio da fala (instante registrado).
  expected_observations:
    - Evento CANCELLED do pedido em curso em até 100 ms.
    - Nenhum START dos dois pedidos da fila.
    - Estado IDLE; um say seguinte fala e dá o hash R1.
  timing: 100 ms do cancel ao CANCELLED
  tolerance: nenhuma
  prohibited_outcomes:
    - Os pedidos da fila começam a falar.
    - O cancelamento acontece por reinício ou pela destruição da tarefa.
    - DONE emitido para o pedido cancelado.
  tier: target
  evidence:
    - Marcadores com horário do PC (bench telemetry); contador de boot.
  cleanup: nenhum
```

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-ASY-01 | `IDLE` · `say` de texto longo | retorno ≤ 5 ms | bloqueio até o fim | target |
| FR-ASY-02 | `say` | `START` e `DONE` com id e campos | evento sem id | target |
| FR-ASY-04 | fila cheia · `say` | `ESP_ERR_NO_MEM`; fila inalterada | descarte do mais antigo | target |
| FR-ASY-05 | build padrão | tarefa com 65 536 B na PSRAM (`heap_caps` da pilha) | pilha na RAM interna com a opção ligada | target |
| FR-ASY-06 | `CONFIG_ESPK_TASK_STACK=32768` | build falha | sucesso | host |
| FR-ASY-07 | mesmo texto pelos dois caminhos | hashes iguais | diferença | target |
| FR-ASY-08 | async desligado · `say` | `ESP_ERR_NOT_SUPPORTED`; nenhuma tarefa | tarefa criada | host · target |
| FR-ASY-09 | cada par da tabela | estado, ação e retorno da tabela | par sem teste | host (lógica de estados) · target |

## 16. Memória e colocação

### 16.1 Requisitos

- **FR-MEM-01** [Must · user · v0.1] `espk_init()` deve devolver `ESP_ERR_NOT_SUPPORTED` num sistema sem PSRAM
  inicializada, sem carregar o motor.
- **FR-MEM-02** [Must · user · v0.1] Com `CONFIG_ESPK_BSS_IN_PSRAM` ligado (padrão), a `.bss` do motor deve ficar na
  PSRAM, conforme o mapa do linker, sem alteração das fontes do upstream.
- **FR-MEM-03** [Must · user · v0.2] O relatório de medidas deve dar, para os dois modos de `.bss`: RAM interna livre
  depois do init, `heap_min` por perfil de carga, RTF e primeira amostra em pt-BR e en.
- **FR-MEM-04** [Must · user · v0.1] As cópias dos arquivos de dados feitas pelo motor devem ficar na PSRAM.
- **FR-MEM-05** [Must · user · v0.1] O relatório de medidas deve dar o tempo de `espk_init()` (montagem e carga dos
  dados) na placa de referência.

### 16.2 Contratos

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-MEM-01 | firmware de teste com PSRAM desligada · `espk_init` | `ESP_ERR_NOT_SUPPORTED`; nada alocado | pânico; dados na RAM interna | target |
| FR-MEM-02 | build padrão | símbolos `phoneme_list`, `frame_pool`, `echo_buf` em `extram_bss` no `.map` | patch na fonte do upstream | host |
| FR-MEM-03 | os dois builds · perfis | tabela completa | modo sem medida | bench |
| FR-MEM-04 | init · `heap_caps_get_info` | PSRAM livre cai pelo pico do relatório (± 5 %); RAM interna não | dados na RAM interna | target |
| FR-MEM-05 | boot | `init_ms` em `ESPK boot` e no relatório | medida ausente | target |

---

# Parte C — Fundação (L0)

## 17. Motor eSpeak NG

### 17.1 Requisitos

- **CON-ENG-01** [Must · user · v0.1] O motor deve ser o eSpeak NG 1.52.0 do tarball com o SHA-256 de §2.2.
- **CON-ENG-02** [Must · user · v0.1] As fontes do upstream em `components/espeak-ng/upstream/` devem ser idênticas às
  do tarball. O script de regeneração, rodado de novo, deve dar `git diff` vazio.
- **CON-ENG-03** [Must · seed:alertalergo · v0.1] Só o runtime síncrono deve ser compilado: sem MBROLA, Klatt, sonic
  nem o modo assíncrono do upstream.
- **FR-ENG-04** [Must · user · v0.1] Se a F2 confirmar a divergência por acento (#1611), o componente deve
  redirecionar no link (`-Wl,--wrap`) as funções `isw*` e `tow*` usadas pelo motor para as funções equivalentes do
  `ucd-tools` do próprio upstream, com `CONFIG_ESPK_UCD_WRAP` ligado por padrão.
- **FR-ENG-05** [Must · user · v0.1] Com `CONFIG_ESPK_UCD_WRAP` desligado (o modo "intacto"), o componente deve
  compilar e funcionar sem o redirecionamento.
- **FR-ENG-06** [Should · user · futuro] Quando a 1.53.0 sair, a migração deve regenerar as fontes e os dados e
  passar de novo por R1, R2 e R3.

### 17.2 Contratos

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| CON-ENG-01 | CI | SHA-256 do tarball conferido antes de extrair | tarball sem conferência | host |
| CON-ENG-02 | rodar o script de regeneração | `git diff --exit-code` sem diferença | qualquer diferença em `upstream/` | host |
| CON-ENG-03 | build | nenhum objeto de MBROLA, Klatt, sonic ou async no `.map` | símbolo presente | host |
| FR-ENG-04 | F2 confirmou · corpus com acento | R3 = R1 com o wrap | fonte do upstream editada | host · target |
| FR-ENG-05 | wrap desligado | build verde; divergência de acentos registrada como esperada | falha de build | host · target |
| FR-ENG-06 | tag 1.53.0 | R1, R2 e R3 verdes na nova versão | migração sem refazer as referências | host · target |

## 18. ESP-IDF e plataforma

### 18.1 Requisitos

- **CON-PLT-01** [Must · user · v0.1] O firmware de pesquisa e os exemplos devem compilar com o ESP-IDF v5.5.5,
  chamado por `scripts/idf.sh`.
- **CON-PLT-02** [Must · user · v0.1] O manifesto do componente deve declarar `idf: ">=5.5"` e os `targets` `esp32`,
  `esp32s2`, `esp32s3` e `esp32p4` (esses quatro; outros chips com PSRAM entram por contribuição com
  evidência).
- **CON-PLT-03** [Must · user · v0.1] O exemplo `hello` deve compilar no CI também com a versão 6.x fixada de §2.2.
- **CON-PLT-04** [Must · user · v0.1] O README deve dizer, por chip, o nível de suporte: "verificado na placa" (só o
  ESP32-S3 na v0.1) ou "compilado no CI".
- **CON-PLT-05** [Must · user · v0.1] A tabela de partições do firmware de pesquisa deve ser a de §2.2.

### 18.2 Contratos

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| CON-PLT-01 | CI | build com a versão registrada no artefato | outra versão do IDF | host |
| CON-PLT-02 | `idf_component.yml` | campos presentes com os valores | chip listado sem build no CI | host |
| CON-PLT-03 | CI | build verde na 6.x | job pulado | host |
| CON-PLT-04 | README × matriz do CI | cada chip com o nível correto | "verificado" sem evidência de placa | host |
| CON-PLT-05 | `partitions.csv` × tabela da FSD; leitura da tabela na placa | idênticas | divergência | host · target |

---

# Parte D — Transversais

## 19. Catálogo de configuração

| Opção | Padrão | Origem |
|---|---|---|
| `CONFIG_ESPK_PARTITION_LABEL` | `espeak` | [user] |
| `CONFIG_ESPK_PARTITION_SUBTYPE` | `0x40` | [user] |
| `CONFIG_ESPK_MOUNT_POINT` | `/espeak` | [user] |
| `CONFIG_ESPK_LANGUAGES` | `en` | [user] |
| `CONFIG_ESPK_LANGUAGES_ALL` | desligado | [user] |
| `CONFIG_ESPK_DEFAULT_VOICE` | `en` | [user] |
| `CONFIG_ESPK_PSRAM_BUDGET_KB` | 2 048 | [user] |
| `CONFIG_ESPK_CAPACITY_WARN_PCT` | 90 | [user] |
| `CONFIG_ESPK_BSS_IN_PSRAM` | ligado | [user] |
| `CONFIG_ESPK_UCD_WRAP` | ligado se a F2 confirmar a #1611 | [user] |
| `CONFIG_ESPK_ASYNC` | ligado | [user] |
| `CONFIG_ESPK_TASK_STACK` | 65 536 | [seed:alertalergo] |
| `CONFIG_ESPK_TASK_STACK_PSRAM` | ligado | [user] |
| `CONFIG_ESPK_TASK_PRIORITY` | 5 | [user] |
| `CONFIG_ESPK_TASK_CORE` | sem afinidade | [user] |
| `CONFIG_ESPK_QUEUE_LEN` | 4 | [user] |
| `CONFIG_ESPK_MAX_TEXT_LEN` | 1 024 | [user] |

- **FR-CFG-01** [Must · derived · v0.1] Cada opção do catálogo deve existir no `Kconfig` do componente com o padrão da
  tabela.
- **FR-CFG-02** [Must · derived · v0.1] Nenhum dos valores do catálogo deve aparecer fixo no código: mudar a opção
  muda o comportamento.

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-CFG-01 | `Kconfig` × tabela | igualdade | opção ausente ou com outro padrão | host |
| FR-CFG-02 | build com rótulo e ponto de montagem alterados | o componente usa os novos valores (FR-DAT-01, FR-DAT-05) | valor fixo no código | host · target |

## 20. Observabilidade

- **FR-LOG-01** [Must · derived · v0.1] Os marcadores do firmware de pesquisa devem ter o formato
  `ESPK <evento> chave=valor …`, numa linha, sem espaço dentro dos valores, estável entre versões. Um campo novo só
  pode ser acrescentado ao fim.
- **FR-LOG-02** [Must · derived · v0.1] O componente deve registrar no log (tag `espk`) cada erro devolvido por
  `espk_init()`, com o código e o motivo.

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-LOG-01 | parser do driver × saída de todos os comandos | cada linha é analisável | campo reordenado entre versões | host |
| FR-LOG-02 | cada caminho de erro de §12, §13 e §16 | linha de log com código e motivo | erro silencioso | target |

## 21. Tratamento de erros

Os códigos estão no Apêndice B. As regras gerais:

- **FR-ERR-01** [Must · derived · v0.1] Nenhuma função pública do componente deve causar pânico, reinício ou
  `abort()` por erro de entrada ou de recurso. Ela devolve um código do Apêndice B.
- **FR-ERR-02** [Must · derived · v0.1] Depois de qualquer erro de `espk_synth()` ou da camada assíncrona, a síntese
  seguinte de um texto válido deve dar o hash R1 desse texto.

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-ERR-01 | cada caminho de erro dos capítulos 12 a 16 | código do Apêndice B | pânico; reinício | host · target |
| FR-ERR-02 | erro provocado · synth válido | hash R1 | estado residual | host · target |

## 22. Segurança

### 22.1 Perfil

- **Ativo:** a disponibilidade do aparelho que usa o componente. O componente não guarda segredo nem dado pessoal.
- **Entrada:** o texto vem do integrador e pode vir de fonte não confiável (rede, BLE).
- **Ameaça:** texto construído para explorar defeitos de memória do motor (#2647, `ReadClause`, corrigido só depois da
  1.52.0) e derrubar ou corromper o aparelho.
- **Fora do perfil:** confidencialidade; integridade da partição de dados contra quem tem acesso físico à flash (o CRC
  pega corrupção acidental, não adulteração).

### 22.2 Requisitos e riscos aceitos

- **FR-SEC-01** [Must · derived · v0.1] O limite de tamanho de texto (FR-SYN-09) deve valer em todas as entradas
  públicas.
- **FR-SEC-02** [Must · derived · v0.1] Bytes que não formam UTF-8 válido não devem causar pânico nem reinício. Um
  teste no host passa por eles com o AddressSanitizer ligado.
- **Risco aceito R-SEC-1:** o componente **não** garante segurança de memória com texto hostil enquanto usa a 1.52.0.
  O README diz isso e recomenda ao integrador validar a origem do texto. A mitigação é seguir a 1.53 (FR-ENG-06).
- **Risco aceito R-SEC-2:** a imagem de dados não é assinada.

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-SEC-01 | texto acima do limite em `synth` e em `say` | `ESP_ERR_INVALID_SIZE` nos dois | um caminho sem limite | host |
| FR-SEC-02 | 1 000 sequências inválidas geradas com semente fixa · ASan | sem relatório do ASan; sem pânico | falha ignorada | host |

## 23. Licença e fonte correspondente

- **CON-LIC-01** [Must · user · v0.1] Todo arquivo próprio deve levar cabeçalho SPDX `GPL-3.0-or-later`, e todo
  arquivo de terceiros deve constar no `REUSE.toml`. `reuse lint` passa no CI.
- **CON-LIC-02** [Must · user · v0.1] O pacote do componente deve conter `LICENSE` (GPL-3.0) e os `COPYING`,
  `COPYING.APACHE`, `COPYING.BSD2` e `COPYING.UCD` do upstream.
- **FR-LIC-03** [Must · user · v0.1] O pacote do componente deve conter os dados compilados de todos os idiomas, o
  `phsource/` e o `dictsource/` do mesmo tarball, e o script de regeneração.
- **FR-LIC-04** [Must · user · v0.1] O script de regeneração, rodado no host a partir das fontes do pacote, deve
  reproduzir os dados compilados do pacote byte a byte.
- **CON-LIC-05** [Must · user · v0.1] O logo do projeto e qualquer arquivo que não seja GPL-compatível devem ficar fora
  do pacote do componente.

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| CON-LIC-01 | `reuse lint` | sem erro | arquivo sem licença | host |
| CON-LIC-02 | pacote gerado | os cinco arquivos presentes | arquivo ausente | host |
| FR-LIC-03 | pacote gerado | dados, fontes e script presentes | dados sem as fontes | host |
| FR-LIC-04 | regenerar a partir do pacote | dados idênticos | diferença | host |
| CON-LIC-05 | lista de arquivos do pacote | sem logo nem arquivo não compatível | arquivo fora da política | host |

## 24. Build, CI e versões

- **CON-BLD-01** [Must · user · v0.1] Toda ferramenta instalada pelo CI e pelo notebook deve ter versão exata: ESP-IDF,
  eSpeak NG, `dependencies.lock`, `requirements.txt` com `==`, `whisper.cpp` e o modelo.
- **FR-BLD-02** [Must · user · v0.1] O CI hospedado deve rodar a cada push: lint, `reuse lint`, testes do host (R1,
  R2, corpora, gerador, capacidade), testes do driver com porta falsa e os builds de §18.
- **FR-BLD-03** [Must · user · v0.1] Os testes de nível `target` e `bench` devem rodar no runner do notebook só a
  partir de uma tag, gravando o artefato do CI daquela tag.
- **FR-BLD-04** [Must · derived · v0.1] O artefato do CI deve conter o app, a imagem de dados, o `flash_args`, a
  tabela de partições e um manifesto com commit, versões e hashes.

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| CON-BLD-01 | arquivos de versão | tudo com versão exata | versão por faixa | host |
| FR-BLD-02 | push | os jobs rodam e bloqueiam o merge quando falham | job opcional | host |
| FR-BLD-03 | tag | runner do notebook grava o artefato da tag e roda `--run-bench` | gravar build local | other |
| FR-BLD-04 | artefato | cinco itens presentes | artefato sem manifesto | host |

## 25. Publicação e comunidade

- **FR-REL-01** [Must · user · v0.1] O componente deve ser publicado no ESP Component Registry como
  `isaacmiranda/espeak-ng`, a partir da pasta `components/espeak-ng/`, só por tag `espeak-ng-vX.Y.Z`.
- **FR-REL-02** [Must · user · v0.1] A versão do componente deve seguir SemVer próprio, começando em 0.1.0. A versão do
  upstream fica no `ORIGIN.md` e na descrição do manifesto.
- **FR-REL-03** [Must · user · v0.1] Antes da primeira publicação, um upload de teste ao *staging* do Registro deve
  provar que o pacote é aceito (OD-02).
- **FR-REL-04** [Must · derived · v0.1] O pacote publicado não deve conter `research/`, `seed/`, `tools/bench/` nem
  `docs/`.
- **FR-REL-05** [Must · user · v0.1] Antes da primeira publicação no Registro, uma issue ou discussion deve estar
  aberta no repositório `dfxpto-cyber/eSpeak-NG-.-Esp32`, propondo colaboração, com o texto aprovado pelo
  responsável. A release não espera resposta.
- **FR-UPS-01** [Must · user · v0.1] Se a F2 confirmar a #1611, um PR ao `espeak-ng/espeak-ng` deve estar aberto, com
  teste, trocando `iswalpha` e funções parecidas pelas do `ucd-tools`, e o link registrado no `ORIGIN.md`.
- **FR-UPS-02** [Should · user · v0.2] As correções de pronúncia pt-BR que valem para qualquer falante, encontradas na
  escuta interna ou no ASR, devem ser propostas ao `dictsource/pt_list` do upstream, cada uma com caso `test_phon`,
  conferidas contra o `master`.
- **FR-AIU-01** [Must · user · v0.1] O arquivo `AI-USE.md`, em inglês e pt-BR, deve descrever como a IA é usada no
  projeto e o que é decisão humana.

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-REL-01 | tag | versão publicada aparece no Registro | publicação de outra pasta | other |
| FR-REL-02 | manifesto | `version` SemVer; versão do upstream na descrição | versão amarrada ao upstream | host |
| FR-REL-03 | upload ao *staging* | aceito | publicação real sem o teste | other |
| FR-REL-04 | pacote gerado | lista sem as pastas proibidas | pasta proibida presente | host |
| FR-REL-05 | antes da tag | link da issue registrado; texto aprovado | publicação antes do contato | other |
| FR-UPS-01 | F2 confirmou | link do PR no `ORIGIN.md` | PR sem teste | other |
| FR-UPS-02 | entradas candidatas | PR com `test_phon` por entrada | entrada sem conferência no `master` | other |
| FR-AIU-01 | release | arquivo presente nos dois idiomas | ausente | host |

## 26. Documentação e idiomas

| Documento | Fonte | Tradução | Acompanha |
|---|---|---|---|
| Código, comentários, commits, logs | inglês | — | — |
| README, guia do integrador, exemplos, `CONTRIBUTING` | inglês | pt-BR | a cada release |
| FSD | pt-BR | resumo em inglês (`FSD-summary.en.md`) | a cada release |
| Método | pt-BR | — | — |
| Protocolo e material de escuta | pt-BR | resumo em inglês | quando publicado |
| Relatórios de medida do CI | inglês | — | — |
| Artigos | idioma do veículo | — | — |

- **FR-DOC-01** [Must · user · v0.1] Cada tradução deve levar no topo `source-revision: <hash>` do commit da fonte que
  traduz.
- **FR-DOC-02** [Must · user · v0.1] No job de release, o CI deve falhar se alguma fonte da tabela mudou depois do
  `source-revision` da sua tradução.
- **FR-DOC-03** [Must · user · v0.1] Nenhum documento do projeto deve afirmar "primeiro TTS pt-BR offline no ESP32" nem
  resultado de inteligibilidade com ouvintes sem o estudo aprovado pelo CEP.

| ID | Pré-condição · estímulo | Esperado | Não pode acontecer | Nível |
|---|---|---|---|---|
| FR-DOC-01 | traduções | campo presente | tradução sem campo | host |
| FR-DOC-02 | fonte alterada depois da tradução · job de release | falha | release verde | host |
| FR-DOC-03 | busca nos documentos | nenhuma ocorrência | afirmação presente | host · other |

---

# Parte E — Operação e verificação

## 27. Procedimentos (roteiro de leitura)

1. **Gravar:** artefato do CI (FR-BLD-04) com `bench flash`, depois de registrar o firmware encontrado na placa
   compartilhada.
2. **Subir:** `ESPK boot` e `ESPK ready` (§5); dados válidos (§12).
3. **Medir:** comandos de §5, perfis de §6, referências de §7.
4. **Escuta interna:** sessão aberta (FR-RES-09), `play` (FR-LST-03), respostas por ferramenta (FR-LST-04).
5. **Sair:** o firmware de pesquisa fica na placa, com o commit registrado na evidência.
6. **Recuperar:** dados corrompidos (§12) e placa que não enumera ficam no manual.

Os passos operacionais estão no [manual](../UserDocumentation/User-Manual.md).

## 28. Verificação e validação

### 28.0 Arquitetura de testes

| Camada | host | target | bench | listening |
|---|---|---|---|---|
| L2 firmware de pesquisa | parser do console | comandos, marcadores | perfis de carga | escuta interna (sem portão) |
| L2 ferramentas (R1, R2, corpora, ASR) | tudo | — | — | — |
| L1 componente | leitor da imagem, gerador, capacidade, núcleo compilado no host, lógica de estados | R3, memória, tempo, watchdog, async | convivência (v0.2) | — |
| L0 motor e ESP-IDF | transitivo (R1, R2) | transitivo (R3) | — | — |

Cada comportamento é testado no nível mais baixo em que o seu defeito aparece ([padrão](../Method/standards/testing.md)).

### 28.1 Aceitação: a jornada

Uma execução comum, de ponta a ponta, sobre os bytes do artefato do CI de uma tag:

1. Gravar o artefato → `ESPK boot` com o commit da tag.
2. `ESPK ready` → imagem válida.
3. `say` de um item do corpus de verificação pt-BR → `ESPK start`, `ESPK done` com `underrun=0`.
4. Hash desse item igual ao de R1.
5. `voice en`, `say` de um item en → hash igual ao de R1.
6. `cancel` no meio de uma fala longa → `ESPK cancelled` em ≤ 100 ms.

A partir da v0.2, a jornada ganha o passo 7: `load all` e os passos 3 e 4 de novo, com `heap_min` ≥ 24 576 B.

### 28.2 Rastreabilidade

A cobertura é **gerada**: `/build` cruza os IDs deste documento com `testing/test-plan.yaml` e produz a matriz e o
relatório de lacunas. Esta FSD não tem coluna de situação.

---

## Apêndice A — Imagem de dados

- Ordem dos bytes: little-endian. Alinhamento: cada arquivo começa em múltiplo de 4 bytes a partir do início do
  payload.
- O CRC-32 é o do polinômio IEEE 802.3 (o mesmo de `esp_rom_crc32_le` com semente 0), calculado da primeira entrada
  da tabela até o fim do payload.
- Os nomes são caminhos relativos ao ponto de montagem, em minúsculas (`phontab`, `pt_dict`, `voices/!v/…`,
  `lang/pt-br`).
- A tabela é ordenada por nome, para a imagem ser determinística (FR-DAT-07).

## Apêndice B — Códigos de erro

| Código | Quando |
|---|---|
| `ESP_ERR_NOT_FOUND` | partição ausente; voz ausente da imagem |
| `ESP_ERR_INVALID_CRC` | `magic` ou CRC inválidos |
| `ESP_ERR_INVALID_VERSION` | versão da imagem diferente da do motor |
| `ESP_ERR_NOT_SUPPORTED` | sem PSRAM; camada assíncrona desligada |
| `ESP_ERR_NO_MEM` | PSRAM livre abaixo do pico; fila cheia |
| `ESP_ERR_INVALID_STATE` | fora do estado exigido |
| `ESP_ERR_INVALID_ARG` | parâmetro fora do intervalo |
| `ESP_ERR_INVALID_SIZE` | texto acima do limite |
| `ESPK_ERR_CANCELLED` | síntese cancelada (base própria do componente, `0x7E00`) |

## Relacionados

- [Decisões abertas](open-issues.md)
- [Método](../Method/00-Overview.md) · [bancada](../Method/project/bancada.md) · [arquitetura](../Method/project/architecture.md)
- [Manual](../UserDocumentation/User-Manual.md)
- Evidência de partida: [`../Ideia/`](../Ideia/), [`../../seed/`](../../seed/)
