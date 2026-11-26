# waveshare_rlcd — driver do ST7305 (BSP Waveshare)

| Item | Valor |
|---|---|
| Origem | https://github.com/waveshareteam/ESP32-S3-RLCD-4.2 |
| Commit | d8bf7813d3b53251577ff03c03596ad6ad3acae0 (2026-10-20) |
| Caminho | `examples/factory/components/port_bsp/display_bsp.{h,cpp}` |
| Licença | Apache-2.0 (`LICENSE`, cópia do repositório de origem) — FSD §29.1 |
| Alterações | nenhuma nos dois arquivos; `CMakeLists.txt` é deste projeto |

Só o driver do display entra (FR-DSP-01). O restante do `port_bsp` (áudio,
botões, ADC, SD) não é usado; o porte para o LVGL 9 em I1 é `l1_display`.
