// SPDX-License-Identifier: GPL-3.0-or-later
// Internal: the data partition and its read-only VFS (FSD §12, Appendix A).
#pragma once

#include <stdint.h>

#include "esp_err.h"

typedef struct __attribute__((packed)) {
    char name[64];  // path relative to the mount point, lower case, NUL-terminated
    uint32_t offset, size;  // offset from the start of the payload
} espk_entry_t;

esp_err_t espk_part_mount(const char *label, uint8_t subtype, const char *base, const char *engine_version,
                          const char **reason);
uint32_t espk_part_count(void);
const espk_entry_t *espk_part_entry(uint32_t i);
