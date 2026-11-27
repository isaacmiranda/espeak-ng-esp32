/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/*
 * Audio output of the research firmware: ES8311 over I2S on the reference board (FSD §2.2).
 * Ported from the AlertAlergo V3 port (seed/alertalergo-port/.../l1_audio, same licence): one
 * playback = open (PA on) -> write... -> close (PA off). 16-bit stereo; the caller duplicates mono.
 */
#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ESPK_AUD_INIT_RATE 22050

esp_err_t espk_aud_init(void);                    /* I2C bus (SDA 13, SCL 14), I2S 0, ES8311 at 0x18 */
esp_err_t espk_aud_open(int vol, int rate);       /* vol 0-100, rate in Hz */
esp_err_t espk_aud_write(const int16_t *pcm, size_t frames);
unsigned espk_aud_underruns(void);                /* writes that found the speaker already dry */
void espk_aud_close(void);

#ifdef __cplusplus
}
#endif
