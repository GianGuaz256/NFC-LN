"""Payment processor service for handling NFC tag payments."""

import logging
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from ..nfc.reader import NFCReader
from ..nfc.ndef import NDEFHandler
from ..lnbits.lnurl import LNURLHandler

logger = logging.getLogger(__name__)


class PaymentProcessorError(Exception):
    """Base exception for payment processor errors."""
    pass


class PaymentProcessorService:
    """
    Service for processing payments from NFC tags.
    
    Runs in daemon mode, continuously listening for tags and processing payments.
    """
    
    def __init__(
        self,
        nfc_reader: NFCReader,
        rate_limit_seconds: float = 2.0,
    ):
        """
        Initialize payment processor service.
        
        Args:
            nfc_reader: NFC reader instance
            rate_limit_seconds: Minimum time between processing same tag
        """
        self.nfc_reader = nfc_reader
        self.ndef_handler = NDEFHandler()
        self.lnurl_handler = LNURLHandler()
        self.rate_limit_seconds = rate_limit_seconds
        
        # Track recently processed tags to prevent duplicates
        self._processed_tags: Dict[str, float] = {}
        
        logger.info("PaymentProcessorService initialized")
    
    def process_tag(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Process a single NFC tag payment.
        
        Args:
            timeout: Timeout for waiting for tag in seconds
        
        Returns:
            Dictionary with payment details if tag processed, None if no tag
        """
        try:
            # Wait for tag
            uid = self.nfc_reader.wait_for_tag(timeout=timeout)
            
            if uid is None:
                return None
            
            uid_hex = uid.hex()
            current_time = time.time()
            
            # Check rate limit
            if uid_hex in self._processed_tags:
                last_processed = self._processed_tags[uid_hex]
                time_since = current_time - last_processed
                
                if time_since < self.rate_limit_seconds:
                    logger.debug(f"Tag {uid_hex} rate limited (last seen {time_since:.1f}s ago)")
                    return None
            
            logger.info(f"Processing tag: {uid_hex}")
            
            # Read NDEF data
            try:
                ndef_data = self.nfc_reader.read_ndef(uid=uid)
            except Exception as e:
                logger.error(f"Failed to read tag {uid_hex}: {e}")
                return {
                    "success": False,
                    "tag_uid": uid_hex,
                    "error": f"Failed to read tag: {e}",
                    "timestamp": datetime.now().isoformat(),
                }
            
            # Extract LNURL
            lnurl = self.ndef_handler.extract_lnurl(ndef_data)
            
            if not lnurl:
                logger.warning(f"No LNURL found on tag {uid_hex}")
                return {
                    "success": False,
                    "tag_uid": uid_hex,
                    "error": "No LNURL found on tag",
                    "timestamp": datetime.now().isoformat(),
                }
            
            # Validate LNURL
            if not self.lnurl_handler.validate(lnurl):
                logger.warning(f"Invalid LNURL on tag {uid_hex}")
                return {
                    "success": False,
                    "tag_uid": uid_hex,
                    "lnurl": lnurl,
                    "error": "Invalid LNURL",
                    "timestamp": datetime.now().isoformat(),
                }
            
            # Update processed tags tracking
            self._processed_tags[uid_hex] = current_time
            
            # Clean up old entries (older than 1 hour)
            self._cleanup_processed_tags(max_age=3600)
            
            result = {
                "success": True,
                "tag_uid": uid_hex,
                "lnurl": lnurl,
                "timestamp": datetime.now().isoformat(),
            }
            
            # Get LNURL parameters
            params = self.lnurl_handler.get_lnurl_params(lnurl)
            result["lnurl_params"] = params
            
            logger.info(f"Successfully processed tag {uid_hex}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing tag: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    def run_daemon(
        self,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        poll_interval: float = 0.5,
    ) -> None:
        """
        Run payment processor in daemon mode.
        
        Continuously listens for NFC tags and processes payments.
        
        Args:
            callback: Optional callback function called with payment details
            poll_interval: Polling interval in seconds
        """
        logger.info("Starting payment processor daemon...")
        logger.info(f"Poll interval: {poll_interval}s, Rate limit: {self.rate_limit_seconds}s")
        
        try:
            while True:
                try:
                    # Process tag
                    result = self.process_tag(timeout=poll_interval)
                    
                    if result is not None:
                        # Log result
                        if result.get("success"):
                            logger.info(f"Payment processed: {result.get('tag_uid')}")
                        else:
                            logger.warning(f"Payment failed: {result.get('error')}")
                        
                        # Call callback if provided
                        if callback:
                            try:
                                callback(result)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"Error in daemon loop: {e}")
                    time.sleep(1)  # Back off on error
                
        except KeyboardInterrupt:
            logger.info("Payment processor daemon stopped by user")
        except Exception as e:
            logger.error(f"Payment processor daemon crashed: {e}")
            raise
    
    def _cleanup_processed_tags(self, max_age: float = 3600) -> None:
        """
        Clean up old entries from processed tags tracking.
        
        Args:
            max_age: Maximum age in seconds
        """
        current_time = time.time()
        to_remove = []
        
        for uid, timestamp in self._processed_tags.items():
            if current_time - timestamp > max_age:
                to_remove.append(uid)
        
        for uid in to_remove:
            del self._processed_tags[uid]
        
        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} old tag entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get payment processor statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "tracked_tags": len(self._processed_tags),
            "rate_limit_seconds": self.rate_limit_seconds,
        }
    
    def reset_rate_limits(self) -> None:
        """Reset rate limit tracking (allow all tags to be processed again)."""
        count = len(self._processed_tags)
        self._processed_tags.clear()
        logger.info(f"Reset rate limits for {count} tag(s)")
    
    def is_tag_rate_limited(self, uid: str) -> bool:
        """
        Check if a tag is currently rate limited.
        
        Args:
            uid: Tag UID (hex string)
        
        Returns:
            True if rate limited
        """
        if uid not in self._processed_tags:
            return False
        
        last_processed = self._processed_tags[uid]
        time_since = time.time() - last_processed
        
        return time_since < self.rate_limit_seconds
