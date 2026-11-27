# SPDX-License-Identifier: GPL-3.0-or-later
# FR-LST-03: the listening corpus, as a header for the `play` command
idf_build_get_property(_python PYTHON)
execute_process(COMMAND ${_python} ${CMAKE_CURRENT_LIST_DIR}/../../../scripts/gen-listen-header.py
                ${CMAKE_CURRENT_LIST_DIR}/../../../tests/corpus/listen ${CMAKE_BINARY_DIR}/gen/listen_corpus.h
                RESULT_VARIABLE _listen_rc)
if(_listen_rc)
    message(FATAL_ERROR "the listening corpus header could not be generated")
endif()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
             ${CMAKE_CURRENT_LIST_DIR}/../../../tests/corpus/listen/en.tsv
             ${CMAKE_CURRENT_LIST_DIR}/../../../tests/corpus/listen/pt-br.tsv)
idf_component_register(SRCS "main.c" "espk_volume.c"
                       INCLUDE_DIRS "${CMAKE_BINARY_DIR}/gen" PRIV_REQUIRES espeak-ng audio_es8311 esp_app_format esp_driver_usb_serial_jtag esp_timer mbedtls heap)
# The short commit the artifact was built from goes into the boot marker (FSD FR-RES-01).
execute_process(COMMAND git rev-parse --short=7 HEAD
                WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
                OUTPUT_VARIABLE ESPK_COMMIT OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
if(NOT ESPK_COMMIT)
    set(ESPK_COMMIT "unknown")
endif()
target_compile_definitions(${COMPONENT_LIB} PRIVATE ESPK_COMMIT="${ESPK_COMMIT}")
# The data image goes to the `espeak` partition and into flash_args, so `bench flash`
# writes it with the app. It is built by scripts/build-image.sh (CI: the host job).
# With ESPK_DATA_DIR the component builds the image itself (language list, capacity checks: FSD 13);
# with ESPK_IMAGE the firmware flashes a ready image (the CI's).
if(NOT DEFINED ENV{ESPK_DATA_DIR})
    if(NOT DEFINED ENV{ESPK_IMAGE} OR NOT EXISTS "$ENV{ESPK_IMAGE}")
        message(FATAL_ERROR "ESPK_DATA_DIR must name the compiled upstream data, or ESPK_IMAGE a ready image "
                            "(scripts/build-image.sh <out>)")
    endif()
    esptool_py_flash_to_partition(flash "espeak" "$ENV{ESPK_IMAGE}")
endif()
