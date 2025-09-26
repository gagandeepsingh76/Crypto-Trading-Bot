import logging 
import sys
import time
import json
from decimal import Decimal
from typing import Optional, Dict, Any, List
from binance import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from datetime import datetime
import requests

class BasicBot:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize the trading bot with API credentials
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet (default: True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        self.setup_logging()
        
        self.client = None
        self.initialize_client()
        
        self.test_connection()
    
    def setup_logging(self):
        """Setup comprehensive logging configuration"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler = logging.FileHandler('bot1.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.propagate = False
    
    def initialize_client(self):
        """Initialize Binance client with multiple configuration attempts"""
        configs = [
            {
                'name': 'Standard Testnet (binance.vision)',
                'testnet': True,
                'base_url': None,
                'futures_url': None
            },
            {
                'name': 'Futures Testnet (binancefuture.com)', 
                'testnet': True,
                'base_url': 'https://testnet.binancefuture.com',
                'futures_url': 'https://testnet.binancefuture.com'
            },
            {
                'name': 'Alternative Testnet Configuration',
                'testnet': True, 
                'base_url': 'https://testnet.binance.vision',
                'futures_url': 'https://testnet.binance.vision'
            }
        ]
        
        for config in configs:
            try:
                if self.testnet:
                    self.logger.info(f"Trying {config['name']}...")
                    client = Client(self.api_key, self.api_secret, testnet=True, tld='com')
                    
                    if config['base_url']:
                        client.API_URL = config['base_url']
                    if config['futures_url']:
                        client.FUTURES_API_URL = config['futures_url']
                else:
                    self.logger.info("Initializing mainnet client...")
                    client = Client(self.api_key, self.api_secret, testnet=False)
                
                server_time = client.futures_time()
                self.client = client
                self.logger.info(f"SUCCESS: Using {config['name']}")
                return
                
            except Exception as e:
                self.logger.warning(f"Failed {config['name']}: {e}")
                continue
        
        raise Exception("Could not initialize client with any configuration")
    
    def test_connection(self):
        """Comprehensive connection and permission testing"""
        try:
            self.logger.info("Testing server connectivity...")
            server_time = self.client.futures_time()
            self.logger.info(f"Server time: {server_time['serverTime']}")
            
            self.logger.info("Testing account access...")
            account_info = self.client.futures_account()
            
            self.logger.info("Testing trading permissions...")
            positions = self.client.futures_position_information()
            
            self.logger.info("=== CONNECTION SUCCESSFUL ===")
            self.logger.info(f"Account Balance: {account_info['totalWalletBalance']} USDT")
            self.logger.info(f"Available Balance: {account_info['availableBalance']} USDT")
            self.logger.info(f"API Permissions: OK ({len(positions)} position entries found)")
            
            return True
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Error: {e.code} - {e.message}")
            self.handle_api_error(e.code, e.message)
            raise
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            raise
    
    def handle_api_error(self, code: int, message: str):
        """Provide specific guidance for API errors"""
        error_solutions = {
            -2015: """
API KEY PERMISSION ERROR (-2015):
1. Verify you're using TESTNET API keys from testnet.binance.vision
2. Ensure 'Enable Futures' is checked in your API settings
3. Check if IP restrictions are blocking your access
4. Try creating fresh API keys and wait 5 minutes
""",
            -1021: """
TIMESTAMP ERROR (-1021):
Your computer clock is out of sync with Binance servers.
Solution: Synchronize your system clock.
""",
            -2014: """
API KEY FORMAT ERROR (-2014):
Your API key format is invalid.
Check for typos or extra spaces in your credentials.
""",
            -1022: """
SIGNATURE ERROR (-1022):
Your API secret is incorrect or request signature failed.
Verify your API secret key is correct.
"""
        }
        
        solution = error_solutions.get(code, f"Unknown error code {code}: {message}")
        print(solution)
    
    def log_request(self, action: str, params: Dict[str, Any]):
        """Log API requests"""
        self.logger.info(f"API REQUEST: {action}")
        self.logger.info(f"Parameters: {json.dumps(params, indent=2)}")
    
    def log_response(self, action: str, response: Dict[str, Any]):
        """Log API responses"""
        self.logger.info(f"API RESPONSE: {action}")
        self.logger.info(f"Response: {json.dumps(response, indent=2, default=str)}")
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information for validation"""
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
        """Validate and adjust quantity based on symbol filters"""
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
        """
        Place a market order
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
        
        Returns:
            Order response dictionary
        """
        try:
            symbol = symbol.upper()
            side = side.upper()
            
            if side not in ['BUY', 'SELL']:
                raise ValueError("Side must be 'BUY' or 'SELL'")
            
            quantity = self.validate_quantity(symbol, quantity)
            
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity
            }
            self.log_request('MARKET_ORDER', params)
            
            self.logger.info(f"Placing MARKET {side} order: {quantity} {symbol}")
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            self.log_response('MARKET_ORDER', order)
            
            self.logger.info(f"SUCCESS: Market order placed")
            self.logger.info(f"Order ID: {order['orderId']}")
            self.logger.info(f"Status: {order['status']}")
            self.logger.info(f"Executed Quantity: {order['executedQty']}")
            
            return order
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Error: {e.code} - {e.message}")
            raise
        except Exception as e:
            self.logger.error(f"Error placing market order: {e}")
            raise
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        """
        Place a limit order
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Limit price
        
        Returns:
            Order response dictionary
        """
        try:
            symbol = symbol.upper()
            side = side.upper()
            
            if side not in ['BUY', 'SELL']:
                raise ValueError("Side must be 'BUY' or 'SELL'")
            
            quantity = self.validate_quantity(symbol, quantity)
            
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'LIMIT',
                'quantity': quantity,
                'price': price
            }
            self.log_request('LIMIT_ORDER', params)
            
            self.logger.info(f"Placing LIMIT {side} order: {quantity} {symbol} at {price}")
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=Client.ORDER_TYPE_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=str(price)
            )
            
            self.log_response('LIMIT_ORDER', order)
            
            self.logger.info(f"SUCCESS: Limit order placed")
            self.logger.info(f"Order ID: {order['orderId']}")
            self.logger.info(f"Status: {order['status']}")
            
            return order
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Error: {e.code} - {e.message}")
            raise
        except Exception as e:
            self.logger.error(f"Error placing limit order: {e}")
            raise
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, 
                              stop_price: float, limit_price: float) -> Dict[str, Any]:
        """
        Place a stop-limit order (Advanced order type)
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'  
            quantity: Order quantity
            stop_price: Stop trigger price
            limit_price: Limit price after trigger
        
        Returns:
            Order response dictionary
        """
        try:
            symbol = symbol.upper()
            side = side.upper()
            
            if side not in ['BUY', 'SELL']:
                raise ValueError("Side must be 'BUY' or 'SELL'")
            
            quantity = self.validate_quantity(symbol, quantity)
            
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'STOP',
                'quantity': quantity,
                'stopPrice': stop_price,
                'price': limit_price
            }
            self.log_request('STOP_LIMIT_ORDER', params)
            
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
            
            self.log_response('STOP_LIMIT_ORDER', order)
            
            self.logger.info(f"SUCCESS: Stop-limit order placed")
            self.logger.info(f"Order ID: {order['orderId']}")
            
            return order
            
        except Exception as e:
            self.logger.error(f"Error placing stop-limit order: {e}")
            raise
    
    def place_oco_order(self, symbol: str, side: str, quantity: float, 
                       price: float, stop_price: float, stop_limit_price: float) -> List[Dict[str, Any]]:
        """
        Place an OCO (One-Cancels-Other) order (Advanced order type)
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity  
            price: Limit order price
            stop_price: Stop loss trigger price
            stop_limit_price: Stop loss limit price
        
        Returns:
            List of order responses
        """
        try:
            symbol = symbol.upper()
            side = side.upper()
            
            if side not in ['BUY', 'SELL']:
                raise ValueError("Side must be 'BUY' or 'SELL'")
            
            quantity = self.validate_quantity(symbol, quantity)
            
            params = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'stopPrice': stop_price,
                'stopLimitPrice': stop_limit_price
            }
            self.log_request('OCO_ORDER', params)
            
            self.logger.info(f"Placing OCO {side} order: {quantity} {symbol}")
            self.logger.info(f"Limit Price: {price}, Stop Price: {stop_price}, Stop Limit: {stop_limit_price}")
            
            orders = []
            
            limit_order = self.place_limit_order(symbol, side, quantity/2, price)
            orders.append(limit_order)
            
            stop_order = self.place_stop_limit_order(symbol, side, quantity/2, stop_price, stop_limit_price)
            orders.append(stop_order)
            
            self.logger.info(f"SUCCESS: OCO-style orders placed (2 separate orders)")
            
            return orders
            
        except Exception as e:
            self.logger.error(f"Error placing OCO order: {e}")
            raise
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status"""
        try:
            self.log_request('GET_ORDER_STATUS', {'symbol': symbol, 'orderId': order_id})
            
            order = self.client.futures_get_order(symbol=symbol.upper(), orderId=order_id)
            
            self.log_response('GET_ORDER_STATUS', order)
            return order
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            self.log_request('CANCEL_ORDER', {'symbol': symbol, 'orderId': order_id})
            
            result = self.client.futures_cancel_order(symbol=symbol.upper(), orderId=order_id)
            
            self.log_response('CANCEL_ORDER', result)
            self.logger.info(f"SUCCESS: Order {order_id} cancelled")
            return result
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            raise
    
    def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        try:
            self.log_request('GET_ACCOUNT_BALANCE', {})
            
            account = self.client.futures_account()
            balance_info = {
                'total_balance': account['totalWalletBalance'],
                'available_balance': account['availableBalance'],
                'total_unrealized_pnl': account['totalUnrealizedProfit'],
                'total_margin_balance': account['totalMarginBalance']
            }
            
            self.log_response('GET_ACCOUNT_BALANCE', balance_info)
            return balance_info
        except Exception as e:
            self.logger.error(f"Error getting account balance: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        try:
            self.log_request('GET_CURRENT_PRICE', {'symbol': symbol})
            
            ticker = self.client.futures_symbol_ticker(symbol=symbol.upper())
            price = float(ticker['price'])
            
            self.log_response('GET_CURRENT_PRICE', {'symbol': symbol, 'price': price})
            return price
        except Exception as e:
            self.logger.error(f"Error getting current price: {e}")
            raise
    
    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open orders"""
        try:
            params = {'symbol': symbol} if symbol else {}
            self.log_request('GET_OPEN_ORDERS', params)
            
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol.upper())
            else:
                orders = self.client.futures_get_open_orders()
            
            self.log_response('GET_OPEN_ORDERS', {'count': len(orders)})
            return orders
        except Exception as e:
            self.logger.error(f"Error getting open orders: {e}")
            raise


def display_menu():
    """Display enhanced CLI menu"""
    print("\n" + "="*60)
    print("        BINANCE FUTURES TRADING BOT (ENHANCED)")
    print("="*60)
    print("📊 BASIC TRADING")
    print("1. Place Market Order")
    print("2. Place Limit Order") 
    print("\n🔧 ADVANCED TRADING")
    print("3. Place Stop-Limit Order")
    print("4. Place OCO Order")
    print("\n📋 ORDER MANAGEMENT") 
    print("5. Check Order Status")
    print("6. Cancel Order")
    print("7. View Open Orders")
    print("\n💰 ACCOUNT INFO")
    print("8. View Account Balance")
    print("9. Get Current Price")
    print("\n⚙️ SYSTEM")
    print("10. View Logs")
    print("11. Exit")
    print("="*60)


def get_user_input(prompt: str, input_type: type = str, allow_empty: bool = False):
    """Enhanced user input with validation"""
    while True:
        try:
            value = input(prompt).strip()
            if not value and not allow_empty:
                print("ERROR: Input cannot be empty")
                continue
            if not value and allow_empty:
                return None
            if input_type == float:
                return float(value)
            elif input_type == int:
                return int(value)
            else:
                return value
        except ValueError:
            print(f"ERROR: Invalid input. Please enter a valid {input_type.__name__}")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return None


def display_order_result(order: Dict[str, Any]):
    """Display formatted order result"""
    print(f"\n{'='*50}")
    print("ORDER EXECUTION RESULT")
    print(f"{'='*50}")
    print(f"Order ID: {order['orderId']}")
    print(f"Symbol: {order['symbol']}")
    print(f"Side: {order['side']}")
    print(f"Type: {order['type']}")
    print(f"Quantity: {order['origQty']}")
    print(f"Status: {order['status']}")
    if 'price' in order and order['price']:
        print(f"Price: {order['price']}")
    if 'executedQty' in order:
        print(f"Executed Quantity: {order['executedQty']}")
    print(f"{'='*50}")


def main():
    """Enhanced main CLI interface"""
    print("="*60)
    print("    WELCOME TO BINANCE FUTURES TRADING BOT")
    print("="*60)
    print("Please enter your API credentials:")
    print("(Use testnet credentials from testnet.binance.vision)")
    
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    
    if not api_key or not api_secret:
        print("ERROR: API credentials are required!")
        return
    
    print("\nTrading Environment:")
    print("1. Testnet (Recommended for learning)")
    print("2. Mainnet (Real trading - USE WITH CAUTION)")
    env_choice = input("Select environment (1-2): ").strip()
    
    testnet = True if env_choice == '1' else False
    
    if not testnet:
        confirm = input("WARNING: You selected MAINNET (real money). Type 'CONFIRM' to proceed: ")
        if confirm != 'CONFIRM':
            print("Switching to testnet for safety.")
            testnet = True
    
    try:
        print(f"\nInitializing bot ({'TESTNET' if testnet else 'MAINNET'})...")
        bot = BasicBot(api_key, api_secret, testnet=testnet)
        
        while True:
            display_menu()
            choice = input("Select an option (1-11): ").strip()
            
            try:
                if choice == '1':
                    print("\n--- MARKET ORDER ---")
                    symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ").upper()
                    side = get_user_input("Enter side (BUY/SELL): ").upper()
                    quantity = get_user_input("Enter quantity: ", float)
                    
                    if symbol and side and quantity:
                        order = bot.place_market_order(symbol, side, quantity)
                        display_order_result(order)
                    
                elif choice == '2':
                    print("\n--- LIMIT ORDER ---")
                    symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ").upper()
                    side = get_user_input("Enter side (BUY/SELL): ").upper()
                    quantity = get_user_input("Enter quantity: ", float)
                    price = get_user_input("Enter limit price: ", float)
                    
                    if all([symbol, side, quantity, price]):
                        order = bot.place_limit_order(symbol, side, quantity, price)
                        display_order_result(order)
                    
                elif choice == '3':
                    print("\n--- STOP-LIMIT ORDER ---")
                    symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ").upper()
                    side = get_user_input("Enter side (BUY/SELL): ").upper()
                    quantity = get_user_input("Enter quantity: ", float)
                    stop_price = get_user_input("Enter stop price: ", float)
                    limit_price = get_user_input("Enter limit price: ", float)
                    
                    if all([symbol, side, quantity, stop_price, limit_price]):
                        order = bot.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
                        display_order_result(order)
                    
                elif choice == '4':
                    print("\n--- OCO ORDER ---")
                    symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ").upper()
                    side = get_user_input("Enter side (BUY/SELL): ").upper()
                    quantity = get_user_input("Enter quantity: ", float)
                    price = get_user_input("Enter limit price: ", float)
                    stop_price = get_user_input("Enter stop price: ", float)
                    stop_limit_price = get_user_input("Enter stop limit price: ", float)
                    
                    if all([symbol, side, quantity, price, stop_price, stop_limit_price]):
                        orders = bot.place_oco_order(symbol, side, quantity, price, stop_price, stop_limit_price)
                        print(f"\nOCO orders placed: {len(orders)} orders")
                        for i, order in enumerate(orders, 1):
                            print(f"\nOrder {i}:")
                            display_order_result(order)
                    
                elif choice == '5':
                    print("\n--- ORDER STATUS ---")
                    symbol = get_user_input("Enter symbol: ").upper()
                    order_id = get_user_input("Enter order ID: ", int)
                    
                    if symbol and order_id:
                        order = bot.get_order_status(symbol, order_id)
                        display_order_result(order)
                    
                elif choice == '6':
                    print("\n--- CANCEL ORDER ---")
                    symbol = get_user_input("Enter symbol: ").upper()
                    order_id = get_user_input("Enter order ID: ", int)
                    
                    if symbol and order_id:
                        result = bot.cancel_order(symbol, order_id)
                        print(f"\nSUCCESS: Order {result['orderId']} cancelled")
                    
                elif choice == '7':
                    print("\n--- OPEN ORDERS ---")
                    symbol = get_user_input("Enter symbol (or press Enter for all): ", allow_empty=True)
                    
                    orders = bot.get_open_orders(symbol)
                    if orders:
                        print(f"\nFound {len(orders)} open orders:")
                        for order in orders:
                            print(f"ID: {order['orderId']}, {order['symbol']}, {order['side']}, {order['origQty']}, Status: {order['status']}")
                    else:
                        print("No open orders found")
                    
                elif choice == '8':
                    print("\n--- ACCOUNT BALANCE ---")
                    balance = bot.get_account_balance()
                    print(f"Total Balance: {balance['total_balance']} USDT")
                    print(f"Available Balance: {balance['available_balance']} USDT")
                    print(f"Margin Balance: {balance['total_margin_balance']} USDT")
                    print(f"Unrealized PnL: {balance['total_unrealized_pnl']} USDT")
                    
                elif choice == '9':
                    print("\n--- CURRENT PRICE ---")
                    symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ").upper()
                    if symbol:
                        price = bot.get_current_price(symbol)
                        print(f"{symbol} Current Price: ${price:,.4f}")
                    
                elif choice == '10':
                    print("\n--- RECENT LOG ENTRIES ---")
                    try:
                        with open('bot1.log', 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            for line in lines[-20:]:
                                print(line.strip())
                    except FileNotFoundError:
                        print("No log file found")
                    
                elif choice == '11':
                    print("\nThank you for using Binance Futures Trading Bot!")
                    print("Happy trading! 🚀")
                    break
                    
                else:
                    print("ERROR: Invalid option. Please select 1-11.")
                    
            except KeyboardInterrupt:
                print("\nOperation cancelled by user")
            except Exception as e:
                print(f"\nERROR: {e}")
                bot.logger.error(f"CLI Error: {e}")
                
    except Exception as e:
        print(f"ERROR: Failed to initialize bot: {e}")
        print("\nTroubleshooting tips:")
        print("1. Verify your API credentials")
        print("2. Ensure 'Enable Futures' permission is enabled")
        print("3. Try creating fresh testnet API keys from testnet.binance.vision")
        print("4. Check the log file 'bot1.log' for detailed errors")


if __name__ == "__main__":
    main()
