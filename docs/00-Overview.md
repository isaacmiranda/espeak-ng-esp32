# espeak-ng-esp32 — Documentação / Documentation

*Português · English summary at the end*

Três planos, três perguntas, três leitores. Toda frase pertence a exatamente um deles.

| Plano | Pergunta | Diretório | Leitor |
|---|---|---|---|
| **O QUÊ** | O que precisa ser verdade sobre o componente e o estudo? | [`Functionality/`](Functionality/) | Quem julga se está correto: revisor, testador, avaliador do estudo |
| **COMO** | Como é construído e alterado? | [`Method/`](Method/) | Quem escreve a próxima mudança, pessoa ou agente |
| **OPERAR** | Como instalo, uso e conduzo uma sessão de escuta? | [`UserDocumentation/`](UserDocumentation/) | Quem integra o componente, opera a bancada ou aplica o teste com ouvintes |

**Ordem de autoridade: a FSD define o alvo; o Método define o caminho.** Em conflito, a FSD vence em *o que precisa ser
verdade* e o Método vence em *como chegar lá*. A documentação do usuário descreve o sistema como construído: se
discordar de um dos dois, está velha.

Nenhum dos três carrega história nem narrativa de justificativas: isso mora no `git log`. A ideia original, o
levantamento do estado da arte e o porte de partida estão em [`Ideia/`](Ideia/) e em [`../seed/`](../seed/), e saem à
medida que a FSD os absorve.

## Por onde começar

| Se você está… | Leia |
|---|---|
| Fazendo uma mudança | [`Method/AI-Workflow.md`](Method/AI-Workflow.md) |
| Julgando a correção | `Functionality/` (vazio até o `/define`) |
| Operando a bancada ou uma sessão de escuta | [`UserDocumentation/User-Manual.md`](UserDocumentation/User-Manual.md) |
| Querendo entender a bancada | [`Method/project/bancada.md`](Method/project/bancada.md) |
| Começando o projeto | [`Ideia/achados-pre-define.md`](Ideia/achados-pre-define.md), depois `/grill-me` e `/define` |

## Roteando uma frase nova

Pergunte em ordem; o primeiro sim vence:

1. Observável de fora e precisa ser verdade → **Functionality**
2. Restringe como o código é escrito ou verificado → **Method**
3. Diz a uma pessoa como rodar, integrar ou aplicar o teste → **UserDocumentation**
4. É sobre colaborar com o assistente de IA → `CLAUDE.md`, que não é um plano
5. Por que uma decisão passada foi tomada → a mensagem do commit

Duas perguntas resolvem os casos difíceis. *Um testador de caixa-preta consegue verificar?* Se sim, é O QUÊ. *Sobreviveria
a uma reescrita em outra linguagem?* Se não, é COMO.

Exemplos: *"a primeira amostra de áudio sai em até X ms depois do pedido"* é Functionality. *"as fontes do eSpeak NG
não são alteradas"* é Method. *"Ponha o fone no ouvinte e toque a lista A"* é UserDocumentation.

## Não há arquivo de decisões

Uma decisão tomada deixa seu **efeito** como conteúdo no presente, no plano que ela governa, e a razão na mensagem do
commit. Mais nada é registrado.

## Regras de escrita

**Presente.** Escreva o que é verdade agora. Sem história, sem "agora usa", "antes", "decidimos", "legado".
**Um só lugar.** Todo fato é dito uma vez; onde mais for preciso, link.

---

## English summary

Three planes: **Functionality** (what must be true — the FSD), **Method** (how it is built and changed), and
**UserDocumentation** (how to install, integrate, operate the bench and run a listening session). The FSD sets the
target, the Method sets the path; the user documentation describes what was built. No decision log: decisions leave
their effect in the plane they govern and their reason in the commit message. The seed material (idea, state-of-the-art
survey, starting port) lives in [`Ideia/`](Ideia/) and [`../seed/`](../seed/) until the FSD absorbs it. The planes are
written in pt-BR first; the English versions follow the policy fixed in the FSD.
