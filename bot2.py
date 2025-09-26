import logging
import sys
from decimal import Decimal
from typing import Optional, Dict, Any
from binance import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import json
from datetime import datetime

class BasicBot:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        if testnet:
            self.client = Client(api_key, api_secret, testnet=True)
            self.client.API_URL = 'https://testnet.binancefuture.com'
        else:
            self.client = Client(api_key, api_secret)
        
        self.setup_logging()
        self.test_connection()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bot2.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def test_connection(self):
        try:
            account_info = self.client.futures_account()
            self.logger.info("Successfully connected to Binance Futures Testnet")
            self.logger.info(f"Account Balance: {account_info['totalWalletBalance']} USDT")
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        try:
            exchange_info = self.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol.upper():
                    return s
            raise ValueError(f"Symbol {symbol} not found")
        except Exception as e:
            self.logger.error(f"Error getting symbol info: {e}")
            raise
    
    def validate_quantity(self, symbol: str, quantity: float) -> float:
        try:
            symbol_info = self.get_symbol_info(symbol)
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    min_qty = float(f['minQty'])
                    max_qty = float(f['maxQty'])
                    step_size = float(f['stepSize'])
                    
                    if quantity < min_qty:
                        raise ValueError(f"Quantity {quantity} below minimum {min_qty}")
                    if quantity > max_qty:
                        raise ValueError(f"Quantity {quantity} above maximum {max_qty}")
                    
                    precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
                    adjusted_qty = round(quantity, precision)
                    
                    return adjusted_qty
            
            return quantity
        except Exception as e:
            self.logger.error(f"Error validating quantity: {e}")
            raise
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        try:
            symbol = symbol.upper()
            side = side.upper()
            
            if side not in ['BUY', 'SELL']:
                raise ValueError("Side must be 'BUY' or 'SELL'")
            
            quantity = self.validate_quantity(symbol, quantity)
            
            self.logger.info(f"Placing MARKET {side} order: {quantity} {symbol}")
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            self.logger.info("Market order placed successfully")
            self.logger.info(f"Order ID: {order['orderId']}")
            self.logger.info(f"Status: {order['status']}")
            
            return order
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error placing market order: {e}")
            raise
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        try:
            symbol = symbol.upper()
            side = side.upper()
            
            if side not in ['BUY', 'SELL']:
                raise ValueError("Side must be 'BUY' or 'SELL'")
            
            quantity = self.validate_quantity(symbol, quantity)
            
            self.logger.info(f"Placing LIMIT {side} order: {quantity} {symbol} at {price}")
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=Client.ORDER_TYPE_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=str(price)
            )
            
            self.logger.info("Limit order placed successfully")
            self.logger.info(f"Order ID: {order['orderId']}")
            self.logger.info(f"Status: {order['status']}")
            
            return order
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error placing limit order: {e}")
            raise
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, stop_price: float, limit_price: float) -> Dict[str, Any]:
        try:
            symbol = symbol.upper()
            side = side.upper()
            
            if side not in ['BUY', 'SELL']:
                raise ValueError("Side must be 'BUY' or 'SELL'")
            
            quantity = self.validate_quantity(symbol, quantity)
            
            self.logger.info(f"Placing STOP_LIMIT {side} order: {quantity} {symbol}")
            self.logger.info(f"Stop Price: {stop_price}, Limit Price: {limit_price}")
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=Client.ORDER_TYPE_STOP,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=str(limit_price),
                stopPrice=str(stop_price)
            )
            
            self.logger.info("Stop-limit order placed successfully")
            self.logger.info(f"Order ID: {order['orderId']}")
            
            return order
            
        except Exception as e:
            self.logger.error(f"Error placing stop-limit order: {e}")
            raise
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        try:
            order = self.client.futures_get_order(symbol=symbol.upper(), orderId=order_id)
            return order
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        try:
            result = self.client.futures_cancel_order(symbol=symbol.upper(), orderId=order_id)
            self.logger.info(f"Order {order_id} cancelled successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            raise
    
    def get_account_balance(self) -> Dict[str, Any]:
        try:
            account = self.client.futures_account()
            return {
                'total_balance': account['totalWalletBalance'],
                'available_balance': account['availableBalance'],
                'total_unrealized_pnl': account['totalUnrealizedProfit']
            }
        except Exception as e:
            self.logger.error(f"Error getting account balance: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol.upper())
            return float(ticker['price'])
        except Exception as e:
            self.logger.error(f"Error getting current price: {e}")
            raise


def display_menu():
    print("\n" + "="*50)
    print("BINANCE FUTURES TRADING BOT (TESTNET)")
    print("="*50)
    print("1. Place Market Order")
    print("2. Place Limit Order") 
    print("3. Place Stop-Limit Order")
    print("4. Check Order Status")
    print("5. Cancel Order")
    print("6. View Account Balance")
    print("7. Get Current Price")
    print("8. Exit")
    print("="*50)


def get_user_input(prompt: str, input_type: type = str):
    while True:
        try:
            value = input(prompt)
            if input_type == float:
                return float(value)
            elif input_type == int:
                return int(value)
            else:
                return value
        except ValueError:
            print(f"Invalid input. Please enter a valid {input_type.__name__}")


def main():
    print("Welcome to Binance Futures Trading Bot!")
    print("Please enter your API credentials:")
    
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    
    if not api_key or not api_secret:
        print("API credentials are required!")
        return
    
    try:
        bot = BasicBot(api_key, api_secret, testnet=True)
        
        while True:
            display_menu()
            choice = input("Select an option (1-8): ").strip()
            
            try:
                if choice == '1':
                    symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ").strip().upper()
                    side = get_user_input("Enter side (BUY/SELL): ").strip().upper()
                    quantity = get_user_input("Enter quantity: ", float)
                    
                    order = bot.place_market_order(symbol, side, quantity)
                    print(f"\nMarket Order Result:")
                    print(f"Order ID: {order['orderId']}")
                    print(f"Status: {order['status']}")
                    print(f"Executed Quantity: {order['executedQty']}")
                    
                elif choice == '2':
                    symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ").strip().upper()
                    side = get_user_input("Enter side (BUY/SELL): ").strip().upper()
                    quantity = get_user_input("Enter quantity: ", float)
                    price = get_user_input("Enter limit price: ", float)
                    
                    order = bot.place_limit_order(symbol, side, quantity, price)
                    print(f"\nLimit Order Result:")
                    print(f"Order ID: {order['orderId']}")
                    print(f"Status: {order['status']}")
                    print(f"Price: {order['price']}")
                    
                elif choice == '3':
                    symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ").strip().upper()
                    side = get_user_input("Enter side (BUY/SELL): ").strip().upper()
                    quantity = get_user_input("Enter quantity: ", float)
                    stop_price = get_user_input("Enter stop price: ", float)
                    limit_price = get_user_input("Enter limit price: ", float)
                    
                    order = bot.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
                    print(f"\nStop-Limit Order Result:")
                    print(f"Order ID: {order['orderId']}")
                    print(f"Status: {order['status']}")
                    
                elif choice == '4':
                    symbol = get_user_input("Enter symbol: ").strip().upper()
                    order_id = get_user_input("Enter order ID: ", int)
                    
                    order = bot.get_order_status(symbol, order_id)
                    print(f"\nOrder Status:")
                    print(f"Order ID: {order['orderId']}")
                    print(f"Status: {order['status']}")
                    print(f"Side: {order['side']}")
                    print(f"Quantity: {order['origQty']}")
                    print(f"Executed: {order['executedQty']}")
                    print(f"Price: {order.get('price', 'N/A')}")
                    
                elif choice == '5':
                    symbol = get_user_input("Enter symbol: ").strip().upper()
                    order_id = get_user_input("Enter order ID: ", int)
                    
                    result = bot.cancel_order(symbol, order_id)
                    print(f"\nOrder cancelled: {result['orderId']}")
                    
                elif choice == '6':
                    balance = bot.get_account_balance()
                    print(f"\nAccount Balance:")
                    print(f"Total Balance: {balance['total_balance']} USDT")
                    print(f"Available Balance: {balance['available_balance']} USDT")
                    print(f"Unrealized PnL: {balance['total_unrealized_pnl']} USDT")
                    
                elif choice == '7':
                    symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ").strip().upper()
                    price = bot.get_current_price(symbol)
                    print(f"\nCurrent Price of {symbol}: ${price:,.2f}")
                    
                elif choice == '8':
                    print("Goodbye! Happy trading!")
                    break
                    
                else:
                    print("Invalid option. Please select 1-8.")
                    
            except Exception as e:
                print(f"\nError: {e}")
                
    except Exception as e:
        print(f"Failed to initialize bot: {e}")


if __name__ == "__main__":
    main()
