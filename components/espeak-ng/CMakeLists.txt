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
idf_component_register(SRCS src/espk.c src/espk_async.c src/espk_fsm.c src/espk_part.c ${UPSTREAM_SRCS}
                       INCLUDE_DIRS include
                       LDFRAGMENTS linker.lf
                       PRIV_INCLUDE_DIRS config upstream/src/include ${U} ${D}/include
                       REQUIRES esp_common
                       PRIV_REQUIRES esp_partition vfs esp_rom esp_timer esp_psram heap freertos)
# Third-party code: warnings do not become errors (the sources are not edited).
set_source_files_properties(${UPSTREAM_SRCS} PROPERTIES COMPILE_OPTIONS "-w;-fwrapv;-fno-exceptions")
target_compile_definitions(${COMPONENT_LIB} PRIVATE LIBESPEAK_NG_EXPORT=1
                           PATH_ESPEAK_DATA="${CONFIG_ESPK_MOUNT_POINT}")

# FR-ENG-04 (issue espeak-ng#1611): the upstream's own way, as its CMake build does (src/CMakeLists.txt puts
# include/compat on the include path). Its wctype.h maps the engine's isw* calls to ucd-tools at compile time, so the
# ESP32 libc (newlib, C locale, ASCII letters only) is not asked. The sources stay untouched.
if(CONFIG_ESPK_UCD_WRAP)
    target_include_directories(${COMPONENT_LIB} BEFORE PRIVATE upstream/src/include/compat)
endif()

# FR-ASY-06: the engine's deepest call chain measured ~39 KB on the AlertAlergo port; 49 152 B is the floor.
if(CONFIG_ESPK_ASYNC AND CONFIG_ESPK_TASK_STACK LESS 49152)
    message(FATAL_ERROR "CONFIG_ESPK_TASK_STACK=${CONFIG_ESPK_TASK_STACK} is below the 49152 B floor (FR-ASY-06)")
endif()

# FR-CAP: language selection, the data image and the capacity checks, at configure time. They need the compiled
# upstream data (the espeak-ng-data of an upstream build): ESPK_DATA_DIR names it. Without it the integrator
# supplies a ready image (the research firmware's ESPK_IMAGE) and no capacity check runs.
if(DEFINED ENV{ESPK_DATA_DIR})
    idf_build_get_property(_python PYTHON)
    idf_build_get_property(_project_dir PROJECT_DIR)
    set(_cap_args --data "$ENV{ESPK_DATA_DIR}" --languages "${CONFIG_ESPK_LANGUAGES}"
        --default-voice "${CONFIG_ESPK_DEFAULT_VOICE}" --budget-kb ${CONFIG_ESPK_PSRAM_BUDGET_KB}
        --warn-pct ${CONFIG_ESPK_CAPACITY_WARN_PCT}
        --out "${CMAKE_BINARY_DIR}/espeak.img" --report "${CMAKE_BINARY_DIR}/espk_capacity.json")
    if(CONFIG_ESPK_LANGUAGES_ALL)
        list(APPEND _cap_args --all)
    endif()
    if(CONFIG_PARTITION_TABLE_CUSTOM)
        list(APPEND _cap_args --partitions "${_project_dir}/${CONFIG_PARTITION_TABLE_CUSTOM_FILENAME}"
             --label "${CONFIG_ESPK_PARTITION_LABEL}")
    endif()
    if(CONFIG_ESPK_ASYNC)
        if(CONFIG_ESPK_TASK_STACK_PSRAM)
            set(_stack_where y)
        else()
            set(_stack_where n)
        endif()
        list(APPEND _cap_args --task-stack ${CONFIG_ESPK_TASK_STACK} --task-stack-psram ${_stack_where})
    endif()
    execute_process(COMMAND ${_python} "${CMAKE_CURRENT_LIST_DIR}/tools/capacity.py" ${_cap_args}
                    RESULT_VARIABLE _cap_rc OUTPUT_VARIABLE _cap_out ERROR_VARIABLE _cap_err)
    message(STATUS "espeak-ng capacity:\n${_cap_out}")
    if(_cap_rc)
        message(FATAL_ERROR "espeak-ng capacity check failed:\n${_cap_err}")
    endif()
    file(READ "${CMAKE_BINARY_DIR}/espk_capacity.json" _cap_json)
    string(JSON _peak GET "${_cap_json}" psram_peak_bytes)
    target_compile_definitions(${COMPONENT_LIB} PRIVATE ESPK_PSRAM_PEAK_BYTES=${_peak})  # FR-CAP-10
    esptool_py_flash_to_partition(flash "${CONFIG_ESPK_PARTITION_LABEL}" "${CMAKE_BINARY_DIR}/espeak.img")
    # a change in the data files is a change in the image: configure again
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
                 "$ENV{ESPK_DATA_DIR}/phondata" "$ENV{ESPK_DATA_DIR}/phontab" "$ENV{ESPK_DATA_DIR}/phonindex")
endif()
