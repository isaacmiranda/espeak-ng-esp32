# SPDX-License-Identifier: GPL-3.0-or-later
# Research firmware for the reference board (FSD §5), built on the espeak-ng component.
cmake_minimum_required(VERSION 3.16)
set(EXTRA_COMPONENT_DIRS ${CMAKE_CURRENT_LIST_DIR}/../../components)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(espk_research)
