# PN532 NFC HAT Wiring Guide

Complete guide for connecting and configuring the PN532 NFC HAT on Raspberry Pi 5.

## Hardware Requirements

- Raspberry Pi 5 (or 4/3/Zero)
- PN532 NFC HAT/Module
- NFC tags (NTAG213, NTAG215, or NTAG216 recommended)

## PN532 HAT Configuration

### Switch Settings (IMPORTANT!)

The PN532 module has two switches/jumpers that MUST be set correctly for I2C mode:

```
┌─────────────────────────────┐
│     PN532 NFC Module        │
│                             │
│  [Switch 1]  [Switch 2]     │
│   ┌─┐ ┌─┐    ┌─┐ ┌─┐       │
│   │0│ │1│    │0│ │1│       │
│   └─┘ └─┘    └─┘ └─┘       │
│                             │
│   For I2C Mode:             │
│   Switch 1: ON (1)          │
│   Switch 2: OFF (0)         │
└─────────────────────────────┘
```

**I2C Mode Settings:**
- Switch 1 (SEL0): **ON** (position 1)
- Switch 2 (SEL1): **OFF** (position 0)

**Alternative Modes (not used):**
- UART: Switch 1 OFF, Switch 2 OFF
- SPI: Switch 1 OFF, Switch 2 ON

## Raspberry Pi GPIO Pinout

The PN532 HAT connects directly to the Raspberry Pi GPIO header:

```
Raspberry Pi GPIO Header (Top View)
┌─────────────────────────────────────┐
│  3.3V  [ 1] [ 2]  5V                │
│   SDA  [ 3] [ 4]  5V                │
│   SCL  [ 5] [ 6]  GND               │
│  GPIO4 [ 7] [ 8]  GPIO14 (TXD)      │
│   GND  [ 9] [10]  GPIO15 (RXD)      │
│ GPIO17 [11] [12]  GPIO18            │
│ GPIO27 [13] [14]  GND               │
│ GPIO22 [15] [16]  GPIO23            │
│  3.3V  [17] [18]  GPIO24            │
│  MOSI  [19] [20]  GND               │
│  MISO  [21] [22]  GPIO25            │
│  SCLK  [23] [24]  CE0               │
│   GND  [25] [26]  CE1               │
└─────────────────────────────────────┘
```

## I2C Connections

For I2C mode, the PN532 uses these pins:

| PN532 Pin | Raspberry Pi Pin | Pin Number | Description |
|-----------|------------------|------------|-------------|
| VCC       | 3.3V             | Pin 1 or 17| Power (3.3V) |
| GND       | GND              | Pin 6, 9, 14, 20, 25 | Ground |
| SDA       | SDA (GPIO 2)     | Pin 3      | I2C Data |
| SCL       | SCL (GPIO 3)     | Pin 5      | I2C Clock |

**IMPORTANT:** 
- Use **3.3V**, NOT 5V! The PN532 is 3.3V compatible.
- If using a HAT, it should sit directly on the GPIO header.

## Physical Installation

### If using a PN532 HAT:

1. **Power off** the Raspberry Pi
2. Align the HAT's 40-pin connector with the Raspberry Pi GPIO header
3. Press down firmly but gently until fully seated
4. Ensure all pins are connected (no gaps)
5. The HAT should sit flat on top of the Pi

### If using a PN532 Module (not HAT):

Use jumper wires to connect:

```
PN532 Module  →  Raspberry Pi
────────────────────────────
VCC (3.3V)    →  Pin 1 (3.3V)
GND           →  Pin 6 (GND)
SDA           →  Pin 3 (SDA)
SCL           →  Pin 5 (SCL)
```

## Enable I2C on Raspberry Pi

### Method 1: Using raspi-config (Recommended)

```bash
sudo raspi-config
```

1. Select: **3 Interface Options**
2. Select: **I5 I2C**
3. Select: **Yes** to enable
4. Select: **OK**
5. Select: **Finish**
6. Reboot: `sudo reboot`

### Method 2: Manual Configuration

Edit `/boot/firmware/config.txt` (or `/boot/config.txt` on older systems):

```bash
sudo nano /boot/firmware/config.txt
```

Add or uncomment this line:
```
dtparam=i2c_arm=on
```

Save and reboot:
```bash
sudo reboot
```

## Verify I2C is Working

After reboot, check if I2C is enabled:

```bash
# Check if I2C device exists
ls /dev/i2c-*

# Should show: /dev/i2c-1
```

Install I2C tools:
```bash
sudo apt-get install i2c-tools
```

Scan for I2C devices:
```bash
sudo i2cdetect -y 1
```

**Expected output with PN532 connected:**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- 24 -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- --
```

The `24` indicates the PN532 is detected at address 0x24.

## Troubleshooting

### No device detected (all `--`)

**Possible causes:**

1. **I2C not enabled**
   - Run `sudo raspi-config` and enable I2C
   - Reboot

2. **Wrong switch settings**
   - Check switches on PN532 module
   - Should be: Switch 1 ON, Switch 2 OFF for I2C

3. **Poor connection**
   - Remove and reseat the HAT
   - Check for bent pins
   - Ensure HAT is fully inserted

4. **Wrong power**
   - Verify using 3.3V, not 5V
   - Check power LED on PN532 (should be lit)

5. **Faulty hardware**
   - Try the PN532 on another Pi
   - Try a different PN532 module

### Device shows as `UU`

This means the device is in use by a kernel driver. This is usually fine.

### Permission denied errors

Add your user to the i2c group:
```bash
sudo usermod -aG i2c $USER
sudo reboot
```

## Testing the Connection

Run the hardware test script:

```bash
cd ~/NFC-LN
python3 test_hardware.py
```

This will check:
- I2C enabled
- Permissions
- PN532 detection
- Firmware version
- Tag reading capability

## NFC Tags

### Recommended Tags

- **NTAG213**: 144 bytes, good for most use cases
- **NTAG215**: 504 bytes, more storage
- **NTAG216**: 888 bytes, maximum storage

### Where to Buy

- Amazon: Search "NTAG213 NFC tags"
- AliExpress: Bulk packs available
- eBay: Various sizes and formats

### Tag Formats

- **Stickers**: Easy to apply anywhere
- **Cards**: Credit card size, durable
- **Key fobs**: Convenient to carry
- **Wristbands**: Wearable

## Additional Resources

- [Adafruit PN532 Guide](https://learn.adafruit.com/adafruit-pn532-rfid-nfc)
- [Raspberry Pi I2C Guide](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#i2c)
- [NFC Forum](https://nfc-forum.org/)

## Support

If you're still having issues:

1. Run the hardware test: `python3 test_hardware.py`
2. Check the output of: `sudo i2cdetect -y 1`
3. Verify switch settings on PN532
4. Take a photo of your wiring
5. Open an issue on GitHub with details

---

**Quick Checklist:**
- [ ] I2C enabled in raspi-config
- [ ] PN532 switches set to I2C mode (1, 0)
- [ ] HAT properly seated on GPIO pins
- [ ] Using 3.3V power (not 5V)
- [ ] Rebooted after enabling I2C
- [ ] User added to i2c group
- [ ] `sudo i2cdetect -y 1` shows device at 0x24
