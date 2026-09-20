# Goodix GXFP SPI fingerprint protocol — interoperability notes

Protocol notes and tools for the Goodix **GXFP5187** and **GXFP51A7** SPI
fingerprint sensors (Huawei MateBook X Pro `MACH-WX9` and MateBook 13 2019
`WRT-WX9`). These are the sensors driven by
[libfprint-goodixtls](https://github.com/Sigfrodr/libfprint-goodixtls).

This repository is a **write-up and a set of tools**, not a code dump. It exists
to make the protocol legible and repeatable for interoperability work on
hardware you own. It deliberately does **not** ship any vendor code, firmware,
key material, or captured biometric data — see [`PROVENANCE.md`](PROVENANCE.md)
for the exact line and why.

## What is here

- [`docs/PROTOCOL.md`](docs/PROTOCOL.md) — SPI framing, checksums, command
  encoding and the command table.
- [`docs/TLS.md`](docs/TLS.md) — the TLS-PSK channel (sensor = client), the
  post-handshake `0xD4`, and the settle race that gates image delivery.
- [`docs/IMAGING.md`](docs/IMAGING.md) — geometry, 12-bit decode, FDT scan
  arming and the DAC/register flow.
- [`docs/HARDWARE.md`](docs/HARDWARE.md) — boards, reset GPIO, PSK addresses,
  runtime prerequisites.
- [`docs/FIRMWARE.md`](docs/FIRMWARE.md) — firmware revisions and how the
  embedded images are *extracted from your own driver package*, not shipped.
- [`tools/`](tools/) — a minimal raw SPI transport, an MCU-state parser, a
  firmware extractor and a recovery script.

## Scope and status

Everything here was observed on real hardware (WRT-WX9, GXFP51A7, firmware
`GF3288_ST411SEC_APP_14003`) plus the published static analysis of the Windows
driver. Where a fact comes from a sibling device or a different firmware
revision, it is marked as such. Confidence is stated per claim; nothing here
should be taken as vendor-endorsed.

## License

- Documentation (`README.md`, `docs/`, `PROVENANCE.md`): CC BY-SA 4.0 — see
  [`LICENSE-docs`](LICENSE-docs).
- Tools (`tools/`): MIT — see [`LICENSE-tools`](LICENSE-tools).

Protocol facts are not copyrightable; the license applies to this presentation
of them. See [`PROVENANCE.md`](PROVENANCE.md) for attribution.
