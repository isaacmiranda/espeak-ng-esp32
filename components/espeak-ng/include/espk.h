// SPDX-License-Identifier: GPL-3.0-or-later
// eSpeak NG for ESP-IDF — public API (FSD §14). One synthesizer per process: the
// upstream engine keeps global state.
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ESPK_ERR_BASE 0x7E00
#define ESPK_ERR_CANCELLED (ESPK_ERR_BASE + 1)  // the PCM callback returned false

// PCM callback: n samples of 16-bit signed mono at espk_sample_rate(). Return false to cancel.
typedef bool (*espk_pcm_cb_t)(const int16_t *pcm, size_t n, void *ctx);

typedef struct {
    const char *voice;  // initial voice id (NULL: CONFIG_ESPK_DEFAULT_VOICE)
} espk_config_t;

// Mounts the data partition, checks it, starts the engine and selects the initial voice.
// ESP_ERR_INVALID_STATE (already initialised), ESP_ERR_NOT_SUPPORTED (no PSRAM),
// ESP_ERR_NOT_FOUND (no partition or voice), ESP_ERR_INVALID_CRC, ESP_ERR_INVALID_VERSION,
// ESP_ERR_NO_MEM, ESP_FAIL (engine refused the data).
esp_err_t espk_init(const espk_config_t *cfg);

// Sample rate the engine produces (0 before espk_init).
int espk_sample_rate(void);

// Switches to a voice present in the image; ESP_ERR_NOT_FOUND keeps the previous one.
esp_err_t espk_set_voice(const char *voice);

// Writes the voice ids present in the image, separated by ',', into buf.
esp_err_t espk_list_voices(char *buf, size_t len);

// Speech rate in words per minute, within the upstream range 80..450.
esp_err_t espk_set_rate(int wpm);

// Synthesises utf8 and calls cb with blocks of PCM until done or cancelled.
esp_err_t espk_synth(const char *utf8, espk_pcm_cb_t cb, void *ctx);

#ifdef __cplusplus
}
#endif
