# Provenance, ownership and what is intentionally excluded

## Method

This work is interoperability analysis of fingerprint hardware the author owns,
against a vendor driver the author is licensed to run. It combines:

1. **Live observation** on a Huawei MateBook 13 2019 (`WRT-WX9`) with a Goodix
   `GXFP51A7` sensor, firmware `GF3288_ST411SEC_APP_14003`, over `spidev`.
2. **Public static analysis** of vendor driver behaviour, referenced but not
   reproduced.
3. **Sibling-device observations** already published by other projects
   (`szlukabence/goodix-fingerprint-spi-linux`,
   `lexakimov/goodix51c0_spi-reversing`, `goodix-fp-linux-dev`). Facts taken
   from there are marked in the docs.

## What this repository does NOT contain, by design

| Excluded | Why |
|---|---|
| Decompiled vendor driver source (`gfspi.dll` output) | It is copyrighted vendor code. Redistributing it is the highest-risk item and adds nothing a protocol description needs. |
| The vendor driver binary (`gfspi.dll`, `Engine_*.dll`, enclave blobs) | Proprietary binaries; obtain from your own licensed package. |
| MCU firmware images (`GF_*SEC_APP_*.bin`) | Copyrighted vendor firmware. `src/content/docs/firmware.md` and `tools/extract_firmware.py` let you extract and hash them from your own copy. |
| Sensor configuration blobs | Vendor-supplied data tables. |
| PSK / PMK / key material | Secret key material. Only the *RAM address* where a device keeps its own key is documented, never a key. |
| Frame captures, decrypted images, biometric templates | Captured data and biometric data. Not redistributed. |
| Vendor transcripts reproduced verbatim | Referenced by link instead. |

## Attribution

- The driver these notes support: **libfprint-goodixtls** by Benjamin Allègre
  (https://github.com/Sigfrodr), LGPL-2.1-or-later.
- Sibling protocol work: `szlukabence/goodix-fingerprint-spi-linux`,
  `lexakimov/goodix51c0_spi-reversing`, `goodix-fp-linux-dev/goodix-ghidra`,
  `goodix-fp-linux-dev/goodix-fp-dump`. Their published facts are credited in
  the relevant sections.
- Firmware-extraction approach: `szlukabence/goodix-fingerprint-spi-linux`.

## Reporting

If you are a rights holder and want something here changed or removed, open an
issue and it will be addressed promptly. The exclusion list above is deliberate:
this repository aims to publish *facts about a protocol*, not anyone's code.
