// SPDX-License-Identifier: GPL-3.0-or-later
// Internal: starts the asynchronous layer once the synchronous core is ready (called by espk_init).
#pragma once

#include "espk.h"

esp_err_t espk_async_start(const espk_config_t *cfg);

// Cancels what is in progress, ends the task and releases the queue (espk_deinit). Requests still queued
// get a CANCELLED event so their owners can free the context. A no-op when there is no task.
void espk_async_stop(void);
