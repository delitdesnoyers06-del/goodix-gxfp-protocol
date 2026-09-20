# TLS-PSK channel and command gate

The sensor is the **TLS client**; the host is the **TLS server**. The channel is
`TLS_PSK_WITH_AES_128_CBC_SHA256` (cipher suite `0x00A8`) with PSK identity
`Client_identity`. No Intel ME / SGX / IAP is involved: the PSK lives in the
sensor's own RAM and can be read back over the wire.

## Getting the PSK

The 48-byte PMK is read with the `0xF2` memory-read command. The address moves
between firmware revisions of the same generation:

| Firmware | Board | PSK address |
|---|---|---|
| `GF3288_ST411SEC_APP_11033` | GXFP5187 (MateBook X Pro) | `0x20007f0c` |
| `GF3288_ST411SEC_APP_14003` | GXFP51A7 (MateBook 13 2019) | `0x20007f14` |

Reading the wrong address does not fail loudly: it returns leading zero bytes
followed by the first part of the key, still reports full length, and the only
symptom is a handshake that dies with "cipher operation failed". On the
GXFP51A7 the key is a clean 48-byte block at `0x20007f14` with zeros on either
side (observed by reading a 128-byte window at `0x20007f00`).

The key itself is device-specific and is never published here.

## Handshake

The host acts as server and drives OpenSSL (or any TLS 1.2 PSK stack). The
record sequence on the wire:

```
client -> server   ClientHello
server -> client   ServerHello
server -> client   ServerKeyExchange        (PSK identity hint, "Client_identity")
server -> client   ServerHelloDone
client -> server   ClientKeyExchange
client -> server   ChangeCipherSpec
client -> server   Finished
server -> client   ChangeCipherSpec
server -> client   Finished
```

Each TLS record travels in its own `0xB0` transport frame. The
**ServerKeyExchange with the PSK identity hint is required on MilanL**
(GXFP51A7): removing it leaves the command gate closed. The ChicagoHS sibling
uses GCM and does without it.

## Opening the command gate: the plaintext `0xD4`

After the handshake the host must send a **plaintext** command `0xD4`
(`TLS_SUCCESSFULLY_ESTABLISHED`, payload `00 00`). Until it does, the firmware
gate drops every `cmd0 <= 5` command — FDT `0x36`, NAV `0x50`, image `0x20`.
The device acknowledges with:

```
b0 03 00 d4 01
```

## The `0xD4` settle race (this is the image blocker)

Issue the `0xD4` **too soon after the server `Finished`** and the device
acknowledges it but never advances its TLS state. Measured on GXFP51A7:

| Gap before `0xD4` | MCU state byte 0 | `0x20` answer |
|---|---|---|
| once `SSL_accept` returns (≈0 ms) | `4` | `d0 03 00 04 00` — reconnect request |
| ≥ 5 ms | `6` | `0xB0` frame with the image TLS record |

With the settle, the record decrypts to 22189 bytes (132×112, 12-bit). The
mechanism is consistent with a race between the server `Finished` being
processed and the `0xD4` being handled; 50 ms is used as a safe margin. The
knob is `GOODIXTLS_D4_DELAY_MS`.

This is why early "TLS reconnect on `0x20`" observations looked like a protocol
omission: `cmd0 == 0xD` is decoded as "TLS reconnect" by the vendor driver, but
the real cause was the `0xD4` timing.

## MCU state (`0xAE`)

Query with command `0xAE`, payload `55`. On `GF3288_ST411SEC_APP_14003` the
reply body is 10 bytes; byte 0 behaves as a state/version code:

| value | meaning (observed) |
|---|---|
| `4` | command gate open, image path not live |
| `6` | image path live (after a correctly-timed `0xD4`) |
| `12` / `0x0c` | gate closed (e.g. ServerKeyExchange omitted) |

The published sibling analysis of a related Milan part documents a wider state
block where byte 1 carries flags: bit 0 `isImageValid`, bit 1 `isTlsConnected`,
bit 2 `isTlsUsed`, bit 3 `isLocked`. On `APP_14003` the `isTlsConnected` bit
read `0` even on the working image path, so **do not gate on that flag alone** —
byte 0 (`6`) is the reliable readiness signal on this firmware.

## `0xD0` reconnect

The device sends a plaintext `d0 03 00 04 00` to ask for a fresh TLS session
(payload `04 00`). The vendor driver answers by restarting its whole init
thread. With the `0xD4` settle this no longer occurs during capture.

## Runtime knobs (driver)

| Variable | Default | Meaning |
|---|---|---|
| `GOODIXTLS_WRITE_GAP_US` | `2000` | CS gap between transport header and body; REQUIRED |
| `GOODIXTLS_D4_DELAY_MS` | `50` | settle after the handshake before `0xD4` |
| `GOODIXTLS_TLS_OK` | `1` | set `0` to skip the `0xD4` (diagnostic) |
| `GOODIXTLS_D0_REINIT` | `0` | full re-init on a `0xD0` request |
