# Padrão — Documentação

Governança dos três planos. A tabela de roteamento está em [`../../00-Overview.md`](../../00-Overview.md) e em nenhum
outro lugar.

- **Presente, não história.** Apague "agora usa", "antes", "a partir de", "decidimos", "legado".
- **Um só lugar.** Todo fato mora num lugar; os outros fazem link.
- **Sem quarto plano.** "Design", "Notas", "Arquitetura" fora dos três planos é COMO com outro chapéu.
- **Um manual, capítulos e não arquivos.** Toda a operação vive em `UserDocumentation/User-Manual.md`.
- **Passos de teste não ficam na FSD.** A FSD nomeia o nível e o critério; o plano de testes e os testes têm os passos.
  Exceção deliberada: o protocolo do estudo de escuta é requisito (o *quê* se mede e como se decide), por isso mora na
  FSD; o roteiro de aplicação mora no manual.
- **O `CLAUDE.md` não é Método.** Configura o assistente e aponta.
- **Sem rascunho.** Nada de `TODO` em documento no ramo principal; o que está pendente mora em
  `docs/Functionality/open-issues.md` ou em `testing/debugging-agenda.md`.
- **Dois idiomas.** README e guia de contribuição existem em inglês e pt-BR desde o início; a política para FSD, Método
  e manual (qual é a fonte, como a tradução acompanha) é fixada na FSD. Uma tradução que discorda da fonte está velha.
- **Afirmações sobre o estado da arte** citam a fonte e a data da busca (`docs/Ideia/pesquisa-2026-11-26/`).
