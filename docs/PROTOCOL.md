# SPI protocol

Observed on GXFP51A7 (`GF3288_ST411SEC_APP_14003`) and consistent with the
GXFP5187 (`GF3288_ST411SEC_APP_11033`) and the published sibling analysis.

## Physical layer

| Property | Value |
|---|---|
| Mode | SPI mode 0 (CPOL 0, CPHA 0), 8-bit words |
| Chip select | normal (active-low), `SPI_CS_HIGH` **not** used |
| Clock | 10 MHz (1 MHz also works) |
| Duplex | reads are full-duplex; drive a dummy byte on MOSI |
| Max frame | ~22 kB for the image — set `spidev bufsiz=65536` |

The device is an ACPI SPI child (e.g. `\_SB.PCI0.SPI1.SPBA`, HID `GXFP51A7`).
It is driven from userspace through `spidev`.

## Transport framing

Every exchange is a 4-byte **transport header** followed by a **message body**.

```
transport header : [type] [len_lo] [len_hi] [sum(type,len_lo,len_hi) & 0xFF]
message body     : [cmd] [len_lo] [len_hi] [payload ...] [checksum]
```

- `type = 0xA0` — cleartext message.
- `type = 0xB0` — the body carries a TLS record.
- `len` is little-endian and counts the body bytes *including* the body
  checksum.
- A header checksum of `0x88` is a "no checksum" marker seen on some frames;
  treat mismatch as advisory, not fatal, on the read side.

### Chip select must be released between header and body

On the GXFP51A7 the header and body are **two separate SPI transfers** with CS
released in between, with a **~2 ms gap** (the Windows driver marks this
REQUIRED). A single combined transfer is silently ignored on this board. The
driver defaults to `GOODIXTLS_WRITE_GAP_US=2000`; without the gap the TLS
handshake fails intermittently.

Reads are the same shape: read the 4-byte header, then read `len` body bytes.

## Message body checksum

```
checksum = (0xAA - sum(all bytes before the checksum)) & 0xFF
```

Observed on the sibling Milan implementation: when the command byte is **odd**,
the checksum carries a `+1` correction. The GXFP51A7 commands used in normal
operation are even, so this does not apply to them; it matters for the `0xAF`
MCU-state variant.

## Command byte encoding

```
cmd      = (group << 4) | (subcmd << 1) | ack_bit
group    = cmd >> 4
subcmd   = (cmd >> 1) & 0x7
ack_bit  = cmd & 1        # 0 = wait for ACK, 1 = fire-and-forget
```

## Command table

Group / subcmd is decoded from the byte. This is the subset that matters for
bring-up and capture; the full map is larger.

| byte | group.sub | meaning | typical payload |
|---|---|---|---|
| `0x01` | 0.0 | init / nop | `00 00 00 00` |
| `0x20` | 2.0 | image, type 0 | `01 00` |
| `0x22` | 2.1 | image, type 1 (finger frame) | `01 00` |
| `0x32` | 3.1 | FDT **down** | `0c 01 <12×u16>` |
| `0x34` | 3.2 | FDT **up** | `0e 01 <12×u16>` |
| `0x36` | 3.3 | FDT **manual** | `0d 01 <12×u16>` |
| `0x50` | 5.0 | navigation frame | `01 00` |
| `0x60` | 6.0 | sleep | `01 00` |
| `0x70` | 7.0 | idle | `14 00` |
| `0x80` | 8.0 | sensor register write | `00 <addr LE16> <data>` |
| `0x82` | 8.1 | sensor register read | `00 <addr LE16> <len LE16>` |
| `0x90` | 9.0 | upload MCU config | 256-byte config |
| `0x94` | 9.2 | set powerdown FDT scan frequency | `64 00` (100) |
| `0xA2` | A.1 | soft reset | `01 00` |
| `0xA6` | A.3 | read OTP | `00 00` |
| `0xA8` | A.4 | firmware version | `00 00` |
| `0xAE` | A.7 | MCU state (reply) | `55` request |
| `0xB0` | B.0 | ACK message | `[acked_cmd] [status]` |
| `0xD0` | D.0 | request TLS / reconnect | — |
| `0xD4` | D.2 | TLS established | `00 00` |
| `0xD5` | D.2,a | TLS unlock | `00 00` |
| `0xE4` | E.2 | read preset data | — |
| `0xF0` | F.0 | firmware update (`UPFW`) | — |

> `0xF0` begins a flash operation, not a chip-id read. Do not probe an unknown
> sensor with it. Chip identity comes from register `0x0000`.

## ACK

A command that waits for an ACK gets a `type=0xA0`, `cmd=0xB0` message whose
payload is `[acked_command_byte] [status]`. Example for an `0xAE` query:

```
a0 06 00 a6                      transport header
b0 03 00 ae 01 48                ACK: command 0xAE, status 0x01
```

## Reads and replies

A reply is a message whose first byte is the command it answers. Long replies
(`0x50` nav ~4.7 kB, `0x20` image ~22 kB) arrive after the ACK and may take
tens of milliseconds; poll until the announced body is complete.

## Bringing up the transport

A robust bring-up order observed on both boards:

1. GPIO reset pulse (see `HARDWARE.md`).
2. Send a nop/init (`0x01`).
3. Read firmware version (`0xA8`).
4. Read OTP (`0xA6`).
5. Upload MCU config (`0x90`) — opens the command gate.
6. Enable + request TLS (`0xD0`).
7. TLS handshake, then plaintext `0xD4` (see `TLS.md`).

A GPIO reset does **not** flush the device's TX queue. After a bad run, stale
frames can survive a reset; only unbinding/rebinding `spidev` clears the kernel
side. See `tools/gx-recover.sh`.

Third-party reference: `szlukabence/goodix-fingerprint-spi-linux`
(`docs/PROTOCOL.md`) and `lexakimov/goodix51c0_spi-reversing`.
