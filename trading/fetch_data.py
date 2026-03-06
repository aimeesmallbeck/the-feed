#!/usr/bin/env python3
"""Fetch BTC data for paper trading"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

print("📊 Fetching BTC/USD historical data...")

# Download 7 days of 1-minute BTC data
btc = yf.download('BTC-USD', period='7d', interval='1m', progress=False)

if len(btc) == 0:
    print("❌ Failed to fetch data")
    exit(1)

# Flatten column names (yfinance returns multi-level columns)
btc.columns = ['close', 'high', 'low', 'open', 'volume']

# Calculate VWAP
typical_price = (btc['high'] + btc['low'] + btc['close']) / 3
btc['vwap'] = (typical_price * btc['volume']).cumsum() / btc['volume'].cumsum()

# Save to CSV
output_file = 'btc_usd_1m.csv'
btc.to_csv(output_file)
print(f"✅ Saved {len(btc)} data points to {output_file}")
print(f"   Date range: {btc.index[0]} to {btc.index[-1]}")
close_min = btc['close'].min() if hasattr(btc['close'].min(), 'item') else btc['close'].min()
close_max = btc['close'].max() if hasattr(btc['close'].max(), 'item') else btc['close'].max()
print(f"   Price range: ${close_min:.2f} - ${close_max:.2f}")
