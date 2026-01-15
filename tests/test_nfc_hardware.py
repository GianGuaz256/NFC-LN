"""Hardware integration tests for NFC reader."""

import pytest
from src.nfc.reader import NFCReader, NFCConnectionError, NFCReadError, NFCWriteError


@pytest.mark.hardware
class TestNFCHardware:
    """Tests that require physical PN532 hardware."""
    
    def test_i2c_connection(self):
        """Test I2C connection to PN532."""
        reader = NFCReader(interface="i2c", i2c_bus=1)
        
        try:
            reader.connect()
            assert reader._initialized is True
        except NFCConnectionError as e:
            pytest.skip(f"PN532 not available: {e}")
        finally:
            reader.disconnect()
    
    def test_spi_connection(self):
        """Test SPI connection to PN532."""
        reader = NFCReader(interface="spi", spi_bus=0, spi_device=0)
        
        try:
            reader.connect()
            assert reader._initialized is True
        except NFCConnectionError as e:
            pytest.skip(f"PN532 not available on SPI: {e}")
        finally:
            reader.disconnect()
    
    def test_wait_for_tag(self):
        """Test waiting for NFC tag."""
        reader = NFCReader(interface="i2c", i2c_bus=1)
        
        try:
            reader.connect()
            
            print("\nPlace an NFC tag near the reader within 5 seconds...")
            uid = reader.wait_for_tag(timeout=5.0)
            
            if uid is None:
                pytest.skip("No tag detected within timeout")
            
            assert isinstance(uid, bytes)
            assert len(uid) > 0
            print(f"Detected tag UID: {uid.hex()}")
            
        except NFCConnectionError as e:
            pytest.skip(f"PN532 not available: {e}")
        finally:
            reader.disconnect()
    
    def test_read_tag_info(self):
        """Test reading tag information."""
        reader = NFCReader(interface="i2c", i2c_bus=1)
        
        try:
            reader.connect()
            
            print("\nPlace an NFC tag near the reader within 5 seconds...")
            uid = reader.wait_for_tag(timeout=5.0)
            
            if uid is None:
                pytest.skip("No tag detected within timeout")
            
            info = reader.get_tag_info(uid=uid)
            
            assert info["present"] is True
            assert info["uid"] == uid.hex()
            assert info["uid_length"] == len(uid)
            
            print(f"Tag info: {info}")
            
        except NFCConnectionError as e:
            pytest.skip(f"PN532 not available: {e}")
        finally:
            reader.disconnect()
    
    def test_write_and_read_ndef(self):
        """Test writing and reading NDEF data."""
        reader = NFCReader(interface="i2c", i2c_bus=1)
        
        try:
            reader.connect()
            
            print("\nPlace a writable NFC tag near the reader within 5 seconds...")
            uid = reader.wait_for_tag(timeout=5.0)
            
            if uid is None:
                pytest.skip("No tag detected within timeout")
            
            # Test NDEF data (simple URI record)
            test_ndef = b"\x03\x10\xd1\x01\x0c\x55\x01example.com\xfe"
            
            # Write NDEF
            print("Writing NDEF data...")
            success = reader.write_ndef(test_ndef, uid=uid)
            assert success is True
            
            # Read back NDEF
            print("Reading NDEF data...")
            read_data = reader.read_ndef(uid=uid)
            
            assert isinstance(read_data, bytes)
            assert len(read_data) > 0
            
            print(f"Written: {test_ndef.hex()}")
            print(f"Read: {read_data[:len(test_ndef)].hex()}")
            
        except NFCConnectionError as e:
            pytest.skip(f"PN532 not available: {e}")
        except (NFCReadError, NFCWriteError) as e:
            pytest.fail(f"NFC operation failed: {e}")
        finally:
            reader.disconnect()
    
    def test_clear_tag(self):
        """Test clearing a tag."""
        reader = NFCReader(interface="i2c", i2c_bus=1)
        
        try:
            reader.connect()
            
            print("\nPlace a writable NFC tag near the reader within 5 seconds...")
            uid = reader.wait_for_tag(timeout=5.0)
            
            if uid is None:
                pytest.skip("No tag detected within timeout")
            
            # Clear tag
            print("Clearing tag...")
            success = reader.clear_tag(uid=uid)
            assert success is True
            
            print("Tag cleared successfully")
            
        except NFCConnectionError as e:
            pytest.skip(f"PN532 not available: {e}")
        except NFCWriteError as e:
            pytest.fail(f"Failed to clear tag: {e}")
        finally:
            reader.disconnect()


@pytest.mark.hardware
def test_context_manager():
    """Test NFCReader context manager."""
    reader = NFCReader(interface="i2c", i2c_bus=1)
    
    try:
        with reader.connection():
            assert reader._initialized is True
    except NFCConnectionError as e:
        pytest.skip(f"PN532 not available: {e}")


def test_invalid_interface():
    """Test invalid interface type."""
    reader = NFCReader(interface="invalid")
    
    with pytest.raises(ValueError):
        reader.connect()
