"""
Lightweight Web UI for the trading bot (Bonus Feature).
A Flask-based dashboard for placing and monitoring orders via the browser.
"""

import os
import json
from typing import Optional

from flask import Flask, render_template_string, request, jsonify
from dotenv import load_dotenv

from bot.client import BinanceClient, BinanceClientError, NetworkError
from bot.logging_config import setup_logging
from bot.orders import OrderManager

load_dotenv()
logger = setup_logging(level="DEBUG")

app = Flask(__name__)

# ── HTML Template ────────────────────────────────────────────────────────────

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot — Binance Futures Testnet</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-card: #1a2332;
            --border: #2a3548;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --accent-purple: #8b5cf6;
            --gradient-buy: linear-gradient(135deg, #10b981, #059669);
            --gradient-sell: linear-gradient(135deg, #ef4444, #dc2626);
        }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }

        /* ── Header ── */
        .header {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-title {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .header-title .logo {
            font-size: 1.5rem;
        }

        .header-title h1 {
            font-size: 1.25rem;
            font-weight: 600;
        }

        .header-title span {
            font-size: 0.75rem;
            color: var(--text-muted);
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
        }

        .header-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            color: var(--accent-green);
        }

        .header-status .dot {
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        /* ── Layout ── */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        @media (max-width: 768px) {
            .container { grid-template-columns: 1fr; padding: 1rem; }
        }

        /* ── Cards ── */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            transition: border-color 0.2s;
        }

        .card:hover {
            border-color: rgba(59, 130, 246, 0.3);
        }

        .card-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* ── Form ── */
        .form-group {
            margin-bottom: 1rem;
        }

        .form-group label {
            display: block;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 0.35rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .form-group input,
        .form-group select {
            width: 100%;
            padding: 0.65rem 0.85rem;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            transition: border-color 0.2s, box-shadow 0.2s;
            outline: none;
        }

        .form-group input:focus,
        .form-group select:focus {
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
        }

        /* ── Side Toggle ── */
        .side-toggle {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .side-btn {
            padding: 0.65rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            background: transparent;
            color: var(--text-secondary);
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .side-btn:hover { border-color: var(--text-muted); }
        .side-btn.buy-active {
            background: var(--gradient-buy);
            border-color: var(--accent-green);
            color: white;
        }
        .side-btn.sell-active {
            background: var(--gradient-sell);
            border-color: var(--accent-red);
            color: white;
        }

        /* ── Submit ── */
        .submit-btn {
            width: 100%;
            padding: 0.85rem;
            margin-top: 0.5rem;
            border: none;
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
            font-weight: 600;
            color: white;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.1s;
        }

        .submit-btn:hover { opacity: 0.9; }
        .submit-btn:active { transform: scale(0.98); }
        .submit-btn.buy { background: var(--gradient-buy); }
        .submit-btn.sell { background: var(--gradient-sell); }
        .submit-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* ── Price Display ── */
        .price-display {
            text-align: center;
            padding: 1.25rem;
            background: rgba(6, 182, 212, 0.05);
            border: 1px solid rgba(6, 182, 212, 0.15);
            border-radius: 10px;
            margin-bottom: 1rem;
        }

        .price-display .label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .price-display .value {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--accent-cyan);
            margin-top: 0.25rem;
        }

        /* ── Result ── */
        .result-panel {
            grid-column: 1 / -1;
        }

        .result-content {
            min-height: 100px;
        }

        .result-empty {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        .result-success {
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 8px;
            padding: 1rem;
        }

        .result-error {
            background: rgba(239, 68, 68, 0.08);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 8px;
            padding: 1rem;
        }

        .result-row {
            display: flex;
            justify-content: space-between;
            padding: 0.4rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.85rem;
        }

        .result-row:last-child { border-bottom: none; }
        .result-row .key { color: var(--text-secondary); }
        .result-row .val { font-weight: 500; }

        /* ── Spinner ── */
        .spinner {
            display: none;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
            margin-right: 0.5rem;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .loading .spinner { display: inline-block; }

        /* ── Notification ── */
        .toast {
            position: fixed;
            top: 1.5rem;
            right: 1.5rem;
            padding: 0.85rem 1.25rem;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 500;
            z-index: 1000;
            transform: translateX(120%);
            transition: transform 0.3s ease;
        }

        .toast.show { transform: translateX(0); }
        .toast.success {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--accent-green);
        }
        .toast.error {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: var(--accent-red);
        }

        /* ── History ── */
        .history-entry {
            padding: 0.75rem;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .history-entry .meta {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.25rem;
        }

        .history-entry .badge {
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
        }

        .badge.buy { background: rgba(16,185,129,0.2); color: var(--accent-green); }
        .badge.sell { background: rgba(239,68,68,0.2); color: var(--accent-red); }
        .badge.success { background: rgba(16,185,129,0.2); color: var(--accent-green); }
        .badge.failed { background: rgba(239,68,68,0.2); color: var(--accent-red); }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-title">
            <span class="logo">🤖</span>
            <h1>Trading Bot</h1>
            <span>TESTNET</span>
        </div>
        <div class="header-status">
            <div class="dot"></div>
            Connected to Binance Futures
        </div>
    </div>

    <div class="container">
        <!-- Order Form Card -->
        <div class="card">
            <div class="card-title">📝 Place Order</div>

            <div class="price-display">
                <div class="label">Current Price</div>
                <div class="value" id="currentPrice">—</div>
            </div>

            <form id="orderForm" onsubmit="return placeOrder(event)">
                <div class="form-group">
                    <label>Symbol</label>
                    <select id="symbol" onchange="fetchPrice()">
                        <option value="BTCUSDT">BTCUSDT</option>
                        <option value="ETHUSDT">ETHUSDT</option>
                        <option value="BNBUSDT">BNBUSDT</option>
                        <option value="SOLUSDT">SOLUSDT</option>
                        <option value="XRPUSDT">XRPUSDT</option>
                        <option value="DOGEUSDT">DOGEUSDT</option>
                        <option value="ADAUSDT">ADAUSDT</option>
                        <option value="LTCUSDT">LTCUSDT</option>
                    </select>
                </div>

                <div class="side-toggle">
                    <button type="button" class="side-btn buy-active" id="buyBtn" onclick="setSide('BUY')">BUY / LONG</button>
                    <button type="button" class="side-btn" id="sellBtn" onclick="setSide('SELL')">SELL / SHORT</button>
                </div>
                <input type="hidden" id="side" value="BUY">

                <div class="form-group">
                    <label>Order Type</label>
                    <select id="orderType" onchange="togglePriceFields()">
                        <option value="MARKET">Market</option>
                        <option value="LIMIT">Limit</option>
                        <option value="STOP_LIMIT">Stop-Limit</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Quantity</label>
                    <input type="text" id="quantity" placeholder="e.g., 0.001" required>
                </div>

                <div class="form-row" id="priceRow" style="display:none;">
                    <div class="form-group">
                        <label>Price</label>
                        <input type="text" id="price" placeholder="Limit price">
                    </div>
                    <div class="form-group" id="stopPriceGroup" style="display:none;">
                        <label>Stop Price</label>
                        <input type="text" id="stopPrice" placeholder="Trigger price">
                    </div>
                </div>

                <button type="submit" class="submit-btn buy" id="submitBtn">
                    <span class="spinner" id="spinner"></span>
                    <span id="submitText">Place BUY Order</span>
                </button>
            </form>
        </div>

        <!-- Order History Card -->
        <div class="card">
            <div class="card-title">📜 Order History</div>
            <div id="history">
                <div class="result-empty">No orders placed yet. Place your first order!</div>
            </div>
        </div>

        <!-- Result Panel -->
        <div class="card result-panel">
            <div class="card-title">📊 Last Order Result</div>
            <div class="result-content" id="resultContent">
                <div class="result-empty">Order results will appear here.</div>
            </div>
        </div>
    </div>

    <div class="toast" id="toast"></div>

    <script>
        let currentSide = 'BUY';
        let orderHistory = [];

        function setSide(side) {
            currentSide = side;
            document.getElementById('side').value = side;
            const buyBtn = document.getElementById('buyBtn');
            const sellBtn = document.getElementById('sellBtn');
            const submitBtn = document.getElementById('submitBtn');
            const submitText = document.getElementById('submitText');

            if (side === 'BUY') {
                buyBtn.className = 'side-btn buy-active';
                sellBtn.className = 'side-btn';
                submitBtn.className = 'submit-btn buy';
                submitText.textContent = 'Place BUY Order';
            } else {
                buyBtn.className = 'side-btn';
                sellBtn.className = 'side-btn sell-active';
                submitBtn.className = 'submit-btn sell';
                submitText.textContent = 'Place SELL Order';
            }
        }

        function togglePriceFields() {
            const type = document.getElementById('orderType').value;
            const priceRow = document.getElementById('priceRow');
            const stopGroup = document.getElementById('stopPriceGroup');

            if (type === 'MARKET') {
                priceRow.style.display = 'none';
            } else {
                priceRow.style.display = 'grid';
                priceRow.style.gridTemplateColumns = type === 'STOP_LIMIT' ? '1fr 1fr' : '1fr';
                stopGroup.style.display = type === 'STOP_LIMIT' ? 'block' : 'none';
            }
        }

        async function fetchPrice() {
            const symbol = document.getElementById('symbol').value;
            try {
                const res = await fetch(`/api/price?symbol=${symbol}`);
                const data = await res.json();
                if (data.price) {
                    document.getElementById('currentPrice').textContent = '$' + parseFloat(data.price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                }
            } catch (e) {
                document.getElementById('currentPrice').textContent = '—';
            }
        }

        function showToast(message, type) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = `toast ${type} show`;
            setTimeout(() => { toast.className = 'toast'; }, 3500);
        }

        async function placeOrder(e) {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const spinner = document.getElementById('spinner');

            btn.disabled = true;
            spinner.style.display = 'inline-block';

            const body = {
                symbol: document.getElementById('symbol').value,
                side: document.getElementById('side').value,
                order_type: document.getElementById('orderType').value,
                quantity: document.getElementById('quantity').value,
                price: document.getElementById('price').value || null,
                stop_price: document.getElementById('stopPrice').value || null,
            };

            try {
                const res = await fetch('/api/order', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                });
                const data = await res.json();

                if (data.success) {
                    showToast('✅ Order placed successfully!', 'success');
                    displayResult(data.order, true);
                    addHistory(body, data.order, true);
                } else {
                    showToast('❌ ' + data.error, 'error');
                    displayResult({ error: data.error }, false);
                    addHistory(body, null, false, data.error);
                }
            } catch (err) {
                showToast('❌ Network error', 'error');
                displayResult({ error: err.message }, false);
            }

            btn.disabled = false;
            spinner.style.display = 'none';
        }

        function displayResult(data, success) {
            const el = document.getElementById('resultContent');

            if (success) {
                const rows = Object.entries(data)
                    .filter(([k, v]) => v !== null && v !== undefined && v !== '')
                    .map(([k, v]) => `<div class="result-row"><span class="key">${k}</span><span class="val">${v}</span></div>`)
                    .join('');
                el.innerHTML = `<div class="result-success">${rows}</div>`;
            } else {
                el.innerHTML = `<div class="result-error"><div class="result-row"><span class="key">Error</span><span class="val">${data.error}</span></div></div>`;
            }
        }

        function addHistory(req, order, success, error) {
            const el = document.getElementById('history');
            const time = new Date().toLocaleTimeString();
            const sideBadge = `<span class="badge ${req.side.toLowerCase()}">${req.side}</span>`;
            const statusBadge = success
                ? '<span class="badge success">✓ Filled</span>'
                : '<span class="badge failed">✗ Failed</span>';

            const entry = document.createElement('div');
            entry.className = 'history-entry';
            entry.innerHTML = `
                <div class="meta">
                    <span>${sideBadge} ${req.order_type} ${req.symbol} × ${req.quantity}</span>
                    <span>${statusBadge}</span>
                </div>
                <div style="color: var(--text-muted); font-size: 0.7rem;">${time}${order ? ' — ID: ' + order.orderId : ''}</div>
            `;

            // Remove empty state message
            const empty = el.querySelector('.result-empty');
            if (empty) empty.remove();

            el.insertBefore(entry, el.firstChild);
        }

        // Initial price fetch
        fetchPrice();
        setInterval(fetchPrice, 10000);
    </script>
</body>
</html>
"""


# ── Helper ───────────────────────────────────────────────────────────────────

def _get_order_manager() -> OrderManager:
    """Create an OrderManager from environment variables."""
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    client = BinanceClient(api_key=api_key, api_secret=api_secret)
    return OrderManager(client)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main trading dashboard."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/price")
def api_price():
    """Fetch current price for a symbol."""
    symbol = request.args.get("symbol", "BTCUSDT")
    try:
        manager = _get_order_manager()
        ticker = manager.client.get_ticker_price(symbol)
        return jsonify({"price": ticker.get("price")})
    except Exception as e:
        logger.error("Price fetch error: %s", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/order", methods=["POST"])
def api_place_order():
    """Place an order via the REST API."""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No JSON body provided"}), 400

    manager = _get_order_manager()
    result = manager.place_order(
        symbol=data.get("symbol", ""),
        side=data.get("side", ""),
        order_type=data.get("order_type", ""),
        quantity=data.get("quantity", ""),
        price=data.get("price"),
        stop_price=data.get("stop_price"),
        time_in_force=data.get("time_in_force"),
    )

    if result.success:
        return jsonify({"success": True, "order": result.to_summary_dict()})
    else:
        return jsonify({"success": False, "error": result.error_message}), 400


@app.route("/api/open-orders")
def api_open_orders():
    """Fetch open orders."""
    symbol = request.args.get("symbol")
    try:
        manager = _get_order_manager()
        orders = manager.get_open_orders(symbol)
        return jsonify({"orders": orders})
    except Exception as e:
        logger.error("Open orders error: %s", str(e))
        return jsonify({"error": str(e)}), 500


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\\n🤖 Trading Bot Web UI starting...")
    print("   → Open http://localhost:5000 in your browser\\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
