#!/usr/bin/env bash
# Vendoriza o eSpeak NG 1.52.0 (FSD §29.1, CON-SW-05, regra 10) e compila os
# dados de idioma pt-BR (NFR-SW-02), a partir do tarball upstream com SHA-256
# travado. Reprodutível: rodar de novo tem de dar `git diff` vazio.
#
#   scripts/gen-espeak.sh
#
# Escreve firmware/components/third_party/espeak-ng/:
#   upstream/   fontes da libespeak-ng e da ucd-tools, sem alteração
#   data/       os 6 arquivos de dados que a voz pt-BR lê (compilados pelo
#               próprio espeak-ng 1.52.0 construído aqui no host)
# O ORIGIN.md e o CMakeLists.txt de lá são deste projeto (não são gerados).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VER=1.52.0
URL="https://github.com/espeak-ng/espeak-ng/archive/refs/tags/$VER.tar.gz"
SHA256=bb4338102ff3b49a81423da8a1a158b420124b055b60fa76cfb4b18677130a23
DST="$ROOT/firmware/components/third_party/espeak-ng"
WORK="${TMPDIR:-/tmp}/aa-espeak-$VER"

mkdir -p "$WORK"
tgz="$WORK/espeak-ng-$VER.tar.gz"
[ -f "$tgz" ] || curl -sSLf -o "$tgz" "$URL"
echo "$SHA256  $tgz" | sha256sum -c --quiet
rm -rf "$WORK/src" && mkdir -p "$WORK/src"
tar -xzf "$tgz" -C "$WORK/src"
SRC="$WORK/src/espeak-ng-$VER"

# --- fontes (só o que o runtime compila; MBROLA, Klatt, sonic, async: fora)
rm -rf "$DST/upstream"
mkdir -p "$DST/upstream/src/libespeak-ng" "$DST/upstream/src/ucd-tools/src/include/ucd" \
         "$DST/upstream/src/include/espeak-ng"
cp "$SRC"/COPYING "$SRC"/COPYING.APACHE "$SRC"/COPYING.BSD2 "$SRC"/COPYING.UCD "$DST/upstream/"
cp "$SRC"/src/libespeak-ng/*.c "$SRC"/src/libespeak-ng/*.h "$DST/upstream/src/libespeak-ng/"
cp "$SRC"/src/include/espeak-ng/*.h "$DST/upstream/src/include/espeak-ng/"
cp "$SRC"/src/ucd-tools/src/*.c "$DST/upstream/src/ucd-tools/src/"
cp "$SRC"/src/ucd-tools/src/include/ucd/*.h "$DST/upstream/src/ucd-tools/src/include/ucd/"
cp "$SRC"/src/ucd-tools/COPYING "$DST/upstream/src/ucd-tools/" 2>/dev/null || true

# --- dados: espeak-ng do host, compilado só para gerar os dados
# pt_listx (o pt_extra de FR-SPK-07): exceções de pronúncia do projeto; o CMake do eSpeak
# o copia e o compilador o lê junto com pt_rules e pt_list.
cp "$DST/pt_listx" "$SRC/dictsource/pt_listx"
B="$WORK/build"
cmake -S "$SRC" -B "$B" -G Ninja -DUSE_MBROLA=OFF -DUSE_LIBSONIC=OFF -DUSE_LIBPCAUDIO=OFF \
      -DUSE_ASYNC=OFF -DUSE_KLATT=OFF -DUSE_SPEECHPLAYER=OFF -DESPEAK_BUILD_MANPAGES=OFF >/dev/null
cmake --build "$B" >/dev/null
D="$B/espeak-ng-data"
rm -rf "$DST/data"
mkdir -p "$DST/data/lang"
cp "$D"/phontab "$D"/phonindex "$D"/phondata "$D"/intonations "$D"/pt_dict "$DST/data/"
# SetVoiceByFile pede o caminho em minúsculas: a voz vai como lang/pt-br
cp "$D"/lang/roa/pt-BR "$DST/data/lang/pt-br"
# linhas extras da voz (OD-19): só entram se o arquivo tiver algo além de comentários,
# para o arquivo da voz continuar igual ao upstream enquanto nada foi escolhido
if grep -qvE '^\s*(//|#|$)' "$DST/voice_pt_br_extra" 2>/dev/null; then
    { echo; echo "// --- voice_pt_br_extra (projeto) ---"; grep -vE '^\s*$' "$DST/voice_pt_br_extra"; } >> "$DST/data/lang/pt-br"
fi
(cd "$DST/data" && find . -type f | sort | xargs sha256sum) > "$DST/data.sha256"
echo "espeak-ng $VER: $(du -cb "$DST"/data/* "$DST"/data/lang/* | tail -1 | cut -f1) bytes de dados"

# --- referência de FR-SPK-04: PCM dos textos fixos pelo eSpeak do upstream
V="$ROOT/tests/host/vectors/speech"
cc -O2 -I"$SRC/src/include" -I"$ROOT/firmware/components/l1_speech/include" "$ROOT/tests/host/speech_pcm.c" "$B/src/libespeak-ng/libespeak-ng.a" \
   "$B/src/ucd-tools/libucd.a" -lm -lpthread -o "$WORK/speech_pcm_ref"
rm -rf "$WORK/ref" && mkdir -p "$WORK/ref"
"$WORK/speech_pcm_ref" "$DST/data" "$V/texts.txt" "$WORK/ref" >/dev/null
(cd "$WORK/ref" && sha256sum -- *.pcm) > "$V/pcm.sha256"
echo "referência: $(wc -l < "$V/pcm.sha256") PCMs em tests/host/vectors/speech/pcm.sha256"
