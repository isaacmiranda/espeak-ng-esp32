/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once

/*
 * l1_speech — eSpeak NG no aparelho (FSD §18.2, FR-PLT-06, NFR-SW-02).
 *
 * spk_hw_init(): acha a partição `espeak`, mapeia-a da flash, confere o
 * cabeçalho e o CRC32 (formato em scripts/gen-espeak-image.py), monta o VFS
 * somente leitura em /es e inicializa o eSpeak com a voz pt-BR. Sem dados
 * válidos a fala fica desligada e `*reason` diz por quê (bad_magic,
 * bad_version, bad_crc, no_partition, init).
 *
 * spk_hw_synth(): síntese síncrona; o PCM (16 bit mono, spk_hw_rate() Hz) sai
 * em pedaços pelo callback, na tarefa de quem chamou. O callback devolve false
 * para interromper.
 */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef bool (*spk_pcm_cb_t)(const int16_t *pcm, size_t n, void *ctx);

esp_err_t spk_hw_init(const char **reason);
int spk_hw_rate(void);
/* ESP_OK = terminou; ESP_ERR_INVALID_STATE = sem init; ESP_FAIL = erro do
 * eSpeak; ESP_ERR_TIMEOUT nunca (quem cronometra é o callback). Interrompido
 * pelo callback = ESP_ERR_NOT_FINISHED. */
/* Velocidade da fala em palavras/min (§31.1 `speech_rate_wpm`); vale na próxima síntese. */
void spk_hw_set_rate(int wpm);

esp_err_t spk_hw_synth(const char *utf8, spk_pcm_cb_t cb, void *ctx);

#ifdef __cplusplus
}
#endif
