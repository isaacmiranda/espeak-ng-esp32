// SPDX-License-Identifier: GPL-3.0-or-later
// Composition root of the research firmware (FSD §5). Phase 1 skeleton: it proves the
// build -> artifact -> flash pipeline by printing the boot marker, and implements no
// requirement yet. The fields that need the component (rate, langs, init_ms) arrive
// with it in /build.
#include <stdio.h>

#include "esp_app_desc.h"
#include "esp_idf_version.h"

void app_main(void)
{
    const esp_app_desc_t *app = esp_app_get_description();
    // ESPK <event> key=value ... (FSD FR-LOG-01)
    printf("ESPK boot fw=%s commit=%s idf=%s\n", app->version, ESPK_COMMIT, esp_get_idf_version());
}
