/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "esp_err.h"
/* Confere a partição `espeak` e monta o VFS em `base`; `*reason` em erro. */
esp_err_t espeak_part_mount(const char *base, const char **reason);
