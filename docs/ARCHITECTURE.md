# LN-NFC Architecture

This document describes the system architecture, design decisions, and data flows for the Lightning Network NFC Payment System.

## System Overview

The LN-NFC system is a Dockerized Python application that bridges NFC hardware (PN532) with Lightning Network payments via LNbits. It enables two primary use cases:

1. **Tag Loading**: Admin creates LNURL-withdraw links and writes them to NFC tags
2. **Payment Processing**: Users tap NFC tags with Lightning wallets to withdraw funds

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │            Docker Container                         │    │
│  │                                                     │    │
│  │  ┌──────────────┐      ┌──────────────────────┐  │    │
│  │  │   CLI App    │      │   Daemon Service     │  │    │
│  │  │  (cli.py)    │      │  (main.py)           │  │    │
│  │  └──────┬───────┘      └──────────┬───────────┘  │    │
│  │         │                          │               │    │
│  │         └──────────┬───────────────┘               │    │
│  │                    │                               │    │
│  │         ┌──────────▼──────────────┐               │    │
│  │         │   Application Layer     │               │    │
│  │         │  - TagLoaderService     │               │    │
│  │         │  - PaymentProcessor     │               │    │
│  │         └──────────┬──────────────┘               │    │
│  │                    │                               │    │
│  │         ┌──────────┴──────────────┐               │    │
│  │         │                         │               │    │
│  │    ┌────▼─────┐            ┌─────▼──────┐       │    │
│  │    │ NFC      │            │ LNbits     │       │    │
│  │    │ Module   │            │ Client     │       │    │
│  │    └────┬─────┘            └─────┬──────┘       │    │
│  │         │                         │               │    │
│  └─────────┼─────────────────────────┼───────────────┘    │
│            │                         │                     │
│     ┌──────▼──────┐                 │                     │
│     │  PN532 HAT  │                 │                     │
│     │  (I2C/SPI)  │                 │                     │
│     └─────────────┘                 │                     │
│                                     │                     │
└─────────────────────────────────────┼─────────────────────┘
                                      │
                                      │ HTTPS
                                      │
                          ┌───────────▼────────────┐
                          │  External LNbits       │
                          │  Instance              │
                          │  - Wallet Management   │
                          │  - LNURL-withdraw      │
                          │  - Lightning Node      │
                          └────────────────────────┘
```

## Component Architecture

### 1. Hardware Layer

#### PN532 NFC HAT
- **Interface**: I2C (default) or SPI
- **Communication**: Direct hardware access via `/dev/i2c-1` or `/dev/spidev*`
- **Capabilities**:
  - Read/write NTAG213/215/216 tags
  - NDEF message handling
  - Tag detection and UID reading

### 2. NFC Module (`src/nfc/`)

#### NFCReader (`reader.py`)
- **Purpose**: Hardware abstraction for PN532 communication
- **Key Features**:
  - Interface-agnostic (I2C/SPI)
  - Connection management and retry logic
  - NDEF read/write operations
  - Tag detection with timeout
- **Dependencies**: `pn532`, `smbus2` (I2C), `spidev` (SPI)

#### NDEFHandler (`ndef.py`)
- **Purpose**: NDEF message encoding/decoding
- **Key Features**:
  - URI record creation
  - LNURL encoding/decoding
  - TLV structure parsing
  - Message validation
- **Dependencies**: `ndeflib`, `bech32`

### 3. LNbits Module (`src/lnbits/`)

#### LNbitsClient (`client.py`)
- **Purpose**: REST API wrapper for LNbits
- **Key Features**:
  - Wallet operations (balance, info)
  - Withdraw link management (create, read, delete)
  - Invoice operations
  - Transaction history
- **Authentication**: API key via `X-Api-Key` header
- **Dependencies**: `httpx`

#### LNURLHandler (`lnurl.py`)
- **Purpose**: LNURL protocol implementation
- **Key Features**:
  - Bech32 encoding/decoding
  - URL validation
  - Lightning URI creation
  - Parameter extraction
- **Dependencies**: `bech32`

### 4. Service Layer (`src/services/`)

#### TagLoaderService (`tag_loader.py`)
- **Purpose**: Orchestrate tag loading workflow
- **Workflow**:
  1. Create withdraw link in LNbits
  2. Encode LNURL as NDEF
  3. Wait for NFC tag
  4. Write NDEF to tag
  5. Verify write operation
- **Error Handling**: Cleanup on failure (delete created links)

#### PaymentProcessorService (`payment_processor.py`)
- **Purpose**: Continuous payment monitoring
- **Features**:
  - Daemon mode operation
  - Rate limiting (prevent duplicate processing)
  - Tag tracking
  - Callback support
- **Use Case**: Unattended payment terminal

### 5. Application Layer

#### Config (`config.py`)
- **Purpose**: Configuration management
- **Features**:
  - Environment variable loading
  - Validation with Pydantic
  - Logging setup
  - Type-safe configuration
- **Source**: `.env` file + environment variables

#### Main (`main.py`)
- **Purpose**: Application entry point
- **Features**:
  - Component initialization
  - Resource management
  - Daemon mode execution
  - Context manager support

#### CLI (`cli.py`)
- **Purpose**: Command-line interface
- **Framework**: Typer + Rich
- **Commands**: load-tag, read-tag, clear-tag, status, daemon, info, list-links

## Data Flow

### Tag Loading Flow

```
Admin → CLI → TagLoaderService → LNbitsClient → LNbits API
                    ↓                                  ↓
              NDEFHandler                         Create Link
                    ↓                                  ↓
              NFCReader                           Return LNURL
                    ↓                                  ↓
              PN532 HAT                          Encode NDEF
                    ↓                                  ↓
              NFC Tag ←──────────────────────── Write Tag
```

**Detailed Steps:**

1. Admin executes `cli.py load-tag --amount 1000`
2. CLI calls `TagLoaderService.load_tag()`
3. Service calls `LNbitsClient.create_withdraw_link()`
4. LNbits creates link and returns LNURL
5. Service calls `NDEFHandler.create_lnurl_record()`
6. NDEF message is encoded
7. Service calls `NFCReader.wait_for_tag()`
8. Admin places tag near reader
9. Service calls `NFCReader.write_ndef()`
10. NDEF written to tag via PN532
11. Service verifies write by reading back
12. Success result returned to CLI

### Payment Processing Flow

```
User Wallet → NFC Tag → (LNURL read by wallet)
                              ↓
                         LNbits API
                              ↓
                    Withdraw Request
                              ↓
                    Lightning Payment
                              ↓
                         User Wallet
```

**Detailed Steps:**

1. User opens Lightning wallet app
2. User taps NFC tag
3. Wallet reads NDEF message
4. Wallet extracts LNURL
5. Wallet decodes LNURL to URL
6. Wallet makes GET request to LNbits
7. LNbits returns withdraw parameters
8. User confirms withdrawal
9. Wallet generates invoice
10. Wallet sends invoice to LNbits
11. LNbits pays invoice
12. User receives sats

### Daemon Mode Flow

```
Daemon Loop:
  1. Poll for NFC tag (0.5s timeout)
  2. If tag detected:
     a. Check rate limit
     b. Read NDEF data
     c. Extract LNURL
     d. Validate LNURL
     e. Log payment details
     f. Call callback (if configured)
  3. Repeat
```

## Security Architecture

### API Key Management
- Stored in `.env` file (not in git)
- Loaded via environment variables
- Never logged or exposed
- Validated on startup

### Rate Limiting
- Prevents duplicate tag processing
- Configurable cooldown period (default: 2s)
- Tag UID tracking with timestamp
- Automatic cleanup of old entries

### LNURL Security
- Supports bech32 encoding (obfuscation)
- HTTPS-only LNbits connections
- Configurable link expiration
- Limited uses per link

### Docker Security
- Non-root user in container (overridden for hardware access)
- Minimal base image (Python slim)
- No unnecessary packages
- Volume mounts for logs only

## Design Decisions

### Why External LNbits?
- **Flexibility**: Use existing LNbits instance
- **Scalability**: LNbits can run on more powerful hardware
- **Maintenance**: Separate concerns (payments vs. NFC)
- **Security**: LNbits handles Lightning node complexity

### Why Docker?
- **Isolation**: Clean environment
- **Portability**: Easy deployment
- **Dependencies**: Consistent Python environment
- **Updates**: Simple rebuild process

### Why I2C Default?
- **Simplicity**: Fewer wires than SPI
- **Reliability**: Well-tested on Raspberry Pi
- **Compatibility**: Works with most PN532 HATs
- **Configuration**: Easy to enable in raspi-config

### Why Typer + Rich?
- **UX**: Beautiful CLI output
- **Type Safety**: Automatic validation
- **Documentation**: Auto-generated help
- **Maintainability**: Clean command structure

## Performance Considerations

### Tag Read/Write Speed
- **Read**: ~100-200ms
- **Write**: ~200-500ms
- **Detection**: ~50-100ms per poll

### API Latency
- **LNbits API**: ~100-500ms (depends on network)
- **Link Creation**: ~200-1000ms
- **Balance Check**: ~100-300ms

### Daemon Mode
- **Poll Interval**: 0.5s (configurable)
- **CPU Usage**: <5% idle, ~10-15% when processing
- **Memory**: ~50-100MB

## Scalability

### Single Device
- **Tags/Hour**: ~100-200 (limited by physical interaction)
- **Concurrent Operations**: 1 (single NFC reader)
- **Storage**: Minimal (logs only)

### Multiple Devices
- Deploy multiple Raspberry Pis
- Each connects to same LNbits instance
- Independent operation
- Centralized payment tracking in LNbits

## Error Handling

### Hardware Errors
- **PN532 Not Found**: Clear error message, setup instructions
- **I2C/SPI Disabled**: Auto-enable via setup script
- **Tag Read Failure**: Retry logic with exponential backoff
- **Tag Write Failure**: Cleanup (delete created link)

### Network Errors
- **LNbits Unreachable**: Connection check on startup
- **API Errors**: Detailed error messages from response
- **Timeout**: Configurable timeout values
- **Retry**: Manual retry via CLI

### Application Errors
- **Invalid Config**: Validation on load with clear messages
- **Missing Dependencies**: Check on import with install instructions
- **Resource Cleanup**: Context managers ensure cleanup

## Monitoring and Logging

### Log Levels
- **DEBUG**: Detailed operation logs
- **INFO**: Normal operations (tag detected, link created)
- **WARNING**: Recoverable errors (tag read retry)
- **ERROR**: Operation failures (API error, write failure)

### Log Destinations
- **Console**: Real-time output
- **File**: Persistent logs at `/app/logs/ln-nfc.log`
- **Docker**: Container logs via `docker compose logs`

### Metrics
- Tag operations (read/write/clear)
- LNbits API calls
- Success/failure rates
- Processing times

## Future Enhancements

### Potential Features
- [ ] Web dashboard for monitoring
- [ ] Multiple tag support (batch operations)
- [ ] QR code generation alongside NFC
- [ ] Webhook notifications
- [ ] Tag inventory management
- [ ] Analytics and reporting
- [ ] Multi-wallet support
- [ ] Tag encryption
- [ ] Offline mode (cache links)
- [ ] Mobile app integration

### Performance Improvements
- [ ] Connection pooling for LNbits
- [ ] Tag write verification optimization
- [ ] Parallel tag processing (multiple readers)
- [ ] Caching of frequently used data

## Conclusion

The LN-NFC architecture prioritizes:
- **Reliability**: Robust error handling and retry logic
- **Simplicity**: Clear separation of concerns
- **Maintainability**: Well-documented, tested code
- **Security**: Safe handling of API keys and payments
- **Flexibility**: Configurable for various use cases

The modular design allows easy extension and modification while maintaining production-ready quality.
