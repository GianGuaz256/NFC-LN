"""Main entry point for LN-NFC application."""

import logging
import sys
from typing import Optional

from .config import load_config, Config
from .nfc.reader import NFCReader
from .lnbits.client import LNbitsClient
from .services.tag_loader import TagLoaderService
from .services.payment_processor import PaymentProcessorService

logger = logging.getLogger(__name__)


class Application:
    """Main application class for LN-NFC."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize application.
        
        Args:
            config: Optional configuration (will load from env if not provided)
        """
        # Load configuration
        if config is None:
            config = load_config()
        
        self.config = config
        
        # Setup logging
        self.config.setup_logging()
        
        logger.info("=" * 60)
        logger.info("LN-NFC Application Starting")
        logger.info("=" * 60)
        logger.info(f"Configuration: {self.config}")
        
        # Initialize components
        self.nfc_reader: Optional[NFCReader] = None
        self.lnbits_client: Optional[LNbitsClient] = None
        self.tag_loader: Optional[TagLoaderService] = None
        self.payment_processor: Optional[PaymentProcessorService] = None
        
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize all application components."""
        if self._initialized:
            logger.warning("Application already initialized")
            return
        
        try:
            logger.info("Initializing components...")
            
            # Initialize NFC Reader
            logger.info(f"Initializing NFC reader ({self.config.nfc_interface})...")
            self.nfc_reader = NFCReader(
                interface=self.config.nfc_interface,
                i2c_bus=self.config.nfc_i2c_bus,
                spi_bus=self.config.nfc_spi_bus,
                spi_device=self.config.nfc_spi_device,
            )
            
            # Connect to NFC reader
            self.nfc_reader.connect()
            logger.info("NFC reader connected successfully")
            
            # Initialize LNbits Client
            logger.info("Initializing LNbits client...")
            self.lnbits_client = LNbitsClient(
                base_url=self.config.lnbits_url,
                api_key=self.config.lnbits_api_key,
                wallet_id=self.config.lnbits_wallet_id,
            )
            
            # Check LNbits connection
            self.lnbits_client.check_connection()
            logger.info("LNbits client connected successfully")
            
            # Get wallet info
            try:
                wallet_info = self.lnbits_client.get_wallet_info()
                balance = wallet_info.get("balance", 0)
                logger.info(f"Wallet balance: {balance // 1000} sats")
            except Exception as e:
                logger.warning(f"Could not fetch wallet info: {e}")
            
            # Initialize Tag Loader Service
            logger.info("Initializing tag loader service...")
            self.tag_loader = TagLoaderService(
                nfc_reader=self.nfc_reader,
                lnbits_client=self.lnbits_client,
                use_bech32=self.config.lnurl_use_bech32,
            )
            
            # Initialize Payment Processor Service
            logger.info("Initializing payment processor service...")
            self.payment_processor = PaymentProcessorService(
                nfc_reader=self.nfc_reader,
                rate_limit_seconds=self.config.rate_limit_seconds,
            )
            
            self._initialized = True
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            self.cleanup()
            raise
    
    def cleanup(self) -> None:
        """Clean up application resources."""
        logger.info("Cleaning up application resources...")
        
        if self.lnbits_client:
            try:
                self.lnbits_client.close()
            except Exception as e:
                logger.error(f"Error closing LNbits client: {e}")
        
        if self.nfc_reader:
            try:
                self.nfc_reader.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting NFC reader: {e}")
        
        logger.info("Cleanup complete")
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
    
    def run_daemon(self) -> None:
        """Run application in daemon mode (continuous payment processing)."""
        if not self._initialized:
            self.initialize()
        
        logger.info("Starting daemon mode...")
        
        def payment_callback(result: dict) -> None:
            """Callback for payment processing."""
            if result.get("success"):
                logger.info(f"✓ Payment processed: {result.get('tag_uid')}")
                logger.info(f"  LNURL: {result.get('lnurl')}")
            else:
                logger.warning(f"✗ Payment failed: {result.get('error')}")
        
        try:
            self.payment_processor.run_daemon(
                callback=payment_callback,
                poll_interval=self.config.poll_interval,
            )
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user")
        except Exception as e:
            logger.error(f"Daemon error: {e}")
            raise
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    try:
        app = Application()
        app.run_daemon()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
