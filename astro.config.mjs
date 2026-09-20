// @ts-check
import { defineConfig } from 'astro/config';
import mermaid from 'astro-mermaid';
import starlight from '@astrojs/starlight';

const REPO = 'https://github.com/delitdesnoyers06-del/goodix-gxfp-protocol';

export default defineConfig({
  site: 'https://delitdesnoyers06-del.github.io',
  base: '/goodix-gxfp-protocol',
  integrations: [
    // Must come before starlight (see astro-mermaid README).
    mermaid({ theme: 'neutral', autoTheme: true, enableLog: false }),
    starlight({
      title: 'Goodix GXFP SPI',
      description:
        'Interoperability notes and tools for the Goodix GXFP5187 and GXFP51A7 SPI fingerprint sensors.',
      logo: { src: './src/assets/logo.svg', alt: 'Goodix GXFP SPI' },
      favicon: '/favicon.svg',
      customCss: ['./src/styles/custom.css'],
      editLink: { baseUrl: `${REPO}/edit/main/` },
      social: [
        { icon: 'github', label: 'GitHub', href: REPO },
      ],
      sidebar: [
        {
          label: 'Protocol',
          items: [
            { label: 'SPI protocol', slug: 'protocol' },
            { label: 'TLS-PSK channel', slug: 'tls' },
            { label: 'Imaging', slug: 'imaging' },
            { label: 'Hardware', slug: 'hardware' },
            { label: 'Firmware', slug: 'firmware' },
          ],
        },
        {
          label: 'Reference',
          items: [
            { label: 'Tools', link: `${REPO}/tree/main/tools` },
            { label: 'Provenance', link: `${REPO}/blob/main/PROVENANCE.md` },
            { label: 'Driver — GXFP51A7 port', link: 'https://github.com/delitdesnoyers06-del/libfprint-goodixtls' },
            { label: 'Upstream driver (GXFP5187)', link: 'https://github.com/Sigfrodr/libfprint-goodixtls' },
          ],
        },
      ],
    }),
  ],
});
