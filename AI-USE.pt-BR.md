<!-- source-revision: da7f901 -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# Como a IA é usada neste projeto

*[English](AI-USE.md)*

Este repositório é construído com um assistente de programação por IA (Claude Code, da Anthropic) que trabalha sob um
método escrito (`docs/Method/AI-Workflow.md`). Esta página diz o que o assistente faz e o que só uma pessoa decide.

## O que o assistente faz

- Escreve e edita código, testes, scripts e documentação, um requisito de cada vez. Toda mudança cita o requisito da
  especificação (`docs/Functionality/FSD.md`) que ela atende.
- Escreve o teste primeiro e o executa: no host, na placa de referência (uma Waveshare ESP32-S3-RLCD-4.2 no notebook
  de desenvolvimento, pelo driver de bancada `python -m bench`) e no CI.
- Registra o que aconteceu no plano de testes (`testing/test-plan.yaml`), com o commit em que rodou. Resultado que não
  rodou fica `not done`; requisito que falha é registrado como falha, com a causa.
- Propõe valores e comportamentos que a especificação ainda não diz. A proposta é marcada como tal e só vira requisito
  quando a pessoa responsável a aceita.
- Faz commits com o trailer `Co-Authored-By` que nomeia o modelo, para que a autoria de cada commit seja visível.

## O que só uma pessoa decide

- **O que o projeto deve fazer**: aceitar ou recusar um requisito, um valor ou uma mudança da especificação.
- **Liberações**: a tag, a publicação no ESP Component Registry e o registro do runner de CI no notebook. O assistente
  nunca cria tag, nunca publica e nunca faz `push` sem ser pedido.
- **Tudo o que é público e dirigido a outros**: o pull request ao upstream, a mensagem a outros mantenedores, o texto
  de qualquer anúncio.
- **Tudo o que pode causar dano**: som acima do volume de bancada, com ouvintes presentes; mudar o sistema com
  `sudo`; apagar ou reescrever histórico que já foi enviado.
- **O estudo de escuta**: o protocolo, a aprovação ética (CEP / Plataforma Brasil), quem ouve e toda afirmação sobre
  inteligibilidade. Nenhuma afirmação sobre ouvintes é feita sem o estudo aprovado.

## O que o assistente não decide e não afirma

Um teste que passa na placa é evidência sobre a placa, não sobre ouvintes. As pontuações de reconhecimento
automático de fala, quando existirem, são estimativas e levam esse rótulo. O projeto não afirma ser o primeiro
sintetizador de fala pt-BR offline no ESP32.

## Material de terceiros que o assistente trouxe

Cada item tem versão fixada e origem registrada; uma pessoa os revisa antes de uma versão.

- **Lista de palavras**: a lista `por_news_2022_10K` do Leipzig Corpora Collection (CC BY 4.0, `LICENSES/CC-BY-4.0.txt`)
  alimenta o corpus de escuta em pt-BR. É texto de notícias em português, não específico do português do Brasil, e
  recebe esse rótulo.
- **Reconhecimento automático de fala**: whisper.cpp `v1.9.6` com o modelo `ggml-small.bin`, ambos fixados por SHA-256
  em `tools/asr/pins.env`, dão a taxa de erro de caracteres e de palavras. Todo número desses leva a ressalva
  "estimativa por reconhecimento automático; não é medida de inteligibilidade com ouvintes".
- **Frases**: as frases "semanticamente imprevisíveis" seguem o desenho de Benoit et al. (1996); o gerador é
  `tools/corpus/sus.py`.
