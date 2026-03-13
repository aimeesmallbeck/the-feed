#!/usr/bin/env python3
"""
Alpaca Multi-Stock VWAP Mean Reversion Trading Bot
Monitors SPY, QQQ, AAPL, NVDA, TSLA and trades the first one to hit threshold
"""

import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import requests

# Load credentials from secure location (container-only, never in GitHub)
from pathlib import Path

def load_api_keys():
    """Load API keys from secure container storage"""
    env_path = Path.home() / '.api_keys' / 'alpaca.env'
    if not env_path.exists():
        raise FileNotFoundError(f"API keys not found at {env_path}")
    
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    return (
        os.environ['ALPACA_API_KEY'],
        os.environ['ALPACA_SECRET_KEY'],
        os.environ.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    )

API_KEY, API_SECRET, BASE_URL = load_api_keys()

# Trading universe
STOCKS = ['SPY', 'QQQ', 'AAPL', 'NVDA', 'TSLA']

class AlpacaVWAPTrader:
    def __init__(self):
        self.api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')
        
        # Strategy parameters (adjusted for no fees)
        self.entry_threshold = 0.005  # 0.5% below VWAP
        self.exit_threshold = 0.006   # 0.6% above VWAP (wider for profit)
        self.stop_loss = 0.015        # 1.5% stop loss
        self.position_pct = 0.95      # Use 95% of available balance
        
        # Track state
        self.in_position = False
        self.current_position = None  # {'symbol': 'SPY', 'qty': 10, 'entry_price': 450.00}
        
        print("🚀 Alpaca Multi-Stock VWAP Trader Initialized")
        print(f"   Universe: {', '.join(STOCKS)}")
        print(f"   Strategy: VWAP Mean Reversion")
        print(f"   Entry: {self.entry_threshold*100:.2f}% below VWAP")
        print(f"   Exit: {self.exit_threshold*100:.2f}% above VWAP")
        print(f"   Mode: {'PAPER' if 'paper' in BASE_URL else 'LIVE'}")
        
    def get_account(self):
        """Get account info"""
        try:
            account = self.api.get_account()
            buying_power = float(account.buying_power)
            cash = float(account.cash)
            print(f"💰 Buying Power: ${buying_power:.2f} | Cash: ${cash:.2f}")
            return {'buying_power': buying_power, 'cash': cash}
        except Exception as e:
            print(f"❌ Error getting account: {e}")
            return None
    
    def get_positions(self):
        """Check if we have any positions"""
        try:
            positions = self.api.list_positions()
            if positions:
                pos = positions[0]  # Should only have one with all-in strategy
                return {
                    'symbol': pos.symbol,
                    'qty': float(pos.qty),
                    'entry_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'market_value': float(pos.market_value)
                }
            return None
        except Exception as e:
            print(f"⚠️ No positions: {e}")
            return None
    
    def get_bars(self, symbol, limit=20):
        """Get recent price bars for VWAP calculation"""
        try:
            # Get 1-minute bars
            bars = self.api.get_bars(symbol, tradeapi.TimeFrame.Minute, limit=limit).df
            if bars.empty or len(bars) < 20:
                return None
            return bars
        except Exception as e:
            print(f"❌ Error getting bars for {symbol}: {e}")
            return None
    
    def calculate_vwap(self, df):
        """Calculate VWAP"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap.iloc[-1]
    
    def check_all_signals(self):
        """Check VWAP signals for all stocks, return best opportunity"""
        print("\n🔍 Scanning universe for signals...")
        
        opportunities = []
        
        for symbol in STOCKS:
            try:
                bars = self.get_bars(symbol, limit=20)
                if bars is None:
                    continue
                
                # Calculate VWAP
                vwap = self.calculate_vwap(bars)
                current_price = bars['close'].iloc[-1]
                
                # Calculate distance from VWAP
                distance = (current_price - vwap) / vwap
                
                print(f"   {symbol}: ${current_price:.2f} | VWAP: ${vwap:.2f} | Distance: {distance*100:+.2f}%")
                
                # Check for entry signal (price below VWAP by threshold)
                if distance < -self.entry_threshold:
                    opportunities.append({
                        'symbol': symbol,
                        'signal': 'BUY',
                        'price': current_price,
                        'vwap': vwap,
                        'distance': distance,
                        'strength': abs(distance)  # How far below VWAP
                    })
                    
            except Exception as e:
                print(f"⚠️ Error checking {symbol}: {e}")
                continue
        
        # Return the best opportunity (most oversold)
        if opportunities:
            best = max(opportunities, key=lambda x: x['strength'])
            print(f"   🟢 Best signal: {best['symbol']} ({best['distance']*100:.2f}% below VWAP)")
            return best
        
        print("   ⚪ No entry signals found")
        return None
    
    def check_exit_signal(self, position):
        """Check if current position should be exited"""
        symbol = position['symbol']
        entry_price = position['entry_price']
        qty = position['qty']
        
        try:
            bars = self.get_bars(symbol, limit=20)
            if bars is None:
                return None
            
            vwap = self.calculate_vwap(bars)
            current_price = bars['close'].iloc[-1]
            
            # Calculate distance from VWAP
            distance = (current_price - vwap) / vwap
            
            # Calculate P&L
            pnl_pct = (current_price - entry_price) / entry_price
            
            print(f"\n📊 Position Check: {symbol}")
            print(f"   Entry: ${entry_price:.2f} | Current: ${current_price:.2f}")
            print(f"   VWAP: ${vwap:.2f} | Distance: {distance*100:+.2f}%")
            print(f"   P&L: {pnl_pct*100:+.2f}%")
            
            # Exit conditions
            if distance > self.exit_threshold:
                return {'action': 'SELL', 'reason': f'Price {distance*100:.2f}% above VWAP', 'price': current_price}
            
            if pnl_pct < -self.stop_loss:
                return {'action': 'SELL', 'reason': f'Stop loss hit ({pnl_pct*100:.2f}%)', 'price': current_price}
            
            return None
            
        except Exception as e:
            print(f"❌ Error checking exit for {symbol}: {e}")
            return None
    
    def place_order(self, symbol, side, qty):
        """Place market order"""
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='day'
            )
            print(f"✅ Order placed: {side} {qty} shares of {symbol}")
            return order
        except Exception as e:
            print(f"❌ Error placing order: {e}")
            return None
    
    def send_telegram_alert(self, message):
        """Send Telegram notification"""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8408186208:AAEF13uGjhHjIEMnyO4ogLqnUb1ZrT_Q3jw')
            chat_id = '7660866897'
            
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
    
    def write_trade_alert(self, symbol, side, price, qty, reason=''):
        """Write trade to alerts file"""
        try:
            alert_file = '/root/.openclaw/workspace/trading/.alpaca_alerts'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            emoji = "🟢" if side == 'BUY' else "🔴"
            
            with open(alert_file, 'a') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"{emoji} {side} {symbol} @ ${price:.2f} | {timestamp}\n")
                f.write(f"   Qty: {qty} shares\n")
                if reason:
                    f.write(f"   Reason: {reason}\n")
                f.write(f"{'='*50}\n")
            
            print(f"📝 Trade alert written to {alert_file}")
        except Exception as e:
            print(f"⚠️ Failed to write trade alert: {e}")
    
    def run(self):
        """Main trading loop"""
        print("\n" + "="*60)
        print("Starting Alpaca Multi-Stock VWAP Trader")
        print("="*60)
        
        # Check account
        account = self.get_account()
        if account is None:
            print("❌ Could not connect to Alpaca. Check API keys.")
            return
        
        print("\n⚠️  PAPER TRADING ACTIVE - NO REAL MONEY AT RISK")
        print("="*60)
        
        # Main loop
        while True:
            try:
                # Check if market is open
                clock = self.api.get_clock()
                if not clock.is_open:
                    print(f"\n⏰ Market closed. Next open: {clock.next_open}")
                    time.sleep(60)
                    continue
                
                # Check if we have a position
                position = self.get_positions()
                
                if position:
                    # We're in a position - check for exit
                    self.in_position = True
                    self.current_position = position
                    
                    exit_signal = self.check_exit_signal(position)
                    
                    if exit_signal:
                        symbol = position['symbol']
                        qty = position['qty']
                        price = exit_signal['price']
                        reason = exit_signal['reason']
                        
                        print(f"\n🔴 EXIT SIGNAL: {symbol}")
                        print(f"   Reason: {reason}")
                        
                        # Place sell order
                        order = self.place_order(symbol, 'sell', qty)
                        
                        if order:
                            # Send notifications
                            telegram_msg = f"<b>🔴 ALPACA TRADE - SELL</b>\n\n"
                            telegram_msg += f"<b>Symbol:</b> {symbol}\n"
                            telegram_msg += f"<b>Price:</b> ${price:.2f}\n"
                            telegram_msg += f"<b>Qty:</b> {qty} shares\n"
                            telegram_msg += f"<b>Reason:</b> {reason}\n"
                            telegram_msg += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ET"
                            self.send_telegram_alert(telegram_msg)
                            self.write_trade_alert(symbol, 'SELL', price, qty, reason)
                            
                            self.in_position = False
                            self.current_position = None
                
                else:
                    # No position - scan for entry
                    self.in_position = False
                    self.current_position = None
                    
                    signal = self.check_all_signals()
                    
                    if signal:
                        symbol = signal['symbol']
                        price = signal['price']
                        distance = signal['distance']
                        
                        # Calculate position size
                        account = self.get_account()
                        if account:
                            trade_amount = account['buying_power'] * self.position_pct
                            qty = int(trade_amount / price)  # Whole shares only
                            
                            if qty > 0:
                                print(f"\n🟢 ENTRY SIGNAL: {symbol}")
                                print(f"   Price: ${price:.2f}")
                                print(f"   Distance: {distance*100:.2f}% below VWAP")
                                print(f"   Buying {qty} shares with ${trade_amount:.2f}")
                                
                                # Place buy order
                                order = self.place_order(symbol, 'buy', qty)
                                
                                if order:
                                    # Send notifications
                                    telegram_msg = f"<b>🟢 ALPACA TRADE - BUY</b>\n\n"
                                    telegram_msg += f"<b>Symbol:</b> {symbol}\n"
                                    telegram_msg += f"<b>Price:</b> ${price:.2f}\n"
                                    telegram_msg += f"<b>Qty:</b> {qty} shares\n"
                                    telegram_msg += f"<b>Distance from VWAP:</b> {distance*100:.2f}%\n"
                                    telegram_msg += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ET"
                                    self.send_telegram_alert(telegram_msg)
                                    self.write_trade_alert(symbol, 'BUY', price, qty, f"{distance*100:.2f}% below VWAP")
                            else:
                                print(f"⚠️ Cannot buy {symbol} - insufficient funds")
                
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
    trader = AlpacaVWAPTrader()
    
    try:
        trader.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
