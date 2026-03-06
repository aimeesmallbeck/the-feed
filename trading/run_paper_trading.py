#!/usr/bin/env python3
"""Run paper trading simulation with fetched data"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from paper_trade_runner import PaperTrader
import pandas as pd

# Load the data
data_file = Path(__file__).parent / 'btc_usd_1m.csv'

if not data_file.exists():
    print("❌ No data file found. Run fetch_data.py first.")
    exit(1)

# Initialize paper trader with data
trader = PaperTrader(
    symbol='BTCUSDT',
    initial_balance=10000.0,
    entry_bias=0.0023,  # 0.23% below VWAP (from MCMC optimization)
    exit_bias=0.0028,   # 0.28% above VWAP
    data_file=str(data_file)
)

print(f"📊 Running simulation on {len(trader.data)} data points...\n")

# Run simulation
trader.run_simulation()

# Print final stats
trader.print_stats()
