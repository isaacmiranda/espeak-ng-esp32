<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# Rascunho: upstream espeak-ng#1611 (não enviado)

## O achado (verificado em 2026-11-27, antes de qualquer envio)

O build CMake do upstream 1.52.0 já resolve a classificação de caracteres largos sozinho:
`src/CMakeLists.txt` faz `target_include_directories(espeak-include INTERFACE include include/compat)`, e
`src/include/compat/wctype.h` redefine `iswalpha`, `iswupper`, `iswspace`, `iswdigit`… como `ucd_*`. No R1 (build CMake
do tarball) o `nm` mostra `ucd_isalpha` indefinido em 6 objetos e nenhum `iswalpha`.

O componente deste projeto compila as fontes pelo ESP-IDF com `PRIV_INCLUDE_DIRS config upstream/src/include …`: **sem
`upstream/src/include/compat`**. Por isso a libc da newlib (C locale) foi chamada, e as letras acentuadas foram
soletradas. O `espk_wrap.c` (FR-ENG-04) refaz em tempo de link o que o `compat/wctype.h` faz em tempo de compilação.

Consequências a decidir (do responsável):

1. **Não há correção a propor ao upstream pelo caminho do `isw*`**: o upstream já tem o shim. Um PR que "troque `iswalpha`
   pelas do `ucd-tools`" seria redundante. O que o upstream poderia ouvir é a documentação do caso: quem compila as fontes
   fora do CMake/autotools precisa de `src/include/compat` no caminho de inclusão.
2. O shim tem um erro de digitação no upstream: `#define toupper udc_toupper` (deveria ser `ucd_toupper`). Hoje ninguém
   chama `toupper` nessas unidades, então não quebra; é candidato a PR pequeno e verdadeiro.
3. **Feito em 2026-11-27 (FSD 0.5.0):** trocar o wrap por `upstream/src/include/compat` no `PRIV_INCLUDE_DIRS` (igual ao upstream, sem
   código nosso). Experimento a rodar antes de decidir: build com essa mudança, PCM da placa × R1 nos 100 itens
   (`tests/target/test_equivalence.py`, silencioso) e o modo intacto. Se igual, o wrap sai e o FR-ENG-04/FR-UPS-01 mudam
   (emenda da FSD).

Experimento concluído: PCM da placa = R1 em 100 de 100 itens com o `compat` e sem o wrap; modo intacto verde. Mesmo assim, **não afirmar** que o upstream tem um defeito.

## Rascunho do comentário na #1611 (em inglês; experimento feito; aguardando aprovação do responsável)

> For anyone building the sources outside CMake/autotools (we hit this with ESP-IDF on ESP32, newlib): the engine's
> `isw*` calls only classify accented letters correctly when `src/include/compat` is on the include path, because
> `compat/wctype.h` maps them to `ucd-tools`. Without it the C library's `iswalpha` is used, which in newlib's C locale
> knows only ASCII, and accented text is spelled letter by letter. Adding that directory to the include path fixed it
> for us with the sources unmodified.

## Rascunho de PR pequeno (separado, opcional)

Título: `compat/wctype.h: fix typo udc_toupper -> ucd_toupper`

Corpo: "`ucd_toupper` is the function declared in `ucd/ucd.h`; `udc_toupper` does not exist, so any translation unit
that includes the shim and calls `toupper()` fails to build. No unit does today."

Patch (uma linha, em `src/include/compat/wctype.h`): `-#define toupper udc_toupper` / `+#define toupper ucd_toupper`.
Verificar antes: compilar uma unidade que chame `toupper` com o shim. Só abrir o PR com o responsável. Registrar o link no
`components/espeak-ng/ORIGIN.md` depois que ele abrir.
