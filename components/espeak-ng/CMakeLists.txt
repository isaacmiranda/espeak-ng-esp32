# SPDX-License-Identifier: GPL-3.0-or-later
# eSpeak NG 1.52.0 as an ESP-IDF component (FSD Part B). The upstream sources in upstream/
# are compiled untouched; only the synchronous runtime (CON-ENG-03): no MBROLA, Klatt,
# speech-player, sonic or async. The data live in a partition, served by a read-only VFS.
set(U upstream/src/libespeak-ng)
set(D upstream/src/ucd-tools/src)
set(UPSTREAM_SRCS
    ${U}/common.c ${U}/mnemonics.c ${U}/error.c ${U}/ieee80.c
    ${U}/compiledata.c ${U}/compiledict.c
    ${U}/dictionary.c ${U}/encoding.c ${U}/intonation.c ${U}/langopts.c
    ${U}/numbers.c ${U}/phoneme.c ${U}/phonemelist.c ${U}/readclause.c
    ${U}/setlengths.c ${U}/soundicon.c ${U}/spect.c ${U}/ssml.c
    ${U}/synthdata.c ${U}/synthesize.c ${U}/tr_languages.c ${U}/translate.c
    ${U}/translateword.c ${U}/voices.c ${U}/wavegen.c ${U}/speech.c ${U}/espeak_api.c
    ${D}/case.c ${D}/categories.c ${D}/ctype.c ${D}/proplist.c ${D}/scripts.c ${D}/tostring.c)
idf_component_register(SRCS src/espk.c src/espk_async.c src/espk_fsm.c src/espk_part.c src/espk_wrap.c ${UPSTREAM_SRCS}
                       INCLUDE_DIRS include
                       PRIV_INCLUDE_DIRS config upstream/src/include ${U} ${D}/include
                       REQUIRES esp_common
                       PRIV_REQUIRES esp_partition vfs esp_rom esp_timer esp_psram heap freertos)
# Third-party code: warnings do not become errors (the sources are not edited).
set_source_files_properties(${UPSTREAM_SRCS} PROPERTIES COMPILE_OPTIONS "-w;-fwrapv;-fno-exceptions")
target_compile_definitions(${COMPONENT_LIB} PRIVATE LIBESPEAK_NG_EXPORT=1
                           PATH_ESPEAK_DATA="${CONFIG_ESPK_MOUNT_POINT}")

# FR-ENG-04: send the engine's wide-character classification to ucd-tools (see src/espk_wrap.c).
# The flags go on the final link, where the engine's objects call the libc.
if(CONFIG_ESPK_UCD_WRAP)
    foreach(fn iswalpha iswalnum iswupper iswlower iswpunct iswspace iswdigit)
        target_link_libraries(${COMPONENT_LIB} INTERFACE "-Wl,--wrap=${fn}")
    endforeach()
endif()
