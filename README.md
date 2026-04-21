# 🤖 Trading Bot — Binance Futures Testnet (USDT-M)

A Python trading bot for placing **Market**, **Limit**, and **Stop-Limit** orders on the Binance Futures Testnet. Features a structured CLI with Rich-powered output, a lightweight Flask web UI, comprehensive logging, and robust error handling.

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package init
│   ├── client.py            # Binance REST API client (HMAC-SHA256 signing)
│   ├── orders.py            # Order placement business logic
│   ├── validators.py        # Input validation & sanitization
│   └── logging_config.py    # Structured logging (file + console)
├── cli.py                   # CLI entry point (Typer + Rich)
├── ui.py                    # Lightweight Web UI (Flask) — Bonus
├── logs/
│   └── trading_bot.log      # Auto-generated log file
├── .env.example             # Environment template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Setup

### 1. Prerequisites

- **Python 3.8+** installed
- A **Binance Futures Testnet** account

### 2. Get Testnet API Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Register / log in
3. Navigate to **API Management**
4. Generate a new API key and secret

### 3. Install Dependencies

```bash
# Clone the repository
git clone <repo-url>
cd trading_bot

# Create a virtual environment (recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your testnet credentials
# BINANCE_API_KEY=your_actual_key
# BINANCE_API_SECRET=your_actual_secret
```

---

## 📖 Usage

### CLI Commands

The bot provides several CLI commands via `cli.py`:

#### Place a Market Order

```bash
# Buy 0.01 BTC at market price
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# Short form
python cli.py order -s BTCUSDT -S BUY -t MARKET -q 0.01
```

#### Place a Limit Order

```bash
# Sell 0.5 ETH at $2000
python cli.py order -s ETHUSDT -S SELL -t LIMIT -q 0.5 -p 2000

# With explicit time-in-force
python cli.py order -s BTCUSDT -S BUY -t LIMIT -q 0.001 -p 50000 --tif GTC
```

#### Place a Stop-Limit Order (Bonus)

```bash
# Stop-Limit buy: triggers at $65000, limit at $65500
python cli.py order -s BTCUSDT -S BUY -t STOP_LIMIT -q 0.001 -p 65500 -sp 65000
```

#### Skip Confirmation Prompt

```bash
python cli.py order -s BTCUSDT -S BUY -t MARKET -q 0.01 --yes
```

#### Interactive Mode (Bonus — Enhanced CLI UX)

Step-by-step guided order placement with prompts and validation:

```bash
python cli.py interactive
```

#### Check Current Price

```bash
python cli.py price -s BTCUSDT
```

#### View Open Orders

```bash
python cli.py open-orders
python cli.py open-orders -s BTCUSDT
```

#### Cancel an Order

```bash
python cli.py cancel -s BTCUSDT -o 123456789
```

#### View Account Info

```bash
python cli.py account
```

### Web UI (Bonus — Lightweight UI)

Launch the Flask-based trading dashboard:

```bash
python ui.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

Features:
- Live price display (auto-refreshes every 10s)
- BUY/SELL toggle with visual feedback
- Support for Market, Limit, and Stop-Limit orders
- Order history panel
- Real-time result display with toast notifications

---

## 📋 CLI Output Examples

### Market Order Output

```
╔══════════════════════════════════════════════╗
║    🤖 Binance Futures Trading Bot           ║
║       Testnet (USDT-M) Edition              ║
╚══════════════════════════════════════════════╝

┌─────────────────────────────────────────────┐
│            📋 Order Request Summary         │
├─────────────────┬───────────────────────────┤
│ Parameter       │ Value                     │
├─────────────────┼───────────────────────────┤
│ Symbol          │ BTCUSDT                   │
│ Side            │ BUY                       │
│ Type            │ MARKET                    │
│ Quantity        │ 0.01                      │
└─────────────────┴───────────────────────────┘

Proceed with this order? [y/n]: y

Connecting to Binance Futures Testnet...

┌─────────────────────────────────────────────┐
│          ✅ Order Placed Successfully       │
├────────────────────┬────────────────────────┤
│ Order ID           │ 123456789              │
│ Symbol             │ BTCUSDT                │
│ Side               │ BUY                    │
│ Type               │ MARKET                 │
│ Status             │ FILLED                 │
│ Original Qty       │ 0.01                   │
│ Executed Qty       │ 0.01                   │
│ Avg Price          │ 64250.50               │
└────────────────────┴────────────────────────┘

🎉 Order executed successfully!
```

---

## 🔧 Supported Order Types

| Type | Required Params | Description |
|------|----------------|-------------|
| **MARKET** | symbol, side, quantity | Executes immediately at current market price |
| **LIMIT** | symbol, side, quantity, price | Places at specified price, waits for fill |
| **STOP_LIMIT** | symbol, side, quantity, price, stop_price | Triggers limit order when stop price is reached |

---

## 📝 Logging

All API requests, responses, and errors are logged to `logs/trading_bot.log`:

- **Console**: INFO level and above (clean, minimal output)
- **Log File**: DEBUG level (full request/response details for audit)
- **Rotation**: 5 MB max file size, 3 backup files retained

Sample log entries:

```
2026-04-21 19:30:00 | INFO     | trading_bot.client | BinanceClient initialized — base URL: https://testnet.binancefuture.com
2026-04-21 19:30:01 | INFO     | trading_bot.orders | Order request — MARKET BUY BTCUSDT qty=0.01 price=N/A
2026-04-21 19:30:02 | DEBUG    | trading_bot.client | API Request: POST /fapi/v1/order | Params: {symbol: BTCUSDT, side: BUY, type: MARKET, quantity: 0.01}
2026-04-21 19:30:02 | INFO     | trading_bot.orders | Order placed successfully — orderId=123456 status=FILLED
```

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   CLI Layer  │     │   Web UI     │     │   Validators     │
│  (cli.py)    │     │  (ui.py)     │     │ (validators.py)  │
└──────┬───────┘     └──────┬───────┘     └────────┬─────────┘
       │                    │                      │
       └────────┬───────────┘                      │
                │                                  │
       ┌────────▼─────────────────────────────────▼──┐
       │           Order Manager (orders.py)         │
       │  validate → build params → call API → log   │
       └──────────────────┬──────────────────────────┘
                          │
       ┌──────────────────▼──────────────────────────┐
       │          Binance Client (client.py)          │
       │  HMAC signing, HTTP, error handling          │
       └──────────────────┬──────────────────────────┘
                          │
                ┌─────────▼──────────┐
                │  Binance Futures   │
                │  Testnet REST API  │
                └────────────────────┘
```

---

## ⚠️ Assumptions

1. **Testnet Only** — This bot is designed exclusively for the Binance Futures Testnet. Do NOT use with real funds.
2. **USDT-M Futures** — Uses the `/fapi/v1/` endpoints for USDT-margined perpetual futures.
3. **One-Way Position Mode** — Assumes the default one-way position mode (not hedge mode).
4. **No Order Book Analysis** — This is a simplified order placement tool, not a trading strategy engine.
5. **Symbol Validation** — Accepts any `<BASE>USDT` pattern. The API will reject invalid symbols with a clear error message.
6. **Quantity Precision** — Quantities are passed as-is. The API enforces its own precision rules per symbol.

---

## ✅ Bonus Features Implemented

- [x] **Stop-Limit Order Type** — Full support for STOP orders with `stopPrice` and `price`
- [x] **Enhanced CLI UX** — Interactive mode, Rich tables, color-coded output, confirmation prompts
- [x] **Lightweight Web UI** — Flask dashboard with live prices, order history, and responsive design

---

## 📄 License

This project was built as an application task submission. 
 
 
