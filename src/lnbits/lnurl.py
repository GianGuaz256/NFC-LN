"""LNURL handling utilities."""

import logging
from typing import Optional
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class LNURLError(Exception):
    """Base exception for LNURL errors."""
    pass


class LNURLHandler:
    """
    Handler for LNURL encoding, decoding, and validation.
    
    Focuses on LNURL-withdraw protocol.
    """
    
    def __init__(self, use_bech32: bool = True):
        """
        Initialize LNURL handler.
        
        Args:
            use_bech32: Whether to use bech32 encoding (True) or plain URLs (False)
        """
        self.use_bech32 = use_bech32
        logger.debug(f"LNURLHandler initialized (bech32: {use_bech32})")
    
    def encode(self, url: str) -> str:
        """
        Encode a URL as LNURL.
        
        Args:
            url: Plain URL string
        
        Returns:
            LNURL string (bech32 encoded if use_bech32=True, otherwise plain URL)
        
        Raises:
            LNURLError: If encoding fails
        """
        try:
            if not self.use_bech32:
                # Return plain URL
                logger.debug(f"Using plain URL: {url}")
                return url
            
            # Encode as bech32 LNURL
            lnurl = self._encode_bech32(url)
            logger.debug(f"Encoded URL to LNURL: {lnurl}")
            return lnurl
            
        except Exception as e:
            logger.error(f"Failed to encode LNURL: {e}")
            raise LNURLError(f"Failed to encode LNURL: {e}")
    
    def decode(self, lnurl: str) -> str:
        """
        Decode LNURL to plain URL.
        
        Args:
            lnurl: LNURL string (bech32 or plain URL)
        
        Returns:
            Plain URL string
        
        Raises:
            LNURLError: If decoding fails
        """
        try:
            # Check if it's already a plain URL
            if lnurl.startswith('http://') or lnurl.startswith('https://'):
                logger.debug("LNURL is already a plain URL")
                return lnurl
            
            # Remove 'lightning:' prefix if present
            if lnurl.lower().startswith('lightning:'):
                lnurl = lnurl[10:]
            
            # Check if it's a bech32 LNURL
            if lnurl.lower().startswith('lnurl'):
                url = self._decode_bech32(lnurl)
                logger.debug(f"Decoded LNURL to URL: {url}")
                return url
            
            # Assume it's already a URL
            return lnurl
            
        except Exception as e:
            logger.error(f"Failed to decode LNURL: {e}")
            raise LNURLError(f"Failed to decode LNURL: {e}")
    
    def validate(self, lnurl: str) -> bool:
        """
        Validate LNURL format.
        
        Args:
            lnurl: LNURL string to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to decode it
            url = self.decode(lnurl)
            
            # Validate URL format
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            return True
            
        except Exception:
            return False
    
    def is_withdraw_url(self, url: str) -> bool:
        """
        Check if URL is an LNURL-withdraw URL.
        
        Args:
            url: URL to check
        
        Returns:
            True if it's a withdraw URL
        """
        try:
            # Decode if it's a bech32 LNURL
            if url.lower().startswith('lnurl'):
                url = self.decode(url)
            
            # Check URL path and query parameters
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Common patterns for LNURL-withdraw
            withdraw_patterns = [
                '/withdraw/',
                '/lnurl/withdraw',
                '/api/v1/lnurl',
            ]
            
            for pattern in withdraw_patterns:
                if pattern in path:
                    return True
            
            # Check query parameters
            params = parse_qs(parsed.query)
            if 'tag' in params and params['tag'][0] == 'withdrawRequest':
                return True
            
            return False
            
        except Exception:
            return False
    
    def _encode_bech32(self, url: str) -> str:
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
    
    def _decode_bech32(self, lnurl: str) -> str:
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
        
        # Decode bech32
        hrp, data = bech32.bech32_decode(lnurl.lower())
        if hrp is None or data is None:
            raise ValueError("Invalid bech32 LNURL")
        
        if hrp != 'lnurl':
            raise ValueError(f"Invalid LNURL prefix: {hrp}")
        
        # Convert from 5-bit to 8-bit
        decoded = bech32.convertbits(data, 5, 8, False)
        if decoded is None:
            raise ValueError("Failed to convert bech32 data")
        
        # Convert to string
        url = bytes(decoded).decode('utf-8')
        return url
    
    def get_lnurl_params(self, lnurl: str) -> dict:
        """
        Extract parameters from LNURL.
        
        Args:
            lnurl: LNURL string
        
        Returns:
            Dictionary with LNURL parameters
        """
        params = {
            "valid": False,
            "type": "unknown",
        }
        
        try:
            # Decode to URL
            url = self.decode(lnurl)
            params["url"] = url
            params["valid"] = True
            
            # Determine type
            if self.is_withdraw_url(url):
                params["type"] = "withdraw"
            
            # Parse URL
            parsed = urlparse(url)
            params["scheme"] = parsed.scheme
            params["host"] = parsed.netloc
            params["path"] = parsed.path
            
            # Parse query parameters
            query_params = parse_qs(parsed.query)
            params["query"] = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
            
        except Exception as e:
            params["error"] = str(e)
        
        return params
    
    def format_for_display(self, lnurl: str, max_length: int = 50) -> str:
        """
        Format LNURL for display (truncate if too long).
        
        Args:
            lnurl: LNURL string
            max_length: Maximum display length
        
        Returns:
            Formatted LNURL string
        """
        if len(lnurl) <= max_length:
            return lnurl
        
        # Truncate with ellipsis
        half = (max_length - 3) // 2
        return f"{lnurl[:half]}...{lnurl[-half:]}"
    
    def create_lightning_uri(self, lnurl: str) -> str:
        """
        Create a lightning: URI from LNURL.
        
        Args:
            lnurl: LNURL string
        
        Returns:
            Lightning URI (lightning:LNURL...)
        """
        # Ensure it's bech32 encoded
        if not lnurl.lower().startswith('lnurl'):
            lnurl = self.encode(lnurl)
        
        return f"lightning:{lnurl}"
    
    def extract_from_uri(self, uri: str) -> Optional[str]:
        """
        Extract LNURL from lightning: URI.
        
        Args:
            uri: Lightning URI
        
        Returns:
            LNURL string, or None if not found
        """
        if uri.lower().startswith('lightning:'):
            return uri[10:]
        
        return None
