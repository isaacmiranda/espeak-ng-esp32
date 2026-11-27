<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# Rascunho: mensagem ao autor de `dfxpto-cyber/eSpeak-NG-.-Esp32` (não enviada; FR-REL-05)

Canal: issue ou discussão no repositório dele, ou o e-mail público do perfil; escolha do responsável. Texto público: nada
de dados pessoais além do que já está no repositório.

---

Olá, Domingos,

Mantenho o `espeak-ng-esp32`, outro componente ESP-IDF para o eSpeak NG 1.52.0 (GPL-3.0-or-later, fontes do upstream sem
alteração, dados numa partição própria, foco em pt-BR e en, medições na placa). Vi o seu porte em pt-PT, que usa a mesma
ideia de partição bruta, e quero deixar claro que o meu trabalho cita o seu como trabalho anterior.

Duas coisas, sem compromisso:

1. **Comparação.** Pretendo medir, na mesma placa e com o mesmo corpus, os dois componentes e o `arduino-espeak-ng`
   (memória, latência, PCM igual ao do upstream). Se preferir que o seu apareça de outra forma, ou não apareça, diga.
2. **Achado sobre acentos.** O eSpeak NG só trata letras acentuadas pela `ucd-tools` quando `src/include/compat` está no
   caminho de inclusão; sem isso, a libc da newlib soletra as letras. Se o seu porte já cuida disso, ótimo; se não, pode
   valer a pena conferir com "ação você".

Obrigado pelo trabalho, e pelo código aberto.

[assinatura do responsável]

---

Antes de enviar: o responsável confere se o achado 2 se confirma no experimento descrito em `upstream-1611.md` e se quer
mesmo propor a comparação (FR-REF-08 é v0.2).
