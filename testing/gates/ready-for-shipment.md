# Portão: Ready for shipment (fecha a Fase 3 para um marco: v0.1 ou v0.2)

**Exclusão permanente:** a evidência é só o que está commitado no repositório, o CI e o que a bancada responde agora. Nunca memória do assistente, transcrições, `docs/Ideia/` nem o relato de quem fez o trabalho.

## Requisitos

| # | Deve ser verdade | Onde olhar | Evidência |
|---|---|---|---|
| 1 | Todo Must/Should do marco atendido | FSD × `testing/test-plan.yaml` | cada ID do marco tem ≥ 1 teste `successful` no commit atual, com o "não pode acontecer" checado |
| 2 | Jornada verde | `JRN-01`…`JRN-06` | `successful` no commit atual |
| 3 | Reconcile vazio nos dois sentidos | plano × `tests/`, `tools/bench/tests/` | nenhuma entrada sem `impl`; nenhum executável sem entrada ou sem `proven_by` |
| 4 | Decisões abertas do marco fechadas | `docs/Functionality/open-issues.md` | OD-01 e OD-02 resolvidas para a v0.1 |
| 5 | Manual atual | `docs/UserDocumentation/User-Manual.md` | status honesto; capítulos 1–3 e 5 escritos |
| 6 | Traduções em dia | arquivos com `source-revision:` | FR-DOC-02 verde |
| 7 | Nenhuma afirmação proibida | todo o repositório | FR-DOC-03 verde |

## Armadilhas

- Resultado `successful` de um commit anterior contado como atual.
- Requisito "atendido" com um teste verde e outro `not done`.
- Número do ASR chamado de inteligibilidade.

**Veredito:** `OPEN`, ou `SHUT` com cada achado: o requisito, onde procurou, o que achou. O verificador não corrige nada.
