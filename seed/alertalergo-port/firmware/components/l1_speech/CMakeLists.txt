# FSD §18.2 / FR-PLT-06 — dados do eSpeak NG na partição `espeak`, servidos por
# um VFS somente leitura em /es, e a síntese síncrona.
idf_component_register(SRCS "espeak_part.c" "speech_synth.c" INCLUDE_DIRS "include"
                       REQUIRES esp_common
                       PRIV_REQUIRES espeak-ng esp_partition vfs esp_rom esp_timer)
