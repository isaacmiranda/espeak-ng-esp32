/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once

/*
 * l1_audio — saída de áudio pelo ES8311 (FSD §18.1, Apêndice B). Uma
 * reprodução = open (liga o PA, FR-AUD-01) → write… → close (desliga o PA).
 * Formato: 16 bit, estéreo, taxa por reprodução (tons a 16 kHz, fala na taxa
 * do eSpeak). Sem marcadores: quem os emite é o app.
 */
#include <stddef.h>
#include <stdint.h>

#include "driver/i2c_master.h"
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define AUD_HW_RATE 16000

/* Cria o canal I²S e o codec no barramento I²C dado. Erro = o ES8311 não
 * respondeu (FR-ERR-01). */
esp_err_t aud_hw_init(i2c_master_bus_handle_t bus);
esp_err_t aud_hw_open(int vol, int rate);    /* vol 0–100 (FR-AUD-03), rate em Hz */
esp_err_t aud_hw_write(const int16_t *pcm, size_t frames);
void aud_hw_close(void);
int aud_hw_pa_level(void);                   /* nível lido do GPIO46 */

#ifdef __cplusplus
}
#endif
