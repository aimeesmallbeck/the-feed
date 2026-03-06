#!/usr/bin/env python3
"""
Simple Kraken Paper Trading Bot
Logs signals and paper trades to file
"""

import requests
import time
import json
from datetime import datetime

LOG_FILE = '/root/.openclaw/workspace/trading/paper_trades.log'

def log_message(msg):
    """Write to log file and print"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def get_btc_price():
    """Get current BTC price from Kraken"""
    try:
        response = requests.get('https://api.kraken.com/0/public/Ticker?pair=XBTUSD', timeout=10)
        data = response.json()
        if data.get('error'):
            return None
        return float(data['result']['XXBTZUSD']['c'][0])
    except Exception as e:
        log_message(f"Error getting price: {e}")
        return None

def get_ohlc():
    """Get recent OHLC data"""
    try:
        response = requests.get('https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1', timeout=10)
        data = response.json()
        if data.get('error'):
            return None
        return data['result']['XXBTZUSD']
    except Exception as e:
        log_message(f"Error getting OHLC: {e}")
        return None

def calculate_vwap(ohlc_data, period=20):
    """Calculate VWAP from recent candles"""
    if not ohlc_data or len(ohlc_data) < period:
        return None
    
    recent = ohlc_data[-period:]
    total_typical_price_volume = 0
    total_volume = 0
    
    for candle in recent:
        high = float(candle[2])
        low = float(candle[3])
        close = float(candle[4])
        volume = float(candle[6])
        
        typical_price = (high + low + close) / 3
        total_typical_price_volume += typical_price * volume
        total_volume += volume
    
    return total_typical_price_volume / total_volume if total_volume > 0 else None

def main():
    log_message("="*60)
    log_message("🚀 Kraken Paper Trading Bot Started")
    log_message("📊 Strategy: VWAP Mean Reversion")
    log_message("💰 Mode: PAPER TRADING (no real money)")
    log_message("="*60)
    
    entry_bias = 0.0023  # 0.23%
    exit_bias = 0.0028   # 0.28%
    position = None  # None, 'LONG', or 'SHORT'
    entry_price = 0
    
    while True:
        try:
            # Get data
            price = get_btc_price()
            ohlc = get_ohlc()
            
            if not price or not ohlc:
                log_message("⚠️ Failed to get data, retrying in 60s...")
                time.sleep(60)
                continue
            
            vwap = calculate_vwap(ohlc)
            if not vwap:
                log_message("⚠️ Failed to calculate VWAP, retrying...")
                time.sleep(60)
                continue
            
            # Calculate distance from VWAP
            distance = (price - vwap) / vwap
            
            # Log status
            log_message(f"Price: ${price:,.2f} | VWAP: ${vwap:,.2f} | Distance: {distance*100:+.2f}% | Position: {position or 'NONE'}")
            
            # Trading logic
            if position is None:
                # Look for entry
                if distance < -entry_bias:
                    # BUY signal
                    position = 'LONG'
                    entry_price = price
                    log_message(f"🟢 PAPER BUY @ ${price:,.2f} | Distance: {distance*100:.2f}% below VWAP")
                    
            elif position == 'LONG':
                # Look for exit
                profit_pct = (price - entry_price) / entry_price
                
                if distance > exit_bias:
                    # SELL signal - take profit
                    log_message(f"🔴 PAPER SELL @ ${price:,.2f} | Profit: {profit_pct*100:+.2f}% | Distance: {distance*100:.2f}% above VWAP")
                    position = None
                    entry_price = 0
                    
                elif profit_pct < -0.015:  # 1.5% stop loss
                    # Stop loss
                    log_message(f"🛑 PAPER STOP LOSS @ ${price:,.2f} | Loss: {profit_pct*100:+.2f}%")
                    position = None
                    entry_price = 0
            
            # Wait before next check
            time.sleep(60)
            
        except KeyboardInterrupt:
            log_message("🛑 Bot stopped by user")
            break
        except Exception as e:
            log_message(f"❌ Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main()
