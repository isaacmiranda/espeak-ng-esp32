# SPDX-License-Identifier: GPL-3.0-or-later
idf_component_register(SRCS "main.c" PRIV_REQUIRES esp_app_format esp_driver_usb_serial_jtag)
# The short commit the artifact was built from goes into the boot marker (FSD FR-RES-01).
execute_process(COMMAND git rev-parse --short=7 HEAD
                WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
                OUTPUT_VARIABLE ESPK_COMMIT OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
if(NOT ESPK_COMMIT)
    set(ESPK_COMMIT "unknown")
endif()
target_compile_definitions(${COMPONENT_LIB} PRIVATE ESPK_COMMIT="${ESPK_COMMIT}")
