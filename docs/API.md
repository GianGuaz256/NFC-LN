# LN-NFC API Reference

Complete reference for CLI commands, configuration options, and troubleshooting.

## Table of Contents

- [CLI Commands](#cli-commands)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Python API](#python-api)
- [Troubleshooting](#troubleshooting)

## CLI Commands

All commands are executed via `python3 cli.py` or `ln-nfc` (if installed).

### `load-tag`

Load an NFC tag with a new LNURL-withdraw link.

**Usage:**
```bash
python3 cli.py load-tag [OPTIONS]
```

**Options:**
- `--amount, -a INTEGER` (required): Amount in satoshis
- `--uses, -u INTEGER`: Number of times link can be used (default: 1)
- `--title, -t TEXT`: Title for the withdraw link (default: "Lightning Gift Card")
- `--timeout FLOAT`: Timeout for waiting for tag in seconds (default: 10.0)

**Examples:**
```bash
# Load tag with 1000 sats, single use
python3 cli.py load-tag --amount 1000

# Load tag with 5000 sats, 3 uses, custom title
python3 cli.py load-tag -a 5000 -u 3 -t "Coffee Card"

# Load tag with 30 second timeout
python3 cli.py load-tag --amount 2000 --timeout 30
```

**Output:**
```
Loading NFC Tag
Amount: 1000 sats
Uses: 1
Title: Lightning Gift Card

✓ Tag loaded successfully!

Tag UID:     04123456789ABC
Link ID:     abc123def456
Amount:      1000 sats
Uses:        1
LNURL:       LNURL1DP68GURN8GHJ7MRWW4EXCTNXD9SHG6NPVCHXXMMD...
```

---

### `read-tag`

Read LNURL from an NFC tag and display information.

**Usage:**
```bash
python3 cli.py read-tag [OPTIONS]
```

**Options:**
- `--timeout FLOAT`: Timeout for waiting for tag in seconds (default: 10.0)

**Examples:**
```bash
# Read tag with default timeout
python3 cli.py read-tag

# Read tag with 5 second timeout
python3 cli.py read-tag --timeout 5
```

**Output:**
```
Reading NFC Tag
Place tag near reader (timeout: 10s)...

✓ Tag read successfully!

Tag UID:     04123456789ABC
LNURL:       LNURL1DP68GURN8GHJ7MRWW4EXCTNXD9SHG6NPVCHXXMMD...
Valid:       True
URL:         https://lnbits.com/withdraw/api/v1/lnurl/abc123
Type:        withdraw
```

---

### `clear-tag`

Clear/format an NFC tag (removes all data).

**Usage:**
```bash
python3 cli.py clear-tag [OPTIONS]
```

**Options:**
- `--timeout FLOAT`: Timeout for waiting for tag in seconds (default: 10.0)
- `--yes, -y`: Skip confirmation prompt

**Examples:**
```bash
# Clear tag with confirmation
python3 cli.py clear-tag

# Clear tag without confirmation
python3 cli.py clear-tag --yes
```

**Output:**
```
Clearing NFC Tag
Place tag near reader (timeout: 10s)...

✓ Tag cleared successfully!
Tag UID: 04123456789ABC
```

---

### `status`

Check system status and LNbits connection.

**Usage:**
```bash
python3 cli.py status
```

**Output:**
```
System Status

LNbits URL:    https://legend.lnbits.com
Connection:    ✓ Connected
Wallet:        My Wallet
Balance:       100000 sats (100000000 msat)
NFC Interface: I2C
```

---

### `daemon`

Run in daemon mode (continuous payment processing).

**Usage:**
```bash
python3 cli.py daemon [OPTIONS]
```

**Options:**
- `--poll-interval FLOAT`: Polling interval in seconds (overrides config)

**Examples:**
```bash
# Run daemon with default settings
python3 cli.py daemon

# Run daemon with 1 second poll interval
python3 cli.py daemon --poll-interval 1.0
```

**Output:**
```
Starting Daemon Mode

Poll interval: 0.5s
Rate limit: 2.0s

Listening for NFC tags... (Press Ctrl+C to stop)

✓ Payment processed: 04123456789ABC
  LNURL: LNURL1DP68GURN8GHJ7MRWW4EXCTNXD9SHG6NPVCHXXMMD...
```

Press `Ctrl+C` to stop the daemon.

---

### `info`

Get detailed information about an NFC tag.

**Usage:**
```bash
python3 cli.py info [OPTIONS]
```

**Options:**
- `--timeout FLOAT`: Timeout for waiting for tag in seconds (default: 10.0)

**Examples:**
```bash
python3 cli.py info
```

**Output:**
```
NFC Tag Information
Place tag near reader (timeout: 10s)...

✓ Tag detected!

Present:       True
UID:           04123456789ABC
UID Length:    7 bytes
Type:          NTAG
NDEF Valid:    True
NDEF Size:     48 bytes
NDEF Records:  1
LNURL:         LNURL1DP68GURN8GHJ7MRWW4EXCTNXD9SHG6NPVCHXXMMD...
LNURL Valid:   True
```

---

### `list-links`

List all LNURL-withdraw links in LNbits.

**Usage:**
```bash
python3 cli.py list-links [OPTIONS]
```

**Options:**
- `--limit, -l INTEGER`: Maximum number of links to display (default: 10)

**Examples:**
```bash
# List 10 most recent links
python3 cli.py list-links

# List 50 links
python3 cli.py list-links --limit 50
```

**Output:**
```
LNURL-Withdraw Links

┌──────────┬──────────────────┬────────────┬──────┬──────┐
│ ID       │ Title            │ Amount     │ Uses │ Used │
├──────────┼──────────────────┼────────────┼──────┼──────┤
│ abc12345 │ Gift Card        │ 1000 sats  │ 1    │ 0    │
│ def67890 │ Coffee Card      │ 500 sats   │ 5    │ 2    │
└──────────┴──────────────────┴────────────┴──────┴──────┘

Showing 2 of 2 link(s)
```

---

### `version`

Display version information.

**Usage:**
```bash
python3 cli.py version
```

**Output:**
```
╭─────────────────────────────────╮
│        Version Info             │
│                                 │
│ LN-NFC                          │
│ Version: 1.0.0                  │
│ Lightning Network NFC Payment   │
│ System                          │
╰─────────────────────────────────╯
```

---

## Configuration

### Configuration File

Configuration is loaded from `.env` file in the project root.

**Create from template:**
```bash
cp .env.example .env
nano .env
```

### Configuration Priority

1. Environment variables (highest priority)
2. `.env` file
3. Default values (lowest priority)

---

## Environment Variables

### Required Variables

#### `LNBITS_URL`
- **Type**: String (URL)
- **Description**: LNbits instance URL
- **Example**: `https://legend.lnbits.com`
- **Validation**: Must start with `http://` or `https://`

#### `LNBITS_API_KEY`
- **Type**: String
- **Description**: LNbits admin or invoice API key
- **Example**: `abc123def456ghi789jkl012mno345pqr678stu901`
- **Security**: Never commit to git, keep secret

### Optional Variables

#### `LNBITS_WALLET_ID`
- **Type**: String
- **Description**: LNbits wallet ID
- **Default**: None (extracted from API key if possible)
- **Example**: `abc123def456`

#### `NFC_INTERFACE`
- **Type**: String (`i2c` or `spi`)
- **Description**: NFC communication interface
- **Default**: `i2c`
- **Options**: `i2c`, `spi`

#### `NFC_I2C_BUS`
- **Type**: Integer
- **Description**: I2C bus number
- **Default**: `1`
- **Common Values**: `1` (Raspberry Pi 5)

#### `NFC_SPI_BUS`
- **Type**: Integer
- **Description**: SPI bus number
- **Default**: `0`

#### `NFC_SPI_DEVICE`
- **Type**: Integer
- **Description**: SPI device number
- **Default**: `0`

#### `LOG_LEVEL`
- **Type**: String
- **Description**: Logging level
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

#### `LOG_FILE`
- **Type**: String (path)
- **Description**: Log file path
- **Default**: `/app/logs/ln-nfc.log`

#### `ADMIN_PIN`
- **Type**: String
- **Description**: Optional PIN for admin operations
- **Default**: None (no PIN required)
- **Example**: `1234`

#### `DEFAULT_TAG_USES`
- **Type**: Integer
- **Description**: Default number of uses for withdraw links
- **Default**: `1`
- **Validation**: Must be >= 1

#### `DEFAULT_TAG_TITLE`
- **Type**: String
- **Description**: Default title for withdraw links
- **Default**: `Lightning Gift Card`

#### `LNURL_USE_BECH32`
- **Type**: Boolean
- **Description**: Use bech32 encoding for LNURL
- **Default**: `true`
- **Options**: `true`, `false`

#### `RATE_LIMIT_SECONDS`
- **Type**: Float
- **Description**: Minimum seconds between processing same tag
- **Default**: `2.0`

#### `POLL_INTERVAL`
- **Type**: Float
- **Description**: Polling interval for daemon mode (seconds)
- **Default**: `0.5`

---

## Python API

### Using as a Library

The LN-NFC application can be used as a Python library:

```python
from src.config import load_config
from src.main import Application

# Load configuration
config = load_config()

# Create application
app = Application(config)

# Initialize
app.initialize()

# Load a tag
result = app.tag_loader.load_tag(
    amount=1000,
    title="My Card",
    uses=1,
    timeout=10.0,
)

print(f"Tag loaded: {result['tag_uid']}")
print(f"LNURL: {result['lnurl']}")

# Cleanup
app.cleanup()
```

### Context Manager

```python
from src.main import Application

with Application() as app:
    # Use application
    result = app.tag_loader.read_tag(timeout=5.0)
    print(result)
```

### Individual Components

```python
from src.nfc.reader import NFCReader
from src.lnbits.client import LNbitsClient

# NFC Reader
reader = NFCReader(interface="i2c", i2c_bus=1)
reader.connect()
uid = reader.wait_for_tag(timeout=5.0)
reader.disconnect()

# LNbits Client
client = LNbitsClient(
    base_url="https://legend.lnbits.com",
    api_key="your_api_key",
)
balance = client.get_wallet_balance()
print(f"Balance: {balance // 1000} sats")
client.close()
```

---

## Troubleshooting

### Common Issues

#### "PN532 not found"

**Cause**: I2C not enabled or PN532 not connected

**Solution:**
```bash
# Enable I2C
sudo raspi-config
# Interface Options -> I2C -> Enable

# Reboot
sudo reboot

# Check I2C devices
sudo i2cdetect -y 1
# Should show device at 0x24
```

#### "Permission denied: /dev/i2c-1"

**Cause**: User not in i2c group

**Solution:**
```bash
sudo usermod -aG i2c $USER
sudo reboot
```

#### "LNbits connection failed"

**Cause**: Invalid URL or API key

**Solution:**
1. Verify URL is accessible:
   ```bash
   curl -I https://your-lnbits-instance.com
   ```

2. Test API key:
   ```bash
   curl -H "X-Api-Key: your_api_key" \
        https://your-lnbits-instance.com/api/v1/wallet
   ```

3. Check `.env` file has correct values

#### "No LNURL found on tag"

**Cause**: Tag is empty or has non-LNURL data

**Solution:**
```bash
# Clear and reload tag
python3 cli.py clear-tag
python3 cli.py load-tag --amount 1000
```

#### "Failed to write NDEF"

**Cause**: Tag is read-only or incompatible

**Solution:**
- Use NTAG213/215/216 tags (recommended)
- Ensure tag is not write-protected
- Try different tag

### Debug Mode

Enable debug logging for detailed output:

```bash
# In .env file
LOG_LEVEL=DEBUG

# Or via environment variable
LOG_LEVEL=DEBUG python3 cli.py load-tag --amount 1000
```

### Testing Hardware

Run hardware tests to verify PN532 connection:

```bash
pytest tests/test_nfc_hardware.py -v -m hardware
```

### Docker Debugging

View container logs:
```bash
docker compose logs -f nfc-service
```

Enter container shell:
```bash
docker compose exec nfc-service /bin/bash
```

Check container status:
```bash
docker compose ps
```

### Getting Help

1. Check logs: `docker compose logs -f`
2. Run tests: `pytest -v`
3. Verify configuration: `python3 cli.py status`
4. Check hardware: `sudo i2cdetect -y 1`
5. Review documentation: `docs/ARCHITECTURE.md`

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 130 | Interrupted by user (Ctrl+C) |

---

## Best Practices

### Security
- Never commit `.env` file to git
- Use strong API keys
- Limit withdraw link amounts
- Monitor transaction logs
- Keep system updated

### Performance
- Use I2C interface (simpler, reliable)
- Adjust poll interval based on use case
- Enable rate limiting to prevent duplicates
- Monitor system resources

### Reliability
- Test tags before deployment
- Keep backup of configuration
- Monitor LNbits connection
- Use systemd for auto-restart
- Regular system updates

---

For more information, see:
- [README.md](../README.md) - Quick start guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [GitHub Issues](https://github.com/your-repo/issues) - Report bugs
