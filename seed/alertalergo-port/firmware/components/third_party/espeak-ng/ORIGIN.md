# espeak-ng — síntese de fala (FSD §18.2, §29.1, CON-SW-05)

| Item | Valor |
|---|---|
| Origem | https://github.com/espeak-ng/espeak-ng |
| Versão | tag `1.52.0` — tarball `archive/refs/tags/1.52.0.tar.gz`, SHA-256 `bb4338102ff3b49a81423da8a1a158b420124b055b60fa76cfb4b18677130a23` |
| Licença | GPL-3.0-or-later (`upstream/COPYING`); partes sob Apache-2.0, BSD-2 e licença do Unicode (`upstream/COPYING.*`) — FSD §29.1 |
| Alterações | nenhuma nas fontes (`upstream/`); `config/config.h` e `CMakeLists.txt` são deste projeto |
| Gerado por | `scripts/gen-espeak.sh` (baixa, confere o SHA-256, copia, compila os dados); rodar de novo dá `git diff` vazio |

## O que entra

- `upstream/src/libespeak-ng`, `upstream/src/include/espeak-ng`, `upstream/src/ucd-tools/src`:
  as fontes da biblioteca. O `CMakeLists.txt` compila só o runtime síncrono; MBROLA,
  Klatt, speech-player, sonic e o modo assíncrono ficam fora (arquivos presentes, não
  compilados).
- `data/`: os dados que a voz pt-BR lê, compilados pelo `espeak-ng --compile` do próprio
  1.52.0, construído no host pelo script a partir das fontes `phsource/` e
  `dictsource/` do tarball. São 735 518 bytes (`data.sha256`). Vão para a partição
  `espeak` (NFR-SW-02), não para o app.
  - `lang/pt-br` é cópia de `espeak-ng-data/lang/roa/pt-BR`: `espeak_ng_SetVoiceByFile`
    converte o caminho para minúsculas.

## Fonte correspondente dos dados (GPL)

Os dados são compilados de `phsource/` e `dictsource/` do tarball acima. A release
(FR-3P-01) leva o tarball upstream junto com o código deste repositório.
