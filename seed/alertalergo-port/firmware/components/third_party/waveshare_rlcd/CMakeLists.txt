# Driver ST7305 da Waveshare, sem alterações (ver ORIGIN.md).
idf_component_register(SRCS "display_bsp.cpp" INCLUDE_DIRS "."
                       REQUIRES esp_lcd esp_driver_gpio esp_driver_spi)
