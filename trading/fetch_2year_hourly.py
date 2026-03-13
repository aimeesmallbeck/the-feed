#!/usr/bin/env python3
"""Fetch 2 years of hourly BTC data for comprehensive backtesting"""

import yfinance as yf
import pandas as pd

print("📊 Fetching 2 years of hourly BTC/USD data...")
print("This covers March 2024 - March 2026 (multiple market cycles)")
print()

# Fetch 2 years of hourly data
btc = yf.download('BTC-USD', period='2y', interval='1h', progress=False)

if len(btc) == 0:
    print("❌ Failed to fetch data")
    exit(1)

# Flatten column names
btc.columns = ['close', 'high', 'low', 'open', 'volume']

# Save to CSV
output_file = 'btc_usd_1h_2year.csv'
btc.to_csv(output_file)

print(f"✅ Successfully fetched {len(btc)} hourly candles")
print(f"   File: {output_file}")
print(f"   Period: {btc.index[0]} to {btc.index[-1]}")
print(f"   Duration: {(btc.index[-1] - btc.index[0]).days} days")
print(f"   Price Range: ${btc['close'].min():,.2f} - ${btc['close'].max():,.2f}")

# Show market phases in the data
print("\n📈 Market Phases in Dataset:")
print("-" * 60)

# Calculate rolling 30-day returns to identify phases
btc_daily = btc['close'].resample('D').last().dropna()
btc_daily = btc_daily.to_frame()
btc_daily['returns_30d'] = btc_daily['close'].pct_change(30) * 100

# Identify major phases
phases = []
current_phase = None
phase_start = btc_daily.index[0]

for i in range(30, len(btc_daily)):
    ret = btc_daily.iloc[i]['returns_30d']
    
    if ret > 20 and current_phase != 'bull':
        if current_phase:
            phases.append((current_phase, phase_start, btc_daily.index[i]))
        current_phase = 'bull'
        phase_start = btc_daily.index[i]
    elif ret < -20 and current_phase != 'bear':
        if current_phase:
            phases.append((current_phase, phase_start, btc_daily.index[i]))
        current_phase = 'bear'
        phase_start = btc_daily.index[i]
    elif -10 < ret < 10 and current_phase != 'sideways':
        if current_phase:
            phases.append((current_phase, phase_start, btc_daily.index[i]))
        current_phase = 'sideways'
        phase_start = btc_daily.index[i]

# Add final phase
if current_phase:
    phases.append((current_phase, phase_start, btc_daily.index[-1]))

# Display phases
for phase, start, end in phases[:10]:  # Show first 10
    duration = (end - start).days
    start_price = btc_daily.loc[start, 'close'] if start in btc_daily.index else btc_daily.iloc[0]['close']
    end_price = btc_daily.loc[end, 'close'] if end in btc_daily.index else btc_daily.iloc[-1]['close']
    change = ((end_price - start_price) / start_price) * 100
    
    emoji = {'bull': '🐂', 'bear': '🐻', 'sideways': '↔️'}.get(phase, '❓')
    print(f"{emoji} {phase.upper():<10} {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')} ({duration:>3} days) {change:>+6.1f}%")

print(f"\n✅ Data ready for comprehensive backtesting!")
