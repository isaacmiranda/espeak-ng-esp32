# Portão: Load defined (fecha a Fase 0)

**Exclusão permanente:** a evidência é só o que está commitado no repositório, o CI e o que a bancada responde agora. Nunca memória do assistente, transcrições, `docs/Ideia/` nem o relato de quem fez o trabalho.

## Requisitos

| # | Deve ser verdade | Onde olhar | Evidência |
|---|---|---|---|
| 1 | Todo Must/Should tem contrato | `docs/Functionality/FSD.md` | uma linha `\| <ID> \|` numa tabela de contrato ou um bloco `id: <ID>` para cada `**FR-…**`, `**NFR-…**`, `**CON-…**` |
| 2 | Toda linha de contrato tem "Não pode acontecer" preenchido | idem | quarta coluna não vazia |
| 3 | Requisitos com origem e marco | idem | cada `**ID** [Prio · origem · marco]` |
| 4 | Sem valor proposto pendente | idem | nenhum `· proposto` em requisito; `approval_status: approved` |
| 5 | Modelos presentes | FSD §2.4 (camadas), §12.2 e Apêndice A (dados), §14.1 (interface), §15.2 (estados), §19 (configuração), §22 (segurança) | seções existem e não estão vazias |
| 6 | Três planos commitados | `docs/00-Overview.md`, `docs/Method/`, `docs/UserDocumentation/User-Manual.md` | `git ls-files` |
| 7 | Decisões abertas nomeiam o requisito bloqueado | `docs/Functionality/open-issues.md` | coluna "Bloqueia" |

## Checagens mecânicas

```bash
F=docs/Functionality/FSD.md
for id in $(grep -oE '\*\*(FR|NFR|CON)-[A-Z]+-[0-9]+\*\*' $F | tr -d '*'); do grep -qE "^\| $id |^id: $id" $F || echo "SEM CONTRATO $id"; done
grep -oE '\*\*(FR|NFR|CON)-[A-Z]+-[0-9]+\*\*' $F | sort | uniq -d          # vazio
grep -nE '^\- \*\*(FR|NFR|CON)' $F | grep -iE 'adequad|suficient|robust|razoáve|aceitáve|inteligív|apropriad|melhor esforço|se possível' # vazio
grep -n '· proposto' $F | grep -E '^\S+:\- \*\*'                         # vazio
git ls-files docs/00-Overview.md docs/Method docs/UserDocumentation | wc -l  # > 0
```

## Julgamento

- Escolha 5 contratos ao acaso (cite os IDs). Um estranho competente montaria o teste só com o contrato, sem ler código?
- Cada fase de §3 entra só com o que as anteriores entregam? Cite a fase e a entrega de que ela depende.

## Armadilhas

- Contrato cuja "Não pode acontecer" repete o esperado negado ("não passa") em vez de nomear a falha disfarçada.
- Valor numérico sem origem (nem `[user]`, nem `[seed:…]`, nem `derived`).

**Veredito:** `OPEN`, ou `SHUT` com cada achado: o requisito, onde procurou, o que achou. O verificador não corrige nada.
