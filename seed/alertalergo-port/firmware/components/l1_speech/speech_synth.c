/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * eSpeak NG síncrono (FSD §18.2). Os dados vêm de /es (espeak_part.c). A voz
 * é carregada pelo arquivo: espeak_ng_SetVoiceByFile põe o caminho em
 * minúsculas e o limita a 60 bytes.
 */
#include <string.h>

#include "espeak-ng/espeak_ng.h"
#include "espeak-ng/speak_lib.h"
#include "espeak_part.h"
#include "l1_speech.h"
#include "speech_params.h"

#define BASE "/es"
#define VOICE BASE "/lang/pt-br"

static bool s_ready;
static spk_pcm_cb_t s_cb;
static void *s_ctx;
static bool s_stopped;

static int on_synth(short *wav, int n, espeak_EVENT *ev)
{
    (void)ev;
    if (wav && n > 0 && !s_stopped && !s_cb(wav, (size_t)n, s_ctx)) s_stopped = true;
    return s_stopped ? 1 : 0;           /* 1 = o eSpeak para a síntese */
}

esp_err_t spk_hw_init(const char **reason)
{
    esp_err_t err = espeak_part_mount(BASE, reason);
    if (err != ESP_OK) return err;
    espeak_ng_InitializePath(BASE);
    if (espeak_ng_Initialize(NULL) != ENS_OK ||
        espeak_ng_InitializeOutput(ENOUTPUT_MODE_SYNCHRONOUS, 0, NULL) != ENS_OK ||
        espeak_ng_SetVoiceByFile(VOICE) != ENS_OK) {
        *reason = "init";
        return ESP_FAIL;
    }
    espeak_SetSynthCallback(on_synth);
    spk_params_apply();                 /* OD-19: velocidade, tom e pausas */
    s_ready = true;
    return ESP_OK;
}

int spk_hw_rate(void)
{
    return s_ready ? espeak_ng_GetSampleRate() : 0;
}

static volatile int s_rate_wpm = 175;                          /* §31.1 speech_rate_wpm */

void spk_hw_set_rate(int wpm)
{
    s_rate_wpm = wpm;
}

esp_err_t spk_hw_synth(const char *utf8, spk_pcm_cb_t cb, void *ctx)
{
    if (!s_ready) return ESP_ERR_INVALID_STATE;
    espeak_SetParameter(espeakRATE, s_rate_wpm, 0);
    s_cb = cb;
    s_ctx = ctx;
    s_stopped = false;
    espeak_ng_STATUS st = espeak_ng_Synthesize(utf8, strlen(utf8) + 1, 0, POS_CHARACTER, 0, espeakCHARS_UTF8, NULL, NULL);
    if (st == ENS_OK) st = espeak_ng_Synchronize();
    if (s_stopped) return ESP_ERR_NOT_FINISHED;
    return st == ENS_OK ? ESP_OK : ESP_FAIL;
}
