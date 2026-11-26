/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/* Volume ceiling and listening session of the research firmware (FSD FR-RES-07, 08, 09).
 * Pure: no hardware, so the host tests drive it directly. */
#include <stdbool.h>
#include <stddef.h>

#define ESPK_VOL_DEFAULT 5
#define ESPK_VOL_CEILING 10

typedef struct {
    int vol;         /* 0-100 */
    bool listening;  /* a listening session is open: the ceiling does not apply */
} espk_vol_t;

void espk_vol_init(espk_vol_t *v);

/* Handles `volume [N]` and `listen open N` / `listen close`. Returns false when the line is not
 * one of these; otherwise writes the ESPK reply line (no newline) into out and returns true. */
bool espk_vol_handle(espk_vol_t *v, const char *line, char *out, size_t n);
