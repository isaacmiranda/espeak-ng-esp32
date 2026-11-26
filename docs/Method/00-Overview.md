# espeak-ng-esp32 — Método (COMO)

O Método é o **contrato de construção**: as regras de como este projeto é construído e alterado. Ponto de entrada para
qualquer tarefa: **[`AI-Workflow.md`](AI-Workflow.md)**.

## Layout

| Caminho | Conteúdo |
|---|---|
| [`AI-Workflow.md`](AI-Workflow.md) | O ciclo que toda mudança segue. Leia antes de mexer em código. |
| [`standards/`](standards/) | Regras portáveis: [engenharia](standards/engineering.md), [testes](standards/testing.md), [documentação](standards/documentation.md). |
| [`project/`](project/) | Ligações deste projeto: [arquitetura](project/architecture.md), [convenções](project/conventions.md), [a bancada](project/bancada.md), [próximos passos](project/proximos-passos.md) (retomada de sessão). |

## Os três planos

| Plano | Pergunta | Documento |
|---|---|---|
| **O QUÊ** | O que precisa ser verdade? | [`../Functionality/`](../Functionality/) (a FSD, criada pelo `/define`) |
| **COMO** | Como é construído e alterado? | Este diretório |
| **OPERAR** | Como rodo? | [`../UserDocumentation/User-Manual.md`](../UserDocumentation/User-Manual.md) |

A FSD define o alvo; o Método define o caminho; o manual descreve o sistema que roda. O `CLAUDE.md` **não** é um plano:
configura o assistente e aponta para cá, sem regras próprias.

## O que mora aqui

Uma regra é do Método quando restringe **como o código é escrito, estruturado ou verificado** sem ser observável de fora
do sistema em execução.

| Frase | Plano | Por quê |
|---|---|---|
| "A síntese não para a tela nem o rádio por mais de X ms" | FSD | Um testador de caixa-preta verifica |
| "As fontes do eSpeak NG ficam sem alteração" | Método | Invisível de fora; é como o código é construído |
| "Ligue a placa na USB do notebook" | Manual | Quem lê está com a placa na mão |
| "Grave com `python -m bench flash dut <artefato>`" | Método | É como o sistema é alterado e verificado |

## Regra de documentação

Os três planos são no presente e de lugar único. Ver [`standards/documentation.md`](standards/documentation.md).
