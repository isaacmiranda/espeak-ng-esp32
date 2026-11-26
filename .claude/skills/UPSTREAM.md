# Origem das skills de fase

Este é o **único arquivo do kit que fala do testbench Raspberry Pi** do upstream. Tudo o mais descreve a bancada (notebook com a placa por USB)
que existe aqui.

- **Upstream:** https://github.com/SensorsIot/Embedded-AI-Harness
- **Commit:** `db6a0933075bb9ff5a99bb8e307a54b6a01af57d` (09/10/2026)
- **Licença:** MIT (`UPSTREAM-LICENSE`)
- **Idioma:** as skills ficam em inglês, como no upstream; os documentos do projeto, em português do Brasil.

- **Caminho do porte:** o porte foi feito uma vez no kit `legua-bancada` (commit `7a986b1`, mesmo commit do upstream) e
  adaptado aqui: VM com repasse USB → notebook com a placa direto na USB; PlatformIO → ESP-IDF puro (skill `esp-idf`);
  sem nível `sim` (um só dispositivo, sem `sim-legua`); segurança de RF → segurança auditiva; prefixo `/dev/espk-`.

Para atualizar: `diff` do upstream entre o commit acima e o novo, e reaplicar o porte nos trechos abaixo.

## Skills trazidas e o que mudou

| Arquivo | Mudança (termo de origem → porte) |
|---|---|
| `grill-me/SKILL.md` | igual |
| `define/SKILL.md` | tabela de atividades: "Testbench skills" → "Bench skills"; evidência "captured by testbench skills" → "captured by the bench driver"; linha do pacote `esp32`: só NVS e watchdog (as bibliotecas de WiFi, BLE, MQTT, OTA, portal cativo, USB HID e log por rede não vieram) |
| `define/references/authoring.md` | evidência "captured by testbench skills" → "captured by the bench driver" |
| `define/references/three-planes.md` | exemplo de OPERAR: "Flash the SD card" / "POST /api/sdr/reset" → "plug the board into the USB port of the bench notebook" / "`ls /dev/espk-*`" |
| `define/references/templates/00-Overview.md` | exemplo "Raspberry Pi Imager" → "plug the board into the USB port of the bench notebook" |
| `define/references/domains/esp32.md` | removidas as linhas e a lista de arquivos das bibliotecas WiFi, portal cativo, MQTT, BLE, BLE NUS, OTA, USB HID, log e Ethernet, e os parâmetros sem uso (`reconnect_deadline_s`, `offline_buffer_depth`, `ble_idle_timeout_s`, `ota_max_stall_ms`) |
| `harness/SKILL.md` | descrição e tabela: passo 4 (capacidades da bancada começam `unproven`, não "como declaradas"), passo 5 (escrever `tools/bench/` com testes em porta falsa; `UDP logging` → canal de log do produto), passo 6 (`setup-action` → `conventions.md` e `bancada` §CI; `testbench` → `bench flash`), passo 7 (devcontainer → o notebook da bancada; etiqueta `testbench` → `bench-notebook`); `chip/info`/`slot` → `bench chip-info`/`role`; pergunta 1: a bancada **entra** na pauta de depuração; capacidade `release-verification` começa `unproven` |
| `commission/SKILL.md` | reescrita: "A lei: nenhum projeto testa o testbench" → "a bancada é equipamento do projeto, começa `unproven`"; "descobrir o testbench" (`$WB`, `/api/info`, `/api/wifi/mode`) → "comissionar a bancada" (`bench discover`, `pytest tools/bench`); `/api/devices`, `/api/chip/info` → `bench chip-info`; `/api/flash` → `bench flash`; `/api/serial/monitor` → `bench wait-event`; slot → papel; "pedido de mudança ao testbench" → mudança em `tools/bench/` com o teste; acrescentada a segurança auditiva (volume de bancada); `gh run download` mantido |
| `build/SKILL.md` | "run on the testbench" → host/sim/bench; portão de Fase 2 ("testbench is commissioned" → "bench is commissioned"); tabela de despacho: `esp-idf-handling`/`esp-pio-handling`, `testbench-*`, `testbench-test-handling`, `setup-action` → `esp-idf`, `bancada`, `conventions.md`; verificação de liberação com `bench flash` e `pytest --run-bench`; "testbench powered off" → notebook sem a placa; índice do pacote `esp32` (só NVS e watchdog) |
| `build/references/change-request.md` | "capability the testbench never declared" → "the bench never declared in `bench.yaml` or the driver" |
| `build/references/gate-checks.md` | "DUT and slot" → "DUT and bench roles"; registro de Fase 2: "testbench record" → "bench record" (comandos do driver, repasse, links, `bench.yaml` = `discover`) |
| `build/references/test-architecture.md` | acrescentado o nível `sim` à tabela de níveis |
| `build/references/test-design.md` | "The testbench is not on this list" → "The bench is on this list"; estados a limpar (WiFi/MQTT/RFC2217/SDR → (NVM, link udev, porta única)); referências de segredo (`WB_TEST_WIFI_PASSWORD`, `mqtt-test`) → `ESPK_TEST_KEY` |
| `build/references/test-lifecycle.md` | `available: yes` "como declarado" para capacidades do testbench → a bancada começa `unproven`; "change request on the testbench repo" → capacidade nova do driver ou *seam*; testbench desligado → notebook sem a placa |
| `build/references/domains/esp32/` | mantidos `nvs-test-cases.md` e `watchdog-test-cases.md` (sem dependência do testbench); **não vieram** `wifi`, `captive-portal`, `mqtt`, `ble`, `ota`, `usb-hid` e `logging` (o produto não usa esses recursos; os dois últimos dependiam de `/api/udplog`, `/api/ble/*`, `/api/mqtt/*`) |
| `define/references/*` (demais) | iguais; os exemplos com MQTT/WiFi/BLE em `requirement-quality.md`, `system-models.md`, `example-output.md` e `complexity-scaling.md` ilustram o **estilo** de requisito e não se referem ao testbench: ficaram |

## Skills do upstream que não vieram

| Skill | O que cobre aqui |
|---|---|
| `testbench-install`, `testbench-integration`, `testbench-test-handling` | `bancada` e `docs/Method/project/bancada.md` |
| `testbench-ble`, `testbench-wifi`, `testbench-mqtt`, `testbench-logging` | nada (o produto não usa); o canal de log do produto é a telemetria serial (`bench telemetry`) |
| `testbench-debug` (OpenOCD/JTAG) | nada por enquanto; um depurador seria capacidade nova do driver |
| `esp-idf-handling`, `esp-pio-handling` | `esp-idf` |
| `setup-action` | `conventions.md` e `bancada.md` §CI |
| `sdr-receiver`, `signal-generator` | nada (a bancada não tem SDR nem gerador; o projeto não usa rádio para a fala) |

Mudanças posteriores nas skills de fase entram aqui, com o commit deste repositório.
