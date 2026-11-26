/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/*
 * Parâmetros da voz do eSpeak NG (FSD §18.2, FR-SPK-01/04) num lugar só: o aparelho
 * (l1_speech) e a ferramenta de host que gera os hashes de PCM (tests/host/speech_pcm.c)
 * aplicam os mesmos valores, para o PCM seguir idêntico entre os dois (FR-SPK-04).
 *
 * Os valores abaixo são os padrões do eSpeak. A escolha para o público com cegueira ou baixa
 * visão (OD-19) é do responsável, depois de ouvir o kit de escuta: mudar aqui, rodar
 * `scripts/gen-espeak.sh` (regenera os hashes de referência) e reaprovar TC-SPK-04.
 * Linhas extras da voz (ex.: `replace 1 y i`) vão em
 * firmware/components/third_party/espeak-ng/voice_pt_br_extra, que o gen-espeak.sh
 * acrescenta ao arquivo da voz pt-BR.
 */
#include "espeak-ng/speak_lib.h"

#define SPK_RATE_WPM 175               /* palavras por minuto (espeakRATE_NORMAL) */
#define SPK_PITCH 50                   /* 0–100 */
#define SPK_WORDGAP 0                  /* pausa extra entre palavras, em unidades de 10 ms */

static inline void spk_params_apply(void)
{
    espeak_SetParameter(espeakRATE, SPK_RATE_WPM, 0);
    espeak_SetParameter(espeakPITCH, SPK_PITCH, 0);
    espeak_SetParameter(espeakWORDGAP, SPK_WORDGAP, 0);
}
