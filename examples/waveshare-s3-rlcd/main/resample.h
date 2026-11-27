/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Linear resampling of the engine's 16-bit mono PCM to the rate of the codec (FSD FR-EXM-04).
 *
 * The engine always makes 22 050 Hz. A codec that runs at another rate needs the PCM converted. This is the
 * simplest converter that is correct across the blocks the callback delivers: linear interpolation between
 * neighbouring samples, with the position and the last sample carried from one block to the next.
 * Good enough for speech; use a polyphase filter when the rate drops a lot and the top of the band matters. */
#pragma once

#include <stddef.h>
#include <stdint.h>

typedef struct {
    int from, to;     /* sample rates, Hz */
    double pos;       /* position of the next output sample, in input samples, relative to the block's start */
    int16_t last;     /* the last input sample of the previous block */
    int have_last;
} resampler_t;

static inline void resampler_init(resampler_t *r, int from, int to)
{
    r->from = from;
    r->to = to;
    r->pos = 0.0;
    r->last = 0;
    r->have_last = 0;
}

/* Converts one block; returns the number of samples written to out (at most cap). */
static inline size_t resample_block(resampler_t *r, const int16_t *in, size_t n, int16_t *out, size_t cap)
{
    const double step = (double)r->from / (double)r->to;
    size_t w = 0;
    /* position p means: between in[floor(p) - 1] and in[floor(p)]; -1 is the carried sample */
    while (w < cap) {
        long i = (long)r->pos;
        if (i >= (long)n) break;
        double frac = r->pos - (double)i;
        int16_t a = i > 0 ? in[i - 1] : (r->have_last ? r->last : in[0]);
        int16_t b = in[i];
        out[w++] = (int16_t)((1.0 - frac) * a + frac * b);
        r->pos += step;
    }
    if (n > 0) {
        r->pos -= (double)n;
        r->last = in[n - 1];
        r->have_last = 1;
    }
    return w;
}
