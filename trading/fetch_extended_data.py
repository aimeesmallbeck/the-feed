#!/usr/bin/env python3
"""Fetch extended BTC historical data for backtesting"""

import yfinance as yf
import pandas as pd
from datetime import datetime

print("📊 Fetching extended BTC/USD historical data...")

# Fetch 3 months of hourly data (best balance of granularity and history)
print("\n1. Fetching 3 months of hourly data...")
btc_hourly = yf.download('BTC-USD', period='3mo', interval='1h', progress=False)
if len(btc_hourly) > 0:
    btc_hourly.columns = ['close', 'high', 'low', 'open', 'volume']
    btc_hourly.to_csv('btc_usd_1h.csv')
    print(f"   ✓ Saved {len(btc_hourly)} hourly candles to btc_usd_1h.csv")
    print(f"   Range: {btc_hourly.index[0]} to {btc_hourly.index[-1]}")

# Fetch 1 year of daily data
print("\n2. Fetching 1 year of daily data...")
btc_daily = yf.download('BTC-USD', period='1y', interval='1d', progress=False)
if len(btc_daily) > 0:
    btc_daily.columns = ['close', 'high', 'low', 'open', 'volume']
    btc_daily.to_csv('btc_usd_1d.csv')
    print(f"   ✓ Saved {len(btc_daily)} daily candles to btc_usd_1d.csv")
    print(f"   Range: {btc_daily.index[0]} to {btc_daily.index[-1]}")

# Also refresh the 1-minute data (7 days max)
print("\n3. Refreshing 1-minute data (7 days)...")
btc_1m = yf.download('BTC-USD', period='7d', interval='1m', progress=False)
if len(btc_1m) > 0:
    btc_1m.columns = ['close', 'high', 'low', 'open', 'volume']
    
    # Calculate VWAP
    typical_price = (btc_1m['high'] + btc_1m['low'] + btc_1m['close']) / 3
    btc_1m['vwap'] = (typical_price * btc_1m['volume']).cumsum() / btc_1m['volume'].cumsum()
    
    btc_1m.to_csv('btc_usd_1m.csv')
    print(f"   ✓ Saved {len(btc_1m)} 1-minute candles to btc_usd_1m.csv")

print("\n✅ All data fetched successfully!")
print("\nFiles created:")
print("  - btc_usd_1m.csv (7 days, 1-minute)")
print("  - btc_usd_1h.csv (3 months, 1-hour)")
print("  - btc_usd_1d.csv (1 year, 1-day)")
