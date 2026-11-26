# Decisões abertas

Cada item nomeia o requisito que bloqueia. O item sai daqui quando a FSD absorver a decisão.

## Decisões abertas

| ID | Decisão | Bloqueia | Como se resolve |
|---|---|---|---|
| OD-01 | Resultado da F2: a divergência por acento (#1611) se confirma no alvo? Há divergência por ponto flutuante? | FR-ENG-04, FR-ENG-05, FR-UPS-01, FR-REF-04, padrão de `CONFIG_ESPK_UCD_WRAP` | experimento da F2 (R3 × R1); emenda da FSD |
| OD-02 | O Registro aceita o pacote com os dados de todos os idiomas mais `phsource/` e `dictsource/`? A documentação não publica limite; o `espeak-ng-data` completo tem ≈ 24 MB instalado. | FR-REL-01, FR-REL-03, FR-LIC-03 | upload de teste ao *staging* (FR-REL-03). Alternativa, se recusado: pacote base (`en`, `pt`) mais pacotes de idioma — exige emenda |
| OD-03 | Licença das Harvard sentences (IEEE 1969) permite redistribuir no repositório? | FR-COR-05 | conferência da licença; sem confirmação, só as frases imprevisíveis geradas |
| OD-04 | Transporte de OTA do firmware de pesquisa (as partições `ota_0`/`ota_1` existem). | nenhum requisito ainda; abre um FR futuro | decisão do responsável quando o OTA entrar no escopo |
| OD-05 | Ligação da ferramenta de escuta com a placa pela rede: transporte (Wi-Fi da placa como cliente ou SoftAP; protocolo) e segurança (autenticação, quem pode mandar `play`). | FR-LST-19 | decisão do responsável quando a ligação por rede entrar num marco; emenda com perfil de segurança próprio |
