#!/usr/bin/env python3
"""
Kraken VWAP Mean Reversion Trading Bot
US-Compliant Automated Trading for BTC/USD
"""

import requests
import base64
import hashlib
import hmac
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import urllib.parse

# Load credentials
load_dotenv('/root/.openclaw/workspace/.env')
API_KEY = os.getenv('KRAKEN_API_KEY')
API_SECRET = os.getenv('KRAKEN_API_SECRET')

# Kraken API endpoints
API_URL = 'https://api.kraken.com'
PUBLIC_ENDPOINT = '/0/public'
PRIVATE_ENDPOINT = '/0/private'

class KrakenTrader:
    def __init__(self, paper_mode=False):
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self.paper_mode = paper_mode
        
        # Strategy parameters (from MCMC optimization)
        self.entry_bias = 0.0023  # 0.23% below VWAP
        self.exit_bias = 0.0028   # 0.28% above VWAP
        self.stop_loss = 0.015    # 1.5% stop loss
        self.position_pct = 0.95  # Use 95% of available balance (leave room for fees)
        
        # Trading pair
        self.pair = 'XXBTZUSD'  # BTC/USD on Kraken
        
        # Track position state
        self.in_position = False
        self.btc_balance = 0.0
        
        print(f"🚀 Kraken Trader Initialized")
        print(f"   Mode: {'PAPER' if paper_mode else 'LIVE'}")
        print(f"   Pair: BTC/USD")
        print(f"   Strategy: VWAP Mean Reversion")
        print(f"   Position Size: {self.position_pct*100:.0f}% of available balance")
        
    def _get_signature(self, urlpath, data):
        """Generate Kraken API signature"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
        return base64.b64encode(signature.digest()).decode()
    
    def _private_request(self, endpoint, data=None):
        """Make authenticated request to Kraken"""
        if data is None:
            data = {}
        
        data['nonce'] = int(time.time() * 1000)
        
        headers = {
            'API-Key': self.api_key,
            'API-Sign': self._get_signature(endpoint, data)
        }
        
        url = API_URL + endpoint
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code}")
        
        result = response.json()
        
        if result.get('error'):
            raise Exception(f"Kraken Error: {result['error']}")
        
        return result['result']
    
    def _public_request(self, endpoint, params=None):
        """Make public request to Kraken"""
        url = API_URL + PUBLIC_ENDPOINT + endpoint
        
        if params:
            url += '?' + urllib.parse.urlencode(params)
        
        response = requests.get(url)
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code}")
        
        result = response.json()
        
        if result.get('error'):
            raise Exception(f"Kraken Error: {result['error']}")
        
        return result['result']
    
    def get_balance(self):
        """Get account balance - uses full available balance"""
        try:
            balance = self._private_request('/0/private/Balance')
            
            # Extract actual balances
            usd_balance = float(balance.get('ZUSD', 0))
            btc_balance = float(balance.get('XXBT', 0))
            
            print(f"💰 Balance: ${usd_balance:.2f} USD | {btc_balance:.6f} BTC")
            
            # Update position tracking
            self.btc_balance = btc_balance
            self.in_position = btc_balance > 0.0001  # Has meaningful BTC position
            
            return {'USD': usd_balance, 'BTC': btc_balance}
        except Exception as e:
            print(f"❌ Error getting balance: {e}")
            return None
    
    def get_ticker(self):
        """Get current BTC price"""
        try:
            ticker = self._public_request('/Ticker', {'pair': 'XBTUSD'})
            price = float(ticker['XXBTZUSD']['c'][0])
            print(f"📊 BTC Price: ${price:,.2f}")
            return price
        except Exception as e:
            print(f"❌ Error getting ticker: {e}")
            return None
    
    def get_ohlc(self, interval=1, since=None):
        """Get OHLC data for VWAP calculation"""
        try:
            params = {
                'pair': 'XBTUSD',
                'interval': interval  # 1 minute
            }
            if since:
                params['since'] = since
            
            ohlc = self._public_request('/OHLC', params)
            
            # Parse data
            data = ohlc['XXBTZUSD']
            df = pd.DataFrame(data, columns=[
                'time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
            ])
            
            # Convert types
            for col in ['open', 'high', 'low', 'close', 'vwap', 'volume']:
                df[col] = df[col].astype(float)
            
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return df
        except Exception as e:
            print(f"❌ Error getting OHLC: {e}")
            return None
    
    def calculate_vwap(self, df, period=20):
        """Calculate VWAP"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).rolling(period).sum() / df['volume'].rolling(period).sum()
        return vwap
    
    def check_signals(self):
        """Check for entry/exit signals"""
        print("\n🔍 Checking signals...")
        
        # Get current balance first
        balance = self.get_balance()
        if balance is None:
            print("❌ Could not get balance")
            return None
        
        # Get recent data
        df = self.get_ohlc(interval=1)
        if df is None or len(df) < 20:
            print("❌ Not enough data")
            return None
        
        # Calculate VWAP
        df['vwap'] = self.calculate_vwap(df)
        
        # Get latest values
        latest = df.iloc[-1]
        price = latest['close']
        vwap = latest['vwap']
        
        if pd.isna(vwap):
            print("❌ VWAP not calculated yet")
            return None
        
        # Calculate distance from VWAP
        distance = (price - vwap) / vwap
        
        print(f"   Price: ${price:,.2f}")
        print(f"   VWAP: ${vwap:,.2f}")
        print(f"   Distance: {distance*100:.2f}%")
        print(f"   In Position: {self.in_position}")
        
        # Check signals - only buy if not in position, only sell if in position
        signal = None
        
        if not self.in_position and distance < -self.entry_bias:
            signal = 'BUY'
            print(f"   🟢 BUY SIGNAL: Price {abs(distance)*100:.2f}% below VWAP")
        elif self.in_position and distance > self.exit_bias:
            signal = 'SELL'
            print(f"   🔴 SELL SIGNAL: Price {distance*100:.2f}% above VWAP")
        else:
            if self.in_position:
                print(f"   ⚪ HOLDING: In position, waiting for exit signal")
            else:
                print(f"   ⚪ NO SIGNAL: Within normal range")
        
        return {
            'signal': signal,
            'price': price,
            'vwap': vwap,
            'distance': distance,
            'balance': balance
        }
    
    def send_telegram_alert(self, message):
        """Send Telegram notification"""
        try:
            # Read bot token from .env
            load_dotenv('/root/.openclaw/workspace/.env')
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8408186208:AAEF13uGjhHjIEMnyO4ogLqnUb1ZrT_Q3jw')
            chat_id = '7660866897'  # Scott's Telegram ID
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                print("📱 Telegram alert sent")
            else:
                print(f"⚠️ Telegram alert failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Telegram alert error: {e}")
    
    def write_trade_alert(self, side, price, amount, txid):
        """Write trade to alerts file"""
        try:
            alert_file = '/root/.openclaw/workspace/trading/.trade_alerts'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(alert_file, 'a') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"🟢 LIVE {side} @ ${price:,.2f} | {timestamp}\n")
                f.write(f"   Amount: {amount:.6f} BTC\n")
                f.write(f"   TXID: {txid}\n")
                f.write(f"{'='*50}\n")
            
            print(f"📝 Trade alert written to {alert_file}")
        except Exception as e:
            print(f"⚠️ Failed to write trade alert: {e}")
    
    def place_order(self, side, volume, price=None, order_type='market'):
        """Place an order"""
        if self.paper_mode:
            print(f"\n📋 PAPER TRADE: {side} {volume} BTC @ ${price:,.2f}")
            return {'txid': 'PAPER_TRADE_' + str(int(time.time()))}
        
        try:
            data = {
                'pair': self.pair,
                'type': side.lower(),
                'ordertype': order_type,
                'volume': str(volume)
            }
            
            if price and order_type == 'limit':
                data['price'] = str(price)
            
            result = self._private_request('/0/private/AddOrder', data)
            print(f"✅ Order placed: {result}")
            
            # Send notifications
            print(f"📝 DEBUG: Checking result for notifications...")
            print(f"📝 DEBUG: result type = {type(result)}, has txid = {'txid' in result if result else False}")
            
            if result and 'txid' in result:
                txid = result['txid'][0] if isinstance(result['txid'], list) else result['txid']
                print(f"📝 DEBUG: Sending notifications for {side} order, txid={txid}")
                
                # Telegram alert
                emoji = "🟢" if side.lower() == 'buy' else "🔴"
                telegram_msg = f"<b>{emoji} LIVE TRADE EXECUTED</b>\n\n"
                telegram_msg += f"<b>Side:</b> {side.upper()}\n"
                telegram_msg += f"<b>Price:</b> ${price:,.2f}\n"
                telegram_msg += f"<b>Amount:</b> {volume:.6f} BTC\n"
                telegram_msg += f"<b>TXID:</b> <code>{txid}</code>\n"
                telegram_msg += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                self.send_telegram_alert(telegram_msg)
                
                # Write to alerts file
                self.write_trade_alert(side.upper(), price, volume, txid)
            else:
                print(f"⚠️ DEBUG: No txid in result, skipping notifications")
            
            return result
        except Exception as e:
            print(f"❌ Error placing order: {e}")
            return None
    
    def run(self):
        """Main trading loop"""
        print("\n" + "="*60)
        print("Starting Kraken VWAP Trader")
        print("="*60)
        
        # Get initial balance
        self.get_balance()
        
        # Main loop
        while True:
            try:
                # Check signals
                signal_data = self.check_signals()
                
                if signal_data and signal_data['signal']:
                    signal = signal_data['signal']
                    price = signal_data['price']
                    balance = signal_data['balance']
                    
                    if signal == 'BUY':
                        # Use 95% of USD balance
                        trade_amount = balance['USD'] * self.position_pct
                        volume = trade_amount / price
                        print(f"\n💵 Buying with ${trade_amount:.2f} ({self.position_pct*100:.0f}% of ${balance['USD']:.2f})")
                        self.place_order('buy', volume, price)
                        
                    elif signal == 'SELL':
                        # Sell 100% of BTC holdings
                        volume = balance['BTC']
                        print(f"\n💵 Selling {volume:.6f} BTC ({self.position_pct*100:.0f}% of holdings)")
                        self.place_order('sell', volume, price)
                
                # Wait before next check
                print(f"\n⏰ Waiting 60 seconds...")
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping trader...")
                break
            except Exception as e:
                print(f"\n❌ Error in main loop: {e}")
                time.sleep(60)

if __name__ == '__main__':
    # Create trader in LIVE mode
    trader = KrakenTrader(paper_mode=False)
    
    # Test connection
    print("\n🧪 Testing connection...")
    price = trader.get_ticker()
    
    if price:
        print("✅ Connection successful!")
        print("⚠️  LIVE TRADING ACTIVE - REAL MONEY AT RISK")
        
        # Run trader
        try:
            trader.run()
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ Connection failed. Check API keys.")
