"""Tests for LNbits API client."""

import pytest
from unittest.mock import Mock, patch
import httpx

from src.lnbits.client import LNbitsClient, LNbitsConnectionError, LNbitsAPIError


def test_client_initialization():
    """Test LNbits client initialization."""
    client = LNbitsClient(
        base_url="https://test.lnbits.com",
        api_key="test_key",
        wallet_id="test_wallet",
    )
    
    assert client.base_url == "https://test.lnbits.com"
    assert client.api_key == "test_key"
    assert client.wallet_id == "test_wallet"


def test_client_context_manager():
    """Test LNbits client context manager."""
    with LNbitsClient(
        base_url="https://test.lnbits.com",
        api_key="test_key",
    ) as client:
        assert client is not None


@patch('httpx.Client.get')
def test_check_connection_success(mock_get):
    """Test successful connection check."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"balance": 100000}
    mock_get.return_value = mock_response
    
    client = LNbitsClient(
        base_url="https://test.lnbits.com",
        api_key="test_key",
    )
    
    result = client.check_connection()
    assert result is True


@patch('httpx.Client.get')
def test_check_connection_failure(mock_get):
    """Test failed connection check."""
    mock_get.side_effect = httpx.HTTPError("Connection failed")
    
    client = LNbitsClient(
        base_url="https://test.lnbits.com",
        api_key="test_key",
    )
    
    with pytest.raises(LNbitsConnectionError):
        client.check_connection()


@patch('httpx.Client.get')
def test_get_wallet_balance(mock_get):
    """Test getting wallet balance."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"balance": 100000000}
    mock_get.return_value = mock_response
    
    client = LNbitsClient(
        base_url="https://test.lnbits.com",
        api_key="test_key",
    )
    
    balance = client.get_wallet_balance()
    assert balance == 100000000


@patch('httpx.Client.post')
def test_create_withdraw_link(mock_post):
    """Test creating withdraw link."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "test_link_123",
        "lnurl": "LNURL1...",
        "url": "https://test.lnbits.com/withdraw/test_link_123",
    }
    mock_post.return_value = mock_response
    
    client = LNbitsClient(
        base_url="https://test.lnbits.com",
        api_key="test_key",
    )
    
    result = client.create_withdraw_link(
        amount=1000,
        title="Test Link",
        uses=1,
    )
    
    assert result["id"] == "test_link_123"
    assert "lnurl" in result


@patch('httpx.Client.get')
def test_get_withdraw_link(mock_get):
    """Test getting withdraw link details."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "test_link_123",
        "title": "Test Link",
        "max_withdrawable": 1000000,
    }
    mock_get.return_value = mock_response
    
    client = LNbitsClient(
        base_url="https://test.lnbits.com",
        api_key="test_key",
    )
    
    result = client.get_withdraw_link("test_link_123")
    assert result["id"] == "test_link_123"


@patch('httpx.Client.delete')
def test_delete_withdraw_link(mock_delete):
    """Test deleting withdraw link."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_delete.return_value = mock_response
    
    client = LNbitsClient(
        base_url="https://test.lnbits.com",
        api_key="test_key",
    )
    
    result = client.delete_withdraw_link("test_link_123")
    assert result is True


@pytest.mark.integration
def test_real_lnbits_connection():
    """Test connection to real LNbits instance (requires LNBITS_URL and LNBITS_API_KEY env vars)."""
    import os
    
    lnbits_url = os.getenv("LNBITS_URL")
    lnbits_api_key = os.getenv("LNBITS_API_KEY")
    
    if not lnbits_url or not lnbits_api_key:
        pytest.skip("LNBITS_URL and LNBITS_API_KEY not set")
    
    client = LNbitsClient(
        base_url=lnbits_url,
        api_key=lnbits_api_key,
    )
    
    try:
        # Test connection
        client.check_connection()
        
        # Get wallet info
        wallet_info = client.get_wallet_info()
        assert "balance" in wallet_info
        
        # Get balance
        balance = client.get_wallet_balance()
        assert isinstance(balance, int)
        
    finally:
        client.close()
