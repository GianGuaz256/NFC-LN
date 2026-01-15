"""Tests for tag operations (tag loader service)."""

import pytest
from unittest.mock import Mock, patch

from src.services.tag_loader import TagLoaderService, TagLoaderError


def test_tag_loader_initialization(mock_nfc_reader, mock_lnbits_client):
    """Test tag loader service initialization."""
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
        use_bech32=True,
    )
    
    assert service.nfc_reader == mock_nfc_reader
    assert service.lnbits_client == mock_lnbits_client


def test_load_tag_success(mock_nfc_reader, mock_lnbits_client):
    """Test successful tag loading."""
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
    )
    
    result = service.load_tag(
        amount=1000,
        title="Test Card",
        uses=1,
        timeout=5.0,
    )
    
    assert result["success"] is True
    assert result["amount"] == 1000
    assert result["uses"] == 1
    assert "link_id" in result
    assert "lnurl" in result
    assert "tag_uid" in result


def test_load_tag_no_tag_detected(mock_nfc_reader, mock_lnbits_client):
    """Test tag loading when no tag is detected."""
    mock_nfc_reader.wait_for_tag.return_value = None
    
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
    )
    
    with pytest.raises(TagLoaderError, match="No NFC tag detected"):
        service.load_tag(amount=1000, timeout=1.0)


def test_load_tag_write_failure(mock_nfc_reader, mock_lnbits_client):
    """Test tag loading when write fails."""
    mock_nfc_reader.write_ndef.return_value = False
    
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
    )
    
    with pytest.raises(TagLoaderError, match="Failed to write"):
        service.load_tag(amount=1000, timeout=5.0)


def test_read_tag_success(mock_nfc_reader, mock_lnbits_client):
    """Test successful tag reading."""
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
    )
    
    result = service.read_tag(timeout=5.0)
    
    assert result["success"] is True
    assert "tag_uid" in result
    assert "lnurl" in result
    assert "valid" in result


def test_read_tag_no_lnurl(mock_nfc_reader, mock_lnbits_client, mock_ndef_handler):
    """Test reading tag with no LNURL."""
    mock_ndef_handler.extract_lnurl.return_value = None
    
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
    )
    service.ndef_handler = mock_ndef_handler
    
    result = service.read_tag(timeout=5.0)
    
    assert result["success"] is False
    assert "error" in result


def test_clear_tag_success(mock_nfc_reader, mock_lnbits_client):
    """Test successful tag clearing."""
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
    )
    
    result = service.clear_tag(timeout=5.0)
    
    assert result["success"] is True
    assert "tag_uid" in result


def test_clear_tag_failure(mock_nfc_reader, mock_lnbits_client):
    """Test tag clearing failure."""
    mock_nfc_reader.clear_tag.return_value = False
    
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
    )
    
    with pytest.raises(TagLoaderError, match="Failed to clear"):
        service.clear_tag(timeout=5.0)


def test_get_tag_info(mock_nfc_reader, mock_lnbits_client):
    """Test getting tag information."""
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
    )
    
    info = service.get_tag_info(timeout=5.0)
    
    assert "present" in info
    assert "uid" in info


def test_verify_tag_success(mock_nfc_reader, mock_lnbits_client):
    """Test successful tag verification."""
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
    )
    
    result = service.verify_tag(link_id="test_link_123", timeout=5.0)
    
    assert result["success"] is True
    assert "verified" in result


def test_verify_tag_mismatch(mock_nfc_reader, mock_lnbits_client, mock_ndef_handler):
    """Test tag verification with LNURL mismatch."""
    mock_ndef_handler.extract_lnurl.return_value = "DIFFERENT_LNURL"
    
    service = TagLoaderService(
        nfc_reader=mock_nfc_reader,
        lnbits_client=mock_lnbits_client,
    )
    service.ndef_handler = mock_ndef_handler
    
    result = service.verify_tag(link_id="test_link_123", timeout=5.0)
    
    assert result["verified"] is False
