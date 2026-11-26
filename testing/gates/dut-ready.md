# Portão: DUT ready (fecha a Fase 2)

**Exclusão permanente:** a evidência é só o que está commitado no repositório, o CI e o que a bancada responde agora. Nunca memória do assistente, transcrições, `docs/Ideia/` nem o relato de quem fez o trabalho.

## Requisitos

| # | Deve ser verdade | Onde olhar | Evidência |
|---|---|---|---|
| 1 | Cada capacidade `bench-*` é `yes` | `testing/test-plan.yaml` | `observed:` com data, commit e a saída do comando com a placa |
| 2 | `bench.yaml` bate com `discover` | `bench.yaml` (`serial` preenchido) | `python -m bench discover` agora: `dut` com o mesmo serial |
| 3 | Link udev | `/dev/espk-dut` | `ls -l /dev/espk-dut` |
| 4 | A placa é a da FSD §2.2 | `python -m bench chip-info dut` | esp32-s3, 16 MB, PSRAM, MAC igual ao registrado |
| 5 | Caminho CI → gravação | evidência em `test-results/` | artefato de um run do CI gravado com `bench flash` e `ESPK boot … commit=` desse run |
| 6 | Agenda sem item do lado do projeto | `testing/debugging-agenda.md` | cada linha resolvida ou movida com motivo |
| 7 | Firmware deixado na placa registrado | evidência da sessão | campo "deixado" no `manifest.yaml` |

## Checagens mecânicas

```bash
.venv/bin/python -m bench discover
.venv/bin/python -m bench chip-info dut
.venv/bin/python -m bench wait-event dut '^ESPK boot' --timeout 15 --reset
```

## Armadilhas

- Gravação "com sucesso" que não prova o lugar: o marcador do artefato tem de aparecer.
- Placa com o firmware do AlertAlergo tomada como a deste projeto.
- `ESPK boot` lido de um log antigo em vez de agora.

**Veredito:** `OPEN`, ou `SHUT` com cada achado: o requisito, onde procurou, o que achou. O verificador não corrige nada.
