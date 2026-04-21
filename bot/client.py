"""
Binance Futures Testnet API client.
Handles authentication, request signing, and low-level HTTP interactions.
"""

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot")

# Binance Futures Testnet base URL (as specified in the assignment)
BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """Raised for Binance API errors."""

    def __init__(self, status_code: int, error_code: int, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(f"Binance API Error [{error_code}]: {message} (HTTP {status_code})")


class NetworkError(Exception):
    """Raised for network-level failures."""
    pass


class BinanceClient:
    """
    Low-level client for the Binance Futures Testnet REST API.

    Handles HMAC-SHA256 request signing, timestamping, and HTTP communication.
    All responses are returned as parsed JSON dictionaries.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL):
        """
        Initialize the Binance client.

        Args:
            api_key: Binance Futures Testnet API key.
            api_secret: Binance Futures Testnet API secret.
            base_url: API base URL (defaults to testnet).
        """
        if not api_key or not api_secret:
            raise ValueError("API key and secret are required. Check your .env file.")

        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")

        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

        logger.info("BinanceClient initialized — base URL: %s", self.base_url)

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Generate HMAC-SHA256 signature for request parameters.

        Args:
            params: Query/body parameters to sign.

        Returns:
            Hex-encoded signature string.
        """
        query_string = urlencode(params, doseq=True)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _get_server_time(self) -> int:
        """
        Fetch Binance server time to avoid timestamp drift issues.

        Returns:
            Server time in milliseconds.
        """
        try:
            resp = self.session.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            resp.raise_for_status()
            server_time = resp.json()["serverTime"]
            logger.debug("Server time fetched: %d", server_time)
            return server_time
        except Exception:
            # Fallback to local time if server time fetch fails
            local_time = int(time.time() * 1000)
            logger.warning("Failed to fetch server time, using local time: %d", local_time)
            return local_time

    def _signed_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a signed API request.

        Args:
            method: HTTP method (GET, POST, DELETE).
            endpoint: API endpoint path (e.g., "/fapi/v1/order").
            params: Request parameters.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            BinanceClientError: For API-level errors.
            NetworkError: For connection/timeout failures.
        """
        if params is None:
            params = {}

        # Add timestamp
        params["timestamp"] = self._get_server_time()

        # Add receive window for timing tolerance
        params["recvWindow"] = 5000

        # Generate and append signature
        params["signature"] = self._generate_signature(params)

        url = f"{self.base_url}{endpoint}"

        logger.debug(
            "API Request: %s %s | Params: %s",
            method.upper(),
            url,
            {k: v for k, v in params.items() if k != "signature"},
        )

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=15)
            elif method.upper() == "POST":
                response = self.session.post(url, data=params, timeout=15)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params, timeout=15)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        except requests.exceptions.ConnectionError as e:
            logger.error("Network connection failed: %s", str(e))
            raise NetworkError(f"Connection failed: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error("Request timed out: %s", str(e))
            raise NetworkError(f"Request timed out: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", str(e))
            raise NetworkError(f"Request failed: {e}") from e

        # Parse response
        try:
            data = response.json()
        except ValueError:
            logger.error("Failed to parse JSON response: %s", response.text)
            raise BinanceClientError(
                response.status_code, -1, f"Invalid JSON response: {response.text}"
            )

        logger.debug("API Response [%d]: %s", response.status_code, data)

        # Handle API errors
        if response.status_code >= 400:
            error_code = data.get("code", -1)
            error_msg = data.get("msg", "Unknown error")
            logger.error(
                "API error — HTTP %d | Code: %d | Message: %s",
                response.status_code,
                error_code,
                error_msg,
            )
            raise BinanceClientError(response.status_code, error_code, error_msg)

        return data

    def get_account_info(self) -> Dict[str, Any]:
        """Fetch account information from the testnet."""
        logger.info("Fetching account information...")
        return self._signed_request("GET", "/fapi/v2/account")

    def get_exchange_info(self) -> Dict[str, Any]:
        """Fetch exchange information (symbols, rules, etc.)."""
        logger.info("Fetching exchange information...")
        try:
            resp = self.session.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch exchange info: %s", str(e))
            raise NetworkError(f"Failed to fetch exchange info: {e}") from e

    def get_ticker_price(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch current price for a symbol.

        Args:
            symbol: Trading pair (e.g., "BTCUSDT").

        Returns:
            Ticker data with 'symbol' and 'price'.
        """
        logger.info("Fetching ticker price for %s...", symbol)
        try:
            resp = self.session.get(
                f"{self.base_url}/fapi/v1/ticker/price",
                params={"symbol": symbol},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch ticker for %s: %s", symbol, str(e))
            raise NetworkError(f"Failed to fetch ticker: {e}") from e

    def place_order(self, **params) -> Dict[str, Any]:
        """
        Place a new order via POST /fapi/v1/order.

        Args:
            **params: Order parameters (symbol, side, type, quantity, etc.)

        Returns:
            Order response dictionary.
        """
        logger.info("Placing order: %s", params)
        return self._signed_request("POST", "/fapi/v1/order", params)

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """
        Fetch all open orders, optionally filtered by symbol.

        Args:
            symbol: Trading pair to filter by (optional).

        Returns:
            List of open order dictionaries.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        logger.info("Fetching open orders (symbol=%s)...", symbol or "ALL")
        return self._signed_request("GET", "/fapi/v1/openOrders", params)

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an existing order.

        Args:
            symbol: Trading pair.
            order_id: Order ID to cancel.

        Returns:
            Cancellation response dictionary.
        """
        params = {"symbol": symbol, "orderId": order_id}
        logger.info("Cancelling order %d for %s...", order_id, symbol)
        return self._signed_request("DELETE", "/fapi/v1/order", params)
