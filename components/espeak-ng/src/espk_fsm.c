// SPDX-License-Identifier: GPL-3.0-or-later
#include "espk_fsm.h"

#include <stdio.h>
#include <string.h>

static const char *const k_states[] = {"UNINIT", "IDLE", "SPEAKING", "CANCELLING"};
static const char *const k_events[] = {"INIT_OK", "INIT_FAIL", "SAY", "SAY_TOO_BIG", "CANCEL", "DEINIT",
                                       "TEXT_END", "ENGINE_ERROR", "SYNTH_STOPPED"};
static const char *const k_results[] = {"OK", "PASS", "INVALID_STATE", "INVALID_SIZE", "NO_MEM"};
static const char *const k_actions[] = {"CREATE_TASK", "ENQUEUE", "STOP", "CLEAR_QUEUE", "EVT_DONE",
                                        "EVT_CANCELLED", "EVT_ERROR", "EVT_START", "END_TASK"};

#define STEP(res, act) ((espk_fsm_step_t){(res), (act)})

espk_fsm_step_t espk_fsm_step(espk_fsm_t *f, espk_ev_t ev)
{
    switch (f->state) {
    case ESPK_ST_UNINIT:
        if (ev == ESPK_EV_INIT_OK) {
            f->state = ESPK_ST_IDLE;
            return STEP(ESPK_R_OK, ESPK_A_CREATE_TASK);
        }
        if (ev == ESPK_EV_INIT_FAIL) return STEP(ESPK_R_PASS, 0);
        if (ev == ESPK_EV_SAY || ev == ESPK_EV_CANCEL) return STEP(ESPK_R_INVALID_STATE, 0);
        break;

    case ESPK_ST_IDLE:
        if (ev == ESPK_EV_SAY) {
            f->state = ESPK_ST_SPEAKING;
            return STEP(ESPK_R_OK, ESPK_A_ENQUEUE | ESPK_A_EVT_START);
        }
        if (ev == ESPK_EV_SAY_TOO_BIG) return STEP(ESPK_R_INVALID_SIZE, 0);
        if (ev == ESPK_EV_CANCEL) return STEP(ESPK_R_OK, 0);
        if (ev == ESPK_EV_DEINIT) {
            f->state = ESPK_ST_UNINIT;
            return STEP(ESPK_R_OK, ESPK_A_END_TASK);
        }
        break;

    case ESPK_ST_SPEAKING:
        if (ev == ESPK_EV_SAY) {
            if (f->waiting >= f->capacity) return STEP(ESPK_R_NO_MEM, 0);
            f->waiting++;
            return STEP(ESPK_R_OK, ESPK_A_ENQUEUE);
        }
        if (ev == ESPK_EV_SAY_TOO_BIG) return STEP(ESPK_R_INVALID_SIZE, 0);
        if (ev == ESPK_EV_TEXT_END) {
            if (f->waiting == 0) {
                f->state = ESPK_ST_IDLE;
                return STEP(ESPK_R_OK, ESPK_A_EVT_DONE);
            }
            f->waiting--;
            return STEP(ESPK_R_OK, ESPK_A_EVT_DONE | ESPK_A_EVT_START);
        }
        if (ev == ESPK_EV_CANCEL) {
            f->state = ESPK_ST_CANCELLING;
            f->waiting = 0;
            return STEP(ESPK_R_OK, ESPK_A_STOP | ESPK_A_CLEAR_QUEUE);
        }
        if (ev == ESPK_EV_ENGINE_ERROR) {
            f->state = ESPK_ST_IDLE;
            f->waiting = 0;
            return STEP(ESPK_R_OK, ESPK_A_EVT_ERROR | ESPK_A_CLEAR_QUEUE);
        }
        if (ev == ESPK_EV_DEINIT) {  // CANCELLING -> UNINIT in one step
            f->state = ESPK_ST_UNINIT;
            f->waiting = 0;
            return STEP(ESPK_R_OK, ESPK_A_STOP | ESPK_A_CLEAR_QUEUE | ESPK_A_END_TASK);
        }
        break;

    case ESPK_ST_CANCELLING:
        if (ev == ESPK_EV_SYNTH_STOPPED) {
            if (f->waiting == 0) {
                f->state = ESPK_ST_IDLE;
                return STEP(ESPK_R_OK, ESPK_A_EVT_CANCELLED);
            }
            f->state = ESPK_ST_SPEAKING;  // a say taken while cancelling speaks right after the CANCELLED
            f->waiting--;
            return STEP(ESPK_R_OK, ESPK_A_EVT_CANCELLED | ESPK_A_EVT_START);
        }
        if (ev == ESPK_EV_SAY) {
            if (f->waiting >= f->capacity) return STEP(ESPK_R_NO_MEM, 0);
            f->waiting++;
            return STEP(ESPK_R_OK, ESPK_A_ENQUEUE);
        }
        if (ev == ESPK_EV_SAY_TOO_BIG) return STEP(ESPK_R_INVALID_SIZE, 0);
        if (ev == ESPK_EV_CANCEL) return STEP(ESPK_R_OK, 0);
        if (ev == ESPK_EV_DEINIT) {
            f->state = ESPK_ST_UNINIT;
            f->waiting = 0;
            return STEP(ESPK_R_OK, ESPK_A_END_TASK);
        }
        break;
    }
    return STEP(ESPK_R_INVALID_STATE, 0);
}

const char *espk_fsm_state_name(espk_st_t s) { return k_states[s]; }
const char *espk_fsm_result_name(espk_res_t r) { return k_results[r]; }

espk_st_t espk_fsm_state_from_name(const char *name)
{
    for (int i = 0; i < 4; i++)
        if (strcmp(name, k_states[i]) == 0) return (espk_st_t)i;
    return ESPK_ST_UNINIT;
}

espk_ev_t espk_fsm_event_from_name(const char *name)
{
    for (int i = 0; i < ESPK_EV__COUNT; i++)
        if (strcmp(name, k_events[i]) == 0) return (espk_ev_t)i;
    return ESPK_EV__COUNT;
}

void espk_fsm_actions_str(unsigned actions, char *out, size_t n)
{
    out[0] = '\0';
    for (int i = 0; i < 9; i++) {
        if (!(actions & (1u << i))) continue;
        size_t len = strlen(out);
        snprintf(out + len, n - len, "%s%s", len ? "," : "", k_actions[i]);
    }
    if (!out[0]) snprintf(out, n, "-");
}
