"""NDEF message handling for NFC tags."""

import logging
from typing import Optional
from urllib.parse import urlparse

try:
    import ndef
except ImportError:
    ndef = None

logger = logging.getLogger(__name__)


class NDEFError(Exception):
    """Base exception for NDEF errors."""
    pass


class NDEFHandler:
    """
    Handler for creating and parsing NDEF messages.
    
    Focuses on URI records for LNURL-withdraw links.
    """
    
    def __init__(self):
        """Initialize NDEF handler."""
        if ndef is None:
            raise ImportError("ndeflib not installed. Run: pip install ndeflib")
        
        logger.debug("NDEFHandler initialized")
    
    def create_uri_record(self, uri: str) -> bytes:
        """
        Create an NDEF message with a URI record.
        
        Args:
            uri: URI string (e.g., LNURL-withdraw link)
        
        Returns:
            Encoded NDEF message as bytes
        
        Raises:
            NDEFError: If URI is invalid or encoding fails
        """
        try:
            # Validate URI
            parsed = urlparse(uri)
            if not parsed.scheme:
                raise NDEFError(f"Invalid URI: missing scheme")
            
            logger.debug(f"Creating NDEF URI record for: {uri}")
            
            # Create URI record
            uri_record = ndef.UriRecord(uri)
            
            # Create NDEF message
            message = ndef.message.Message([uri_record])
            
            # Encode to bytes
            encoded = b''.join(ndef.message_encoder(message))
            
            logger.info(f"Created NDEF message ({len(encoded)} bytes)")
            return encoded
            
        except Exception as e:
            logger.error(f"Failed to create NDEF URI record: {e}")
            raise NDEFError(f"Failed to create NDEF URI record: {e}")
    
    def create_lnurl_record(self, lnurl: str) -> bytes:
        """
        Create an NDEF message for an LNURL-withdraw link.
        
        Args:
            lnurl: LNURL-withdraw string (bech32 encoded or plain URL)
        
        Returns:
            Encoded NDEF message as bytes
        
        Raises:
            NDEFError: If LNURL is invalid
        """
        try:
            # Check if it's a bech32 LNURL or plain URL
            if lnurl.lower().startswith('lnurl'):
                # It's already a bech32 LNURL, decode it to get the URL
                url = self._decode_lnurl(lnurl)
                logger.debug(f"Decoded LNURL to URL: {url}")
            else:
                # It's a plain URL
                url = lnurl
            
            # Create URI record with the URL
            return self.create_uri_record(url)
            
        except Exception as e:
            logger.error(f"Failed to create LNURL record: {e}")
            raise NDEFError(f"Failed to create LNURL record: {e}")
    
    def parse_message(self, data: bytes) -> list:
        """
        Parse an NDEF message from raw bytes.
        
        Args:
            data: Raw NDEF message data
        
        Returns:
            List of parsed NDEF records
        
        Raises:
            NDEFError: If parsing fails
        """
        try:
            logger.debug(f"Parsing NDEF message ({len(data)} bytes)")
            
            # Find NDEF TLV in data
            ndef_data = self._extract_ndef_tlv(data)
            if not ndef_data:
                raise NDEFError("No NDEF TLV found in data")
            
            # Parse NDEF message
            records = list(ndef.message_decoder(ndef_data))
            
            logger.info(f"Parsed {len(records)} NDEF record(s)")
            return records
            
        except Exception as e:
            logger.error(f"Failed to parse NDEF message: {e}")
            raise NDEFError(f"Failed to parse NDEF message: {e}")
    
    def extract_uri(self, data: bytes) -> Optional[str]:
        """
        Extract URI from NDEF message.
        
        Args:
            data: Raw NDEF message data
        
        Returns:
            URI string if found, None otherwise
        """
        try:
            records = self.parse_message(data)
            
            for record in records:
                if isinstance(record, ndef.UriRecord):
                    uri = record.uri
                    logger.info(f"Extracted URI: {uri}")
                    return uri
            
            logger.warning("No URI record found in NDEF message")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract URI: {e}")
            return None
    
    def extract_lnurl(self, data: bytes) -> Optional[str]:
        """
        Extract LNURL from NDEF message.
        
        Args:
            data: Raw NDEF message data
        
        Returns:
            LNURL string (bech32 encoded) if found, None otherwise
        """
        try:
            uri = self.extract_uri(data)
            if not uri:
                return None
            
            # Check if it's an LNURL-related URL
            if 'lnurl' in uri.lower() or 'lightning' in uri.lower():
                # Try to encode as bech32 LNURL
                try:
                    lnurl = self._encode_lnurl(uri)
                    logger.info(f"Encoded URL to LNURL: {lnurl}")
                    return lnurl
                except Exception:
                    # If encoding fails, return the URL as-is
                    return uri
            
            return uri
            
        except Exception as e:
            logger.error(f"Failed to extract LNURL: {e}")
            return None
    
    def _extract_ndef_tlv(self, data: bytes) -> Optional[bytes]:
        """
        Extract NDEF data from TLV structure.
        
        Args:
            data: Raw tag data with TLV structure
        
        Returns:
            NDEF message bytes, or None if not found
        """
        # Look for NDEF TLV (Type = 0x03)
        i = 0
        while i < len(data):
            tlv_type = data[i]
            
            if tlv_type == 0x00:
                # NULL TLV, skip
                i += 1
                continue
            
            if tlv_type == 0xFE:
                # Terminator TLV
                break
            
            if i + 1 >= len(data):
                break
            
            tlv_length = data[i + 1]
            
            if tlv_type == 0x03:
                # NDEF Message TLV found
                if i + 2 + tlv_length <= len(data):
                    return data[i + 2:i + 2 + tlv_length]
            
            # Move to next TLV
            i += 2 + tlv_length
        
        return None
    
    def _decode_lnurl(self, lnurl: str) -> str:
        """
        Decode bech32 LNURL to URL.
        
        Args:
            lnurl: Bech32 encoded LNURL string
        
        Returns:
            Decoded URL
        """
        try:
            import bech32
        except ImportError:
            raise ImportError("bech32 library not installed. Run: pip install bech32")
        
        # Remove 'lightning:' prefix if present
        if lnurl.lower().startswith('lightning:'):
            lnurl = lnurl[10:]
        
        # Decode bech32
        hrp, data = bech32.bech32_decode(lnurl)
        if hrp is None or data is None:
            raise ValueError("Invalid bech32 LNURL")
        
        # Convert from 5-bit to 8-bit
        decoded = bech32.convertbits(data, 5, 8, False)
        if decoded is None:
            raise ValueError("Failed to convert bech32 data")
        
        # Convert to string
        url = bytes(decoded).decode('utf-8')
        return url
    
    def _encode_lnurl(self, url: str) -> str:
        """
        Encode URL to bech32 LNURL.
        
        Args:
            url: URL string
        
        Returns:
            Bech32 encoded LNURL
        """
        try:
            import bech32
        except ImportError:
            raise ImportError("bech32 library not installed. Run: pip install bech32")
        
        # Convert URL to bytes
        url_bytes = url.encode('utf-8')
        
        # Convert from 8-bit to 5-bit
        data = bech32.convertbits(url_bytes, 8, 5, True)
        if data is None:
            raise ValueError("Failed to convert URL to bech32 data")
        
        # Encode as bech32
        lnurl = bech32.bech32_encode('lnurl', data)
        if lnurl is None:
            raise ValueError("Failed to encode LNURL")
        
        return lnurl.upper()
    
    def validate_ndef_message(self, data: bytes) -> bool:
        """
        Validate NDEF message structure.
        
        Args:
            data: Raw NDEF message data
        
        Returns:
            True if valid, False otherwise
        """
        try:
            records = self.parse_message(data)
            return len(records) > 0
        except Exception:
            return False
    
    def get_message_info(self, data: bytes) -> dict:
        """
        Get information about an NDEF message.
        
        Args:
            data: Raw NDEF message data
        
        Returns:
            Dictionary with message information
        """
        info = {
            "valid": False,
            "size": len(data),
            "records": 0,
            "types": [],
        }
        
        try:
            records = self.parse_message(data)
            info["valid"] = True
            info["records"] = len(records)
            
            for record in records:
                record_type = type(record).__name__
                info["types"].append(record_type)
                
                if isinstance(record, ndef.UriRecord):
                    info["uri"] = record.uri
                elif isinstance(record, ndef.TextRecord):
                    info["text"] = record.text
            
        except Exception as e:
            info["error"] = str(e)
        
        return info
