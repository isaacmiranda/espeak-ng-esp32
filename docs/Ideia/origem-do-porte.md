# Origem do porte

Tudo em [`../../seed/alertalergo-port/`](../../seed/alertalergo-port/) foi copiado, sem alteração, do repositório
`alertalergo-v3-firmware` (privado), commit `19787f215c560247d58c7df59ae8357b00ba3483` (2026-11-19), mantendo os
caminhos relativos. O AlertAlergo é GPL-3.0-or-later (FSD CON-SW-06); a cópia é feita pelo mesmo responsável.

| Caminho no seed | O que é | Observação |
|---|---|---|
| `firmware/components/third_party/espeak-ng/` | eSpeak NG 1.52.0 vendorizado: `upstream/` intocado, `config/config.h`, `CMakeLists.txt`, `data/` compilado (pt, pt-BR), `pt_listx`, `ORIGIN.md` | `pt_listx`: 8 fármacos com tônica corrigida |
| `firmware/components/l1_speech/` | VFS somente leitura `/es` sobre a partição (`espeak_part.c`), síntese síncrona (`speech_synth.c`), parâmetros | o núcleo original do porte |
| `firmware/components/l1_audio/` | driver do codec ES8311 por I2S (`esp_codec_dev` ~1.4.0, Apache-2.0) | específico da placa |
| `firmware/components/third_party/waveshare_rlcd/` | BSP da tela da Waveshare (Apache-2.0) | só se a L2 usar a tela |
| `firmware/main/speech-glue-excerpt.c` | trecho do `main.c` (linhas 400–640): tarefa de áudio, tarefa de síntese, `speech_boot/say/cancel` | vira parte da L1 no `/build` |
| `firmware/partitions.csv`, `firmware/sdkconfig.defaults` | tabela de 16 MB do AlertAlergo (partição `espeak` 1 MiB, subtipo 0x40) e opções | a do produto; a pesquisa define a sua |
| `scripts/gen-espeak.sh` | baixa o tarball (SHA-256 fixado), copia as fontes, compila os dados, gera a referência de PCM | reprodutível: rodar de novo dá `git diff` vazio |
| `scripts/gen-espeak-image.py` | monta a imagem "AAES" da partição (cabeçalho, tamanho, CRC32) | |
| `scripts/idf.sh` | ESP-IDF fixado num ambiente limpo | |
| `tests/host/` | TC-SPK-04 (PCM idêntico ao upstream, 10 textos), TC-SPK-05 (fonemas dos fármacos), vetores e o trecho do `CMakeLists` | |
| `tests/target/test_speech.py` | TC-SPK-21..25 no aparelho (dados no boot, marcadores, fala ≤ 1,5 s após o tom, 50 falas seguidas, heap mínima) | usa a infraestrutura de testes do AlertAlergo |

## Evidência medida no AlertAlergo (não refeita aqui)

- `.text` do eSpeak 139 164 B; `.rodata` 109 746 B; `.bss` interna 89 783 B; dados 735 518 B (imagem 735 910 B).
- Heap interna mínima durante a fala com SoftAP + BLE + tela: 39 828 B (artefato do CI de `286a657`).
- TC-SPK-21..24 verdes em `b228a76`; TC-SPK-25 verde em `86b38a1`; TC-SPK-04/05 verdes no host.

Essa evidência é do firmware do AlertAlergo. Neste repositório ela vale como ponto de partida e hipótese; o requisito
só fecha com evidência gerada aqui (artefato do CI deste repositório gravado na placa).

## O que ficou de fora

Tudo que é do produto AlertAlergo: textos de alerta, tabela de fármacos, leitura de pulseiras, telas, configuração,
rede, API. O dicionário `pt_listx` veio porque é contribuição de pronúncia de fármacos, não dado de paciente.
