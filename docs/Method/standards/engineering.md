# Padrão — Convenções de engenharia

Regras de construção sem ligação com o projeto. Cada uma é uma regra no presente.

- **Reutilize antes de acrescentar** — procure função, módulo, skill ou código do `seed/` antes de escrever novo.
- **A menor mudança que satisfaz a regra** — sem escopo especulativo, sem refatoração carona.
- **Um módulo por componente** — nunca dobre uma interface dentro do seu único consumidor.
- **Dependências apontam para um só lado** — camadas de baixo nunca importam as de cima.
- **Extraia núcleos puros** — separe a decisão da E/S (montador da imagem, normalização de texto, conferência de
  cabeçalho) para que o nível host as alcance.
- **Código de terceiros fica intocado** — o eSpeak NG entra como está no tarball fixado; adaptação mora ao lado
  (configuração, VFS, CMake). Uma correção necessária vai ao upstream e, até entrar lá, é um *patch* versionado com o
  motivo e o link do PR.
- **Verificação antes do commit** — build, lint e testes passam (comandos em
  [`../project/conventions.md`](../project/conventions.md)).
- **Erros falham alto** — mensagens acionáveis, sem captura silenciosa, sem código de retorno engolido.
- **Segredos e dados pessoais nunca em código nem em documentação** — só o *lugar* deles é documentado.
- **Commits** — curtos, em inglês, no imperativo, assinados (`-s`), com o id do requisito. Nunca commite saída gerada
  que não seja vetor de teste, artefato de build, chave ou dado de participante.
