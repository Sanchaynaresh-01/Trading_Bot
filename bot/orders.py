"""
Order placement logic for the trading bot.
Encapsulates the business logic for placing Market, Limit, and Stop-Limit orders
on Binance Futures Testnet.
"""

import logging
from typing import Any, Dict, Optional

from bot.client import BinanceClient, BinanceClientError, NetworkError
from bot.validators import validate_order_input, ValidationError

logger = logging.getLogger("trading_bot")


class OrderResult:
    """
    Structured result from an order placement attempt.

    Attributes:
        success: Whether the order was placed successfully.
        order_data: Raw API response dictionary (on success).
        error_message: Human-readable error string (on failure).
        request_summary: Dictionary summarizing what was requested.
    """

    def __init__(
        self,
        success: bool,
        order_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        request_summary: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.order_data = order_data or {}
        self.error_message = error_message
        self.request_summary = request_summary or {}

    @property
    def order_id(self) -> Optional[int]:
        return self.order_data.get("orderId")

    @property
    def status(self) -> Optional[str]:
        return self.order_data.get("status")

    @property
    def executed_qty(self) -> Optional[str]:
        return self.order_data.get("executedQty")

    @property
    def avg_price(self) -> Optional[str]:
        return self.order_data.get("avgPrice")

    @property
    def client_order_id(self) -> Optional[str]:
        return self.order_data.get("clientOrderId")

    @property
    def orig_qty(self) -> Optional[str]:
        return self.order_data.get("origQty")

    @property
    def price(self) -> Optional[str]:
        return self.order_data.get("price")

    @property
    def order_type(self) -> Optional[str]:
        return self.order_data.get("type")

    @property
    def side(self) -> Optional[str]:
        return self.order_data.get("side")

    @property
    def symbol(self) -> Optional[str]:
        return self.order_data.get("symbol")

    def to_summary_dict(self) -> Dict[str, Any]:
        """Return a clean summary of the order result for display."""
        if self.success:
            return {
                "orderId": self.order_id,
                "clientOrderId": self.client_order_id,
                "symbol": self.symbol,
                "side": self.side,
                "type": self.order_type,
                "status": self.status,
                "origQty": self.orig_qty,
                "executedQty": self.executed_qty,
                "price": self.price,
                "avgPrice": self.avg_price,
            }
        else:
            return {
                "success": False,
                "error": self.error_message,
                "request": self.request_summary,
            }


class OrderManager:
    """
    Manages order placement on Binance Futures Testnet.

    Validates inputs, constructs API parameters, places orders, and logs results.
    """

    def __init__(self, client: BinanceClient):
        """
        Initialize OrderManager with a BinanceClient instance.

        Args:
            client: Configured BinanceClient for API communication.
        """
        self.client = client
        logger.info("OrderManager initialized.")

    def _build_order_params(self, validated: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build API-compatible order parameters from validated input.

        Args:
            validated: Dictionary of validated order parameters.

        Returns:
            Dictionary ready for the Binance API call.
        """
        order_type = validated["order_type"]

        # Map internal type names to Binance API type names
        api_type_map = {
            "MARKET": "MARKET",
            "LIMIT": "LIMIT",
            "STOP_LIMIT": "STOP",
        }

        params = {
            "symbol": validated["symbol"],
            "side": validated["side"],
            "type": api_type_map.get(order_type, order_type),
            "quantity": str(validated["quantity"]),
        }

        # Add price for LIMIT and STOP_LIMIT
        if validated.get("price") is not None:
            params["price"] = str(validated["price"])

        # Add stop price for STOP_LIMIT
        if validated.get("stop_price") is not None:
            params["stopPrice"] = str(validated["stop_price"])

        # Add timeInForce for LIMIT and STOP_LIMIT
        if validated.get("time_in_force") is not None:
            params["timeInForce"] = validated["time_in_force"]

        return params

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None,
        stop_price: Optional[str] = None,
        time_in_force: Optional[str] = None,
    ) -> OrderResult:
        """
        Validate inputs and place an order on Binance Futures Testnet.

        Args:
            symbol: Trading pair (e.g., "BTCUSDT").
            side: "BUY" or "SELL".
            order_type: "MARKET", "LIMIT", or "STOP_LIMIT".
            quantity: Order quantity as string.
            price: Limit price (required for LIMIT/STOP_LIMIT).
            stop_price: Stop trigger price (required for STOP_LIMIT).
            time_in_force: GTC, IOC, or FOK (default: GTC for LIMIT).

        Returns:
            OrderResult with success/failure details.
        """
        request_summary = {
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": quantity,
            "price": price,
            "stop_price": stop_price,
            "time_in_force": time_in_force,
        }

        # Step 1: Validate inputs
        try:
            validated = validate_order_input(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                time_in_force=time_in_force,
            )
        except ValidationError as e:
            logger.error("Validation failed: %s", str(e))
            return OrderResult(
                success=False,
                error_message=str(e),
                request_summary=request_summary,
            )

        # Step 2: Build API parameters
        params = self._build_order_params(validated)

        logger.info(
            "Order request — %s %s %s qty=%s price=%s stopPrice=%s tif=%s",
            validated["order_type"],
            validated["side"],
            validated["symbol"],
            validated["quantity"],
            validated.get("price", "N/A"),
            validated.get("stop_price", "N/A"),
            validated.get("time_in_force", "N/A"),
        )

        # Step 3: Place order via API
        try:
            response = self.client.place_order(**params)

            logger.info(
                "Order placed successfully — orderId=%s status=%s executedQty=%s avgPrice=%s",
                response.get("orderId"),
                response.get("status"),
                response.get("executedQty"),
                response.get("avgPrice"),
            )

            return OrderResult(
                success=True,
                order_data=response,
                request_summary=request_summary,
            )

        except BinanceClientError as e:
            logger.error("Binance API error while placing order: %s", str(e))
            return OrderResult(
                success=False,
                error_message=f"API Error: {e.message} (code: {e.error_code})",
                request_summary=request_summary,
            )
        except NetworkError as e:
            logger.error("Network error while placing order: %s", str(e))
            return OrderResult(
                success=False,
                error_message=f"Network Error: {str(e)}",
                request_summary=request_summary,
            )
        except Exception as e:
            logger.exception("Unexpected error while placing order: %s", str(e))
            return OrderResult(
                success=False,
                error_message=f"Unexpected Error: {str(e)}",
                request_summary=request_summary,
            )

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Fetch the current market price for a symbol.

        Args:
            symbol: Trading pair.

        Returns:
            Current price as float, or None on failure.
        """
        try:
            ticker = self.client.get_ticker_price(symbol)
            price = float(ticker.get("price", 0))
            logger.info("Current price for %s: %.2f", symbol, price)
            return price
        except Exception as e:
            logger.error("Failed to fetch price for %s: %s", symbol, str(e))
            return None

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """Fetch all open orders, optionally filtered by symbol."""
        try:
            return self.client.get_open_orders(symbol)
        except Exception as e:
            logger.error("Failed to fetch open orders: %s", str(e))
            return []

    def cancel_order(self, symbol: str, order_id: int) -> Optional[Dict[str, Any]]:
        """Cancel an order by ID and symbol."""
        try:
            result = self.client.cancel_order(symbol, order_id)
            logger.info("Order %d cancelled successfully.", order_id)
            return result
        except Exception as e:
            logger.error("Failed to cancel order %d: %s", order_id, str(e))
            return None
