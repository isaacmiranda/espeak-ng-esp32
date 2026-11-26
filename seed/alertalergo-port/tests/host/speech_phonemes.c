/*
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * TC-SPK-05 (FR-SPK-07): pronúncia dos fármacos da lista de referência.
 *   speech_phonemes <dir-de-dados>            confere a tabela abaixo (0 = ok)
 *   speech_phonemes <dir-de-dados> --print    imprime «palavra<TAB>fonemas» da tabela
 * Cada linha é o campo como o aparelho o fala (sem acento, FR-SLOT-01) e os
 * fonemas do eSpeak (mnemônicos) com a sílaba tônica e os hiatos corretos do
 * português. Os 9 verbetes de pt_listx são os que o eSpeak errava sem ele.
 */
#include <espeak-ng/espeak_ng.h>
#include <espeak-ng/speak_lib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static const struct {
    const char *word, *ph;
} T[] = {
#include "vectors/speech/drug_phonemes.inc"
};

int main(int argc, char **argv)
{
    if (argc < 2) return 2;
    int print = argc > 2 && strcmp(argv[2], "--print") == 0;
    char link[32], es[64], voice[96];
    snprintf(link, sizeof link, "/tmp/aaes%ld", (long)getpid());   /* ver speech_pcm.c */
    if (mkdir(link, 0700) != 0) return 3;
    snprintf(es, sizeof es, "%s/d", link);
    char *abs = realpath(argv[1], NULL);
    if (!abs || symlink(abs, es) != 0) return 3;
    free(abs);
    espeak_ng_InitializePath(es);
    int rc = 0;
    if (espeak_ng_Initialize(NULL) != ENS_OK) rc = 4;
    snprintf(voice, sizeof voice, "%s/lang/pt-br", es);
    if (!rc && espeak_ng_SetVoiceByFile(voice) != ENS_OK) rc = 5;
    for (size_t i = 0; !rc && i < sizeof T / sizeof *T; i++) {
        const void *p = T[i].word;
        const char *got = espeak_TextToPhonemes(&p, espeakCHARS_UTF8, 0);
        if (print) printf("%s\t%s\n", T[i].word, got ? got : "(null)");
        else if (!got || strcmp(got, T[i].ph) != 0) {
            printf("FAIL %s: esperado «%s», saiu «%s»\n", T[i].word, T[i].ph, got ? got : "(null)");
            rc = 1;
        }
    }
    unlink(es);
    rmdir(link);
    return rc;
}
