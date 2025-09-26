#!/usr/bin/env python3
"""
Paper trading bot - simulates trading without real API keys
Useful for learning and testing strategies
"""

import json
import time
from datetime import datetime
from typing import Dict, Any
import requests

class PaperTradingBot:
    def __init__(self):
        """Initialize paper trading bot with simulated balance"""
        self.balance = 10000.0  # Starting with $10,000 USDT
        self.positions = {}
        self.orders = []
        self.order_id_counter = 1
        
        print("🎯 PAPER TRADING BOT INITIALIZED")
        print(f"📊 Starting Balance: ${self.balance:,.2f} USDT")
        print("⚠️  Note: This is SIMULATED trading (no real money)")
    
    def get_current_price(self, symbol: str) -> float:
        """Get real market price from Binance public API"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
            response = requests.get(url, timeout=5)
            data = response.json()
            return float(data['price'])
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            # Return mock prices for common symbols
            mock_prices = {
                'BTCUSDT': 43000.0,
                'ETHUSDT': 2500.0,
                'BNBUSDT': 300.0
            }
            return mock_prices.get(symbol.upper(), 1000.0)
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Simulate a market order"""
        current_price = self.get_current_price(symbol)
        total_cost = quantity * current_price
        
        order = {
            'orderId': self.order_id_counter,
            'symbol': symbol.upper(),
            'side': side.upper(),
            'type': 'MARKET',
            'quantity': quantity,
            'price': current_price,
            'total_cost': total_cost,
            'status': 'FILLED',
            'timestamp': datetime.now().isoformat()
        }
        
        if side.upper() == 'BUY':
            if self.balance >= total_cost:
                self.balance -= total_cost
                self.positions[symbol] = self.positions.get(symbol, 0) + quantity
                print(f"✅ BUY ORDER EXECUTED")
                print(f"   📦 Bought {quantity} {symbol} at ${current_price:,.2f}")
                print(f"   💰 Cost: ${total_cost:,.2f}")
                print(f"   💳 Remaining Balance: ${self.balance:,.2f}")
            else:
                order['status'] = 'REJECTED'
                print(f"❌ INSUFFICIENT BALANCE")
                print(f"   Required: ${total_cost:,.2f}")
                print(f"   Available: ${self.balance:,.2f}")
        
        else:  # SELL
            current_position = self.positions.get(symbol, 0)
            if current_position >= quantity:
                self.balance += total_cost
                self.positions[symbol] = current_position - quantity
                print(f"✅ SELL ORDER EXECUTED")
                print(f"   📤 Sold {quantity} {symbol} at ${current_price:,.2f}")
                print(f"   💰 Received: ${total_cost:,.2f}")
                print(f"   💳 New Balance: ${self.balance:,.2f}")
            else:
                order['status'] = 'REJECTED'
                print(f"❌ INSUFFICIENT POSITION")
                print(f"   Required: {quantity}")
                print(f"   Available: {current_position}")
        
        self.orders.append(order)
        self.order_id_counter += 1
        return order
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        """Simulate a limit order"""
        current_price = self.get_current_price(symbol)
        
        order = {
            'orderId': self.order_id_counter,
            'symbol': symbol.upper(),
            'side': side.upper(),
            'type': 'LIMIT',
            'quantity': quantity,
            'price': price,
            'current_market_price': current_price,
            'status': 'NEW',
            'timestamp': datetime.now().isoformat()
        }
        
        # Simulate immediate fill if price is favorable
        if (side.upper() == 'BUY' and price >= current_price) or \
           (side.upper() == 'SELL' and price <= current_price):
            # Would fill immediately
            order['status'] = 'FILLED'
            order['filled_price'] = current_price
            total_cost = quantity * current_price
            
            if side.upper() == 'BUY' and self.balance >= total_cost:
                self.balance -= total_cost
                self.positions[symbol] = self.positions.get(symbol, 0) + quantity
            elif side.upper() == 'SELL' and self.positions.get(symbol, 0) >= quantity:
                self.balance += total_cost
                self.positions[symbol] = self.positions.get(symbol, 0) - quantity
            else:
                order['status'] = 'REJECTED'
        
        print(f"📋 LIMIT ORDER PLACED")
        print(f"   {side} {quantity} {symbol} at ${price:,.2f}")
        print(f"   Current Market: ${current_price:,.2f}")
        print(f"   Status: {order['status']}")
        
        self.orders.append(order)
        self.order_id_counter += 1
        return order
    
    def get_account_balance(self) -> Dict[str, Any]:
        """Get simulated account balance"""
        total_value = self.balance
        
        # Calculate position values
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                current_price = self.get_current_price(symbol)
                position_value = quantity * current_price
                total_value += position_value
        
        return {
            'cash_balance': self.balance,
            'positions': self.positions,
            'total_portfolio_value': total_value
        }
    
    def get_order_history(self) -> list:
        """Get order history"""
        return self.orders[-10:]  # Last 10 orders

def main():
    """Paper trading CLI"""
    bot = PaperTradingBot()
    
    while True:
        print("\n" + "="*40)
        print("📄 PAPER TRADING BOT")
        print("="*40)
        print("1. Place Market Order")
        print("2. Place Limit Order")
        print("3. View Account Balance")
        print("4. View Order History")
        print("5. Get Current Price")
        print("6. Exit")
        print("="*40)
        
        choice = input("Select option (1-6): ").strip()
        
        try:
            if choice == '1':
                symbol = input("Symbol (e.g., BTCUSDT): ").strip()
                side = input("Side (BUY/SELL): ").strip()
                quantity = float(input("Quantity: "))
                bot.place_market_order(symbol, side, quantity)
                
            elif choice == '2':
                symbol = input("Symbol (e.g., BTCUSDT): ").strip()
                side = input("Side (BUY/SELL): ").strip()
                quantity = float(input("Quantity: "))
                price = float(input("Limit Price: "))
                bot.place_limit_order(symbol, side, quantity, price)
                
            elif choice == '3':
                balance = bot.get_account_balance()
                print(f"\n💰 ACCOUNT SUMMARY")
                print(f"Cash Balance: ${balance['cash_balance']:,.2f}")
                print(f"Total Portfolio: ${balance['total_portfolio_value']:,.2f}")
                print(f"Positions: {balance['positions']}")
                
            elif choice == '4':
                orders = bot.get_order_history()
                print(f"\n📋 RECENT ORDERS")
                for order in orders:
                    print(f"#{order['orderId']}: {order['side']} {order['quantity']} {order['symbol']} - {order['status']}")
                    
            elif choice == '5':
                symbol = input("Symbol (e.g., BTCUSDT): ").strip()
                price = bot.get_current_price(symbol)
                print(f"\n📈 {symbol} Current Price: ${price:,.2f}")
                
            elif choice == '6':
                print("👋 Happy paper trading!")
                break
                
            else:
                print("❌ Invalid option")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()