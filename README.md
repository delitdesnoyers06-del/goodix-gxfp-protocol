# Goodix GXFP SPI fingerprint protocol

Protocol notes and tools for the Goodix **GXFP5187** and **GXFP51A7** SPI
fingerprint sensors (Huawei MateBook X Pro `MACH-WX9` and MateBook 13 2019
`WRT-WX9`). These are the sensors driven by
[libfprint-goodixtls](https://github.com/Sigfrodr/libfprint-goodixtls).

**Read it as a site:** <https://delitdesnoyers06-del.github.io/goodix-gxfp-protocol/>

This repository is a write-up and a set of tools, not a code dump. It
deliberately does **not** ship vendor code, firmware images, configuration
blobs, key material or captured biometrics — see [`PROVENANCE.md`](PROVENANCE.md)
for the exact line and why.

## Layout

| Path | Contents |
|---|---|
| `src/content/docs/protocol.md` | SPI transport framing, checksums, command table |
| `src/content/docs/tls.md` | TLS-PSK channel, the post-handshake `0xD4` and the settle race |
| `src/content/docs/imaging.md` | geometry, 12-bit decode, FDT scan arming, DAC/register flow |
| `src/content/docs/hardware.md` | boards, reset GPIO lines/polarity, `spidev` prerequisites |
| `src/content/docs/firmware.md` | firmware revisions and extraction |
| `tools/` | raw SPI transport, MCU-state probe, firmware extractor, recovery |
| `astro.config.mjs` | Astro Starlight site configuration |
| `.github/workflows/deploy.yml` | builds and publishes the site to GitHub Pages |

## Build the site locally

```sh
npm install
npm run dev      # http://localhost:4321/goodix-gxfp-protocol/
npm run build    # static output in dist/
npm run preview  # serve the built site
```

The site is [Astro](https://astro.build/) +
[Starlight](https://starlight.astro.build/), with
[Pagefind](https://pagefind.app/) search and
[Mermaid](https://mermaid.js.org/) diagrams. It is published automatically on
every push to `main`.

## License

- Documentation (`README.md`, `PROVENANCE.md`, `src/content/docs/`):
  CC BY-SA 4.0 — see [`LICENSE-docs`](LICENSE-docs).
- Tools (`tools/`): MIT — see [`LICENSE-tools`](LICENSE-tools).
