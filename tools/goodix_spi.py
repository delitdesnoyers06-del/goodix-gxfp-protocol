#!/usr/bin/env python3
"""Minimal, dependency-free SPI transport and framing for Goodix GXFP sensors.

Uses only the Linux UAPI (`fcntl`/`ioctl`); no `spidev` Python module is needed.
The transport rules encoded here are described in ../docs/PROTOCOL.md:

  * transport header `[type][len LE16][sum(first 3)]`
  * header and body are two separate transfers with CS released between them
  * a ~2 ms gap is required between the two on GXFP51A7
  * message body checksum is `(0xAA - sum) & 0xFF`

Run as root (or with ACL access to /dev/spidevX.Y and /dev/gpiochipN).

    sudo python3 goodix_spi.py --dev /dev/spidev1.0 probe
"""
import argparse
import ctypes
import fcntl
import os
import struct
import subprocess
import sys
import time

SPI_IOC_MAGIC = ord("k")
_IOC_READ, _IOC_WRITE = 2, 1


def _ioc(direction, type_, nr, size):
    return (direction << 30) | (size << 16) | (type_ << 8) | nr


SPI_IOC_WR_MODE = _ioc(_IOC_WRITE, SPI_IOC_MAGIC, 1, 1)
SPI_IOC_WR_BITS_PER_WORD = _ioc(_IOC_WRITE, SPI_IOC_MAGIC, 3, 1)
SPI_IOC_WR_MAX_SPEED_HZ = _ioc(_IOC_WRITE, SPI_IOC_MAGIC, 4, 4)
SPI_IOC_MESSAGE = lambda n: _ioc(_IOC_WRITE, SPI_IOC_MAGIC, 0, 32 * n)

# struct spi_ioc_transfer (32 bytes on 64-bit)
_XFER = "<QQIIHBBBBBB"
assert struct.calcsize(_XFER) == 32

PKT_PLAIN = 0xA0
PKT_TLS = 0xB0

CMD_MCU_STATE = 0xAE
CMD_FW_VERSION = 0xA8


class Spi:
    """One /dev/spidevX.Y, SPI mode 0, 8 bits (mode and clock configurable)."""

    def __init__(self, path, mode=0, speed=10_000_000, bits=8):
        self.fd = os.open(path, os.O_RDWR)
        fcntl.ioctl(self.fd, SPI_IOC_WR_MODE, struct.pack("B", mode))
        fcntl.ioctl(self.fd, SPI_IOC_WR_BITS_PER_WORD, struct.pack("B", bits))
        fcntl.ioctl(self.fd, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack("<I", speed))
        self.speed = speed
        self.bits = bits

    def close(self):
        os.close(self.fd)

    def duplex(self, tx):
        """One full-duplex transfer; returns len(tx) bytes."""
        n = len(tx)
        txb = ctypes.create_string_buffer(tx, n)
        rxb = ctypes.create_string_buffer(n)
        packed = struct.pack(
            _XFER,
            ctypes.addressof(txb), ctypes.addressof(rxb),
            n, self.speed, 0, self.bits, 0, 0, 0, 0, 0,
        )
        fcntl.ioctl(self.fd, SPI_IOC_MESSAGE(1), packed)
        return bytes(rxb.raw[:n])


def transport_header(ptype, body_len):
    h = bytes([ptype, body_len & 0xFF, (body_len >> 8) & 0xFF])
    return h + bytes([sum(h) & 0xFF])


def body_checksum(data):
    return (0xAA - sum(data)) & 0xFF


def make_body(cmd, payload=b"", ack=True):
    """Build a message body. `cmd` is the full command byte."""
    ln = len(payload) + 1
    b = bytes([cmd, ln & 0xFF, (ln >> 8) & 0xFF]) + payload
    return b + bytes([body_checksum(b)])


class Link:
    """Framed dialogue over a Spi, with the required split write."""

    def __init__(self, spi, write_gap_s=0.002):
        self.spi = spi
        self.gap = write_gap_s

    def write(self, body, ptype=PKT_PLAIN):
        self.spi.duplex(transport_header(ptype, len(body)))
        time.sleep(self.gap)
        self.spi.duplex(body)

    def read(self, max_len=65536):
        hdr = self.spi.duplex(b"\x00" * 4)
        if hdr[0] not in (PKT_PLAIN, PKT_TLS):
            return None
        n = hdr[1] | (hdr[2] << 8)
        if not 0 < n <= max_len:
            return None
        return hdr[0], self.spi.duplex(b"\x00" * n)

    def command(self, cmd, payload=b"", reply_cmd=None, timeout=0.5):
        """Send a command and collect frames until `reply_cmd` (or deadline)."""
        self.write(make_body(cmd, payload))
        deadline = time.time() + timeout
        while time.time() < deadline:
            frame = self.read()
            if frame is None:
                continue
            _, body = frame
            if body and body[0] == reply_cmd:
                return body
        return None


def query_mcu_state(link):
    body = link.command(CMD_MCU_STATE, b"\x55", reply_cmd=CMD_MCU_STATE, timeout=0.6)
    if not body:
        return None
    return body[3:-1]      # strip cmd/len and checksum


def parse_mcu_state(payload):
    if not payload:
        return {}
    st = {"state": payload[0], "raw": payload.hex(" ")}
    if len(payload) > 1:
        f = payload[1]
        st.update(
            is_image_valid=f & 1,
            is_tls_connected=(f >> 1) & 1,
            is_tls_used=(f >> 2) & 1,
            is_locked=(f >> 3) & 1,
        )
    return st


def read_firmware_version(link):
    body = link.command(CMD_FW_VERSION, b"\x00\x00", reply_cmd=CMD_FW_VERSION)
    if not body:
        return None
    return body[3:-1].split(b"\x00", 1)[0].decode("latin1", "replace")


def gpio_reset(line, active_high):
    """Short reset pulse via libgpiod's gpioset, matching docs/HARDWARE.md."""
    assert_cmd = [f"{line}={1 if active_high else 0}"]
    release_cmd = [f"{line}={0 if active_high else 1}"]
    subprocess.run(["gpioset", "gpiochip0"] + assert_cmd, check=False)
    time.sleep(0.01)
    subprocess.run(["gpioset", "gpiochip0"] + release_cmd, check=False)
    time.sleep(0.12)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dev", default="/dev/spidev1.0")
    ap.add_argument("--speed", type=int, default=10_000_000)
    ap.add_argument("--reset", action="store_true",
                    help="pulse the reset line first (GXFP51A7: 264 active-high)")
    ap.add_argument("--reset-line", type=int, default=264)
    ap.add_argument("--reset-active-high", type=int, default=1)
    ap.add_argument("action", choices=["probe", "reset"], nargs="?", default="probe")
    args = ap.parse_args()

    if args.action == "reset":
        gpio_reset(args.reset_line, bool(args.reset_active_high))
        print(f"pulsed gpiochip0 line {args.reset_line}")
        return 0

    if args.reset:
        gpio_reset(args.reset_line, bool(args.reset_active_high))

    spi = Spi(args.dev, speed=args.speed)
    link = Link(spi)
    try:
        fw = read_firmware_version(link)
        print("firmware:", fw if fw else "(no reply)")
        state = query_mcu_state(link)
        if state is None:
            print("mcu state: (no reply)")
            return 1
        for k, v in parse_mcu_state(state).items():
            print(f"  {k:18}: {v}")
    finally:
        spi.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
