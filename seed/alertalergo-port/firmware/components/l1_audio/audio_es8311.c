/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "l1_audio.h"

#include "driver/gpio.h"
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
#define PA_GAIN 6                    /* dB, o do BSP Waveshare e do commissioning A3 */

static esp_codec_dev_handle_t s_dev;

esp_err_t aud_hw_init(i2c_master_bus_handle_t bus)
{
    if (!bus) return ESP_ERR_INVALID_ARG;
    esp_err_t err = i2c_master_probe(bus, ADDR_ES8311, 100);
    if (err != ESP_OK) return err;

    i2s_chan_handle_t tx = NULL;
    i2s_chan_config_t chan = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    chan.auto_clear = true;                   /* sem dados, o I²S manda zeros */
    err = i2s_new_channel(&chan, &tx, NULL);
    if (err != ESP_OK) return err;
    i2s_std_config_t std = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(AUD_HW_RATE),
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
    err = aud_hw_open(0, AUD_HW_RATE);
    aud_hw_close();
    return err;
}

esp_err_t aud_hw_open(int vol, int rate)
{
    if (!s_dev) return ESP_ERR_INVALID_STATE;
    esp_codec_dev_sample_info_t fs = {.bits_per_sample = 16, .channel = 2, .sample_rate = (uint32_t)rate};
    if (esp_codec_dev_open(s_dev, &fs) != ESP_CODEC_DEV_OK) return ESP_FAIL;
    if (esp_codec_dev_set_out_vol(s_dev, vol) != ESP_CODEC_DEV_OK) {
        esp_codec_dev_close(s_dev);
        return ESP_FAIL;
    }
    return ESP_OK;
}

esp_err_t aud_hw_write(const int16_t *pcm, size_t frames)
{
    if (!s_dev) return ESP_ERR_INVALID_STATE;
    return esp_codec_dev_write(s_dev, (void *)pcm, (int)(frames * 2 * sizeof *pcm)) == ESP_CODEC_DEV_OK ? ESP_OK
                                                                                                      : ESP_FAIL;
}

void aud_hw_close(void)
{
    if (s_dev) esp_codec_dev_close(s_dev);
}

/* O esp_codec_dev configura o PA só como saída; sem o buffer de entrada a
 * leitura dá 0. Liga a entrada sem mudar o nível de saída (commissioning A3). */
int aud_hw_pa_level(void)
{
    gpio_input_enable(PIN_PA);
    return gpio_get_level(PIN_PA);
}
