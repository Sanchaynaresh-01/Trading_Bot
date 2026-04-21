"""
Input validation utilities for the trading bot.
Validates symbols, sides, order types, quantities, and prices before API submission.
"""

import re
from typing import Optional

# Supported trading pairs on Binance Futures Testnet (common ones)
SUPPORTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT",
    "XRPUSDT", "SOLUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT",
    "AVAXUSDT", "LINKUSDT", "UNIUSDT", "ATOMUSDT", "ETCUSDT",
]

VALID_SIDES = ["BUY", "SELL"]
VALID_ORDER_TYPES = ["MARKET", "LIMIT", "STOP_LIMIT"]
VALID_TIME_IN_FORCE = ["GTC", "IOC", "FOK"]


class ValidationError(Exception):
    """Raised when user input fails validation."""
    pass


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalize a trading symbol.

    Args:
        symbol: Trading pair string (e.g., "btcusdt", "BTCUSDT").

    Returns:
        Uppercased symbol string.

    Raises:
        ValidationError: If symbol format is invalid.
    """
    symbol = symbol.strip().upper()

    if not re.match(r"^[A-Z]{2,10}USDT$", symbol):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected format: <BASE>USDT (e.g., BTCUSDT)."
        )

    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side.

    Args:
        side: "BUY" or "SELL".

    Returns:
        Uppercased side string.

    Raises:
        ValidationError: If side is not BUY or SELL.
    """
    side = side.strip().upper()

    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}."
        )

    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: "MARKET", "LIMIT", or "STOP_LIMIT".

    Returns:
        Uppercased order type string.

    Raises:
        ValidationError: If order type is unsupported.
    """
    order_type = order_type.strip().upper().replace("-", "_")

    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(VALID_ORDER_TYPES)}."
        )

    return order_type


def validate_quantity(quantity: str) -> float:
    """
    Validate order quantity.

    Args:
        quantity: Quantity as a string (e.g., "0.001").

    Returns:
        Quantity as a positive float.

    Raises:
        ValidationError: If quantity is not a valid positive number.
    """
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid quantity '{quantity}'. Must be a positive number."
        )

    if qty <= 0:
        raise ValidationError(
            f"Quantity must be greater than 0, got {qty}."
        )

    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate order price. Required for LIMIT and STOP_LIMIT orders.

    Args:
        price: Price as a string, or None.
        order_type: The order type (to determine if price is required).

    Returns:
        Price as a positive float, or None for MARKET orders.

    Raises:
        ValidationError: If price is missing for LIMIT/STOP_LIMIT or invalid.
    """
    requires_price = order_type in ("LIMIT", "STOP_LIMIT")

    if price is None or str(price).strip() == "":
        if requires_price:
            raise ValidationError(
                f"Price is required for {order_type} orders."
            )
        return None

    try:
        p = float(price)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid price '{price}'. Must be a positive number."
        )

    if p <= 0:
        raise ValidationError(
            f"Price must be greater than 0, got {p}."
        )

    return p


def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate stop price. Required for STOP_LIMIT orders.

    Args:
        stop_price: Stop trigger price as a string, or None.
        order_type: The order type.

    Returns:
        Stop price as a positive float, or None.

    Raises:
        ValidationError: If stop price is missing for STOP_LIMIT or invalid.
    """
    if order_type != "STOP_LIMIT":
        return None

    if stop_price is None or str(stop_price).strip() == "":
        raise ValidationError(
            "Stop price is required for STOP_LIMIT orders."
        )

    try:
        sp = float(stop_price)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid stop price '{stop_price}'. Must be a positive number."
        )

    if sp <= 0:
        raise ValidationError(
            f"Stop price must be greater than 0, got {sp}."
        )

    return sp


def validate_time_in_force(tif: Optional[str], order_type: str) -> Optional[str]:
    """
    Validate time-in-force parameter. Required for LIMIT and STOP_LIMIT orders.

    Args:
        tif: Time in force string (GTC, IOC, FOK).
        order_type: The order type.

    Returns:
        Uppercased TIF string, or None for MARKET.

    Raises:
        ValidationError: If TIF is invalid for the order type.
    """
    if order_type == "MARKET":
        return None

    if tif is None or str(tif).strip() == "":
        return "GTC"  # Default for LIMIT orders

    tif = tif.strip().upper()

    if tif not in VALID_TIME_IN_FORCE:
        raise ValidationError(
            f"Invalid timeInForce '{tif}'. Must be one of: {', '.join(VALID_TIME_IN_FORCE)}."
        )

    return tif


def validate_order_input(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
    time_in_force: Optional[str] = None,
) -> dict:
    """
    Validate all order inputs and return a cleaned dictionary.

    Args:
        symbol: Trading pair.
        side: BUY or SELL.
        order_type: MARKET, LIMIT, or STOP_LIMIT.
        quantity: Order quantity.
        price: Limit price (optional for MARKET).
        stop_price: Stop trigger price (optional, for STOP_LIMIT).
        time_in_force: GTC, IOC, or FOK (optional).

    Returns:
        Dictionary with validated and normalized order parameters.

    Raises:
        ValidationError: If any input is invalid.
    """
    validated_type = validate_order_type(order_type)

    result = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validated_type,
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, validated_type),
        "stop_price": validate_stop_price(stop_price, validated_type),
        "time_in_force": validate_time_in_force(time_in_force, validated_type),
    }

    return result
