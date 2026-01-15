"""End-to-end integration tests."""

import pytest
import time
from unittest.mock import Mock

from src.main import Application
from src.config import Config


@pytest.mark.e2e
class TestEndToEnd:
    """End-to-end tests requiring full system."""
    
    def test_application_initialization(self, mock_config):
        """Test application initialization."""
        app = Application(config=mock_config)
        
        # Mock the components to avoid hardware requirements
        app.nfc_reader = Mock()
        app.nfc_reader.connect = Mock()
        app.nfc_reader._initialized = True
        
        app.lnbits_client = Mock()
        app.lnbits_client.check_connection = Mock(return_value=True)
        app.lnbits_client.get_wallet_info = Mock(return_value={
            "balance": 100000000,
            "name": "Test Wallet"
        })
        
        try:
            app.initialize()
            assert app._initialized is True
        finally:
            app.cleanup()
    
    def test_application_context_manager(self, mock_config):
        """Test application context manager."""
        app = Application(config=mock_config)
        
        # Mock components
        app.nfc_reader = Mock()
        app.nfc_reader.connect = Mock()
        app.nfc_reader.disconnect = Mock()
        app.nfc_reader._initialized = True
        
        app.lnbits_client = Mock()
        app.lnbits_client.check_connection = Mock(return_value=True)
        app.lnbits_client.get_wallet_info = Mock(return_value={"balance": 100000000})
        app.lnbits_client.close = Mock()
        
        with app:
            assert app._initialized is True
    
    @pytest.mark.integration
    @pytest.mark.hardware
    def test_full_tag_load_cycle(self):
        """Test complete tag loading cycle (requires hardware and LNbits)."""
        import os
        
        # Check for required environment variables
        if not os.getenv("LNBITS_URL") or not os.getenv("LNBITS_API_KEY"):
            pytest.skip("LNBITS_URL and LNBITS_API_KEY not set")
        
        app = Application()
        
        try:
            app.initialize()
            
            print("\n=== Full Tag Load Test ===")
            print("Place a writable NFC tag near the reader within 10 seconds...")
            
            # Load tag
            result = app.tag_loader.load_tag(
                amount=100,  # 100 sats
                title="E2E Test Card",
                uses=1,
                timeout=10.0,
            )
            
            assert result["success"] is True
            assert result["amount"] == 100
            
            print(f"✓ Tag loaded: {result['tag_uid']}")
            print(f"  Link ID: {result['link_id']}")
            
            # Wait a moment
            time.sleep(1)
            
            # Read tag back
            print("\nPlace the same tag near the reader again...")
            read_result = app.tag_loader.read_tag(timeout=10.0)
            
            assert read_result["success"] is True
            assert read_result["lnurl"] == result["lnurl"]
            
            print(f"✓ Tag read successfully")
            print(f"  LNURL matches: {read_result['lnurl'] == result['lnurl']}")
            
            # Clean up: delete the link
            app.lnbits_client.delete_withdraw_link(result["link_id"])
            print(f"\n✓ Cleaned up link: {result['link_id']}")
            
        finally:
            app.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.hardware
    def test_payment_processor_single_tag(self):
        """Test payment processor with single tag (requires hardware)."""
        import os
        
        if not os.getenv("LNBITS_URL") or not os.getenv("LNBITS_API_KEY"):
            pytest.skip("LNBITS_URL and LNBITS_API_KEY not set")
        
        app = Application()
        
        try:
            app.initialize()
            
            print("\n=== Payment Processor Test ===")
            print("Place an NFC tag with LNURL near the reader within 10 seconds...")
            
            # Process single tag
            result = app.payment_processor.process_tag(timeout=10.0)
            
            if result is None:
                pytest.skip("No tag detected within timeout")
            
            assert "success" in result
            assert "tag_uid" in result
            
            if result["success"]:
                print(f"✓ Payment processed: {result['tag_uid']}")
                print(f"  LNURL: {result.get('lnurl', 'N/A')[:50]}...")
            else:
                print(f"✗ Payment failed: {result.get('error')}")
            
        finally:
            app.cleanup()
    
    def test_config_validation(self):
        """Test configuration validation."""
        import os
        
        # Set valid config
        os.environ["LNBITS_URL"] = "https://test.lnbits.com"
        os.environ["LNBITS_API_KEY"] = "test_key"
        
        config = Config()
        assert config.lnbits_url == "https://test.lnbits.com"
        assert config.lnbits_api_key == "test_key"
    
    def test_config_invalid_url(self):
        """Test configuration with invalid URL."""
        import os
        
        os.environ["LNBITS_URL"] = "not-a-url"
        os.environ["LNBITS_API_KEY"] = "test_key"
        
        with pytest.raises(Exception):
            Config()
    
    def test_config_logging_setup(self, mock_config, tmp_path):
        """Test logging configuration."""
        mock_config.log_file = str(tmp_path / "test.log")
        mock_config.setup_logging()
        
        # Check that log file was created
        assert (tmp_path / "test.log").exists()


@pytest.mark.e2e
@pytest.mark.integration
def test_lnbits_withdraw_link_lifecycle():
    """Test complete lifecycle of withdraw link (requires LNbits)."""
    import os
    
    lnbits_url = os.getenv("LNBITS_URL")
    lnbits_api_key = os.getenv("LNBITS_API_KEY")
    
    if not lnbits_url or not lnbits_api_key:
        pytest.skip("LNBITS_URL and LNBITS_API_KEY not set")
    
    from src.lnbits.client import LNbitsClient
    
    client = LNbitsClient(
        base_url=lnbits_url,
        api_key=lnbits_api_key,
    )
    
    try:
        # Create link
        print("\nCreating withdraw link...")
        link = client.create_withdraw_link(
            amount=50,
            title="E2E Test Link",
            uses=1,
        )
        
        assert "id" in link
        assert "lnurl" in link
        link_id = link["id"]
        
        print(f"✓ Created link: {link_id}")
        
        # Get link details
        print("Fetching link details...")
        details = client.get_withdraw_link(link_id)
        assert details["id"] == link_id
        
        print(f"✓ Retrieved link details")
        
        # List links
        print("Listing all links...")
        links = client.list_withdraw_links()
        assert any(l["id"] == link_id for l in links)
        
        print(f"✓ Found link in list ({len(links)} total)")
        
        # Delete link
        print("Deleting link...")
        success = client.delete_withdraw_link(link_id)
        assert success is True
        
        print(f"✓ Deleted link")
        
    finally:
        client.close()
