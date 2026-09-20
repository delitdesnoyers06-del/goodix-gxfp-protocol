---
title: "Imaging: geometry, decode, FDT and DAC"
description: Sensor geometry, the 12-bit pixel decode, FDT scan arming and the DAC/register flow.
---

## Geometry

Selected from the sensor type reported by the device, not hard-coded:

| chip id | sensor type | backend | columns × rows | FDT data |
|---|---|---|---|---|
| `0x2205` | 3 | MilanL | **132 × 112** | 24 bytes (12 × u16) |
| `0x2503`–`0x2504` | 12 | ChicagoHS | 80 × 64 | 12 bytes (6 × u16) |

The captured record length confirms the geometry independently: a 132 × 112
frame at 12 bits is `132 · 112 · 12 / 8 = 22176` bytes of pixels.

## Image record

The image is exactly **one TLS application-data record inside one `0xB0`
transport frame** — no reassembly. Because it is larger than a conforming TLS
record (about 22 kB against 16384), it is decrypted by hand rather than by a
TLS library.

Observed on GXFP51A7:

```
TCP/TLS record  22245 bytes = 5 (record header) + 16 (explicit IV) + 22224 (ciphertext)
plaintext       22189 bytes
pixel header    8 bytes      (tag, u16 length, five zero bytes)
pixels          22176 bytes  (132 · 112 · 12 / 8)
```

Decrypt is AES-128-CBC with the client write key and explicit IV, then verify
the TLS 1.2 MAC over `seq || type || version || length || content` before
accepting the record. Sequence numbers advance once per record.

## 12-bit pixel decode

Six bytes carry four pixels:

```
p0 = ((b0 & 0x0F) << 8) | b1
p1 =  (b3        << 4) | (b0 >> 4)
p2 = ((b5 & 0x0F) << 8) | b2
p3 =  (b4        << 4) | (b5 >> 4)
step = 6 bytes -> 4 pixels
```

## FDT: scan arming and touch detection

The device has a fast, twelve-zone finger-detection ("FDT") mode separate from
a full capture. Values are 16-bit and a finger pulls them **down**.

Three FDT mode commands, payload `[header][base_type]` followed by twelve
16-bit base values:

```
0x32  header 0x0c   FDT down
0x34  header 0x0e   FDT up
0x36  header 0x0d   FDT manual   (measure; reply carries the measured values)
```

The `0x36` reply payload is:

```
[irq_status u16][touchflag u16][12 × u16 measured][8 trailing bytes]
```

### Deriving the scan base from a measurement

The base sent back with `down`/`manual` is derived from the measured values.
The formula is backend-specific:

```
MilanL (0x2205):     v[i] = ((m[i] >> 1) << 8) | (m[i] >> 1)        # both bytes equal
MilanL up:           d = (m[i] >> 1) + delta;  v[i] = (d << 8) | d
ChicagoHS (0x2504):  v[i] = ((m[i] >> 1) << 8) | 0x80
```

`delta` is a per-unit offset read from sensor register `0x0082`; `0x15` is the
fallback used when that register has not been read. Using the ChicagoHS `|0x80`
form on MilanL sends the wrong scan base.

## Register flow

| command | purpose |
|---|---|
| `0x82 00 82 00 02 00` | read register `0x0082` → high byte is `fdt_delta` |
| `0x80 00 20 02 <lo> <hi>` | write register `0x0220` (DAC) |
| `0x82 00 20 02 00 02` | read register `0x0220` (DAC) |
| `0x82 00 5c 00 02 00` | read register `0x005c` (Tcode) |

**MilanL DAC** is read from `0x0220`/`0x005c` and written to `0x0220` only.
The ChicagoHS hardcoded writes to `0x0220/0x0236/0x0238/0x023a` are **wrong for
MilanL** and must not be used.

## Capture sequence (background and finger)

A working sequence on GXFP51A7:

```
0xAE            query MCU state
0x36 manual     first pass: measure the base
0x50 nav        navigation frame
0x36 manual     second pass with the derived base
[0x32 down]     arm the scan (finger frame only)
0x20            get image -> ACK, then the 0xB0 image record
[0x34 up]       release after a finger capture
```

The background frame is captured **unarmed**; the finger frame arms `down`
first. The exact baseline values matter for image quality but not for whether
the record is delivered.
