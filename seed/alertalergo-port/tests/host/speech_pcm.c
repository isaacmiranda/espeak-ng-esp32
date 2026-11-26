/*
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * PCM do eSpeak NG para uma lista de textos (FSD FR-SPK-04).
 *   speech_pcm <dir-de-dados> <textos.txt> <dir-de-saída>
 * Grava <saída>/NN.pcm (16 bit mono, na taxa do eSpeak) por linha, com a mesma
 * configuração do aparelho (l1_speech): síncrono, voz pt-BR pelo arquivo.
 * Compilado contra o eSpeak do upstream gera a referência
 * (scripts/gen-espeak.sh); contra as fontes vendorizadas, o teste.
 *
 * O eSpeak limita o caminho da voz a 60 bytes e o põe em minúsculas: os
 * dados são vistos por um link simbólico curto em /tmp, de nome minúsculo.
 */
#include <espeak-ng/espeak_ng.h>
#include <espeak-ng/speak_lib.h>
#include "speech_params.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static FILE *g_out;

static int on_pcm(short *wav, int n, espeak_EVENT *ev)
{
    (void)ev;
    if (wav && n > 0) fwrite(wav, sizeof *wav, (size_t)n, g_out);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 4) return 2;
    char link[32];   /* só minúsculas e dígitos: SetVoiceByFile põe o caminho em minúsculas */
    snprintf(link, sizeof link, "/tmp/aaes%ld", (long)getpid());
    if (mkdir(link, 0700) != 0) return 3;
    char es[64];
    snprintf(es, sizeof es, "%s/d", link);
    char *abs = realpath(argv[1], NULL);
    if (!abs || symlink(abs, es) != 0) return 3;
    free(abs);
    espeak_ng_InitializePath(es);
    int rc = 0;
    if (espeak_ng_Initialize(NULL) != ENS_OK ||
        espeak_ng_InitializeOutput(ENOUTPUT_MODE_SYNCHRONOUS, 0, NULL) != ENS_OK) rc = 4;
    char voice[96];
    snprintf(voice, sizeof voice, "%s/lang/pt-br", es);
    if (!rc && espeak_ng_SetVoiceByFile(voice) != ENS_OK) rc = 5;
    espeak_SetSynthCallback(on_pcm);
    spk_params_apply();                  /* os mesmos parâmetros do aparelho */
    FILE *in = rc ? NULL : fopen(argv[2], "r");
    char line[512];
    for (int i = 0; in && fgets(line, sizeof line, in); i++) {
        line[strcspn(line, "\n")] = '\0';
        char path[512];
        snprintf(path, sizeof path, "%s/%02d.pcm", argv[3], i);
        if (!(g_out = fopen(path, "wb"))) { rc = 6; break; }
        if (espeak_ng_Synthesize(line, strlen(line) + 1, 0, POS_CHARACTER, 0, espeakCHARS_UTF8, NULL, NULL) != ENS_OK ||
            espeak_ng_Synchronize() != ENS_OK) rc = 7;
        fclose(g_out);
        if (rc) break;
    }
    if (in) fclose(in);
    printf("rate=%d\n", espeak_ng_GetSampleRate());
    unlink(es);
    rmdir(link);
    return rc;
}
