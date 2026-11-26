# Lista de fármacos de referência para a fala (FSD FR-SPK-07, NFR-SPK-01)

**Situação: lista fornecida pelo responsável em 2026-11-16** (substitui a proposta do
assistente de 2026-11-08). O seed 04 pede «os fármacos mais comuns» e uma lista de 20 para
a avaliação de inteligibilidade; esta é a lista
escolhida por ele. O nome 20 veio como «Loratadin»; está aqui como «loratadina» (a confirmar).

O aparelho fala o campo como o codec o guarda (FR-SLOT-01: sem acento), em
minúsculas — por isso a coluna «falado» é a que importa para a pronúncia.

| # | Fármaco | Falado pelo aparelho |
|---|---|---|
| 1 | losartana potássica | losartana potassica |
| 2 | cloridrato de metformina | cloridrato de metformina |
| 3 | hidroclorotiazida | hidroclorotiazida |
| 4 | sinvastatina | sinvastatina |
| 5 | omeprazol | omeprazol |
| 6 | maleato de enalapril | maleato de enalapril |
| 7 | besilato de anlodipino | besilato de anlodipino |
| 8 | ácido acetilsalicílico | acido acetilsalicilico |
| 9 | glibenclamida | glibenclamida |
| 10 | insulina humana | insulina humana |
| 11 | atenolol | atenolol |
| 12 | cloridrato de fluoxetina | cloridrato de fluoxetina |
| 13 | clonazepam | clonazepam |
| 14 | dipirona | dipirona |
| 15 | paracetamol | paracetamol |
| 16 | ibuprofeno | ibuprofeno |
| 17 | amoxicilina | amoxicilina |
| 18 | prednisona | prednisona |
| 19 | sulfato de salbutamol | sulfato de salbutamol |
| 20 | loratadina | loratadina |

## Procedimento (manual)

1. Ouvir `alergia-<n>.wav` de cada linha (gerados no host com o eSpeak NG
   vendorizado, a mesma síntese do aparelho: `tests/host/speech_pcm.c`).
2. Anotar os que não forem reconhecidos de primeira: esses ganham entrada no
   `pt_extra` (FR-SPK-07) e são ouvidos de novo.
3. NFR-SPK-01: 2 avaliadores da enfermagem, ≥ 18 de 20 corretos cada, no
   aparelho, em volume de produto.
