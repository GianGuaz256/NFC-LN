"""NFC Reader module for PN532 HAT communication."""

import logging
import time
from typing import Optional, Literal
from contextlib import contextmanager

try:
    import board
    import busio
    from digitalio import DigitalInOut
    from adafruit_pn532.i2c import PN532_I2C
    from adafruit_pn532.spi import PN532_SPI
    PN532_AVAILABLE = True
except ImportError:
    PN532_AVAILABLE = False
    PN532_I2C = None
    PN532_SPI = None

logger = logging.getLogger(__name__)


class NFCReaderError(Exception):
    """Base exception for NFC reader errors."""
    pass


class NFCConnectionError(NFCReaderError):
    """Raised when NFC reader connection fails."""
    pass


class NFCReadError(NFCReaderError):
    """Raised when reading from NFC tag fails."""
    pass


class NFCWriteError(NFCReaderError):
    """Raised when writing to NFC tag fails."""
    pass


class NFCReader:
    """
    NFC Reader interface for PN532 HAT.
    
    Supports both I2C and SPI communication interfaces.
    """
    
    def __init__(
        self,
        interface: Literal["i2c", "spi"] = "i2c",
        i2c_bus: int = 1,
        spi_bus: int = 0,
        spi_device: int = 0,
        reset_pin: Optional[int] = None,
        req_pin: Optional[int] = None,
    ):
        """
        Initialize NFC Reader.
        
        Args:
            interface: Communication interface ('i2c' or 'spi')
            i2c_bus: I2C bus number (default: 1 for Raspberry Pi)
            spi_bus: SPI bus number (default: 0)
            spi_device: SPI device number (default: 0)
            reset_pin: GPIO pin for reset (optional)
            req_pin: GPIO pin for request (optional)
        """
        if not PN532_AVAILABLE:
            raise ImportError("adafruit-circuitpython-pn532 library not installed. Run: pip install adafruit-circuitpython-pn532")
        
        self.interface = interface
        self.i2c_bus = i2c_bus
        self.spi_bus = spi_bus
        self.spi_device = spi_device
        self.reset_pin = reset_pin
        self.req_pin = req_pin
        self._pn532 = None
        self._initialized = False
        
        logger.info(f"NFCReader initialized with {interface.upper()} interface")
    
    def connect(self) -> None:
        """
        Connect to the PN532 NFC reader.
        
        Raises:
            NFCConnectionError: If connection fails
        """
        try:
            if self.interface == "i2c":
                self._connect_i2c()
            elif self.interface == "spi":
                self._connect_spi()
            else:
                raise ValueError(f"Unsupported interface: {self.interface}")
            
            self._initialized = True
            
            # Get firmware version for verification
            try:
                ic, ver, rev, support = self._pn532.firmware_version
                logger.info(f"PN532 Firmware version: {ver}.{rev}")
            except Exception as e:
                logger.warning(f"Could not read firmware version: {e}")
            
        except Exception as e:
            logger.error(f"Failed to connect to PN532: {e}")
            raise NFCConnectionError(f"Failed to connect to PN532: {e}")
    
    def _connect_i2c(self) -> None:
        """Connect via I2C interface."""
        logger.info(f"Connecting to PN532 via I2C (bus {self.i2c_bus})...")
        i2c = busio.I2C(board.SCL, board.SDA)
        self._pn532 = PN532_I2C(i2c, debug=False)
    
    def _connect_spi(self) -> None:
        """Connect via SPI interface."""
        logger.info(f"Connecting to PN532 via SPI (bus {self.spi_bus}, device {self.spi_device})...")
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs_pin = DigitalInOut(board.D5)
        self._pn532 = PN532_SPI(spi, cs_pin, debug=False)
    
    def disconnect(self) -> None:
        """Disconnect from the NFC reader."""
        self._initialized = False
        self._pn532 = None
        logger.info("Disconnected from PN532")
    
    @contextmanager
    def connection(self):
        """Context manager for NFC reader connection."""
        try:
            if not self._initialized:
                self.connect()
            yield self
        finally:
            pass  # Keep connection alive for reuse
    
    def wait_for_tag(self, timeout: float = 5.0) -> Optional[bytes]:
        """
        Wait for an NFC tag to be present.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            Tag UID as bytes, or None if timeout
        """
        if not self._initialized:
            raise NFCConnectionError("Reader not connected. Call connect() first.")
        
        logger.debug(f"Waiting for NFC tag (timeout: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                uid = self._pn532.read_passive_target(timeout=0.5)
                if uid:
                    logger.info(f"Tag detected: UID={uid.hex()}")
                    return uid
            except Exception as e:
                logger.debug(f"Error reading tag: {e}")
            
            time.sleep(0.1)
        
        logger.debug("No tag detected within timeout")
        return None
    
    def read_ndef(self, uid: Optional[bytes] = None, max_retries: int = 3) -> bytes:
        """
        Read NDEF data from an NFC tag.
        
        Args:
            uid: Tag UID (optional, will wait for tag if not provided)
            max_retries: Maximum number of read attempts
        
        Returns:
            Raw NDEF data as bytes
        
        Raises:
            NFCReadError: If reading fails
        """
        if not self._initialized:
            raise NFCConnectionError("Reader not connected. Call connect() first.")
        
        if uid is None:
            uid = self.wait_for_tag()
            if uid is None:
                raise NFCReadError("No tag present")
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Reading NDEF data (attempt {attempt + 1}/{max_retries})...")
                
                # Read NDEF message using NTAG/Mifare Ultralight commands
                data = self._read_ntag_ndef()
                
                if data:
                    logger.info(f"Successfully read {len(data)} bytes of NDEF data")
                    return data
                
            except Exception as e:
                logger.warning(f"Read attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise NFCReadError(f"Failed to read NDEF after {max_retries} attempts: {e}")
                time.sleep(0.5)
        
        raise NFCReadError("Failed to read NDEF data")
    
    def _read_ntag_ndef(self) -> bytes:
        """Read NDEF data from NTAG/Mifare Ultralight tag."""
        # NTAG213/215/216 have NDEF data starting at page 4
        # Each page is 4 bytes
        data = bytearray()
        
        # Read capability container (page 3)
        try:
            cc = self._pn532.ntag2xx_read_block(3)
            if not cc or len(cc) < 4:
                raise NFCReadError("Failed to read capability container")
        except Exception as e:
            raise NFCReadError(f"Failed to read capability container: {e}")
        
        # Read NDEF TLV (starting at page 4)
        page = 4
        max_pages = 135  # NTAG216 max
        
        while page < max_pages:
            try:
                block = self._pn532.ntag2xx_read_block(page)
                if not block:
                    break
                
                data.extend(block)
                page += 1
                
                # Check for NDEF terminator (0xFE)
                if 0xFE in block:
                    break
            except Exception:
                break
        
        return bytes(data)
    
    def write_ndef(self, ndef_data: bytes, uid: Optional[bytes] = None, max_retries: int = 3) -> bool:
        """
        Write NDEF data to an NFC tag.
        
        Args:
            ndef_data: NDEF data to write
            uid: Tag UID (optional, will wait for tag if not provided)
            max_retries: Maximum number of write attempts
        
        Returns:
            True if write successful
        
        Raises:
            NFCWriteError: If writing fails
        """
        if not self._initialized:
            raise NFCConnectionError("Reader not connected. Call connect() first.")
        
        if uid is None:
            uid = self.wait_for_tag()
            if uid is None:
                raise NFCWriteError("No tag present")
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Writing NDEF data (attempt {attempt + 1}/{max_retries})...")
                
                # Write NDEF message using NTAG/Mifare Ultralight commands
                self._write_ntag_ndef(ndef_data)
                
                logger.info(f"Successfully wrote {len(ndef_data)} bytes of NDEF data")
                return True
                
            except Exception as e:
                logger.warning(f"Write attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise NFCWriteError(f"Failed to write NDEF after {max_retries} attempts: {e}")
                time.sleep(0.5)
        
        return False
    
    def _write_ntag_ndef(self, ndef_data: bytes) -> None:
        """Write NDEF data to NTAG/Mifare Ultralight tag."""
        # Prepare data with TLV structure
        # TLV: Type (0x03 = NDEF), Length, Value, Terminator (0xFE)
        if len(ndef_data) > 254:
            raise NFCWriteError("NDEF data too large (max 254 bytes)")
        
        # Build TLV
        tlv_data = bytearray([0x03, len(ndef_data)])  # Type and Length
        tlv_data.extend(ndef_data)
        tlv_data.append(0xFE)  # Terminator
        
        # Pad to 4-byte boundary
        while len(tlv_data) % 4 != 0:
            tlv_data.append(0x00)
        
        # Write data starting at page 4
        page = 4
        for i in range(0, len(tlv_data), 4):
            block = bytes(tlv_data[i:i+4])
            if len(block) < 4:
                block = block + bytes(4 - len(block))
            
            try:
                self._pn532.ntag2xx_write_block(page, block)
            except Exception as e:
                raise NFCWriteError(f"Failed to write page {page}: {e}")
            
            page += 1
    
    def clear_tag(self, uid: Optional[bytes] = None) -> bool:
        """
        Clear/format an NFC tag.
        
        Args:
            uid: Tag UID (optional, will wait for tag if not provided)
        
        Returns:
            True if clear successful
        
        Raises:
            NFCWriteError: If clearing fails
        """
        if not self._initialized:
            raise NFCConnectionError("Reader not connected. Call connect() first.")
        
        if uid is None:
            uid = self.wait_for_tag()
            if uid is None:
                raise NFCWriteError("No tag present")
        
        try:
            logger.info("Clearing NFC tag...")
            
            # Write empty NDEF message
            empty_ndef = bytes([0x03, 0x00, 0xFE, 0x00])  # Empty TLV
            
            # Write to page 4
            try:
                self._pn532.ntag2xx_write_block(4, empty_ndef)
                logger.info("Tag cleared successfully")
                return True
            except Exception as e:
                raise NFCWriteError(f"Failed to clear tag: {e}")
                
        except Exception as e:
            logger.error(f"Failed to clear tag: {e}")
            raise NFCWriteError(f"Failed to clear tag: {e}")
    
    def get_tag_info(self, uid: Optional[bytes] = None) -> dict:
        """
        Get information about an NFC tag.
        
        Args:
            uid: Tag UID (optional, will wait for tag if not provided)
        
        Returns:
            Dictionary with tag information
        """
        if not self._initialized:
            raise NFCConnectionError("Reader not connected. Call connect() first.")
        
        if uid is None:
            uid = self.wait_for_tag()
            if uid is None:
                return {"present": False}
        
        info = {
            "present": True,
            "uid": uid.hex(),
            "uid_length": len(uid),
        }
        
        try:
            # Try to read capability container
            cc = self._pn532.ntag2xx_read_block(3)
            if cc and len(cc) >= 4:
                info["type"] = "NTAG"
                info["ndef_capable"] = cc[0] == 0xE1
                info["version"] = f"{cc[1]}.{cc[2]}"
                info["size"] = cc[2] * 8  # Size in bytes
        except Exception as e:
            logger.debug(f"Could not read tag details: {e}")
        
        return info
