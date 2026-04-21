"""
Quick validation & import tests for the trading bot.
Run with: python test_bot.py
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def test_imports():
    """Test that all modules import correctly."""
    print("[TEST] Importing modules...")
    from bot import __version__
    from bot.client import BinanceClient, BinanceClientError, NetworkError
    from bot.orders import OrderManager, OrderResult
    from bot.validators import validate_order_input, ValidationError
    from bot.logging_config import setup_logging
    print(f"  PASS - All modules imported (v{__version__})")
    return True


def test_validators():
    """Test input validation logic."""
    from bot.validators import validate_order_input, ValidationError

    print("\n[TEST] Validator tests...")
    passed = 0
    total = 0

    # --- Valid inputs ---
    valid_cases = [
        ("BTCUSDT", "BUY", "MARKET", "0.01", None, None, None),
        ("ethusdt", "sell", "limit", "0.5", "2500", None, "GTC"),
        ("BTCUSDT", "BUY", "STOP_LIMIT", "0.01", "65500", "65000", "GTC"),
        ("DOGEUSDT", "SELL", "MARKET", "100", None, None, None),
    ]

    for i, (sym, side, otype, qty, price, stop, tif) in enumerate(valid_cases):
        total += 1
        try:
            result = validate_order_input(sym, side, otype, qty, price, stop, tif)
            print(f"  PASS - Valid case {i+1}: {otype} {side} {sym}")
            passed += 1
        except Exception as e:
            print(f"  FAIL - Valid case {i+1}: {e}")

    # --- Invalid inputs (should raise ValidationError) ---
    invalid_cases = [
        ("", "BUY", "MARKET", "0.01", None, None, None, "empty symbol"),
        ("BTCUSDT", "HOLD", "MARKET", "0.01", None, None, None, "invalid side"),
        ("BTCUSDT", "BUY", "TWAP", "0.01", None, None, None, "invalid type"),
        ("BTCUSDT", "BUY", "MARKET", "-5", None, None, None, "negative qty"),
        ("BTCUSDT", "BUY", "MARKET", "abc", None, None, None, "non-numeric qty"),
        ("BTCUSDT", "BUY", "LIMIT", "0.01", None, None, None, "missing price for LIMIT"),
        ("BTCUSDT", "BUY", "STOP_LIMIT", "0.01", "65000", None, None, "missing stop price"),
    ]

    for sym, side, otype, qty, price, stop, tif, desc in invalid_cases:
        total += 1
        try:
            validate_order_input(sym, side, otype, qty, price, stop, tif)
            print(f"  FAIL - Should have raised error: {desc}")
        except Exception:
            print(f"  PASS - Caught invalid input: {desc}")
            passed += 1

    print(f"\n  Results: {passed}/{total} passed")
    return passed == total


def test_order_result():
    """Test OrderResult data class."""
    from bot.orders import OrderResult

    print("\n[TEST] OrderResult tests...")

    # Success case
    result = OrderResult(
        success=True,
        order_data={
            "orderId": 123,
            "status": "FILLED",
            "executedQty": "0.01",
            "avgPrice": "87000.00",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "origQty": "0.01",
            "clientOrderId": "test123",
        },
    )
    assert result.success is True
    assert result.order_id == 123
    assert result.status == "FILLED"
    summary = result.to_summary_dict()
    assert "orderId" in summary
    print("  PASS - OrderResult success case")

    # Failure case
    result2 = OrderResult(success=False, error_message="Test error")
    assert result2.success is False
    assert result2.error_message == "Test error"
    summary2 = result2.to_summary_dict()
    assert summary2["success"] is False
    print("  PASS - OrderResult failure case")

    return True


def test_client_init():
    """Test BinanceClient initialization."""
    from bot.client import BinanceClient

    print("\n[TEST] BinanceClient tests...")

    # Should raise ValueError with empty credentials
    try:
        client = BinanceClient(api_key="", api_secret="")
        print("  FAIL - Should have raised ValueError")
        return False
    except ValueError:
        print("  PASS - Rejects empty credentials")

    # Should initialize with valid credentials
    client = BinanceClient(api_key="test_key", api_secret="test_secret")
    assert client.api_key == "test_key"
    assert client.base_url == "https://testnet.binancefuture.com"
    print("  PASS - Initializes with valid credentials")

    # Test signature generation
    sig = client._generate_signature({"symbol": "BTCUSDT", "side": "BUY"})
    assert len(sig) == 64  # SHA256 hex digest
    print("  PASS - Signature generation works")

    return True


def test_cli_importable():
    """Test that CLI module is importable."""
    print("\n[TEST] CLI module...")
    # We just check it imports without errors
    # (can't test full Typer app in a script easily)
    try:
        import cli
        print("  PASS - CLI module imports successfully")
        return True
    except Exception as e:
        print(f"  FAIL - CLI import error: {e}")
        return False


def test_ui_importable():
    """Test that UI module is importable."""
    print("\n[TEST] UI module...")
    try:
        import ui
        print("  PASS - UI module imports successfully")
        return True
    except Exception as e:
        print(f"  FAIL - UI import error: {e}")
        return False


def main():
    print("=" * 50)
    print("  TRADING BOT — TEST SUITE")
    print("=" * 50)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Validators", test_validators()))
    results.append(("OrderResult", test_order_result()))
    results.append(("BinanceClient", test_client_init()))
    results.append(("CLI Module", test_cli_importable()))
    results.append(("UI Module", test_ui_importable()))

    print("\n" + "=" * 50)
    print("  SUMMARY")
    print("=" * 50)
    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_pass = False

    print(f"\n  Overall: {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    print("=" * 50)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
