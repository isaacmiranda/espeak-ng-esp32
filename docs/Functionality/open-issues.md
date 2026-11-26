# Decisões abertas

Cada item nomeia o requisito que bloqueia. O item sai daqui quando a FSD absorver a decisão.

## Decisões abertas

| ID | Decisão | Bloqueia | Como se resolve |
|---|---|---|---|
| OD-02 | O Registro aceita o pacote com os dados de todos os idiomas mais `phsource/` e `dictsource/`? A documentação não publica limite; o `espeak-ng-data` completo tem ≈ 24 MB instalado. | FR-REL-01, FR-REL-03, FR-LIC-03 | upload de teste ao *staging* (FR-REL-03). Alternativa, se recusado: pacote base (`en`, `pt`) mais pacotes de idioma — exige emenda |
