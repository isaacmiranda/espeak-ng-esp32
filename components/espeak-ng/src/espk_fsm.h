// SPDX-License-Identifier: GPL-3.0-or-later
// State table of the async layer (FSD 15.2) as a pure function: no FreeRTOS, no engine. The task
// (espk.c) performs the actions this returns; the host tests drive the table directly (FR-ASY-09).
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef enum { ESPK_ST_UNINIT, ESPK_ST_IDLE, ESPK_ST_SPEAKING, ESPK_ST_CANCELLING } espk_st_t;

typedef enum {
    ESPK_EV_INIT_OK,
    ESPK_EV_INIT_FAIL,
    ESPK_EV_SAY,          // a text that fits
    ESPK_EV_SAY_TOO_BIG,  // a text above CONFIG_ESPK_MAX_TEXT_LEN
    ESPK_EV_CANCEL,
    ESPK_EV_DEINIT,
    ESPK_EV_TEXT_END,      // the synthesis of the current request ended
    ESPK_EV_ENGINE_ERROR,  // the engine failed on the current request
    ESPK_EV_SYNTH_STOPPED, // the synthesis stopped after a stop request
    ESPK_EV__COUNT
} espk_ev_t;

typedef enum {
    ESPK_R_OK,
    ESPK_R_PASS,  // the caller returns the error it already has (a failed init)
    ESPK_R_INVALID_STATE,
    ESPK_R_INVALID_SIZE,
    ESPK_R_NO_MEM,
} espk_res_t;

// In the order the task performs them: queue and stop first, then the events, the next START last.
enum {
    ESPK_A_CREATE_TASK = 1 << 0,
    ESPK_A_ENQUEUE = 1 << 1,
    ESPK_A_STOP = 1 << 2,
    ESPK_A_CLEAR_QUEUE = 1 << 3,
    ESPK_A_EVT_DONE = 1 << 4,
    ESPK_A_EVT_CANCELLED = 1 << 5,
    ESPK_A_EVT_ERROR = 1 << 6,
    ESPK_A_EVT_START = 1 << 7,
    ESPK_A_END_TASK = 1 << 8,
};

typedef struct {
    espk_st_t state;
    int waiting;   // requests queued behind the one being spoken
    int capacity;  // CONFIG_ESPK_QUEUE_LEN
} espk_fsm_t;

typedef struct {
    espk_res_t result;
    unsigned actions;  // ESPK_A_* bits, performed in the order of the enum
} espk_fsm_step_t;

// Applies an event: updates f and says what to return and do. A pair outside the table changes nothing
// and gives ESPK_R_INVALID_STATE.
espk_fsm_step_t espk_fsm_step(espk_fsm_t *f, espk_ev_t ev);

// Names, for the host harness and for logs.
const char *espk_fsm_state_name(espk_st_t s);
const char *espk_fsm_result_name(espk_res_t r);
espk_st_t espk_fsm_state_from_name(const char *name);
espk_ev_t espk_fsm_event_from_name(const char *name);
void espk_fsm_actions_str(unsigned actions, char *out, size_t n);
