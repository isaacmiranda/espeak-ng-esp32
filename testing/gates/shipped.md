# Portão: Shipped (liberação)

**Exclusão permanente:** a evidência é só o que está commitado no repositório, o CI e o que a bancada responde agora. Nunca memória do assistente, transcrições, `docs/Ideia/` nem o relato de quem fez o trabalho.

## Requisitos

| # | Deve ser verdade | Onde olhar | Evidência |
|---|---|---|---|
| 1 | Release vem de uma tag | `gh release view <tag>` | tag aponta para o commit do portão "Ready for shipment" |
| 2 | Jornada verde nos bytes publicados | run do `release.yml` da tag | `release-verify` `success` gravando o artefato daquela tag |
| 3 | Componente publicado | ESP Component Registry, `isaacmiranda/espeak-ng` | versão = tag `espeak-ng-vX.Y.Z`; `staging` testado antes (FR-REL-03) |
| 4 | Contato com o `dfxpto` antes da 1ª publicação | link registrado | FR-REL-05 |

**Veredito:** `OPEN`, ou `SHUT` com cada achado: o requisito, onde procurou, o que achou. O verificador não corrige nada.
