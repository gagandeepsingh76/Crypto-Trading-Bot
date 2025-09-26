# 🚀 Crypto Trading Bots Collection
 - A collection of powerful Binance trading bots written in Python — ranging from paper trading simulations to fully functional market execution bots.

## 📂 Project Structure
 - ├── bot1.py                  # Best bot with advanced features
 - ├── bot1.log                 # Log file for bot1
 - ├── bot2.py                  # Intermediate bot (less advanced than bot1)
 - ├── bot2.log                 # Log file for bot2
 - ├── paper_trading_bot.py     # Safe paper trading bot (simulation)
 - ├── paper_trading_bot.log    # Log file for paper trading bot

## ⚡ Bots Overview
### 🔥 1. bot1.py — The Best Trading Bot
 - Full-featured Binance Futures trading bot
 - Handles Market, Limit, and Stop-Limit orders
 - Robust error handling & logging
 - Account balance tracking
 - Order management (status, cancel, history)
 - Recommended for real testing (with Testnet or live keys)

### ⚡ 2. bot2.py — Basic Trading Bot
 - A simpler version of bot1.py
 - Supports basic order placements
 - Fewer checks and features
 - Good for learning Binance API basics

### 📝 3. paper_trading_bot.py — Paper Trading Simulator
 - Perfect for beginners
 - No real API keys required (completely safe)

#### Simulates:
 - Market Orders
 - Limit Orders
 - Portfolio balance & positions
 - Order history
 - Uses real-time Binance prices (with fallback mock prices)
 - Great for learning trading without risk

## 🔑 Requirements
 - Python 3.8+
### Install dependencies:
 - pip install python-binance requests

## ⚙️ Usage
### 🟢 Run Paper Trading Bot (Safe Mode)
 - python paper_trading_bot.py

## 🔥 Run Advanced Trading Bot (bot1.py)
 - python bot1.py
#### You’ll need Binance API Key & Secret (use Testnet for safety).
## ⚡ Run Basic Trading Bot (bot2.py)
 - python bot2.py

## 📊 Logging
### All bots maintain log files for easier debugging:
 - bot1.log
 - bot2.log
 - paper_trading_bot.log

## ⚠️ Disclaimer
### This project is for educational purposes only.
### Cryptocurrency trading is risky. Use Testnet or paper trading before going live.
### The author is not responsible for financial losses.

