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

// Events of the asynchronous layer (FSD 15), delivered from the synthesis task.
typedef enum { ESPK_EVT_START = 1, ESPK_EVT_DONE, ESPK_EVT_CANCELLED, ESPK_EVT_ERROR } espk_evt_type_t;

typedef struct {
    espk_evt_type_t type;
    uint32_t id;         // the request's id, as espk_say() returned it
    void *pcm_ctx;       // the ctx the request was queued with (free it on DONE, CANCELLED or ERROR)
    uint32_t samples;    // DONE: samples delivered
    uint32_t synth_ms;   // DONE: time from START to the end of the synthesis
    uint32_t first_ms;   // DONE: time from START to the first block of PCM
    uint32_t cancel_ms;  // CANCELLED: time from espk_cancel() to this event
    esp_err_t err;       // ERROR: the engine's error
} espk_evt_t;

typedef void (*espk_evt_cb_t)(const espk_evt_t *evt, void *ctx);

typedef struct {
    const char *voice;       // initial voice id (NULL: CONFIG_ESPK_DEFAULT_VOICE)
    espk_evt_cb_t evt_cb;    // events of espk_say() requests (NULL: none)
    void *evt_ctx;
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

// Asynchronous layer (CONFIG_ESPK_ASYNC). espk_say() copies the text, queues the request and returns at once
// with its id; the PCM goes to cb(ctx) from the synthesis task, events to the config's evt_cb. ESP_ERR_NO_MEM:
// the queue is full; ESP_ERR_INVALID_SIZE: text above CONFIG_ESPK_MAX_TEXT_LEN; ESP_ERR_INVALID_STATE: not
// initialised. espk_cancel() stops the request being spoken, drops the queued ones and returns at once; the
// CANCELLED event follows. With the layer off both return ESP_ERR_NOT_SUPPORTED.
esp_err_t espk_say(const char *utf8, espk_pcm_cb_t cb, void *ctx, uint32_t *id);
esp_err_t espk_cancel(void);

#ifdef __cplusplus
}
#endif
