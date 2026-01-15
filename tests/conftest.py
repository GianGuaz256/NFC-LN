"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, MagicMock
import os

# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "hardware: marks tests that require physical PN532 hardware"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests that require external services (LNbits)"
    )
    config.addinivalue_line(
        "markers", "e2e: marks end-to-end tests"
    )


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    from src.config import Config
    
    # Set test environment variables
    os.environ["LNBITS_URL"] = "https://test.lnbits.com"
    os.environ["LNBITS_API_KEY"] = "test_api_key_12345"
    os.environ["LNBITS_WALLET_ID"] = "test_wallet_id"
    os.environ["NFC_INTERFACE"] = "i2c"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    config = Config()
    return config


@pytest.fixture
def mock_nfc_reader():
    """Mock NFC reader for testing."""
    from src.nfc.reader import NFCReader
    
    reader = Mock(spec=NFCReader)
    reader._initialized = True
    reader.wait_for_tag = Mock(return_value=bytes.fromhex("04123456789ABC"))
    reader.read_ndef = Mock(return_value=b"\x03\x10\xd1\x01\x0c\x55\x01example.com")
    reader.write_ndef = Mock(return_value=True)
    reader.clear_tag = Mock(return_value=True)
    reader.get_tag_info = Mock(return_value={
        "present": True,
        "uid": "04123456789ABC",
        "uid_length": 7,
        "type": "NTAG",
    })
    
    return reader


@pytest.fixture
def mock_lnbits_client():
    """Mock LNbits client for testing."""
    from src.lnbits.client import LNbitsClient
    
    client = Mock(spec=LNbitsClient)
    client.check_connection = Mock(return_value=True)
    client.get_wallet_balance = Mock(return_value=100000000)  # 100k sats in msat
    client.get_wallet_info = Mock(return_value={
        "id": "test_wallet",
        "name": "Test Wallet",
        "balance": 100000000,
    })
    client.create_withdraw_link = Mock(return_value={
        "id": "test_link_123",
        "lnurl": "LNURL1DP68GURN8GHJ7MRWW4EXCTNXD9SHG6NPVCHXXMMD9AKXUATJDSKHQCTE8AEK2UMND9HKU0FHXGCNXV3JXGMNXV3JXGCNXV3JXGCNXV3JXGCNXV3JXGCNXV3JXGCNXV3JXGCNXV3JXGCNXV3JXGCNXV3JXGCNXV3JXGCNXV3JXGCNXV3JX",
        "url": "https://test.lnbits.com/withdraw/api/v1/lnurl/test_link_123",
    })
    client.get_withdraw_link = Mock(return_value={
        "id": "test_link_123",
        "title": "Test Link",
        "max_withdrawable": 1000000,
        "uses": 1,
        "used": 0,
    })
    client.list_withdraw_links = Mock(return_value=[])
    client.delete_withdraw_link = Mock(return_value=True)
    
    return client


@pytest.fixture
def mock_ndef_handler():
    """Mock NDEF handler for testing."""
    from src.nfc.ndef import NDEFHandler
    
    handler = Mock(spec=NDEFHandler)
    handler.create_uri_record = Mock(return_value=b"\x03\x10\xd1\x01\x0c\x55\x01example.com")
    handler.create_lnurl_record = Mock(return_value=b"\x03\x10\xd1\x01\x0c\x55\x01example.com")
    handler.extract_uri = Mock(return_value="https://example.com")
    handler.extract_lnurl = Mock(return_value="LNURL1...")
    handler.validate_ndef_message = Mock(return_value=True)
    
    return handler


@pytest.fixture
def mock_lnurl_handler():
    """Mock LNURL handler for testing."""
    from src.lnbits.lnurl import LNURLHandler
    
    handler = Mock(spec=LNURLHandler)
    handler.encode = Mock(return_value="LNURL1...")
    handler.decode = Mock(return_value="https://example.com")
    handler.validate = Mock(return_value=True)
    handler.is_withdraw_url = Mock(return_value=True)
    handler.get_lnurl_params = Mock(return_value={
        "valid": True,
        "type": "withdraw",
        "url": "https://example.com",
    })
    
    return handler


@pytest.fixture
def sample_lnurl():
    """Sample LNURL for testing."""
    return "LNURL1DP68GURN8GHJ7MRWW4EXCTNXD9SHG6NPVCHXXMMD9AKXUATJDSKHQCTE8AEK2UMND9HKU"


@pytest.fixture
def sample_tag_uid():
    """Sample tag UID for testing."""
    return bytes.fromhex("04123456789ABC")


@pytest.fixture
def sample_ndef_data():
    """Sample NDEF data for testing."""
    # NDEF message with URI record
    return b"\x03\x10\xd1\x01\x0c\x55\x01example.com\xfe"
