/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "espk_audio.h"

#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_timer.h"
#include "driver/i2s_std.h"
#include "esp_codec_dev.h"
#include "esp_codec_dev_defaults.h"

/* Apêndice B / §2.2.2 [vendor] */
#define PIN_MCLK 16
#define PIN_BCLK 9
#define PIN_WS 45
#define PIN_DOUT 8
#define PIN_PA 46
#define ADDR_ES8311 0x18
#define PIN_SDA 13
#define PIN_SCL 14
#define PA_GAIN 6                    /* dB, o do BSP Waveshare e do commissioning A3 */

static esp_codec_dev_handle_t s_dev;
// FR-RES-12: the I2S has no underrun event for a blocking writer, so count the writes that
// arrive after the audio queued so far has already finished playing (the speaker ran dry).
static int64_t s_deadline_us;
static unsigned s_underruns;
static int s_rate;

esp_err_t espk_aud_init(void)
{
    i2c_master_bus_handle_t bus = NULL;
    i2c_master_bus_config_t bc = {.i2c_port = I2C_NUM_0, .sda_io_num = PIN_SDA, .scl_io_num = PIN_SCL,
                                  .clk_source = I2C_CLK_SRC_DEFAULT, .glitch_ignore_cnt = 7,
                                  .flags.enable_internal_pullup = true};
    esp_err_t err = i2c_new_master_bus(&bc, &bus);
    if (err != ESP_OK) return err;
    err = i2c_master_probe(bus, ADDR_ES8311, 100);
    if (err != ESP_OK) return err;

    i2s_chan_handle_t tx = NULL;
    i2s_chan_config_t chan = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    chan.auto_clear = true;                   /* sem dados, o I²S manda zeros */
    err = i2s_new_channel(&chan, &tx, NULL);
    if (err != ESP_OK) return err;
    i2s_std_config_t std = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(ESPK_AUD_INIT_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {.mclk = PIN_MCLK, .bclk = PIN_BCLK, .ws = PIN_WS, .dout = PIN_DOUT, .din = I2S_GPIO_UNUSED},
    };
    err = i2s_channel_init_std_mode(tx, &std);
    if (err != ESP_OK) return err;

    audio_codec_i2c_cfg_t i2c_cfg = {.port = I2C_NUM_0, .addr = ES8311_CODEC_DEFAULT_ADDR, .bus_handle = bus};
    const audio_codec_ctrl_if_t *ctrl = audio_codec_new_i2c_ctrl(&i2c_cfg);
    const audio_codec_gpio_if_t *gpio_if = audio_codec_new_gpio();
    audio_codec_i2s_cfg_t i2s_cfg = {.port = I2S_NUM_0, .tx_handle = tx};
    const audio_codec_data_if_t *data = audio_codec_new_i2s_data(&i2s_cfg);
    es8311_codec_cfg_t es = {
        .codec_mode = ESP_CODEC_DEV_WORK_MODE_DAC,
        .ctrl_if = ctrl,
        .gpio_if = gpio_if,
        .pa_pin = PIN_PA,
        .use_mclk = true,
        .hw_gain.pa_gain = PA_GAIN,
    };
    const audio_codec_if_t *codec = (ctrl && gpio_if && data) ? es8311_codec_new(&es) : NULL;
    if (!codec) return ESP_FAIL;
    esp_codec_dev_cfg_t dev_cfg = {.dev_type = ESP_CODEC_DEV_TYPE_OUT, .codec_if = codec, .data_if = data};
    s_dev = esp_codec_dev_new(&dev_cfg);
    if (!s_dev) return ESP_FAIL;
    /* es8311_codec_new liga o PA (es8311_open interno); um open/close do
     * dispositivo o desliga pelo próprio driver: PA baixo em repouso (FR-AUD-01). */
    err = espk_aud_open(0, ESPK_AUD_INIT_RATE);
    espk_aud_close();
    return err;
}

esp_err_t espk_aud_open(int vol, int rate)
{
    if (!s_dev) return ESP_ERR_INVALID_STATE;
    esp_codec_dev_sample_info_t fs = {.bits_per_sample = 16, .channel = 2, .sample_rate = (uint32_t)rate};
    if (esp_codec_dev_open(s_dev, &fs) != ESP_CODEC_DEV_OK) return ESP_FAIL;
    s_rate = rate;
    s_deadline_us = 0;
    s_underruns = 0;
    if (esp_codec_dev_set_out_vol(s_dev, vol) != ESP_CODEC_DEV_OK) {
        esp_codec_dev_close(s_dev);
        return ESP_FAIL;
    }
    return ESP_OK;
}

esp_err_t espk_aud_write(const int16_t *pcm, size_t frames)
{
    if (!s_dev) return ESP_ERR_INVALID_STATE;
    int64_t now = esp_timer_get_time();
    if (s_deadline_us != 0 && now > s_deadline_us) s_underruns++;
    if (s_deadline_us < now) s_deadline_us = now;
    s_deadline_us += (int64_t)frames * 1000000 / s_rate;
    return esp_codec_dev_write(s_dev, (void *)pcm, (int)(frames * 2 * sizeof *pcm)) == ESP_CODEC_DEV_OK ? ESP_OK
                                                                                                      : ESP_FAIL;
}

unsigned espk_aud_underruns(void)
{
    return s_underruns;
}

void espk_aud_close(void)
{
    if (s_dev) esp_codec_dev_close(s_dev);
}

