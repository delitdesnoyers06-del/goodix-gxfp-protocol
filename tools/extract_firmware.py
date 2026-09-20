#!/usr/bin/env python3
"""Extract the MCU firmware images embedded in a Goodix Windows driver package.

Both MCU application images ship inside `gfspi.dll` (in `.rdata`) as records of
the form:

    [u8 name_len][name ASCII][raw image]

The records carry no length field, so the length is taken from a small known
table and proven by the SHA-256 check. Nothing here redistributes the images:
you extract them from a driver package you are licensed to use.

Usage:
    python3 extract_firmware.py /path/to/gfspi.dll -o ./firmware

On Windows the DLL lives under
    C:\\Windows\\System32\\DriverStore\\FileRepository\\gfspi.inf_amd64_*\\
"""
import argparse
import hashlib
import os
import sys

# Verified against gfspi.dll v1.1.141.40
#   sha256(gfspi.dll) = 36033fbf507620776d9fb686ecfe7847ff41fcbdee6e2afad119e28c6f81ca04
KNOWN = {
    "GF_ST411SEC_APP_14115": {
        "size": 85994,
        "sha256": "6e6cc79bedfbd51cf02f92a00cf3d42a0f1083c134e919b60b265f93f8f37aa4",
        "mcu": "STM32 (ST411), flash @0x08000000, image base 0x08020000",
    },
    "GF_HC460SEC_APP_14104": {
        "size": 84150,
        "sha256": "7c752777ea13741d8e7c8ceb45f814f485bbe8de5fc7134685ad2d9b2a650699",
        "mcu": "HDSC HC32 (HC460), flash @0x00000000",
    },
}


def find_images(blob, name):
    """Offsets of the image bytes for every `[len][name][image]` record."""
    marker = bytes([len(name)]) + name.encode("ascii")
    offsets, at = [], 0
    while True:
        at = blob.find(marker, at)
        if at < 0:
            return offsets
        offsets.append(at + len(marker))
        at += 1


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("dll", help="path to gfspi.dll")
    ap.add_argument("-o", "--outdir", default=".", help="output directory")
    args = ap.parse_args()

    with open(args.dll, "rb") as fh:
        blob = fh.read()
    print(f"{args.dll} ({len(blob)} bytes)")
    print(f"sha256 {hashlib.sha256(blob).hexdigest()}\n")

    os.makedirs(args.outdir, exist_ok=True)
    found = 0
    for name, meta in KNOWN.items():
        offsets = find_images(blob, name)
        if not offsets:
            print(f"  {name:24} NOT FOUND")
            continue

        image = blob[offsets[0]:offsets[0] + meta["size"]]
        digest = hashlib.sha256(image).hexdigest()
        status = "OK" if digest == meta["sha256"] else "MISMATCH"
        out = os.path.join(args.outdir, name + ".bin")
        with open(out, "wb") as fh:
            fh.write(image)
        found += 1

        sp = int.from_bytes(image[0:4], "little")
        reset = int.from_bytes(image[4:8], "little")
        print(f"  {name}")
        print(f"     copies embedded : {len(offsets)}")
        print(f"     offset in file  : 0x{offsets[0]:x} (first copy)")
        print(f"     size            : {meta['size']} bytes")
        print(f"     sha256          : {digest}  {status}")
        print(f"     vectors         : SP 0x{sp:08x}, reset 0x{reset:08x}")
        print(f"     MCU             : {meta['mcu']}")
        print(f"     written to      : {out}\n")

    if not found:
        sys.exit("no known firmware records found -- is this the right DLL?")
    print(f"extracted {found} image(s)")


if __name__ == "__main__":
    main()
