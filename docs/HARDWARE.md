# Hardware: boards, GPIO, prerequisites

## Supported boards

| ACPI HID | Laptop | Sensor backend | Firmware | Geometry |
|---|---|---|---|---|
| `GXFP5187` | Huawei MateBook X Pro (`MACH-WX9`) | GXFP5187 | `GF3288_ST411SEC_APP_11033` | 132 × 112 |
| `GXFP51A7` | Huawei MateBook 13 2019 (`WRT-WX9`) | MilanL, chip `0x2205`, type 3 | `GF3288_ST411SEC_APP_14003` | 132 × 112 |

Both sit on an Intel LPSS `pxa2xx-spi` controller and are reached through
`spidev`, e.g.:

```
PCI 00:1e.3 -> pxa2xx-spi.3 -> spi_master/spi1 -> spi-GXFP51A7:00 -> /dev/spidev1.0
```

They are driven from userspace by
[libfprint-goodixtls](https://github.com/Sigfrodr/libfprint-goodixtls).

## GPIO

| Signal | GXFP5187 | GXFP51A7 | Notes |
|---|---|---|---|
| Reset | `gpiochip0` line **58**, **active-low** | `gpiochip0` line **264**, **active-high** | short pulse only |
| Interrupt | `gpiochip0` line 48 | `gpiochip0` line 48 | level, active-high |

Reset semantics:

- Use a **short pulse**, not a hold. Holding the line asserted was measured to
  *prevent* recovery where a pulse succeeds.
- On GXFP51A7 the line is active-high: drive HIGH to assert, LOW to run.
  The line and polarity were decoded from the ACPI `_CRS`/DSDT and confirmed on
  hardware (with the line LOW the sensor answers; HIGH leaves the interrupt
  asserted and the bus silent).
- On this board, line 58 is an unrelated pad — do not drive it.

The interrupt line is not required for a working capture (the reference
implementation polls), but the vendor driver is interrupt-driven.

## Runtime prerequisites

- Bind the ACPI SPI device to `spidev` (no ACPI modalias exists for these
  sensors, so it is forced):
  ```sh
  echo spidev > /sys/bus/spi/devices/spi-GXFP51A7:00/driver_override
  echo spi-GXFP51A7:00 > /sys/bus/spi/drivers/spidev/bind
  ```
- Raise the `spidev` buffer or the ~22 kB image frame is truncated:
  ```
  options spidev bufsiz=65536
  ```
- The driver matches on the spidev subsystem's ACPI id (`GXFP5187` /
  `GXFP51A7`).

## Recovery from a wedged device

A GPIO reset does **not** flush the device's TX queue; stale frames can survive
it. A `spidev` unbind/rebind is what gives a clean state. See
[`tools/gx-recover.sh`](../tools/gx-recover.sh).

## Firmware identity

The firmware version is read with command `0xA8`. It is a string such as
`GF3288_ST411SEC_APP_14003`. See [`FIRMWARE.md`](FIRMWARE.md).
