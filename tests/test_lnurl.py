"""Tests for LNURL handling."""

import pytest
from src.lnbits.lnurl import LNURLHandler, LNURLError


def test_lnurl_handler_initialization():
    """Test LNURL handler initialization."""
    handler = LNURLHandler(use_bech32=True)
    assert handler.use_bech32 is True
    
    handler = LNURLHandler(use_bech32=False)
    assert handler.use_bech32 is False


def test_encode_plain_url():
    """Test encoding plain URL (no bech32)."""
    handler = LNURLHandler(use_bech32=False)
    url = "https://example.com/withdraw/123"
    
    result = handler.encode(url)
    assert result == url


def test_encode_bech32():
    """Test encoding URL to bech32 LNURL."""
    handler = LNURLHandler(use_bech32=True)
    url = "https://example.com/withdraw"
    
    result = handler.encode(url)
    assert result.upper().startswith("LNURL")


def test_decode_plain_url():
    """Test decoding plain URL."""
    handler = LNURLHandler()
    url = "https://example.com/withdraw/123"
    
    result = handler.decode(url)
    assert result == url


def test_decode_bech32():
    """Test decoding bech32 LNURL."""
    handler = LNURLHandler()
    
    # Sample LNURL (encodes "https://example.com")
    lnurl = "lnurl1dp68gurn8ghj7um9wfmxjcm99e3k7mf0v9cxj0m385ekvcenxc6r2c35xvukxefcv5mkvv34x5ekzd3ev56nyd3hxqurzepexejxxepnxscrvwfnv9nxzcn9xq6xyefhvgcxxcmyxymnserxfq5fns"
    
    result = handler.decode(lnurl)
    assert result.startswith("https://")


def test_decode_with_lightning_prefix():
    """Test decoding LNURL with lightning: prefix."""
    handler = LNURLHandler()
    lnurl = "lightning:lnurl1dp68gurn8ghj7um9wfmxjcm99e3k7mf0v9cxj0m385ekvcenxc6r2c35xvukxefcv5mkvv34x5ekzd3ev56nyd3hxqurzepexejxxepnxscrvwfnv9nxzcn9xq6xyefhvgcxxcmyxymnserxfq5fns"
    
    result = handler.decode(lnurl)
    assert result.startswith("https://")


def test_validate_valid_url():
    """Test validating valid URL."""
    handler = LNURLHandler()
    url = "https://example.com/withdraw/123"
    
    result = handler.validate(url)
    assert result is True


def test_validate_invalid_url():
    """Test validating invalid URL."""
    handler = LNURLHandler()
    
    result = handler.validate("not-a-url")
    assert result is False


def test_is_withdraw_url():
    """Test checking if URL is withdraw URL."""
    handler = LNURLHandler()
    
    # Valid withdraw URLs
    assert handler.is_withdraw_url("https://example.com/withdraw/123") is True
    assert handler.is_withdraw_url("https://example.com/lnurl/withdraw") is True
    
    # Invalid withdraw URLs
    assert handler.is_withdraw_url("https://example.com/pay/123") is False


def test_get_lnurl_params():
    """Test extracting LNURL parameters."""
    handler = LNURLHandler()
    url = "https://example.com/withdraw/123"
    
    params = handler.get_lnurl_params(url)
    
    assert params["valid"] is True
    assert params["url"] == url
    assert params["scheme"] == "https"
    assert params["host"] == "example.com"


def test_format_for_display():
    """Test formatting LNURL for display."""
    handler = LNURLHandler()
    
    # Short LNURL
    short = "LNURL123"
    assert handler.format_for_display(short, max_length=50) == short
    
    # Long LNURL
    long = "LNURL" + "X" * 100
    formatted = handler.format_for_display(long, max_length=50)
    assert len(formatted) <= 50
    assert "..." in formatted


def test_create_lightning_uri():
    """Test creating lightning: URI."""
    handler = LNURLHandler(use_bech32=True)
    url = "https://example.com/withdraw"
    
    result = handler.create_lightning_uri(url)
    assert result.startswith("lightning:LNURL")


def test_extract_from_uri():
    """Test extracting LNURL from lightning: URI."""
    handler = LNURLHandler()
    uri = "lightning:LNURL1DP68GURN..."
    
    result = handler.extract_from_uri(uri)
    assert result == "LNURL1DP68GURN..."
    
    # Non-lightning URI
    assert handler.extract_from_uri("https://example.com") is None


def test_round_trip_encoding():
    """Test encoding and decoding round trip."""
    handler = LNURLHandler(use_bech32=True)
    original_url = "https://example.com/withdraw/test123"
    
    # Encode
    lnurl = handler.encode(original_url)
    assert lnurl.upper().startswith("LNURL")
    
    # Decode
    decoded_url = handler.decode(lnurl)
    assert decoded_url == original_url
