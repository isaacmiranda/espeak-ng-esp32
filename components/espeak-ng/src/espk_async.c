// SPDX-License-Identifier: GPL-3.0-or-later
// Asynchronous layer (FSD 15): a synthesis task with a queue over the synchronous core. The state table
// lives in espk_fsm.c; this file only performs what it says. Built on the public espk_synth().
#include "espk_async.h"

#include "sdkconfig.h"

#ifndef CONFIG_ESPK_ASYNC
esp_err_t espk_async_start(const espk_config_t *cfg)
{
    (void)cfg;
    return ESP_OK;  // FR-ASY-08: no task is created
}
esp_err_t espk_say(const char *utf8, espk_pcm_cb_t cb, void *ctx, uint32_t *id)
{
    (void)utf8, (void)cb, (void)ctx, (void)id;
    return ESP_ERR_NOT_SUPPORTED;
}
esp_err_t espk_cancel(void) { return ESP_ERR_NOT_SUPPORTED; }
#else

#include <stdatomic.h>
#include <string.h>

#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "espk_fsm.h"
#include "freertos/FreeRTOS.h"
#include "freertos/idf_additions.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

static const char *TAG = "espk_async";

#define RING (CONFIG_ESPK_QUEUE_LEN + 1)  // the request being spoken plus those waiting

typedef struct {
    uint32_t id;
    char *text;
    espk_pcm_cb_t cb;
    void *ctx;
} item_t;

static SemaphoreHandle_t s_lock, s_wake;
static espk_fsm_t s_fsm = {.state = ESPK_ST_UNINIT, .capacity = CONFIG_ESPK_QUEUE_LEN};
static item_t s_q[RING];
static int s_head, s_count;
static uint32_t s_next_id;
static atomic_bool s_stop;
static int64_t s_cancel_t0;
static espk_evt_cb_t s_evt_cb;
static void *s_evt_ctx;

static void emit(const espk_evt_t *e)
{
    if (s_evt_cb) s_evt_cb(e, s_evt_ctx);
}

// Takes the requests behind the first `keep` ones out of the ring (caller holds s_lock); returns them in out.
// keep is 1 while the request being spoken is still in the ring, 0 once it has left.
static int drop_waiting(item_t *out, int keep)
{
    int n = 0;
    while (s_count > keep) {
        int tail = (s_head + s_count - 1) % RING;
        out[n++] = s_q[tail];
        s_count--;
    }
    return n;
}

typedef struct {
    espk_pcm_cb_t cb;
    void *ctx;
    uint32_t samples;
    int64_t t0, first_us;
} run_t;

static bool on_pcm(const int16_t *pcm, size_t n, void *arg)
{
    run_t *r = arg;
    if (atomic_load(&s_stop)) return false;  // espk_cancel(): the engine stops at this block
    if (r->samples == 0) r->first_us = esp_timer_get_time() - r->t0;
    r->samples += (uint32_t)n;
    return r->cb(pcm, n, r->ctx);
}

static void task(void *arg)
{
    (void)arg;
    for (;;) {
        xSemaphoreTake(s_wake, portMAX_DELAY);
        for (;;) {
            xSemaphoreTake(s_lock, portMAX_DELAY);
            if (s_count == 0) {
                xSemaphoreGive(s_lock);
                break;
            }
            item_t it = s_q[s_head];
            xSemaphoreGive(s_lock);

            espk_evt_t e = {.type = ESPK_EVT_START, .id = it.id, .pcm_ctx = it.ctx};
            emit(&e);
            run_t r = {.cb = it.cb, .ctx = it.ctx, .t0 = esp_timer_get_time()};
            esp_err_t err = atomic_load(&s_stop) ? ESPK_ERR_CANCELLED : espk_synth(it.text, on_pcm, &r);
            int64_t end_us = esp_timer_get_time();

            xSemaphoreTake(s_lock, portMAX_DELAY);
            espk_ev_t ev;
            if (s_fsm.state == ESPK_ST_CANCELLING) {
                ev = ESPK_EV_SYNTH_STOPPED;  // even if the text ended first: a cancelled request is never DONE
            } else {
                ev = err == ESP_OK ? ESPK_EV_TEXT_END : ESPK_EV_ENGINE_ERROR;
            }
            espk_fsm_step_t st = espk_fsm_step(&s_fsm, ev);
            s_head = (s_head + 1) % RING;  // the request just finished leaves the ring
            s_count--;
            item_t dropped[RING];
            int nd = (st.actions & ESPK_A_CLEAR_QUEUE) ? drop_waiting(dropped, 0) : 0;
            if (ev == ESPK_EV_SYNTH_STOPPED) atomic_store(&s_stop, false);
            int64_t cancel_t0 = s_cancel_t0;
            xSemaphoreGive(s_lock);

            free(it.text);
            e = (espk_evt_t){.id = it.id, .pcm_ctx = it.ctx};
            if (st.actions & ESPK_A_EVT_DONE) {
                e.type = ESPK_EVT_DONE;
                e.samples = r.samples;
                e.synth_ms = (uint32_t)((end_us - r.t0) / 1000);
                e.first_ms = (uint32_t)(r.first_us / 1000);
                emit(&e);
            } else if (st.actions & ESPK_A_EVT_CANCELLED) {
                e.type = ESPK_EVT_CANCELLED;
                e.cancel_ms = (uint32_t)((end_us - cancel_t0) / 1000);
                emit(&e);
            } else if (st.actions & ESPK_A_EVT_ERROR) {
                e.type = ESPK_EVT_ERROR;
                e.err = err;
                emit(&e);
            }
            for (int i = nd - 1; i >= 0; i--) {  // requests dropped from the queue are CANCELLED too (their ctx is theirs)
                emit(&(espk_evt_t){.type = ESPK_EVT_CANCELLED, .id = dropped[i].id, .pcm_ctx = dropped[i].ctx});
                free(dropped[i].text);
            }
        }
    }
}

esp_err_t espk_async_start(const espk_config_t *cfg)
{
    s_evt_cb = cfg ? cfg->evt_cb : NULL;
    s_evt_ctx = cfg ? cfg->evt_ctx : NULL;
    s_lock = xSemaphoreCreateMutex();
    s_wake = xSemaphoreCreateBinary();
    if (!s_lock || !s_wake) return ESP_ERR_NO_MEM;
    UBaseType_t caps = CONFIG_ESPK_TASK_STACK_PSRAM ? MALLOC_CAP_SPIRAM : MALLOC_CAP_INTERNAL;
    if (xTaskCreatePinnedToCoreWithCaps(task, "espk", CONFIG_ESPK_TASK_STACK, NULL, CONFIG_ESPK_TASK_PRIORITY, NULL,
                                        tskNO_AFFINITY, caps) != pdPASS) {
        ESP_LOGE(TAG, "task: ESP_ERR_NO_MEM (stack %d)", CONFIG_ESPK_TASK_STACK);
        return ESP_ERR_NO_MEM;
    }
    espk_fsm_step(&s_fsm, ESPK_EV_INIT_OK);
    return ESP_OK;
}

static esp_err_t to_err(espk_res_t r)
{
    switch (r) {
    case ESPK_R_OK:
    case ESPK_R_PASS: return ESP_OK;
    case ESPK_R_INVALID_SIZE: return ESP_ERR_INVALID_SIZE;
    case ESPK_R_NO_MEM: return ESP_ERR_NO_MEM;
    default: return ESP_ERR_INVALID_STATE;
    }
}

esp_err_t espk_say(const char *utf8, espk_pcm_cb_t cb, void *ctx, uint32_t *id)
{
    if (!utf8 || !cb) return ESP_ERR_INVALID_ARG;
    size_t n = strnlen(utf8, CONFIG_ESPK_MAX_TEXT_LEN + 1);
    bool big = n > CONFIG_ESPK_MAX_TEXT_LEN;
    char *copy = big ? NULL : heap_caps_malloc(n + 1, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!big && !copy) return ESP_ERR_NO_MEM;
    if (copy) memcpy(copy, utf8, n + 1);

    if (!s_lock) {
        free(copy);
        return ESP_ERR_INVALID_STATE;
    }
    xSemaphoreTake(s_lock, portMAX_DELAY);
    espk_fsm_step_t st = espk_fsm_step(&s_fsm, big ? ESPK_EV_SAY_TOO_BIG : ESPK_EV_SAY);
    if (st.result == ESPK_R_OK) {
        uint32_t new_id = ++s_next_id;
        s_q[(s_head + s_count) % RING] = (item_t){new_id, copy, cb, ctx};
        s_count++;
        if (id) *id = new_id;
    }
    xSemaphoreGive(s_lock);
    if (st.result != ESPK_R_OK) {
        free(copy);
        return to_err(st.result);
    }
    xSemaphoreGive(s_wake);
    return ESP_OK;
}

esp_err_t espk_cancel(void)
{
    if (!s_lock) return ESP_ERR_INVALID_STATE;
    item_t dropped[RING];
    int nd = 0;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    espk_fsm_step_t st = espk_fsm_step(&s_fsm, ESPK_EV_CANCEL);
    if (st.actions & ESPK_A_STOP) {
        s_cancel_t0 = esp_timer_get_time();
        atomic_store(&s_stop, true);
    }
    if (st.actions & ESPK_A_CLEAR_QUEUE) nd = drop_waiting(dropped, 1);
    xSemaphoreGive(s_lock);
    for (int i = nd - 1; i >= 0; i--) {
        emit(&(espk_evt_t){.type = ESPK_EVT_CANCELLED, .id = dropped[i].id, .pcm_ctx = dropped[i].ctx});
        free(dropped[i].text);
    }
    return to_err(st.result);
}

#endif  // CONFIG_ESPK_ASYNC
