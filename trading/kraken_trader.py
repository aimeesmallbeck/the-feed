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

# Load credentials
load_dotenv('/root/.openclaw/workspace/.env')
API_KEY = os.getenv('KRAKEN_API_KEY')
API_SECRET = os.getenv('KRAKEN_API_SECRET')

# Kraken API endpoints
API_URL = 'https://api.kraken.com'
PUBLIC_ENDPOINT = '/0/public'
PRIVATE_ENDPOINT = '/0/private'

class KrakenTrader:
    def __init__(self, paper_mode=True):
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self.paper_mode = paper_mode
        
        # Strategy parameters (from MCMC optimization)
        self.entry_bias = 0.0023  # 0.23% below VWAP
        self.exit_bias = 0.0028   # 0.28% above VWAP
        self.stop_loss = 0.015    # 1.5% stop loss
        self.position_size = 100  # USD per trade
        
        # Trading pair
        self.pair = 'XXBTZUSD'  # BTC/USD on Kraken
        
        print(f"🚀 Kraken Trader Initialized")
        print(f"   Mode: {'PAPER' if paper_mode else 'LIVE'}")
        print(f"   Pair: BTC/USD")
        print(f"   Strategy: VWAP Mean Reversion")
        
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
        """Get account balance"""
        try:
            balance = self._private_request('/0/private/Balance')
            print(f"💰 Balance: {balance}")
            return balance
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
        
        # Check signals
        signal = None
        
        if distance < -self.entry_bias:
            signal = 'BUY'
            print(f"   🟢 BUY SIGNAL: Price {abs(distance)*100:.2f}% below VWAP")
        elif distance > self.exit_bias:
            signal = 'SELL'
            print(f"   🔴 SELL SIGNAL: Price {distance*100:.2f}% above VWAP")
        else:
            print(f"   ⚪ NO SIGNAL: Within normal range")
        
        return {
            'signal': signal,
            'price': price,
            'vwap': vwap,
            'distance': distance
        }
    
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
                    
                    # Calculate position size
                    volume = self.position_size / price
                    
                    if signal == 'BUY':
                        self.place_order('buy', volume, price)
                    elif signal == 'SELL':
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
    import urllib.parse
    
    # Create trader in paper mode
    trader = KrakenTrader(paper_mode=True)
    
    # Test connection
    print("\n🧪 Testing connection...")
    price = trader.get_ticker()
    
    if price:
        print("✅ Connection successful!")
        
        # Run trader
        try:
            trader.run()
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ Connection failed. Check API keys.")
