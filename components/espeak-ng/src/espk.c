// SPDX-License-Identifier: GPL-3.0-or-later
// Synchronous core of the component (FSD §14) over the untouched upstream engine.
#include "espk.h"

#include <stdatomic.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "esp_log.h"
#include "esp_psram.h"
#include "espeak-ng/espeak_ng.h"
#include "espeak-ng/speak_lib.h"
#include "espk_async.h"
#include "espk_part.h"

static const char *TAG = "espk";

static bool s_ready;
static atomic_bool s_busy;
static espk_pcm_cb_t s_cb;
static void *s_ctx;
static bool s_stopped;
static char s_voice[48];

static int on_synth(short *wav, int n, espeak_EVENT *ev)
{
    (void)ev;
    if (wav && n > 0 && !s_stopped && !s_cb((const int16_t *)wav, (size_t)n, s_ctx)) s_stopped = true;
    return s_stopped ? 1 : 0;  // 1 tells the engine to stop
}

// "lang/roa/pt-br" for voice id "pt-br": the voice id is the voice file's name.
static const char *voice_path(const char *voice)
{
    for (uint32_t i = 0; i < espk_part_count(); i++) {
        const char *n = espk_part_entry(i)->name;
        const char *slash = strrchr(n, '/');
        if (strncmp(n, "lang/", 5) == 0 && slash && strcasecmp(slash + 1, voice) == 0) return n;
    }
    return NULL;
}

static esp_err_t select_voice(const char *voice)
{
    const char *rel = voice ? voice_path(voice) : NULL;
    if (!rel) return ESP_ERR_NOT_FOUND;
    char path[96];
    snprintf(path, sizeof path, "%s/%s", CONFIG_ESPK_MOUNT_POINT, rel);
    if (espeak_ng_SetVoiceByFile(path) != ENS_OK) return ESP_ERR_NOT_FOUND;
    strlcpy(s_voice, voice, sizeof s_voice);
    return ESP_OK;
}

esp_err_t espk_init(const espk_config_t *cfg)
{
    if (s_ready) return ESP_ERR_INVALID_STATE;
    if (!esp_psram_is_initialized()) {
        ESP_LOGE(TAG, "init: ESP_ERR_NOT_SUPPORTED (no PSRAM)");
        return ESP_ERR_NOT_SUPPORTED;
    }
    const char *reason = "";
    esp_err_t err = espk_part_mount(CONFIG_ESPK_PARTITION_LABEL, CONFIG_ESPK_PARTITION_SUBTYPE,
                                    CONFIG_ESPK_MOUNT_POINT, PACKAGE_VERSION, &reason);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "init: %s (%s)", esp_err_to_name(err), reason);
        return err;
    }
    espeak_ng_InitializePath(CONFIG_ESPK_MOUNT_POINT);
    if (espeak_ng_Initialize(NULL) != ENS_OK ||
        espeak_ng_InitializeOutput(ENOUTPUT_MODE_SYNCHRONOUS, 0, NULL) != ENS_OK) {
        ESP_LOGE(TAG, "init: ESP_FAIL (engine refused the data)");
        return ESP_FAIL;
    }
    espeak_SetSynthCallback(on_synth);
    const char *voice = cfg && cfg->voice ? cfg->voice : CONFIG_ESPK_DEFAULT_VOICE;
    err = select_voice(voice);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "init: %s (voice %s)", esp_err_to_name(err), voice);
        return err;
    }
    s_ready = true;
    err = espk_async_start(cfg);
    if (err != ESP_OK) {
        s_ready = false;
        return err;
    }
    return ESP_OK;
}

int espk_sample_rate(void) { return s_ready ? espeak_ng_GetSampleRate() : 0; }

esp_err_t espk_set_voice(const char *voice)
{
    if (!s_ready) return ESP_ERR_INVALID_STATE;
    if (!voice_path(voice)) return ESP_ERR_NOT_FOUND;
    return select_voice(voice);
}

esp_err_t espk_list_voices(char *buf, size_t len)
{
    if (!s_ready) return ESP_ERR_INVALID_STATE;
    if (!buf || len == 0) return ESP_ERR_INVALID_ARG;
    buf[0] = '\0';
    for (uint32_t i = 0; i < espk_part_count(); i++) {
        const char *n = espk_part_entry(i)->name;
        const char *slash = strrchr(n, '/');
        if (strncmp(n, "lang/", 5) != 0 || !slash) continue;
        if (buf[0]) strlcat(buf, ",", len);
        if (strlcat(buf, slash + 1, len) >= len) return ESP_ERR_INVALID_SIZE;
    }
    return ESP_OK;
}

esp_err_t espk_set_rate(int wpm)
{
    if (!s_ready) return ESP_ERR_INVALID_STATE;
    if (wpm < 80 || wpm > 450) return ESP_ERR_INVALID_ARG;
    return espeak_ng_SetParameter(espeakRATE, wpm, 0) == ENS_OK ? ESP_OK : ESP_FAIL;
}

esp_err_t espk_synth(const char *utf8, espk_pcm_cb_t cb, void *ctx)
{
    if (!s_ready) return ESP_ERR_INVALID_STATE;
    if (!utf8 || !cb) return ESP_ERR_INVALID_ARG;
    size_t n = strnlen(utf8, CONFIG_ESPK_MAX_TEXT_LEN + 1);
    if (n > CONFIG_ESPK_MAX_TEXT_LEN) return ESP_ERR_INVALID_SIZE;
    bool idle = false;
    if (!atomic_compare_exchange_strong(&s_busy, &idle, true)) return ESP_ERR_INVALID_STATE;
    s_cb = cb;
    s_ctx = ctx;
    s_stopped = false;
    espeak_ng_STATUS st = espeak_ng_Synthesize(utf8, n + 1, 0, POS_CHARACTER, 0, espeakCHARS_UTF8, NULL, NULL);
    if (st == ENS_OK) st = espeak_ng_Synchronize();
    bool stopped = s_stopped;
    atomic_store(&s_busy, false);
    if (stopped) return ESPK_ERR_CANCELLED;
    return st == ENS_OK ? ESP_OK : ESP_FAIL;
}
