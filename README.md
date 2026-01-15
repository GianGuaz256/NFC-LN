# LN-NFC: Lightning Network NFC Payment System

A production-ready Python application for Raspberry Pi 5 that enables Lightning Network payments via NFC tags using the PN532 NFC HAT and LNbits.

## Features

- 🏷️ **Load NFC tags** with LNURL-withdraw links (pre-fund with sats)
- 📱 **Tap-to-pay** functionality for Lightning wallet users
- 🔌 **External LNbits integration** via REST API
- 🐳 **Dockerized deployment** for easy management
- 🛠️ **CLI interface** for tag management
- 🔄 **Daemon mode** for continuous payment processing
- ✅ **Comprehensive testing** suite

## Quick Start

### Prerequisites

- Raspberry Pi 5 (or compatible)
- PN532 NFC HAT (I2C or SPI)
- LNbits instance with LNURL-withdraw extension
- Docker and Docker Compose

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd LN-NFC
   ```

2. **Run the setup script:**
   ```bash
   chmod +x setup-pi.sh
   sudo ./setup-pi.sh
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Edit the following required variables:
   ```bash
   LNBITS_URL=https://your-lnbits-instance.com
   LNBITS_API_KEY=your-admin-api-key
   LNBITS_WALLET_ID=your-wallet-id
   ```

4. **Reboot the Raspberry Pi:**
   ```bash
   sudo reboot
   ```

5. **Start the service:**
   ```bash
   docker compose up -d
   ```

## Usage

### CLI Commands

The application provides a command-line interface for managing NFC tags:

#### Load a Tag
```bash
python3 cli.py load-tag --amount 1000 --uses 1 --title "Gift Card"
```

#### Read a Tag
```bash
python3 cli.py read-tag
```

#### Clear a Tag
```bash
python3 cli.py clear-tag
```

#### Check Status
```bash
python3 cli.py status
```

#### Run Daemon Mode
```bash
python3 cli.py daemon
```

#### Get Tag Info
```bash
python3 cli.py info
```

#### List Withdraw Links
```bash
python3 cli.py list-links --limit 10
```

### Docker Commands

```bash
# Start service
docker compose up -d

# View logs
docker compose logs -f

# Stop service
docker compose down

# Rebuild image
docker compose build
```

### Systemd Service

Enable auto-start on boot:
```bash
sudo systemctl enable ln-nfc
sudo systemctl start ln-nfc
```

Check service status:
```bash
sudo systemctl status ln-nfc
```

## How It Works

### Loading a Tag (Admin Flow)

1. Admin runs `load-tag` command with amount and parameters
2. System creates LNURL-withdraw link in LNbits
3. LNURL is encoded as NDEF message
4. Admin places NFC tag near reader
5. NDEF message is written to tag
6. Tag is ready for use

### Redeeming a Tag (User Flow)

1. User taps NFC tag with Lightning wallet app
2. Wallet reads LNURL from tag
3. Wallet contacts LNbits server
4. User confirms withdrawal
5. Sats are sent to user's wallet

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LNBITS_URL` | LNbits instance URL | Required |
| `LNBITS_API_KEY` | LNbits admin API key | Required |
| `LNBITS_WALLET_ID` | LNbits wallet ID | Optional |
| `NFC_INTERFACE` | NFC interface (i2c/spi) | `i2c` |
| `NFC_I2C_BUS` | I2C bus number | `1` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEFAULT_TAG_USES` | Default uses per tag | `1` |
| `LNURL_USE_BECH32` | Use bech32 encoding | `true` |

See `.env.example` for all available options.

## Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only (no hardware required)
pytest -m "not hardware and not integration"

# Hardware tests (requires PN532)
pytest -m hardware

# Integration tests (requires LNbits)
pytest -m integration

# End-to-end tests
pytest -m e2e
```

### Test Coverage
```bash
pytest --cov=src --cov-report=html
```

## Troubleshooting

### NFC Reader Not Detected

1. Check I2C is enabled:
   ```bash
   sudo raspi-config
   # Interface Options -> I2C -> Enable
   ```

2. Scan for I2C devices:
   ```bash
   sudo i2cdetect -y 1
   ```
   You should see the PN532 at address `0x24`.

3. Check permissions:
   ```bash
   sudo usermod -aG i2c $USER
   sudo reboot
   ```

### LNbits Connection Failed

1. Verify LNbits URL is accessible:
   ```bash
   curl -I https://your-lnbits-instance.com
   ```

2. Check API key is valid:
   ```bash
   curl -H "X-Api-Key: your-api-key" \
        https://your-lnbits-instance.com/api/v1/wallet
   ```

3. Ensure LNURL-withdraw extension is enabled in LNbits

### Docker Issues

1. Check Docker service:
   ```bash
   sudo systemctl status docker
   ```

2. View container logs:
   ```bash
   docker compose logs -f nfc-service
   ```

3. Rebuild container:
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

## Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design and data flows.

## API Reference

See [API.md](docs/API.md) for CLI commands and configuration options.

## Security Considerations

- Store API keys securely in `.env` file (never commit to git)
- Use HTTPS for LNbits connections
- Limit withdraw link amounts and uses
- Monitor transaction logs regularly
- Keep system and dependencies updated

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review test examples

## Acknowledgments

- LNbits for the Lightning backend
- PN532 library maintainers
- Lightning Network community

---

**Made with ⚡ for the Lightning Network**
