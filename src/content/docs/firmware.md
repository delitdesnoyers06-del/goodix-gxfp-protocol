---
title: "Firmware"
description: Firmware revisions that change protocol behaviour, and how to extract images from your own driver package.
---

## The sensor already runs its firmware

There is no bootloader waiting for a blob during normal operation. The host
reads the version (`0xA8`), compares, and skips an update when it matches. A
sensor that is silent is not "missing firmware".

## Images embedded in the vendor driver (not shipped here)

The vendor driver package bundles two application images in its `.rdata`, as
records of the form `[u8 name_len][name ASCII][raw image]`. They can be
extracted **from your own licensed copy** with
[`tools/extract_firmware.py`](https://github.com/delitdesnoyers06-del/goodix-gxfp-protocol/blob/main/tools/extract_firmware.py). This repository
ships the extractor and the hashes, never the blobs.

Known images (from the driver package, v1.1.141.40):

| Name | Size | MCU | SHA256 |
|---|---|---|---|
| `GF_ST411SEC_APP_14115` | 85994 | STM32 (flash `0x08000000`) | `6e6cc79bedfbd51cf02f92a00cf3d42a0f1083c134e919b60b265f93f8f37aa4` |
| `GF_HC460SEC_APP_14104` | 84150 | HDSC HC32 (flash `0x00000000`) | `7c752777ea13741d8e7c8ceb45f814f485bbe8de5fc7134685ad2d9b2a650699` |

Names appearing only as strings, with no embedded image:
`MILAN_HC460SEC_IAP_14102`, `GF_HC460SEC_APP_14102`.

## Revision differences that matter

The firmware revision changes protocol details on the same generation:

| Revision | Board | PSK RAM address | Notes |
|---|---|---|---|
| `GF3288_ST411SEC_APP_11033` | GXFP5187 | `0x20007f0c` | |
| `GF3288_ST411SEC_APP_14003` | GXFP51A7 (this unit) | `0x20007f14` | MilanL; split writes; `0xD4` settle |
| `GF_ST411SEC_APP_14115` | (embedded image) | — | newer than the unit observed; not verified here |

The unit used for this work reports `APP_14003`, **not** the `14115` image
embedded in the driver package — they are different revisions.

## The update path (if you ever need it)

Firmware update uses command group `0xF` (`0xF0`, "UPFW"). Two MCU vendors need
different IAP variants (ST vs HDSC). Treat this as a flash operation: probing an
unknown sensor with `0xF0` asks it to begin writing. It is not a chip-id read.
