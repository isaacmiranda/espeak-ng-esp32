# SPDX-License-Identifier: GPL-3.0-or-later
# `hello`: start the component, synthesise one sentence in the default voice, log the sample rate, the duration
# and the SHA-256 of the PCM. No audio output, so it runs on any chip with PSRAM (FSD FR-EXM-01).
cmake_minimum_required(VERSION 3.16)
# In this repository the component is next door. Out of it, depend on the Registry's isaacmiranda/espeak-ng
# in main/idf_component.yml instead (see the README).
set(EXTRA_COMPONENT_DIRS ${CMAKE_CURRENT_LIST_DIR}/../../components)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(espk_hello)
