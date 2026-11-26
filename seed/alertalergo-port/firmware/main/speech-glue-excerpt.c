/* SPDX-License-Identifier: GPL-3.0-or-later
 * Excerpt of alertalergo-v3-firmware firmware/main/main.c @ 19787f2, lines 400-640:
 * audio task (tone/speech), speech task, speech_boot/say/cancel, audio_boot.
 * Evidence for the research FSD, not a build unit. */
    }
}

/* ---- áudio (FSD §18.1) ------------------------------------------------- */

typedef enum { AUD_REQ_TONE, AUD_REQ_SPEECH } aud_kind_t;

typedef struct {
    aud_kind_t kind;
    aud_clip_t clip;                   /* TONE */
    const char *reason;                /* TONE; literal: vive para sempre */
    uint32_t id;                       /* SPEECH: a fala (FR-SPK-02) */
    size_t chars;                      /* SPEECH: code points do texto */
    const int16_t *pcm;                /* SPEECH: mono, s_spk_rate Hz */
    size_t n;
} aud_req_t;

/* ---- fala (FSD §18.2) ----------------------------------------------------
 * A síntese roda na tarefa "spk" (prioridade baixa) e enche um buffer na
 * PSRAM; a tarefa de áudio o toca depois do tom (FR-ALR-04) e emite
 * SPEECH start/done. Uma fala por vez: a próxima espera o fim desta.
 * FR-SPK-03: o callback cede a CPU a cada pedaço. FR-SPK-05: sem áudio em 3 s
 * a síntese para com err=timeout. Silêncio (FR-ALR-07) interrompe: abort. */
#define SPK_TIMEOUT_US 3000000
#define SPK_STACK 65536              /* medido: ~39 KB na fala de paciente; o resto é folga */
#define SPK_MAX_S 12                   /* buffer: a fala mais longa de §11.2 cabe com folga */

typedef struct {
    uint32_t id;
    char text[SPK_TEXT_MAX];
} spk_req_t;

static QueueHandle_t s_spk_q;          /* NULL = fala desligada (FR-PLT-06, FR-ERR-01) */
static SemaphoreHandle_t s_spk_played; /* a tarefa de áudio terminou o buffer */
static int16_t *s_spk_buf;
static size_t s_spk_cap, s_spk_len;
static int s_spk_rate;
static int64_t s_spk_t0;
static bool s_spk_timeout;
static atomic_bool s_spk_cancel;
static atomic_uint s_spk_next_id = 1;

/* O I²S guarda até ~90 ms (6 × 240 quadros); sem esta cauda de silêncio o
 * close cortaria o fim do som. Na entrada, 60 ms de silêncio com o PA já
 * ligado e uma rampa de AUD_FADE_MS: sem isso o começo estalava (escuta de
 * 2026-11-08). */
#define AUD_TAIL_FRAMES 1440
#define AUD_LEAD_MS 60

static void write_zeros(int16_t *buf, size_t frames_cap, size_t frames)
{
    memset(buf, 0, frames_cap * 2 * sizeof *buf);
    for (size_t k = 0; k < frames; k += frames_cap) aud_hw_write(buf, frames - k < frames_cap ? frames - k : frames_cap);
}

static void audio_task(void *arg)
{
    enum { FRAMES = 256 };
    static int16_t buf[FRAMES * 2];
    for (;;) {
        aud_req_t r;
        xQueueReceive(s_aud_q, &r, portMAX_DELAY);
        int vol = atomic_load(&s_vol);
        char m[80];
        bool speech = r.kind == AUD_REQ_SPEECH;
        if (speech) {
            if (atomic_load(&s_spk_cancel)) {          /* silêncio ligou antes de começar */
                if (spk_abort_marker(m, sizeof m, r.id)) printf("%s\n", m);
                xSemaphoreGive(s_spk_played);
                continue;
            }
        } else if (aud_play_marker(m, sizeof m, r.clip, r.reason, vol)) {
            printf("%s\n", m);                             /* FR-AUD-04 */
        }
        int64_t t0 = esp_timer_get_time();
        if (aud_hw_open(vol, speech ? s_spk_rate : AUD_RATE) != ESP_OK) {
            printf("AUDIO fail err=open\n");
            if (speech) {
                if (spk_fail_marker(m, sizeof m, r.id, "audio")) printf("%s\n", m);
                xSemaphoreGive(s_spk_played);
            }
            continue;
        }
        printf("AUDIO pa=%d\n", aud_hw_pa_level());                 /* FR-AUD-01 */
        int rate = speech ? s_spk_rate : AUD_RATE;
        size_t fade = (size_t)rate * AUD_FADE_MS / 1000;
        write_zeros(buf, FRAMES, (size_t)rate * AUD_LEAD_MS / 1000);
        bool aborted = false;
        if (speech) {
            if (spk_start_marker(m, sizeof m, r.id, r.chars)) printf("%s\n", m);   /* ao começar o áudio */
            for (size_t i = 0; i < r.n && !aborted; i += FRAMES) {
                size_t k = r.n - i < FRAMES ? r.n - i : FRAMES;
                for (size_t j = 0; j < k; j++) {
                    int32_t v = aud_speech_sample(r.pcm[i + j]) * (int32_t)aud_fade_q8(i + j, fade) / 256;
                    buf[2 * j] = buf[2 * j + 1] = (int16_t)v;
                }
                aud_hw_write(buf, k);
                aborted = atomic_load(&s_spk_cancel);
            }
        } else {
            aud_synth_t s;
            aud_synth_start(&s, r.clip);
            size_t n, pos = 0;
            while ((n = aud_synth_fill(&s, buf, FRAMES, vol)) > 0) {
                for (size_t j = 0; j < n && pos + j < fade; j++) {
                    uint16_t f = aud_fade_q8(pos + j, fade);
                    buf[2 * j] = (int16_t)(buf[2 * j] * f / 256);
                    buf[2 * j + 1] = (int16_t)(buf[2 * j + 1] * f / 256);
                }
                pos += n;
                aud_hw_write(buf, n);
            }
        }
        write_zeros(buf, FRAMES, AUD_TAIL_FRAMES);
        aud_hw_close();
        uint32_t ms = (uint32_t)((esp_timer_get_time() - t0) / 1000);
        printf("AUDIO pa=%d\n", aud_hw_pa_level());
        if (speech) {
            size_t ok = aborted ? spk_abort_marker(m, sizeof m, r.id)
                                : spk_done_marker(m, sizeof m, r.id, ms,
                                                  (uint32_t)heap_caps_get_minimum_free_size(MALLOC_CAP_INTERNAL));
            if (ok) printf("%s\n", m);                     /* FR-SPK-02/06 */
            xSemaphoreGive(s_spk_played);
        } else if (aud_done_marker(m, sizeof m, r.clip, ms)) {
            printf("%s\n", m);
        }
    }
}

static bool on_spk_pcm(const int16_t *pcm, size_t n, void *ctx)
{
    (void)ctx;
    if (atomic_load(&s_spk_cancel)) return false;
    if (s_spk_len == 0 && esp_timer_get_time() - s_spk_t0 > SPK_TIMEOUT_US) {
        s_spk_timeout = true;                             /* FR-SPK-05 */
        return false;
    }
    if (s_spk_len + n > s_spk_cap) return false;          /* não cabe: falha, nunca truncada */
    memcpy(s_spk_buf + s_spk_len, pcm, n * sizeof *pcm);
    s_spk_len += n;
    vTaskDelay(1);                                        /* FR-SPK-03: a IDLE roda */
    return true;
}

static void speech_task(void *arg)
{
    for (;;) {
        spk_req_t r;
        xQueueReceive(s_spk_q, &r, portMAX_DELAY);
        char m[80];
        s_spk_len = 0;
        s_spk_t0 = esp_timer_get_time();
        s_spk_timeout = false;
        esp_err_t err = spk_hw_synth(r.text, on_spk_pcm, NULL);
        if (s_spk_len == 0 && esp_timer_get_time() - s_spk_t0 > SPK_TIMEOUT_US) s_spk_timeout = true;
        const char *fail = s_spk_timeout ? "timeout"
                         : atomic_load(&s_spk_cancel) ? NULL
                         : err == ESP_ERR_NOT_FINISHED ? "too_long"
                         : err != ESP_OK ? "synth"
                         : s_spk_len == 0 ? "empty" : NULL;
        if (atomic_load(&s_spk_cancel) && !s_spk_timeout) {
            if (spk_abort_marker(m, sizeof m, r.id)) printf("%s\n", m);
            continue;
        }
        if (fail) {
            if (spk_fail_marker(m, sizeof m, r.id, fail)) printf("%s\n", m);
            continue;
        }
        aud_req_t a = {.kind = AUD_REQ_SPEECH, .id = r.id, .chars = spk_chars(r.text), .pcm = s_spk_buf, .n = s_spk_len};
        xSemaphoreTake(s_spk_played, 0);
        if (xQueueSend(s_aud_q, &a, pdMS_TO_TICKS(1000)) != pdTRUE) {
            if (spk_fail_marker(m, sizeof m, r.id, "busy")) printf("%s\n", m);
            continue;
        }
        xSemaphoreTake(s_spk_played, portMAX_DELAY);      /* o buffer é um só */
    }
}

/* FR-PLT-06: dados da fala conferidos depois do splash; sem eles, só os tons. */
static void speech_boot(void)
{
    const char *why = "codec";                            /* FR-ERR-01: sem áudio, sem fala */
    esp_err_t err = s_aud_q ? spk_hw_init(&why) : ESP_ERR_INVALID_STATE;
    if (err == ESP_OK) {
        s_spk_rate = spk_hw_rate();
        s_spk_cap = (size_t)s_spk_rate * SPK_MAX_S;
        s_spk_buf = heap_caps_malloc(s_spk_cap * sizeof *s_spk_buf, MALLOC_CAP_SPIRAM);
        if (!s_spk_buf || s_spk_rate <= 0) {
            err = ESP_ERR_NO_MEM;
            why = "no_mem";
        }
    }
    char m[64];
    if (spk_ready_marker(m, sizeof m, err == ESP_OK, why)) printf("%s\n", m);
    if (err != ESP_OK) return;
    s_spk_played = xSemaphoreCreateBinary();
    s_spk_q = xQueueCreate(2, sizeof(spk_req_t));
    /* A pilha do eSpeak é funda (o upstream sugere 80 KB): fica na PSRAM.
     * Esta tarefa nunca grava na flash, então pode ter pilha externa. */
    if (xTaskCreateWithCaps(speech_task, "spk", SPK_STACK, NULL, 2, NULL, MALLOC_CAP_SPIRAM) != pdPASS) {
        printf("SPEECH ready=0 reason=no_mem\n");
        s_spk_q = NULL;
    }
}

/* Enfileira uma fala; nunca bloqueia (FR-ALR-05). Devolve o id, ou 0. */
static uint32_t speech_say(const char *text)
{
    spk_req_t r = {.id = atomic_fetch_add(&s_spk_next_id, 1)};
    if (!s_spk_q || !text || !*text || strlen(text) >= sizeof r.text) return 0;
    strcpy(r.text, text);
    atomic_store(&s_spk_cancel, false);
    return xQueueSend(s_spk_q, &r, 0) == pdTRUE ? r.id : 0;
}

/* FR-ALR-07: o silêncio interrompe a fala em curso e a que está na fila. */
static void speech_cancel(void)
{
    atomic_store(&s_spk_cancel, true);
    if (s_spk_q) xQueueReset(s_spk_q);
}

/* FR-ERR-01: sem ES8311 o tom (e a fala) ficam desligados; o resto segue. */
static void audio_boot(void)
{
    esp_err_t err = s_i2c ? aud_hw_init(s_i2c) : ESP_ERR_INVALID_STATE;
    if (err != ESP_OK) {
        printf("AUDIO fail err=codec\n");
        return;
    }
    s_aud_q = xQueueCreate(4, sizeof(aud_req_t));
    xTaskCreate(audio_task, "aud", 3072, NULL, 5, NULL);
    printf("AUDIO pa=%d\n", aud_hw_pa_level());                     /* em repouso: 0 */
}

/* Nunca bloqueia (FR-ALR-05): fila cheia descarta o tom. */
static bool audio_play(aud_clip_t c, const char *reason)
{
    aud_req_t r = {.kind = AUD_REQ_TONE, .clip = c, .reason = reason};
    return s_aud_q && xQueueSend(s_aud_q, &r, 0) == pdTRUE;
}
