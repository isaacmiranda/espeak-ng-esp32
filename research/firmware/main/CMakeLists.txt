# SPDX-License-Identifier: GPL-3.0-or-later
idf_component_register(SRCS "main.c" "espk_volume.c"
                       PRIV_REQUIRES espeak-ng audio_es8311 esp_app_format esp_driver_usb_serial_jtag esp_timer mbedtls heap)
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
if(NOT DEFINED ENV{ESPK_IMAGE} OR NOT EXISTS "$ENV{ESPK_IMAGE}")
    message(FATAL_ERROR "ESPK_IMAGE must name the data image: run scripts/build-image.sh <out> first")
endif()
esptool_py_flash_to_partition(flash "espeak" "$ENV{ESPK_IMAGE}")
