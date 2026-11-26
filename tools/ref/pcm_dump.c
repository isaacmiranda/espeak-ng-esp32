/*
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * PCM of eSpeak NG for each line of a text file, through the public synchronous API
 * (the same calls the component makes). Linked against the R1 build of the upstream.
 *
 *   pcm_dump <espeak-ng-data dir> <voice name> <texts.txt> <out dir> [rate_wpm]
 *
 * Writes <out>/NNNN.pcm (16-bit signed mono, native byte order) per line and prints
 * "rate=<Hz>" once. The voice and the parameters stay the upstream defaults unless
 * rate_wpm is given.
 */
#include <espeak-ng/espeak_ng.h>
#include <espeak-ng/speak_lib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static FILE *g_out;

static int on_pcm(short *wav, int n, espeak_EVENT *ev)
{
    (void)ev;
    if (wav && n > 0) fwrite(wav, sizeof *wav, (size_t)n, g_out);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 5 && argc != 6) {
        fprintf(stderr, "usage: pcm_dump <data> <voice> <texts> <out> [rate]\n");
        return 2;
    }
    espeak_ng_InitializePath(argv[1]);
    if (espeak_ng_Initialize(NULL) != ENS_OK ||
        espeak_ng_InitializeOutput(ENOUTPUT_MODE_SYNCHRONOUS, 0, NULL) != ENS_OK) return 3;
    if (espeak_ng_SetVoiceByName(argv[2]) != ENS_OK) return 4;
    if (argc == 6 && espeak_ng_SetParameter(espeakRATE, atoi(argv[5]), 0) != ENS_OK) return 5;
    espeak_SetSynthCallback(on_pcm);
    FILE *in = fopen(argv[3], "r");
    if (!in) return 6;
    static char line[8192];
    int rc = 0;
    for (int i = 0; fgets(line, sizeof line, in); i++) {
        line[strcspn(line, "\n")] = '\0';
        char path[4096];
        snprintf(path, sizeof path, "%s/%04d.pcm", argv[4], i);
        if (!(g_out = fopen(path, "wb"))) { rc = 7; break; }
        if (espeak_ng_Synthesize(line, strlen(line) + 1, 0, POS_CHARACTER, 0, espeakCHARS_UTF8, NULL, NULL) != ENS_OK ||
            espeak_ng_Synchronize() != ENS_OK) rc = 8;
        fclose(g_out);
        if (rc) break;
    }
    fclose(in);
    printf("rate=%d\n", espeak_ng_GetSampleRate());
    return rc;
}
