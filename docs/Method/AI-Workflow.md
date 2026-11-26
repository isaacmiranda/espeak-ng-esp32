# espeak-ng-esp32 — Fluxo de trabalho com IA (o contrato de construção)

Leia antes de qualquer mudança. É assim que a funcionalidade nova é construída e que a documentação acompanha.

## O ciclo

**1. Localize o contrato.** Ache a regra da FSD que o trabalho serve, em `docs/Functionality/`. Se não houver, o
trabalho começa definindo o **O QUÊ** (um requisito novo, atômico e falseável) pelo `/define`, não escrevendo código.
Mudança sem regra é escopo extra ou requisito não documentado; os dois se resolvem antes da implementação. O código em
`seed/` não é contrato: é evidência que a FSD absorve ou descarta.

**2. Construa pelo Método.** Siga [`standards/`](standards/) e [`project/`](project/). Reuse antes de criar — em
especial o porte de `seed/alertalergo-port/`, que já roda na placa. A menor mudança que satisfaz a regra: sem escopo
especulativo, sem refatoração carona.

**3. Teste, o portão.** Uma mudança não está pronta até o teste existir e passar, **no nível mais barato que pega a
falha** (`host` → `target` → `bench`; `listening` só para o que só um ouvinte decide;
[`standards/testing.md`](standards/testing.md)). O teste nasce antes do código e começa vermelho (`xfail`). Correção de
defeito reproduz a falha primeiro. Tudo o que precisa de placa roda atrás do portão da jornada, com `pytest --run-bench`.

**4. Reconcilie os planos.**
- A **FSD** absorve o comportamento novo ou alterado. Confira contra o código; não transcreva defeito como requisito.
- O **manual** absorve o que um integrador, operador ou aplicador do teste notaria.
- O **Método** só muda quando a lição vale universalmente para este projeto: diga qual regra entra e por quê.
- Tudo no presente. Os documentos públicos acompanham nos dois idiomas, conforme a política da FSD.

**5. Confira nas duas direções.** Todo teste declarado em `testing/test-plan.yaml` existe no código, e todo teste no
código está declarado (*reconcile*). Todo comando `bench …` citado nos documentos existe em `tools/bench/` e vice-versa:

```bash
python -m bench --help            # lista dos comandos do driver
grep -rhoE "bench [a-z-]+" docs .claude CLAUDE.md | sort -u   # os citados
```

## Portão de qualidade do requisito

Antes de entrar na FSD, um requisito é **atômico** (uma obrigação), **falseável** (pré-condição, estímulo, resposta
observável, prazo, tolerância, comportamento na falha, nível de teste), **sem palavras vagas** (*adequado, natural,
inteligível, razoável, suficiente, robusto, aceitável, melhor esforço*) e **com proveniência** (`[user]`, `[derived]`,
`[code]`, `[pack:esp32]`, `[seed:alertalergo]`, `[lit:<fonte>]`). "Inteligível" só entra com o método de medida, a
população de ouvintes e o limiar.

## Gravando uma mudança na placa

A bancada roda a partir do **artefato do CI**, não do que está compilado no notebook. Para iterar, compile localmente
nas mesmas versões fixadas do CI e grave com `bench flash`; para fechar requisito e para sessão de escuta que gera dado
do estudo, grave o artefato do CI e registre seu commit. **Nunca** controle a placa por um terminal serial aberto à mão:
todo comando passa por `python -m bench`. Precisar de um terminal à mão significa que falta uma capacidade ao driver.

## Papéis

Qualquer mudança pode tocar a FSD e o manual. Mudar o Método re-escopa toda mudança futura. As skills de fase
(`.claude/skills/`) são o porte do upstream; toda mudança nelas entra também em `.claude/skills/UPSTREAM.md`.
