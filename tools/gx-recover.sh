#!/bin/bash
# Recover a wedged Goodix GXFP51A7 / GXFP5187 sensor on Linux.
#
# A GPIO reset pulse does not flush the device's TX queue, so stale frames can
# survive it. What actually clears a desynchronised state is unbinding and
# rebinding the spidev kernel driver. Run as root.
#
#   sudo ./gx-recover.sh
set -e

CHIP=gpiochip0
DEV=
for d in spi-GXFP51A7:00 spi-GXFP5187:00; do
  [ -d "/sys/bus/spi/devices/$d" ] && { DEV=$d; break; }
done
DEV=${DEV:-spi-GXFP5187:00}

# Reset line and polarity are board-specific (see ../docs/HARDWARE.md):
#   GXFP5187  gpiochip0 line 58  active-low   (assert 0, release 1)
#   GXFP51A7  gpiochip0 line 264 active-high  (assert 1, release 0)
if [ "$DEV" = "spi-GXFP51A7:00" ]; then
  RST_LINE=264; RST_ASSERT=1; RST_RELEASE=0
else
  RST_LINE=58;  RST_ASSERT=0; RST_RELEASE=1
fi

echo "stopping fprintd"
systemctl stop fprintd 2>/dev/null || true
sleep 1

echo "unbinding spidev ($DEV)"
echo "$DEV" > /sys/bus/spi/drivers/spidev/unbind 2>/dev/null || true
sleep 1

echo "reset pulse on $CHIP line $RST_LINE (short, not held)"
gpioset "$CHIP" "$RST_LINE=$RST_ASSERT" || true
sleep 0.1
gpioset "$CHIP" "$RST_LINE=$RST_RELEASE" || true
sleep 1

echo "rebinding spidev"
modprobe spidev
echo spidev > "/sys/bus/spi/devices/$DEV/driver_override"
echo "$DEV" > /sys/bus/spi/drivers/spidev/bind 2>/dev/null || true
sleep 1

echo "restarting fprintd"
systemctl start fprintd 2>/dev/null || true
echo "done"
