"""Tag loader service for creating and writing LNURL-withdraw tags."""

import logging
from typing import Optional, Dict, Any

from ..nfc.reader import NFCReader
from ..nfc.ndef import NDEFHandler
from ..lnbits.client import LNbitsClient
from ..lnbits.lnurl import LNURLHandler

logger = logging.getLogger(__name__)


class TagLoaderError(Exception):
    """Base exception for tag loader errors."""
    pass


class TagLoaderService:
    """
    Service for loading NFC tags with LNURL-withdraw links.
    
    Coordinates between LNbits API, LNURL encoding, and NFC writing.
    """
    
    def __init__(
        self,
        nfc_reader: NFCReader,
        lnbits_client: LNbitsClient,
        use_bech32: bool = True,
    ):
        """
        Initialize tag loader service.
        
        Args:
            nfc_reader: NFC reader instance
            lnbits_client: LNbits client instance
            use_bech32: Whether to use bech32 LNURL encoding
        """
        self.nfc_reader = nfc_reader
        self.lnbits_client = lnbits_client
        self.ndef_handler = NDEFHandler()
        self.lnurl_handler = LNURLHandler(use_bech32=use_bech32)
        
        logger.info("TagLoaderService initialized")
    
    def load_tag(
        self,
        amount: int,
        title: str = "Lightning Gift Card",
        uses: int = 1,
        wait_time: int = 1,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Load an NFC tag with a new LNURL-withdraw link.
        
        Args:
            amount: Amount in satoshis
            title: Title/description for the link
            uses: Number of times the link can be used
            wait_time: Wait time between uses in seconds
            timeout: Timeout for waiting for tag in seconds
        
        Returns:
            Dictionary with operation details:
                - success: bool
                - link_id: str
                - lnurl: str
                - amount: int
                - tag_uid: str
        
        Raises:
            TagLoaderError: If loading fails
        """
        try:
            logger.info(f"Loading tag with {amount} sats ({uses} use(s))...")
            
            # Step 1: Create withdraw link in LNbits
            logger.debug("Creating withdraw link in LNbits...")
            link_data = self.lnbits_client.create_withdraw_link(
                amount=amount,
                title=title,
                uses=uses,
                wait_time=wait_time,
            )
            
            link_id = link_data.get("id")
            lnurl = link_data.get("lnurl")
            
            if not lnurl:
                raise TagLoaderError("No LNURL returned from LNbits")
            
            logger.info(f"Created withdraw link: {link_id}")
            
            # Step 2: Encode LNURL as NDEF message
            logger.debug("Encoding LNURL as NDEF...")
            ndef_data = self.ndef_handler.create_lnurl_record(lnurl)
            
            # Step 3: Wait for NFC tag
            logger.info(f"Waiting for NFC tag (timeout: {timeout}s)...")
            uid = self.nfc_reader.wait_for_tag(timeout=timeout)
            
            if uid is None:
                # Clean up: delete the created link
                logger.warning("No tag detected, cleaning up...")
                try:
                    self.lnbits_client.delete_withdraw_link(link_id)
                except Exception as e:
                    logger.error(f"Failed to clean up link: {e}")
                
                raise TagLoaderError("No NFC tag detected within timeout")
            
            # Step 4: Write NDEF to tag
            logger.info(f"Writing LNURL to tag (UID: {uid.hex()})...")
            success = self.nfc_reader.write_ndef(ndef_data, uid=uid)
            
            if not success:
                raise TagLoaderError("Failed to write NDEF to tag")
            
            # Step 5: Verify write
            logger.debug("Verifying tag write...")
            try:
                read_data = self.nfc_reader.read_ndef(uid=uid)
                read_lnurl = self.ndef_handler.extract_lnurl(read_data)
                
                if read_lnurl and read_lnurl.lower() == lnurl.lower():
                    logger.info("Tag verification successful!")
                else:
                    logger.warning("Tag verification failed - LNURL mismatch")
            except Exception as e:
                logger.warning(f"Tag verification failed: {e}")
            
            result = {
                "success": True,
                "link_id": link_id,
                "lnurl": lnurl,
                "amount": amount,
                "uses": uses,
                "tag_uid": uid.hex(),
                "title": title,
            }
            
            logger.info(f"Successfully loaded tag {uid.hex()} with {amount} sats")
            return result
            
        except Exception as e:
            logger.error(f"Failed to load tag: {e}")
            raise TagLoaderError(f"Failed to load tag: {e}")
    
    def read_tag(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Read LNURL from an NFC tag.
        
        Args:
            timeout: Timeout for waiting for tag in seconds
        
        Returns:
            Dictionary with tag information:
                - success: bool
                - tag_uid: str
                - lnurl: str
                - valid: bool
        
        Raises:
            TagLoaderError: If reading fails
        """
        try:
            logger.info(f"Waiting for NFC tag to read (timeout: {timeout}s)...")
            
            # Wait for tag
            uid = self.nfc_reader.wait_for_tag(timeout=timeout)
            
            if uid is None:
                raise TagLoaderError("No NFC tag detected within timeout")
            
            logger.info(f"Reading tag (UID: {uid.hex()})...")
            
            # Read NDEF data
            ndef_data = self.nfc_reader.read_ndef(uid=uid)
            
            # Extract LNURL
            lnurl = self.ndef_handler.extract_lnurl(ndef_data)
            
            if not lnurl:
                logger.warning("No LNURL found on tag")
                return {
                    "success": False,
                    "tag_uid": uid.hex(),
                    "error": "No LNURL found on tag",
                }
            
            # Validate LNURL
            valid = self.lnurl_handler.validate(lnurl)
            
            result = {
                "success": True,
                "tag_uid": uid.hex(),
                "lnurl": lnurl,
                "valid": valid,
            }
            
            # Get LNURL parameters
            if valid:
                params = self.lnurl_handler.get_lnurl_params(lnurl)
                result["params"] = params
            
            logger.info(f"Successfully read LNURL from tag {uid.hex()}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to read tag: {e}")
            raise TagLoaderError(f"Failed to read tag: {e}")
    
    def clear_tag(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Clear/format an NFC tag.
        
        Args:
            timeout: Timeout for waiting for tag in seconds
        
        Returns:
            Dictionary with operation result
        
        Raises:
            TagLoaderError: If clearing fails
        """
        try:
            logger.info(f"Waiting for NFC tag to clear (timeout: {timeout}s)...")
            
            # Wait for tag
            uid = self.nfc_reader.wait_for_tag(timeout=timeout)
            
            if uid is None:
                raise TagLoaderError("No NFC tag detected within timeout")
            
            logger.info(f"Clearing tag (UID: {uid.hex()})...")
            
            # Clear tag
            success = self.nfc_reader.clear_tag(uid=uid)
            
            if not success:
                raise TagLoaderError("Failed to clear tag")
            
            result = {
                "success": True,
                "tag_uid": uid.hex(),
            }
            
            logger.info(f"Successfully cleared tag {uid.hex()}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to clear tag: {e}")
            raise TagLoaderError(f"Failed to clear tag: {e}")
    
    def get_tag_info(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Get information about an NFC tag.
        
        Args:
            timeout: Timeout for waiting for tag in seconds
        
        Returns:
            Dictionary with tag information
        
        Raises:
            TagLoaderError: If reading fails
        """
        try:
            logger.info(f"Waiting for NFC tag (timeout: {timeout}s)...")
            
            # Wait for tag
            uid = self.nfc_reader.wait_for_tag(timeout=timeout)
            
            if uid is None:
                raise TagLoaderError("No NFC tag detected within timeout")
            
            # Get basic tag info
            info = self.nfc_reader.get_tag_info(uid=uid)
            
            # Try to read NDEF data
            try:
                ndef_data = self.nfc_reader.read_ndef(uid=uid)
                ndef_info = self.ndef_handler.get_message_info(ndef_data)
                info["ndef"] = ndef_info
                
                # Try to extract LNURL
                lnurl = self.ndef_handler.extract_lnurl(ndef_data)
                if lnurl:
                    info["lnurl"] = lnurl
                    info["lnurl_valid"] = self.lnurl_handler.validate(lnurl)
            except Exception as e:
                logger.debug(f"Could not read NDEF data: {e}")
                info["ndef_error"] = str(e)
            
            logger.info(f"Retrieved info for tag {uid.hex()}")
            return info
            
        except Exception as e:
            logger.error(f"Failed to get tag info: {e}")
            raise TagLoaderError(f"Failed to get tag info: {e}")
    
    def verify_tag(self, link_id: str, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Verify that a tag contains the expected LNURL for a given link ID.
        
        Args:
            link_id: LNbits withdraw link ID
            timeout: Timeout for waiting for tag in seconds
        
        Returns:
            Dictionary with verification result
        
        Raises:
            TagLoaderError: If verification fails
        """
        try:
            logger.info(f"Verifying tag for link {link_id}...")
            
            # Get expected LNURL from LNbits
            link_data = self.lnbits_client.get_withdraw_link(link_id)
            expected_lnurl = link_data.get("lnurl")
            
            if not expected_lnurl:
                raise TagLoaderError("Could not retrieve LNURL from LNbits")
            
            # Read tag
            tag_data = self.read_tag(timeout=timeout)
            
            if not tag_data.get("success"):
                return {
                    "success": False,
                    "verified": False,
                    "error": tag_data.get("error", "Failed to read tag"),
                }
            
            tag_lnurl = tag_data.get("lnurl")
            
            # Compare LNURLs
            verified = tag_lnurl and tag_lnurl.lower() == expected_lnurl.lower()
            
            result = {
                "success": True,
                "verified": verified,
                "link_id": link_id,
                "tag_uid": tag_data.get("tag_uid"),
                "expected_lnurl": expected_lnurl,
                "tag_lnurl": tag_lnurl,
            }
            
            if verified:
                logger.info(f"Tag verification successful for link {link_id}")
            else:
                logger.warning(f"Tag verification failed - LNURL mismatch")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to verify tag: {e}")
            raise TagLoaderError(f"Failed to verify tag: {e}")
