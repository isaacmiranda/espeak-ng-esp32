# Contributing / Como contribuir

*English below · Português abaixo*

## English

Thank you for your interest. The project is in **Phase 0 (definition)**: the specification is being written, so the
most useful contributions right now are issues — reports of running eSpeak NG on ESP32 boards, measurements, pt-BR
pronunciation problems, and pointers to related work.

- **Every code change cites the requirement it serves** (`docs/Functionality/`). A change without one starts as an
  issue proposing the requirement.
- **eSpeak NG sources stay unmodified.** Engine fixes go to [espeak-ng](https://github.com/espeak-ng/espeak-ng)
  first; reference the upstream PR in your issue.
- **Tests first**: every change brings the test that proves it, at the cheapest tier that catches the defect (host
  before target).
- **License**: contributions are accepted under GPL-3.0-or-later. Sign off your commits (`git commit -s`,
  [DCO](https://developercertificate.org/)). Add SPDX headers to new files.
- **No personal data**: listening-study data that could identify a person never enters the repository.
- Commit messages: short, imperative, in English, with the requirement id, e.g. `Add data partition reader (FR-DAT-01)`.
- AI assistance is used in this repository and must be disclosed in the pull request when you use it.

## Português

Obrigado pelo interesse. O projeto está na **Fase 0 (definição)**: a especificação está sendo escrita, então as
contribuições mais úteis agora são *issues* — relatos de uso do eSpeak NG em placas ESP32, medições, problemas de
pronúncia em pt-BR e indicações de trabalhos relacionados.

- **Toda mudança de código cita o requisito que atende** (`docs/Functionality/`). Mudança sem requisito começa como
  *issue* propondo o requisito.
- **As fontes do eSpeak NG ficam sem alteração.** Correções do motor vão primeiro ao
  [espeak-ng](https://github.com/espeak-ng/espeak-ng); cite o PR do upstream na sua *issue*.
- **Teste primeiro**: toda mudança traz o teste que a prova, no nível mais barato que pega o defeito (host antes da
  placa).
- **Licença**: contribuições são aceitas sob GPL-3.0-or-later. Assine os commits (`git commit -s`,
  [DCO](https://developercertificate.org/)). Ponha cabeçalho SPDX em arquivos novos.
- **Sem dados pessoais**: dado do estudo de escuta que identifique uma pessoa nunca entra no repositório.
- Mensagens de commit: curtas, no imperativo, em inglês, com o id do requisito.
- Este repositório usa assistência de IA; declare no *pull request* quando você usar.
