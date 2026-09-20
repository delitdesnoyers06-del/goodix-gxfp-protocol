# Tools

Small, self-contained helpers. They talk to the hardware; run the SPI/GPIO ones
as root (or grant access via ACLs).

| Tool | Purpose |
|---|---|
| `goodix_spi.py` | Dependency-free raw SPI transport + framing, `probe` (firmware version, MCU state) and `reset`. |
| `extract_firmware.py` | Extract the MCU images embedded in your own `gfspi.dll`; verifies SHA-256. |
| `gx-recover.sh` | Unbind/rebind `spidev` and pulse the reset line to clear a wedged sensor. |

## Examples

```sh
# is the sensor alive, and what firmware/MCU state does it report?
sudo python3 goodix_spi.py --dev /dev/spidev1.0 probe

# reset it first (GXFP51A7 defaults: line 264, active-high)
sudo python3 goodix_spi.py --reset --reset-line 264 --reset-active-high 1 probe

# recover a wedged sensor
sudo ./gx-recover.sh

# pull the firmware images out of your own driver package
python3 extract_firmware.py /path/to/gfspi.dll -o ./firmware
```

`goodix_spi.py` sends the transport header and body as two SPI transfers with a
2 ms gap (`--` hard-coded to match `GOODIXTLS_WRITE_GAP_US=2000`); see
[`../src/content/docs/protocol.md`](../src/content/docs/protocol.md) for why.

None of these tools contain or write key material. The sensor's own PSK is read
through command `0xF2` by the driver; it is never handled here.
