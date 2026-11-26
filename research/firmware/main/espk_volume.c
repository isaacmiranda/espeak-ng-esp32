/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "espk_volume.h"

#include <stdio.h>
#include <string.h>

void espk_vol_init(espk_vol_t *v)
{
    v->vol = ESPK_VOL_DEFAULT;
    v->listening = false;
}

// strictly digits, at most 3 of them; 0-100
static bool parse_vol(const char *s, int *out)
{
    size_t n = strlen(s);
    if (n == 0 || n > 3) return false;
    int x = 0;
    for (size_t i = 0; i < n; i++) {
        if (s[i] < '0' || s[i] > '9') return false;
        x = x * 10 + (s[i] - '0');
    }
    if (x > 100) return false;
    *out = x;
    return true;
}

bool espk_vol_handle(espk_vol_t *v, const char *line, char *out, size_t n)
{
    int x;
    if (strcmp(line, "volume") == 0) {
        snprintf(out, n, "ESPK volume ok=%d", v->vol);
    } else if (strncmp(line, "volume ", 7) == 0) {
        if (!parse_vol(line + 7, &x)) {
            snprintf(out, n, "ESPK volume err=range");
        } else if (x > ESPK_VOL_CEILING && !v->listening) {
            snprintf(out, n, "ESPK volume err=ceiling");
        } else {
            v->vol = x;
            snprintf(out, n, "ESPK volume ok=%d", x);
        }
    } else if (strncmp(line, "listen open", 11) == 0 && (line[11] == ' ' || line[11] == '\0')) {
        if (line[11] == '\0' || !parse_vol(line + 12, &x)) {
            snprintf(out, n, "ESPK listen err=range");
        } else {
            v->listening = true;
            v->vol = x;
            snprintf(out, n, "ESPK listen ok=open");
        }
    } else if (strcmp(line, "listen close") == 0) {
        v->listening = false;
        v->vol = ESPK_VOL_DEFAULT;  // leaving a session never leaves the loud volume behind
        snprintf(out, n, "ESPK listen ok=close");
    } else {
        return false;
    }
    return true;
}
