"""LNbits API client for managing Lightning payments."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class LNbitsError(Exception):
    """Base exception for LNbits errors."""
    pass


class LNbitsConnectionError(LNbitsError):
    """Raised when connection to LNbits fails."""
    pass


class LNbitsAPIError(LNbitsError):
    """Raised when LNbits API returns an error."""
    pass


class LNbitsClient:
    """
    Client for interacting with LNbits API.
    
    Handles wallet operations and LNURL-withdraw link creation.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        wallet_id: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize LNbits client.
        
        Args:
            base_url: LNbits instance URL (e.g., https://legend.lnbits.com)
            api_key: Admin or invoice API key
            wallet_id: Wallet ID (optional, can be extracted from API key)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.wallet_id = wallet_id
        self.timeout = timeout
        
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "X-Api-Key": api_key,
                "Content-Type": "application/json",
            }
        )
        
        logger.info(f"LNbitsClient initialized for {base_url}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def close(self):
        """Close HTTP client."""
        self._client.close()
    
    def check_connection(self) -> bool:
        """
        Check connection to LNbits instance.
        
        Returns:
            True if connection successful
        
        Raises:
            LNbitsConnectionError: If connection fails
        """
        try:
            logger.debug("Checking LNbits connection...")
            response = self._client.get(f"{self.base_url}/api/v1/wallet")
            response.raise_for_status()
            
            logger.info("Successfully connected to LNbits")
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to connect to LNbits: {e}")
            raise LNbitsConnectionError(f"Failed to connect to LNbits: {e}")
    
    def get_wallet_balance(self) -> int:
        """
        Get wallet balance in millisatoshis.
        
        Returns:
            Balance in millisatoshis
        
        Raises:
            LNbitsAPIError: If API request fails
        """
        try:
            logger.debug("Fetching wallet balance...")
            response = self._client.get(f"{self.base_url}/api/v1/wallet")
            response.raise_for_status()
            
            data = response.json()
            balance = data.get("balance", 0)
            
            logger.info(f"Wallet balance: {balance} msat ({balance // 1000} sats)")
            return balance
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get wallet balance: {e}")
            raise LNbitsAPIError(f"Failed to get wallet balance: {e}")
    
    def get_wallet_info(self) -> Dict[str, Any]:
        """
        Get detailed wallet information.
        
        Returns:
            Dictionary with wallet details
        
        Raises:
            LNbitsAPIError: If API request fails
        """
        try:
            logger.debug("Fetching wallet info...")
            response = self._client.get(f"{self.base_url}/api/v1/wallet")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Wallet: {data.get('name', 'Unknown')}")
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get wallet info: {e}")
            raise LNbitsAPIError(f"Failed to get wallet info: {e}")
    
    def create_withdraw_link(
        self,
        amount: int,
        title: str = "Lightning Gift Card",
        uses: int = 1,
        wait_time: int = 1,
        webhook_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an LNURL-withdraw link.
        
        Args:
            amount: Amount in satoshis
            title: Title/description for the link
            uses: Number of times the link can be used
            wait_time: Wait time between uses in seconds
            webhook_url: Optional webhook URL for notifications
        
        Returns:
            Dictionary with withdraw link details including:
                - id: Link ID
                - lnurl: LNURL-withdraw string
                - url: Plain URL
                - amount: Amount in satoshis
        
        Raises:
            LNbitsAPIError: If link creation fails
        """
        try:
            logger.debug(f"Creating withdraw link: {amount} sats, {uses} use(s)")
            
            # Prepare request data
            data = {
                "title": title,
                "min_withdrawable": amount,
                "max_withdrawable": amount,
                "uses": uses,
                "wait_time": wait_time,
                "is_unique": True,
            }
            
            if webhook_url:
                data["webhook_url"] = webhook_url
            
            # Create withdraw link via LNbits withdraw extension
            response = self._client.post(
                f"{self.base_url}/withdraw/api/v1/links",
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Created withdraw link: {result.get('id')}")
            logger.debug(f"LNURL: {result.get('lnurl')}")
            
            return result
            
        except httpx.HTTPError as e:
            error_msg = f"Failed to create withdraw link: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                except Exception:
                    error_msg += f" - {e.response.text}"
            
            logger.error(error_msg)
            raise LNbitsAPIError(error_msg)
    
    def get_withdraw_link(self, link_id: str) -> Dict[str, Any]:
        """
        Get details of an existing withdraw link.
        
        Args:
            link_id: Withdraw link ID
        
        Returns:
            Dictionary with link details
        
        Raises:
            LNbitsAPIError: If request fails
        """
        try:
            logger.debug(f"Fetching withdraw link: {link_id}")
            
            response = self._client.get(
                f"{self.base_url}/withdraw/api/v1/links/{link_id}"
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Retrieved withdraw link: {link_id}")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get withdraw link: {e}")
            raise LNbitsAPIError(f"Failed to get withdraw link: {e}")
    
    def list_withdraw_links(self) -> List[Dict[str, Any]]:
        """
        List all withdraw links.
        
        Returns:
            List of withdraw link dictionaries
        
        Raises:
            LNbitsAPIError: If request fails
        """
        try:
            logger.debug("Fetching withdraw links...")
            
            response = self._client.get(
                f"{self.base_url}/withdraw/api/v1/links"
            )
            response.raise_for_status()
            
            result = response.json()
            links = result if isinstance(result, list) else []
            
            logger.info(f"Retrieved {len(links)} withdraw link(s)")
            return links
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to list withdraw links: {e}")
            raise LNbitsAPIError(f"Failed to list withdraw links: {e}")
    
    def delete_withdraw_link(self, link_id: str) -> bool:
        """
        Delete a withdraw link.
        
        Args:
            link_id: Withdraw link ID
        
        Returns:
            True if deletion successful
        
        Raises:
            LNbitsAPIError: If deletion fails
        """
        try:
            logger.debug(f"Deleting withdraw link: {link_id}")
            
            response = self._client.delete(
                f"{self.base_url}/withdraw/api/v1/links/{link_id}"
            )
            response.raise_for_status()
            
            logger.info(f"Deleted withdraw link: {link_id}")
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to delete withdraw link: {e}")
            raise LNbitsAPIError(f"Failed to delete withdraw link: {e}")
    
    def create_invoice(
        self,
        amount: int,
        memo: str = "",
        webhook: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a Lightning invoice.
        
        Args:
            amount: Amount in satoshis
            memo: Invoice memo/description
            webhook: Optional webhook URL
        
        Returns:
            Dictionary with invoice details including payment_hash and payment_request
        
        Raises:
            LNbitsAPIError: If invoice creation fails
        """
        try:
            logger.debug(f"Creating invoice: {amount} sats")
            
            data = {
                "out": False,
                "amount": amount,
                "memo": memo,
            }
            
            if webhook:
                data["webhook"] = webhook
            
            response = self._client.post(
                f"{self.base_url}/api/v1/payments",
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created invoice: {result.get('payment_hash')}")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to create invoice: {e}")
            raise LNbitsAPIError(f"Failed to create invoice: {e}")
    
    def pay_invoice(self, payment_request: str) -> Dict[str, Any]:
        """
        Pay a Lightning invoice.
        
        Args:
            payment_request: BOLT11 payment request
        
        Returns:
            Dictionary with payment details
        
        Raises:
            LNbitsAPIError: If payment fails
        """
        try:
            logger.debug("Paying invoice...")
            
            data = {
                "out": True,
                "bolt11": payment_request,
            }
            
            response = self._client.post(
                f"{self.base_url}/api/v1/payments",
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Payment successful: {result.get('payment_hash')}")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to pay invoice: {e}")
            raise LNbitsAPIError(f"Failed to pay invoice: {e}")
    
    def check_payment(self, payment_hash: str) -> Dict[str, Any]:
        """
        Check payment status.
        
        Args:
            payment_hash: Payment hash
        
        Returns:
            Dictionary with payment status
        
        Raises:
            LNbitsAPIError: If check fails
        """
        try:
            logger.debug(f"Checking payment: {payment_hash}")
            
            response = self._client.get(
                f"{self.base_url}/api/v1/payments/{payment_hash}"
            )
            response.raise_for_status()
            
            result = response.json()
            paid = result.get("paid", False)
            logger.info(f"Payment {payment_hash}: {'paid' if paid else 'pending'}")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to check payment: {e}")
            raise LNbitsAPIError(f"Failed to check payment: {e}")
    
    def get_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent transactions.
        
        Args:
            limit: Maximum number of transactions to retrieve
        
        Returns:
            List of transaction dictionaries
        
        Raises:
            LNbitsAPIError: If request fails
        """
        try:
            logger.debug(f"Fetching {limit} transactions...")
            
            response = self._client.get(
                f"{self.base_url}/api/v1/payments",
                params={"limit": limit}
            )
            response.raise_for_status()
            
            result = response.json()
            transactions = result if isinstance(result, list) else []
            
            logger.info(f"Retrieved {len(transactions)} transaction(s)")
            return transactions
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get transactions: {e}")
            raise LNbitsAPIError(f"Failed to get transactions: {e}")
