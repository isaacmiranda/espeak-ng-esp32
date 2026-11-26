// SPDX-License-Identifier: GPL-3.0-or-later
// Internal: starts the asynchronous layer once the synchronous core is ready (called by espk_init).
#pragma once

#include "espk.h"

esp_err_t espk_async_start(const espk_config_t *cfg);
