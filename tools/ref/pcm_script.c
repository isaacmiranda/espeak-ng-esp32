/*
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * Runs a script on the upstream engine through the public synchronous API, the same
 * calls the component makes, and writes the PCM of every `say` step (FSD §7).
 *
 *   pcm_script <espeak-ng-data dir> <script> <out dir>
 *
 * Script, one step per line: `init <voice>` (first), `voice <voice>`, `rate <wpm>`,
 * `say <text>`. Writes <out>/NNNN.pcm (16-bit signed mono) for the k-th `say`
 * and prints "rate=<Hz>" once. The engine keeps state between utterances, so the
 * order of the steps is part of the result.
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
    if (argc != 4) {
        fprintf(stderr, "usage: pcm_script <data> <script> <out>\n");
        return 2;
    }
    FILE *in = fopen(argv[2], "r");
    if (!in) return 6;
    espeak_ng_InitializePath(argv[1]);
    if (espeak_ng_Initialize(NULL) != ENS_OK ||
        espeak_ng_InitializeOutput(ENOUTPUT_MODE_SYNCHRONOUS, 0, NULL) != ENS_OK) return 3;
    espeak_SetSynthCallback(on_pcm);
    static char line[8192];
    int rc = 0, say = 0, inited = 0;
    while (!rc && fgets(line, sizeof line, in)) {
        line[strcspn(line, "\n")] = '\0';
        char *arg = strchr(line, ' ');
        if (arg) *arg++ = '\0';
        if (!strcmp(line, "init") || !strcmp(line, "voice")) {
            if (!arg || espeak_ng_SetVoiceByName(arg) != ENS_OK) rc = 4;
            inited = 1;
        } else if (!strcmp(line, "rate")) {
            if (!arg || espeak_ng_SetParameter(espeakRATE, atoi(arg), 0) != ENS_OK) rc = 5;
        } else if (!strcmp(line, "say")) {
            if (!inited || !arg) { rc = 9; break; }
            char path[4096];
            snprintf(path, sizeof path, "%s/%04d.pcm", argv[3], say++);
            if (!(g_out = fopen(path, "wb"))) { rc = 7; break; }
            if (espeak_ng_Synthesize(arg, strlen(arg) + 1, 0, POS_CHARACTER, 0, espeakCHARS_UTF8, NULL, NULL) != ENS_OK ||
                espeak_ng_Synchronize() != ENS_OK) rc = 8;
            fclose(g_out);
        } else if (line[0]) {
            rc = 10;
        }
    }
    fclose(in);
    printf("rate=%d\n", espeak_ng_GetSampleRate());
    return rc;
}
