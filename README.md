# 🤖 Trading Bot — Binance Futures Testnet (USDT-M)

A Python trading bot for placing **Market**, **Limit**, and **Stop-Limit** orders on the Binance Futures Testnet.
Features a structured CLI with Rich-powered output, a lightweight Flask web UI, comprehensive logging, and robust error handling.

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py
│   ├── orders.py
│   ├── validators.py
│   └── logging_config.py
├── cli.py
├── ui.py
├── logs/
│   └── trading_bot.log
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Setup

### 1. Prerequisites

* Python 3.8+
* Binance Futures Testnet account

### 2. Get API Credentials

1. Go to https://testnet.binancefuture.com
2. Login / Register
3. Open **API Management**
4. Generate API Key & Secret

---

### 3. Install Dependencies

```bash
git clone <repo-url>
cd trading_bot

python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

---

## 📖 Usage

### Place Market Order

```bash
python cli.py order -s BTCUSDT -S BUY -t MARKET -q 0.01
```

---

### Place Limit Order

```bash
python cli.py order -s ETHUSDT -S SELL -t LIMIT -q 0.5 -p 2000
```

---

### Stop-Limit Order

```bash
python cli.py order -s BTCUSDT -S BUY -t STOP_LIMIT -q 0.001 -p 65500 -sp 65000
```

---

### Interactive Mode

```bash
python cli.py interactive
```

---

### Check Price

```bash
python cli.py price -s BTCUSDT
```

---

### Open Orders

```bash
python cli.py open-orders
```

---

### Cancel Order

```bash
python cli.py cancel -s BTCUSDT -o 123456789
```

---

### Account Info

```bash
python cli.py account
```

---

## 🌐 Web UI

```bash
python ui.py
```

Open: http://localhost:5000

**Features:**

* Live price updates
* Market / Limit / Stop-Limit orders
* Order history
* Real-time notifications

---

## 🔧 Supported Order Types

| Type       | Required Params                           | Description                 |
| ---------- | ----------------------------------------- | --------------------------- |
| MARKET     | symbol, side, quantity                    | Executes instantly          |
| LIMIT      | symbol, side, quantity, price             | Executes at specified price |
| STOP_LIMIT | symbol, side, quantity, price, stop_price | Triggered limit order       |

---

## 📝 Logging

Logs stored in:

```
logs/trading_bot.log
```

* Console → INFO level
* File → DEBUG level
* Auto rotation enabled

---

## 🏗️ Architecture

```
CLI / Web UI
      ↓
Order Manager (orders.py)
      ↓
Binance Client (client.py)
      ↓
Binance Futures API
```

---

## ⚠️ Assumptions

* Testnet only (no real funds)
* USDT-M Futures
* One-way mode
* No trading strategy logic
* Basic symbol validation

---

## ✅ Features

* Market, Limit, Stop-Limit orders
* CLI + Interactive mode
* Flask Web UI
* Logging & error handling

---

## 📄 License

This project was built as an application task submission.
