# Portão: DUT ready (fecha a Fase 2)

**Exclusão permanente:** a evidência é só o que está commitado no repositório, o CI e o que a bancada responde agora. Nunca memória do assistente, transcrições, `docs/Ideia/` nem o relato de quem fez o trabalho.

## Requisitos

| # | Deve ser verdade | Onde olhar | Evidência |
|---|---|---|---|
| 1 | Cada capacidade `bench-*` é `yes` | `testing/test-plan.yaml` | `observed:` com data, commit e a saída do comando com a placa |
| 2 | `bench.yaml` bate com `discover` | `bench.yaml` (`serial` preenchido) | `python -m bench discover` agora: `dut` com o mesmo serial |
| 3 | Link udev | `/dev/espk-dut` | `ls -l /dev/espk-dut` |
| 4 | A placa é a da FSD §2.2 | `python -m bench chip-info dut` | esp32-s3, 16 MB, PSRAM, MAC igual ao registrado |
| 5 | Caminho CI → gravação | `testing/test-plan.yaml` → `bench-flash.observed`; e agora: `gh run list -w ci` + `bench wait-event dut '^ESPK boot' --reset` | o run citado existe e foi `success`; o `commit=` do `ESPK boot` de agora é o do run mais recente gravado |
| 6 | Agenda sem item do lado do projeto | `testing/debugging-agenda.md` | cada linha resolvida ou movida com motivo |
| 7 | Firmware encontrado e deixado registrados | `testing/test-plan.yaml` → `dut.observed` (`found`, `left`) | os dois campos preenchidos; `left` bate com o `ESPK boot` de agora |

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
- `test-results/` está no `.gitignore`: a evidência que conta é o `observed:` do plano e a resposta da bancada agora.

**Veredito:** `OPEN`, ou `SHUT` com cada achado: o requisito, onde procurou, o que achou. O verificador não corrige nada.
