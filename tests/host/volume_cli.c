/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Host harness for the firmware's volume/listen parser: one console line per stdin line. */
#include <stdio.h>
#include <string.h>

#include "espk_volume.h"

int main(void)
{
    espk_vol_t v;
    espk_vol_init(&v);
    char line[256], out[128];
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\r\n")] = '\0';
        puts(espk_vol_handle(&v, line, out, sizeof out) ? out : "unhandled");
    }
    return 0;
}
