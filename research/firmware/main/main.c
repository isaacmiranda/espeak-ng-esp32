// SPDX-License-Identifier: GPL-3.0-or-later
// Composition root of the research firmware (FSD §5): the component, the console and the
// markers. Load profiles arrive with their requirements.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "driver/usb_serial_jtag.h"
#include "driver/usb_serial_jtag_vfs.h"
#include "esp_app_desc.h"
#include "espk_audio.h"
#include "espk_volume.h"
#include "esp_heap_caps.h"
#include "esp_idf_version.h"
#include "esp_timer.h"
#include "espk.h"
#include "freertos/FreeRTOS.h"
#include "freertos/idf_additions.h"
#include "freertos/task.h"
#include "mbedtls/sha256.h"

#define CONSOLE_LINE_MAX 1100  // FR-RES-16: texts up to 1 024 bytes plus the command word
#define CONSOLE_STACK (16 * 1024)  // the console only parses; the synthesis has its own task (FR-ASY-05)


// One per say request: allocated by the console, freed by the event that ends the request.
typedef struct {
    mbedtls_sha256_context sha;
    unsigned bytes;  // size of the text received (FR-RES-03)
    bool sound;      // false: --mute (FR-RES-04), the PCM only goes to the hash
    bool opened;     // the codec is open for this request
} say_ctx_t;

static bool s_audio_ok;
static espk_vol_t s_vol;  // FR-RES-07, 08, 09

static bool on_pcm(const int16_t *pcm, size_t n, void *arg)
{
    say_ctx_t *c = arg;
    mbedtls_sha256_update(&c->sha, (const unsigned char *)pcm, n * sizeof *pcm);
    if (c->sound && c->opened) {
        // the engine delivers mono; the codec path is stereo: write in small stereo chunks
        int16_t st[2 * 256];
        for (size_t i = 0; i < n;) {
            size_t k = n - i < 256 ? n - i : 256;
            for (size_t j = 0; j < k; j++) st[2 * j] = st[2 * j + 1] = pcm[i + j];
            if (espk_aud_write(st, k) != ESP_OK) return false;
            i += k;
        }
    }
    return true;
}

static void end_request(say_ctx_t *c)
{
    if (c->opened) espk_aud_close();
    mbedtls_sha256_free(&c->sha);
    free(c);
}

// Events of the asynchronous layer, from the synthesis task (FR-RES-03, 10, 11, 12)
static void on_event(const espk_evt_t *e, void *arg)
{
    (void)arg;
    say_ctx_t *c = e->pcm_ctx;
    switch (e->type) {
    case ESPK_EVT_START:
        printf("ESPK start id=%u\n", (unsigned)e->id);  // FR-RES-11
        if (c->sound && espk_aud_open(s_vol.vol, espk_sample_rate()) == ESP_OK) {
            c->opened = true;
        } else if (c->sound) {
            printf("ESPK error id=%u code=no_audio\n", (unsigned)e->id);
            c->sound = false;
        }
        break;
    case ESPK_EVT_DONE: {
        unsigned underrun = c->opened ? espk_aud_underruns() : 0;
        unsigned char d[32];
        mbedtls_sha256_finish(&c->sha, d);
        char hex[65];
        for (int i = 0; i < 32; i++) sprintf(hex + 2 * i, "%02x", d[i]);
        printf("ESPK done id=%u samples=%u synth_ms=%u first_ms=%u audio_ms=%llu heap_min=%u sha256=%s bytes=%u "
               "underrun=%u\n",
               (unsigned)e->id, (unsigned)e->samples, (unsigned)e->synth_ms, (unsigned)e->first_ms,
               (unsigned long long)e->samples * 1000ULL / (unsigned long long)espk_sample_rate(),
               (unsigned)heap_caps_get_minimum_free_size(MALLOC_CAP_INTERNAL), hex, c->bytes, underrun);
        end_request(c);
        break;
    }
    case ESPK_EVT_CANCELLED:  // FR-RES-10
        printf("ESPK cancelled id=%u cancel_ms=%u\n", (unsigned)e->id, (unsigned)e->cancel_ms);
        end_request(c);
        break;
    case ESPK_EVT_ERROR:
        printf("ESPK error id=%u code=%s\n", (unsigned)e->id, esp_err_to_name(e->err));
        end_request(c);
        break;
    }
}

// say [--mute] <text>: queue the text; the answer is the events (FR-RES-03, 04, 11)
static void cmd_say(const char *text, bool sound)
{
    size_t bytes = strlen(text);
    if (bytes > CONFIG_ESPK_MAX_TEXT_LEN) {  // FR-RES-16
        printf("ESPK error code=too_long\n");
        return;
    }
    if (sound && !s_audio_ok) {
        printf("ESPK error code=no_audio\n");
        return;
    }
    say_ctx_t *c = calloc(1, sizeof *c);
    if (!c) {
        printf("ESPK error code=no_mem\n");
        return;
    }
    c->sound = sound;
    c->bytes = (unsigned)bytes;
    mbedtls_sha256_init(&c->sha);
    mbedtls_sha256_starts(&c->sha, 0);
    uint32_t id;
    int64_t t0 = esp_timer_get_time();
    esp_err_t err = espk_say(text, on_pcm, c, &id);
    unsigned queue_us = (unsigned)(esp_timer_get_time() - t0);  // FR-ASY-01
    if (err != ESP_OK) {
        printf("ESPK error code=%s\n", esp_err_to_name(err));
        end_request(c);
    } else {
        printf("ESPK queued id=%u queue_us=%u\n", (unsigned)id, queue_us);
    }
}

// The synchronous path, for FR-ASY-07: the same text through espk_synth(), hash only
static bool on_hash(const int16_t *pcm, size_t n, void *arg)
{
    mbedtls_sha256_update(arg, (const unsigned char *)pcm, n * sizeof *pcm);
    return true;
}

static void cmd_synth(const char *text)
{
    mbedtls_sha256_context sha;
    mbedtls_sha256_init(&sha);
    mbedtls_sha256_starts(&sha, 0);
    esp_err_t err = espk_synth(text, on_hash, &sha);
    unsigned char d[32];
    mbedtls_sha256_finish(&sha, d);
    mbedtls_sha256_free(&sha);
    char hex[65];
    for (int i = 0; i < 32; i++) sprintf(hex + 2 * i, "%02x", d[i]);
    if (err != ESP_OK) {
        printf("ESPK error code=%s\n", esp_err_to_name(err));
    } else {
        printf("ESPK sync sha256=%s bytes=%u\n", hex, (unsigned)strlen(text));
    }
}

static void cmd_taskinfo(void)  // FR-ASY-05, FR-ASY-08
{
    espk_task_info_t ti;
    if (espk_task_info(&ti) != ESP_OK) {
        printf("ESPK taskinfo none\n");
    } else {
        printf("ESPK taskinfo stack=%u psram=%d hwm=%u\n", (unsigned)ti.stack_bytes, ti.stack_in_psram,
               (unsigned)ti.stack_hwm_bytes);
    }
}

static void dispatch(char *line)
{
    char reply[64];
    if (espk_vol_handle(&s_vol, line, reply, sizeof reply)) {
        printf("%s\n", reply);
    } else if (strncmp(line, "say --mute ", 11) == 0) {
        cmd_say(line + 11, false);
    } else if (strncmp(line, "say ", 4) == 0) {
        cmd_say(line + 4, true);
    } else if (strcmp(line, "cancel") == 0) {  // FR-RES-10: the answer is the cancelled event, if one follows
        esp_err_t err = espk_cancel();
        if (err != ESP_OK) printf("ESPK cancel err=%s\n", esp_err_to_name(err));
    } else if (strncmp(line, "synth ", 6) == 0) {
        cmd_synth(line + 6);
    } else if (strcmp(line, "taskinfo") == 0) {
        cmd_taskinfo();
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
    usb_serial_jtag_driver_config_t ucfg = {.tx_buffer_size = 1024, .rx_buffer_size = 4096};
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&ucfg));
    usb_serial_jtag_vfs_use_driver();
    setvbuf(stdin, NULL, _IONBF, 0);

    espk_vol_init(&s_vol);
    s_audio_ok = espk_aud_init() == ESP_OK;  // FR-ERR-01: a missing codec is reported, not fatal
    int64_t t0 = esp_timer_get_time();
    espk_config_t cfg = {.evt_cb = on_event};
    esp_err_t err = espk_init(&cfg);
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
        xTaskCreateWithCaps(console_task, "console", CONSOLE_STACK, NULL, 5, NULL, MALLOC_CAP_SPIRAM);
    }
    for (unsigned k = 1;; k++) {
        printf("ESPK alive n=%u\n", k);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
