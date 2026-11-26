# eSpeak NG 1.52.0 (GPL-3.0-or-later), sem alterações nas fontes (ver ORIGIN.md).
# Só o runtime síncrono: sem MBROLA, Klatt, speech-player, sonic, async.
# Os dados ficam fora do app, na partição `espeak` (NFR-SW-02), servidos em
# /es pelo VFS de l1_speech.
set(U upstream/src/libespeak-ng)
set(D upstream/src/ucd-tools/src)
set(SRCS
    ${U}/common.c ${U}/mnemonics.c ${U}/error.c ${U}/ieee80.c
    ${U}/compiledata.c ${U}/compiledict.c
    ${U}/dictionary.c ${U}/encoding.c ${U}/intonation.c ${U}/langopts.c
    ${U}/numbers.c ${U}/phoneme.c ${U}/phonemelist.c ${U}/readclause.c
    ${U}/setlengths.c ${U}/soundicon.c ${U}/spect.c ${U}/ssml.c
    ${U}/synthdata.c ${U}/synthesize.c ${U}/tr_languages.c ${U}/translate.c
    ${U}/translateword.c ${U}/voices.c ${U}/wavegen.c ${U}/speech.c ${U}/espeak_api.c
    ${D}/case.c ${D}/categories.c ${D}/ctype.c ${D}/proplist.c ${D}/scripts.c ${D}/tostring.c)
idf_component_register(SRCS ${SRCS}
                       INCLUDE_DIRS upstream/src/include
                       PRIV_INCLUDE_DIRS config ${U} ${D}/include)
# Código de terceiros: avisos não viram erro (não editamos as fontes).
target_compile_options(${COMPONENT_LIB} PRIVATE -w -fwrapv -fno-exceptions)
target_compile_definitions(${COMPONENT_LIB} PRIVATE LIBESPEAK_NG_EXPORT=1 PATH_ESPEAK_DATA="/es")
target_compile_definitions(${COMPONENT_LIB} INTERFACE LIBESPEAK_NG_EXPORT=1)
