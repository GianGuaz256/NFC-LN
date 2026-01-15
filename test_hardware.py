#!/usr/bin/env python3
"""Hardware testing script for PN532 NFC HAT on Raspberry Pi."""

import sys
import subprocess

print("=" * 60)
print("PN532 NFC HAT Hardware Test")
print("=" * 60)
print()

# Test 1: Check I2C is enabled
print("Test 1: Checking if I2C is enabled...")
try:
    result = subprocess.run(['ls', '/dev/i2c-1'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ I2C is enabled (/dev/i2c-1 exists)")
    else:
        print("✗ I2C is NOT enabled")
        print("  Run: sudo raspi-config")
        print("  Navigate to: Interface Options -> I2C -> Enable")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error checking I2C: {e}")
    sys.exit(1)

print()

# Test 2: Check I2C permissions
print("Test 2: Checking I2C permissions...")
try:
    import os
    import grp
    
    # Check if user is in i2c group
    user = os.getenv('USER')
    i2c_group = grp.getgrnam('i2c')
    
    if user in i2c_group.gr_mem:
        print(f"✓ User '{user}' is in i2c group")
    else:
        print(f"✗ User '{user}' is NOT in i2c group")
        print(f"  Run: sudo usermod -aG i2c {user}")
        print("  Then reboot: sudo reboot")
except Exception as e:
    print(f"⚠ Could not check group membership: {e}")

print()

# Test 3: Scan I2C bus
print("Test 3: Scanning I2C bus for devices...")
try:
    result = subprocess.run(['i2cdetect', '-y', '1'], capture_output=True, text=True)
    print(result.stdout)
    
    if '24' in result.stdout:
        print("✓ PN532 detected at address 0x24!")
    else:
        print("✗ PN532 NOT detected")
        print()
        print("Possible issues:")
        print("  1. PN532 HAT not properly connected to GPIO pins")
        print("  2. PN532 HAT switches not set to I2C mode")
        print("  3. Loose connection or faulty HAT")
        print()
        print("See wiring guide: docs/WIRING.md")
        sys.exit(1)
except FileNotFoundError:
    print("✗ i2cdetect not found. Install with: sudo apt-get install i2c-tools")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error scanning I2C: {e}")
    sys.exit(1)

print()

# Test 4: Test Python I2C library
print("Test 4: Testing Python I2C libraries...")
try:
    import board
    import busio
    print("✓ board and busio libraries available")
except ImportError as e:
    print(f"✗ Missing library: {e}")
    print("  Install with: pip3 install adafruit-blinka")
    sys.exit(1)

print()

# Test 5: Test PN532 library
print("Test 5: Testing PN532 library...")
try:
    from adafruit_pn532.i2c import PN532_I2C
    print("✓ PN532 library available")
except ImportError as e:
    print(f"✗ Missing library: {e}")
    print("  Install with: pip3 install adafruit-circuitpython-pn532")
    sys.exit(1)

print()

# Test 6: Initialize PN532
print("Test 6: Initializing PN532...")
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c, debug=False)
    
    ic, ver, rev, support = pn532.firmware_version
    print(f"✓ PN532 initialized successfully!")
    print(f"  Firmware version: {ver}.{rev}")
except Exception as e:
    print(f"✗ Failed to initialize PN532: {e}")
    sys.exit(1)

print()

# Test 7: Test tag reading
print("Test 7: Testing NFC tag detection...")
print("Place an NFC tag near the reader within 10 seconds...")
try:
    uid = pn532.read_passive_target(timeout=10)
    
    if uid:
        print(f"✓ Tag detected!")
        print(f"  UID: {uid.hex()}")
        print(f"  UID Length: {len(uid)} bytes")
    else:
        print("⚠ No tag detected within timeout")
        print("  This is OK if you don't have a tag ready")
except Exception as e:
    print(f"✗ Error reading tag: {e}")

print()
print("=" * 60)
print("Hardware test complete!")
print("=" * 60)
