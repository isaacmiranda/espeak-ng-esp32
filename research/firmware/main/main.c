// SPDX-License-Identifier: GPL-3.0-or-later
// Composition root of the research firmware (FSD §5). It prints the boot marker, a
// heartbeat that the bench can observe at any moment, and runs the console: every line
// that is not a known command gets `ESPK error code=unknown_command` (FR-RES-15). The
// commands themselves arrive with the component in /build.
#include <stdio.h>

#include "driver/usb_serial_jtag.h"
#include "driver/usb_serial_jtag_vfs.h"
#include "esp_app_desc.h"
#include "esp_idf_version.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define CONSOLE_LINE_MAX 1100  // FR-RES-16: texts up to 1 024 bytes plus the command word

static void console_task(void *arg)
{
    static char line[CONSOLE_LINE_MAX];
    size_t n = 0;
    bool overflow = false;
    for (;;) {
        int c = fgetc(stdin);
        if (c == EOF) {
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }
        if (c == '\r') {
            continue;
        }
        if (c == '\n') {
            if (overflow) {
                printf("ESPK error code=too_long\n");
            } else if (n > 0) {
                printf("ESPK error code=unknown_command\n");
            }
            n = 0;
            overflow = false;
            continue;
        }
        if (n < sizeof(line) - 1) {
            line[n++] = (char)c;
        } else {
            overflow = true;
        }
    }
}

void app_main(void)
{
    usb_serial_jtag_driver_config_t cfg = USB_SERIAL_JTAG_DRIVER_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&cfg));
    usb_serial_jtag_vfs_use_driver();
    setvbuf(stdin, NULL, _IONBF, 0);

    const esp_app_desc_t *app = esp_app_get_description();
    // ESPK <event> key=value ... (FSD FR-LOG-01)
    printf("ESPK boot fw=%s commit=%s idf=%s\n", app->version, ESPK_COMMIT, esp_get_idf_version());
    xTaskCreate(console_task, "console", 4096, NULL, 5, NULL);

    for (unsigned k = 1;; k++) {
        printf("ESPK alive n=%u\n", k);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
