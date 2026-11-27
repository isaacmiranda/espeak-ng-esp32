// SPDX-License-Identifier: GPL-3.0-or-later
// Speak a pt-BR sentence through the ES8311 codec of the Waveshare ESP32-S3-RLCD-4.2 at volume 5 (FSD FR-EXM-03),
// resampling the PCM when the codec runs at another rate than the engine's 22 050 Hz (FR-EXM-04).
#include <stdio.h>
#include <stdlib.h>

#include "esp_log.h"
#include "espk.h"
#include "espk_audio.h"
#include "mbedtls/sha256.h"
#include "resample.h"
#include "sdkconfig.h"

static const char *TAG = "espk-ws";
static const char *SENTENCE = "Atenção: a bateria está fraca.";

typedef struct {
    mbedtls_sha256_context sha;
    resampler_t rs;
    bool resample;
    bool open;
} run_t;

// A block of PCM from the engine, on the component's task: 16-bit mono at espk_sample_rate()
static bool on_pcm(const int16_t *pcm, size_t n, void *arg)
{
    run_t *r = arg;
    mbedtls_sha256_update(&r->sha, (const unsigned char *)pcm, n * sizeof *pcm);  // the hash is of the engine's PCM
    // the codec takes stereo: duplicate the mono samples, in small chunks; resample first when the rates differ
    for (size_t i = 0; i < n;) {
        int16_t mono[256], st[2 * 256];
        size_t k = n - i < 128 ? n - i : 128;
        size_t m;
        if (r->resample) {
            m = resample_block(&r->rs, pcm + i, k, mono, 256);
        } else {
            for (size_t j = 0; j < k; j++) mono[j] = pcm[i + j];
            m = k;
        }
        for (size_t j = 0; j < m; j++) st[2 * j] = st[2 * j + 1] = mono[j];
        if (m && r->open && espk_aud_write(st, m) != ESP_OK) return false;
        i += k;
    }
    return true;
}

static void finish(run_t *r)
{
    if (r->open) espk_aud_close();
    mbedtls_sha256_free(&r->sha);
    free(r);
}

// START, DONE, CANCELLED and ERROR, on the component's task. The engine needs a deep stack: espk_say() runs it
// on the component's own task, so app_main()'s small stack is not touched.
static void on_event(const espk_evt_t *e, void *arg)
{
    (void)arg;
    run_t *r = e->pcm_ctx;
    switch (e->type) {
    case ESPK_EVT_START:
        r->open = espk_aud_open(CONFIG_EXAMPLE_VOLUME, CONFIG_EXAMPLE_CODEC_RATE) == ESP_OK;
        if (!r->open) ESP_LOGE(TAG, "the codec would not open");
        break;
    case ESPK_EVT_DONE: {
        unsigned underrun = espk_aud_underruns();
        unsigned char d[32];
        mbedtls_sha256_finish(&r->sha, d);
        char hex[65];
        for (int i = 0; i < 32; i++) sprintf(hex + 2 * i, "%02x", d[i]);
        ESP_LOGI(TAG, "said voice=pt-br volume=%d underrun=%u codec_rate=%d engine_rate=%d samples=%u sha256=%s",
                 CONFIG_EXAMPLE_VOLUME, underrun, CONFIG_EXAMPLE_CODEC_RATE, espk_sample_rate(), (unsigned)e->samples,
                 hex);
        finish(r);
        break;
    }
    case ESPK_EVT_ERROR:
        ESP_LOGE(TAG, "synthesis failed: %s", esp_err_to_name(e->err));
        finish(r);
        break;
    case ESPK_EVT_CANCELLED:
        finish(r);
        break;
    }
}

void app_main(void)
{
    espk_config_t cfg = {.voice = "pt-br", .evt_cb = on_event};
    esp_err_t err = espk_init(&cfg);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "espk_init: %s", esp_err_to_name(err));
        return;
    }
    if (espk_aud_init() != ESP_OK) {
        ESP_LOGE(TAG, "the ES8311 did not answer");
        return;
    }
    const int engine_rate = espk_sample_rate();
    run_t *r = calloc(1, sizeof *r);
    r->resample = CONFIG_EXAMPLE_CODEC_RATE != engine_rate;
    resampler_init(&r->rs, engine_rate, CONFIG_EXAMPLE_CODEC_RATE);
    mbedtls_sha256_init(&r->sha);
    mbedtls_sha256_starts(&r->sha, 0);
    err = espk_say(SENTENCE, on_pcm, r, NULL);  // returns at once; the events say what happened
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "espk_say: %s", esp_err_to_name(err));
        finish(r);
    }
}
