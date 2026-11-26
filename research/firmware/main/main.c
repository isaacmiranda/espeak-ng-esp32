// SPDX-License-Identifier: GPL-3.0-or-later
// Composition root of the research firmware (FSD §5): the component, the console and the
// markers. Audio output, cancel and load profiles arrive with their requirements.
#include <stdio.h>
#include <string.h>

#include "driver/usb_serial_jtag.h"
#include "driver/usb_serial_jtag_vfs.h"
#include "esp_app_desc.h"
#include "esp_heap_caps.h"
#include "esp_idf_version.h"
#include "esp_timer.h"
#include "espk.h"
#include "freertos/FreeRTOS.h"
#include "freertos/idf_additions.h"
#include "freertos/task.h"
#include "mbedtls/sha256.h"

#define CONSOLE_LINE_MAX 1100  // FR-RES-16: texts up to 1 024 bytes plus the command word
#define SYNTH_STACK (64 * 1024)  // CONFIG_ESPK_TASK_STACK default (FSD §19), in PSRAM

typedef struct {
    mbedtls_sha256_context sha;
    size_t samples;
    int64_t t0, first_us;
} say_ctx_t;

static unsigned s_id;

static bool on_pcm(const int16_t *pcm, size_t n, void *arg)
{
    say_ctx_t *c = arg;
    if (c->samples == 0) c->first_us = esp_timer_get_time() - c->t0;
    mbedtls_sha256_update(&c->sha, (const unsigned char *)pcm, n * sizeof *pcm);
    c->samples += n;
    return true;
}

// say --mute <text>: synthesise, hash the PCM delivered to the callback (FR-RES-03, FR-RES-04)
static void cmd_say_mute(const char *text)
{
    size_t bytes = strlen(text);
    if (bytes > CONFIG_ESPK_MAX_TEXT_LEN) {  // FR-RES-16
        printf("ESPK error code=too_long\n");
        return;
    }
    say_ctx_t c = {0};
    mbedtls_sha256_init(&c.sha);
    mbedtls_sha256_starts(&c.sha, 0);
    unsigned id = ++s_id;
    c.t0 = esp_timer_get_time();
    esp_err_t err = espk_synth(text, on_pcm, &c);
    int64_t synth_us = esp_timer_get_time() - c.t0;
    unsigned char d[32];
    mbedtls_sha256_finish(&c.sha, d);
    mbedtls_sha256_free(&c.sha);
    if (err != ESP_OK) {
        printf("ESPK error id=%u code=%s\n", id, esp_err_to_name(err));
        return;
    }
    char hex[65];
    for (int i = 0; i < 32; i++) sprintf(hex + 2 * i, "%02x", d[i]);
    int rate = espk_sample_rate();
    printf("ESPK done id=%u samples=%u synth_ms=%lld first_ms=%lld audio_ms=%llu heap_min=%u sha256=%s bytes=%u\n", id,
           (unsigned)c.samples, synth_us / 1000, c.first_us / 1000,
           (unsigned long long)c.samples * 1000ULL / (unsigned long long)rate,
           (unsigned)heap_caps_get_minimum_free_size(MALLOC_CAP_INTERNAL), hex, (unsigned)bytes);
}

static void dispatch(char *line)
{
    if (strncmp(line, "say --mute ", 11) == 0) {
        cmd_say_mute(line + 11);
    } else if (strncmp(line, "voice ", 6) == 0) {
        if (espk_set_voice(line + 6) == ESP_OK) {
            printf("ESPK voice ok=%s\n", line + 6);
        } else {
            printf("ESPK voice err=not_found\n");
        }
    } else {
        printf("ESPK error code=unknown_command\n");
    }
}

static void console_task(void *arg)
{
    static char line[CONSOLE_LINE_MAX];
    size_t n = 0;
    bool overflow = false;
    for (;;) {
        int c = fgetc(stdin);
        if (c == EOF) {
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }
        if (c == '\r') continue;
        if (c == '\n') {
            line[n] = '\0';
            if (overflow) {
                printf("ESPK error code=too_long\n");
            } else if (n > 0) {
                dispatch(line);
            }
            n = 0;
            overflow = false;
            continue;
        }
        if (n < sizeof(line) - 1) {
            line[n++] = (char)c;
        } else {
            overflow = true;
        }
    }
}

void app_main(void)
{
    // A 1 024-byte text arrives in a burst faster than the console task drains the default
    // 256-byte ring: bytes were lost on the bench (the `bytes=` field of ESPK done shows it).
    usb_serial_jtag_driver_config_t cfg = {.tx_buffer_size = 1024, .rx_buffer_size = 4096};
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&cfg));
    usb_serial_jtag_vfs_use_driver();
    setvbuf(stdin, NULL, _IONBF, 0);

    int64_t t0 = esp_timer_get_time();
    esp_err_t err = espk_init(NULL);
    int64_t init_ms = (esp_timer_get_time() - t0) / 1000;
    static char langs[256] = "";
    if (err == ESP_OK) espk_list_voices(langs, sizeof langs);

    const esp_app_desc_t *app = esp_app_get_description();
    printf("ESPK boot fw=%s commit=%s idf=%s espeak=1.52.0 rate=%d bss=internal langs=%s init_ms=%lld\n",
           app->version, ESPK_COMMIT, esp_get_idf_version(), espk_sample_rate(), langs[0] ? langs : "none",
           init_ms);
    if (err != ESP_OK) {
        printf("ESPK error code=%s\n", esp_err_to_name(err));
    } else {
        printf("ESPK ready\n");
        xTaskCreateWithCaps(console_task, "console", SYNTH_STACK, NULL, 5, NULL, MALLOC_CAP_SPIRAM);
    }
    for (unsigned k = 1;; k++) {
        printf("ESPK alive n=%u\n", k);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
