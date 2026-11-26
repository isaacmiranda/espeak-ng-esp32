# FSD §18.1 — ES8311 por I²S (§2.2.2) com o PA no GPIO46.
idf_component_register(SRCS "audio_es8311.c" INCLUDE_DIRS "include"
                       REQUIRES esp_common esp_driver_i2c
                       PRIV_REQUIRES esp_driver_i2s esp_driver_gpio)
