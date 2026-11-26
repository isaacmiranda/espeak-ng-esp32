# SPDX-License-Identifier: GPL-3.0-or-later
idf_component_register(SRCS "audio_es8311.c" INCLUDE_DIRS "include"
                       REQUIRES esp_common esp_driver_i2c
                       PRIV_REQUIRES esp_driver_i2s esp_driver_gpio esp_timer)
