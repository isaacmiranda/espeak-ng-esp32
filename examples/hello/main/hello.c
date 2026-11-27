// SPDX-License-Identifier: GPL-3.0-or-later
// Synthesise one sentence and log what came out; nothing is played (FSD FR-EXM-01).
//
// The engine needs a deep stack (the component's floor is 48 KB), far more than the main task has. espk_say()
// runs it on the component's own task, whose stack CONFIG_ESPK_TASK_STACK sizes: that is the way to use it
// from app_main. espk_synth() runs the engine on the caller's stack and is for a task you sized yourself.
#include <stdio.h>
#include <stdlib.h>

#include "esp_log.h"
#include "espk.h"
#include "mbedtls/sha256.h"

static const char *TAG = "espk-hello";

typedef struct {
    mbedtls_sha256_context sha;
} run_t;

// The PCM arrives in blocks of 16-bit mono samples, from the component's task; return false to cancel
static bool on_pcm(const int16_t *pcm, size_t n, void *arg)
{
    run_t *r = arg;
    mbedtls_sha256_update(&r->sha, (const unsigned char *)pcm, n * sizeof *pcm);
    return true;
}

// START, DONE, CANCELLED and ERROR of each request, from the component's task
static void on_event(const espk_evt_t *e, void *arg)
{
    (void)arg;
    run_t *r = e->pcm_ctx;
    switch (e->type) {
    case ESPK_EVT_DONE: {
        unsigned char digest[32];
        mbedtls_sha256_finish(&r->sha, digest);
        char hex[65];
        for (int i = 0; i < 32; i++) sprintf(hex + 2 * i, "%02x", digest[i]);
        int rate = espk_sample_rate();
        ESP_LOGI(TAG, "rate=%d duration_ms=%u sha256=%s", rate, (unsigned)(e->samples * 1000ULL / (unsigned)rate), hex);
        break;
    }
    case ESPK_EVT_ERROR:
        ESP_LOGE(TAG, "synthesis failed: %s", esp_err_to_name(e->err));
        break;
    default:
        break;
    }
    if (e->type != ESPK_EVT_START) {  // the request is over: its context is ours to free
        mbedtls_sha256_free(&r->sha);
        free(r);
    }
}

void app_main(void)
{
    espk_config_t cfg = {.evt_cb = on_event};  // the voice is CONFIG_ESPK_DEFAULT_VOICE
    esp_err_t err = espk_init(&cfg);           // the data partition, the engine, the task
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "espk_init: %s", esp_err_to_name(err));
        return;
    }
    run_t *r = calloc(1, sizeof *r);
    mbedtls_sha256_init(&r->sha);
    mbedtls_sha256_starts(&r->sha, 0);
    err = espk_say("Hello from eSpeak NG on the ESP32.", on_pcm, r, NULL);  // returns at once
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "espk_say: %s", esp_err_to_name(err));
        free(r);
    }
}
