# SPDX-License-Identifier: GPL-3.0-or-later
idf_component_register(SRCS "main.c" PRIV_REQUIRES espeak-ng audio_es8311 esp_timer mbedtls)
