/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Host harness for examples/waveshare-s3-rlcd/main/resample.h: resample_cli <from> <to> <block> <kind>
 * kind: dc (constant 1000) or tone (440 Hz at 12000); 22050 input samples; prints the output samples. */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "resample.h"

int main(int argc, char **argv)
{
    if (argc != 5) return 2;
    int from = atoi(argv[1]), to = atoi(argv[2]), block = atoi(argv[3]);
    enum { N = 22050 };
    static int16_t in[N], out[4 * N];
    for (int i = 0; i < N; i++)
        in[i] = argv[4][0] == 'd' ? 1000 : (int16_t)(12000.0 * sin(2.0 * M_PI * 440.0 * i / from));
    resampler_t r;
    resampler_init(&r, from, to);
    size_t total = 0;
    for (int i = 0; i < N; i += block) {
        int n = N - i < block ? N - i : block;
        total += resample_block(&r, in + i, (size_t)n, out + total, 4 * N - total);
    }
    for (size_t i = 0; i < total; i++) printf("%d\n", out[i]);
    return 0;
}
