"""
Log generation script — Run this AFTER configuring your .env file with valid API keys.
Places one MARKET order and one LIMIT order on Binance Futures Testnet,
generating the log files required for the assignment deliverables.

Usage:
    python generate_logs.py
"""

import os
import sys
import shutil

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

from bot.logging_config import setup_logging, LOG_FILE
from bot.client import BinanceClient
from bot.orders import OrderManager


def main():
    logger = setup_logging(level="DEBUG")

    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")

    if not api_key or not api_secret or api_key == "your_api_key_here":
        print("\n[ERROR] API credentials not configured!")
        print("1. Copy .env.example to .env")
        print("2. Add your Binance Futures Testnet API key and secret")
        print("3. Get credentials at: https://testnet.binancefuture.com")
        sys.exit(1)

    client = BinanceClient(api_key=api_key, api_secret=api_secret)
    manager = OrderManager(client)

    print("\n" + "=" * 60)
    print("  LOG GENERATION SCRIPT")
    print("  Placing test orders on Binance Futures Testnet...")
    print("=" * 60)

    # ── 1. Fetch current BTC price for reference ─────────────────
    print("\n[1/3] Fetching current BTCUSDT price...")
    btc_price = manager.get_current_price("BTCUSDT")
    if btc_price:
        print(f"      Current BTCUSDT price: ${btc_price:,.2f}")
    else:
        print("      WARNING: Could not fetch price, using default")
        btc_price = 87000.0

    # ── 2. Place MARKET order ────────────────────────────────────
    print("\n[2/3] Placing MARKET BUY order (BTCUSDT, qty=0.001)...")
    market_result = manager.place_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity="0.001",
    )

    if market_result.success:
        print(f"      SUCCESS - Order ID: {market_result.order_id}")
        print(f"      Status: {market_result.status}")
        print(f"      Executed Qty: {market_result.executed_qty}")
        print(f"      Avg Price: {market_result.avg_price}")
    else:
        print(f"      FAILED - {market_result.error_message}")

    # ── 3. Place LIMIT order ─────────────────────────────────────
    # Set limit price slightly ABOVE market so it stays open (status: NEW/PARTIALLY_FILLED)
    limit_price = int(btc_price * 1.05)  # Round to nearest integer for tick size consistency
    print(f"\n[3/3] Placing LIMIT SELL order (BTCUSDT, qty=0.001, price=${limit_price:,.2f})...")
    limit_result = manager.place_order(
        symbol="BTCUSDT",
        side="SELL",
        order_type="LIMIT",
        quantity="0.001",
        price=str(limit_price),
        time_in_force="GTC",
    )

    if limit_result.success:
        print(f"      SUCCESS - Order ID: {limit_result.order_id}")
        print(f"      Status: {limit_result.status}")
        print(f"      Original Qty: {limit_result.orig_qty}")
        print(f"      Price: {limit_result.price}")
    else:
        print(f"      FAILED - {limit_result.error_message}")

    # ── Copy log file to individual log files ────────────────────
    log_dir = os.path.dirname(LOG_FILE)
    print(f"\n{'=' * 60}")
    print(f"  Log file generated: {LOG_FILE}")

    if os.path.exists(LOG_FILE):
        # Copy the combined log to individual named files for clarity
        shutil.copy2(LOG_FILE, os.path.join(log_dir, "market_order.log"))
        shutil.copy2(LOG_FILE, os.path.join(log_dir, "limit_order.log"))
        print(f"  Copied to: {os.path.join(log_dir, 'market_order.log')}")
        print(f"  Copied to: {os.path.join(log_dir, 'limit_order.log')}")

    print(f"\n  MARKET order: {'PASSED' if market_result.success else 'FAILED'}")
    print(f"  LIMIT order:  {'PASSED' if limit_result.success else 'FAILED'}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
