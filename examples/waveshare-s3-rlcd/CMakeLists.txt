# SPDX-License-Identifier: GPL-3.0-or-later
# `waveshare-s3-rlcd`: speak a pt-BR sentence through the ES8311 codec of the reference board, at volume 5
# (FSD FR-EXM-03), and show how to resample the PCM when the codec runs at another rate (FR-EXM-04).
cmake_minimum_required(VERSION 3.16)
set(EXTRA_COMPONENT_DIRS ${CMAKE_CURRENT_LIST_DIR}/../../components ${CMAKE_CURRENT_LIST_DIR}/components)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(espk_waveshare)
