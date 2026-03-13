#!/usr/bin/env python3
"""
Backtest Hybrid Strategy (Grid + VWAP) on historical data
"""

import pandas as pd
import numpy as np

def load_data():
    """Load the BTC/USD 1-minute data"""
    df = pd.read_csv('/root/.openclaw/workspace/trading/btc_usd_1m.csv')
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df = df.sort_values('Datetime')
    return df

def calculate_vwap(df, window=60):
    """Calculate VWAP over a rolling window"""
    df = df.copy()
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    
    # Rolling VWAP
    df['vwap'] = df['tp_volume'].rolling(window=window, min_periods=1).sum() / df['volume'].rolling(window=window, min_periods=1).sum()
    return df

def backtest_vwap_only(df, threshold=0.002):
    """Original VWAP strategy"""
    df = calculate_vwap(df)
    
    position = 0  # 0 = none, 1 = long
    entry_price = 0
    trades = []
    pnl = 0
    
    for i in range(1, len(df)):
        price = df.iloc[i]['close']
        vwap = df.iloc[i]['vwap']
        
        if pd.isna(vwap):
            continue
            
        distance = (price - vwap) / vwap
        
        # Buy signal: price below VWAP by threshold
        if position == 0 and distance < -threshold:
            position = 1
            entry_price = price
            trades.append({'type': 'BUY', 'price': price, 'time': df.iloc[i]['Datetime']})
        
        # Sell signal: price above VWAP by threshold
        elif position == 1 and distance > threshold:
            profit = (price - entry_price) / entry_price
            pnl += profit
            trades.append({'type': 'SELL', 'price': price, 'profit': profit, 'time': df.iloc[i]['Datetime']})
            position = 0
    
    return trades, pnl

def backtest_grid_only(df, grid_size=100, grid_range=10):
    """Grid trading strategy"""
    # Calculate grid levels based on price range
    min_price = df['close'].min()
    max_price = df['close'].max()
    mid_price = (min_price + max_price) / 2
    
    # Create grid around mid price
    grid_levels = []
    for i in range(-grid_range, grid_range + 1):
        grid_levels.append(mid_price + (i * grid_size))
    
    # Track orders and positions
    buy_orders = {level: False for level in grid_levels}  # False = not filled
    sell_orders = {level: False for level in grid_levels}
    position = 0
    entry_price = 0
    trades = []
    pnl = 0
    
    for i in range(len(df)):
        price = df.iloc[i]['close']
        
        # Check if any buy orders should be filled
        for level in grid_levels:
            if price <= level and not buy_orders[level]:
                buy_orders[level] = True
                if position == 0:
                    position = 1
                    entry_price = price
                    trades.append({'type': 'BUY', 'price': price, 'grid_level': level, 'time': df.iloc[i]['Datetime']})
        
        # Check if any sell orders should be filled
        for level in grid_levels:
            if price >= level and not sell_orders[level]:
                sell_orders[level] = True
                if position == 1:
                    profit = (price - entry_price) / entry_price
                    pnl += profit
                    trades.append({'type': 'SELL', 'price': price, 'profit': profit, 'grid_level': level, 'time': df.iloc[i]['Datetime']})
                    position = 0
                    # Reset orders for next cycle
                    buy_orders = {level: False for level in grid_levels}
                    sell_orders = {level: False for level in grid_levels}
    
    return trades, pnl

def backtest_hybrid(df, vwap_threshold=0.002, grid_size=100):
    """Hybrid: 60% Grid + 40% VWAP"""
    df = calculate_vwap(df)
    
    # Grid setup
    min_price = df['close'].min()
    max_price = df['close'].max()
    mid_price = (min_price + max_price) / 2
    grid_levels = [mid_price + (i * grid_size) for i in range(-10, 11)]
    
    # State
    grid_position = 0
    grid_entry = 0
    vwap_position = 0
    vwap_entry = 0
    
    grid_trades = []
    vwap_trades = []
    grid_pnl = 0
    vwap_pnl = 0
    
    buy_orders = {level: False for level in grid_levels}
    sell_orders = {level: False for level in grid_levels}
    
    for i in range(1, len(df)):
        price = df.iloc[i]['close']
        vwap = df.iloc[i]['vwap']
        
        # === GRID STRATEGY (60% allocation) ===
        for level in grid_levels:
            if price <= level and not buy_orders[level]:
                buy_orders[level] = True
                if grid_position == 0:
                    grid_position = 1
                    grid_entry = price
                    grid_trades.append({'type': 'GRID_BUY', 'price': price})
        
        for level in grid_levels:
            if price >= level and not sell_orders[level]:
                sell_orders[level] = True
                if grid_position == 1:
                    profit = (price - grid_entry) / grid_entry
                    grid_pnl += profit
                    grid_trades.append({'type': 'GRID_SELL', 'price': price, 'profit': profit})
                    grid_position = 0
                    buy_orders = {level: False for level in grid_levels}
                    sell_orders = {level: False for level in grid_levels}
        
        # === VWAP STRATEGY (40% allocation) ===
        if not pd.isna(vwap):
            distance = (price - vwap) / vwap
            
            if vwap_position == 0 and distance < -vwap_threshold:
                vwap_position = 1
                vwap_entry = price
                vwap_trades.append({'type': 'VWAP_BUY', 'price': price})
            
            elif vwap_position == 1 and distance > vwap_threshold:
                profit = (price - vwap_entry) / vwap_entry
                vwap_pnl += profit
                vwap_trades.append({'type': 'VWAP_SELL', 'price': price, 'profit': profit})
                vwap_position = 0
    
    # Combine results (weighted)
    total_pnl = (grid_pnl * 0.6) + (vwap_pnl * 0.4)
    all_trades = grid_trades + vwap_trades
    
    return all_trades, total_pnl, grid_pnl, vwap_pnl

def main():
    print("=" * 60)
    print("HYBRID STRATEGY BACKTEST")
    print("=" * 60)
    
    df = load_data()
    print(f"\nData: {len(df)} 1-minute candles")
    print(f"Period: {df['Datetime'].min()} to {df['Datetime'].max()}")
    print(f"Price Range: ${df['close'].min():,.2f} - ${df['close'].max():,.2f}")
    
    # VWAP Only
    print("\n" + "=" * 60)
    print("STRATEGY 1: VWAP Mean Reversion Only (±0.2%)")
    print("=" * 60)
    vwap_trades, vwap_pnl = backtest_vwap_only(df, threshold=0.002)
    print(f"Trades: {len([t for t in vwap_trades if t['type'] == 'SELL'])}")
    print(f"Total Return: {vwap_pnl*100:.2f}%")
    
    # Grid Only
    print("\n" + "=" * 60)
    print("STRATEGY 2: Grid Trading Only ($100 spacing)")
    print("=" * 60)
    grid_trades, grid_pnl = backtest_grid_only(df, grid_size=100)
    print(f"Trades: {len([t for t in grid_trades if t['type'] == 'SELL'])}")
    print(f"Total Return: {grid_pnl*100:.2f}%")
    
    # Hybrid
    print("\n" + "=" * 60)
    print("STRATEGY 3: HYBRID (60% Grid + 40% VWAP)")
    print("=" * 60)
    hybrid_trades, hybrid_pnl, grid_only_pnl, vwap_only_pnl = backtest_hybrid(df)
    grid_count = len([t for t in hybrid_trades if t['type'] == 'GRID_SELL'])
    vwap_count = len([t for t in hybrid_trades if t['type'] == 'VWAP_SELL'])
    print(f"Grid Trades: {grid_count}")
    print(f"VWAP Trades: {vwap_count}")
    print(f"Grid Return (unweighted): {grid_only_pnl*100:.2f}%")
    print(f"VWAP Return (unweighted): {vwap_only_pnl*100:.2f}%")
    print(f"HYBRID Return (60/40 weighted): {hybrid_pnl*100:.2f}%")
    
    # Comparison
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(f"VWAP Only:     {vwap_pnl*100:>8.2f}%")
    print(f"Grid Only:     {grid_pnl*100:>8.2f}%")
    print(f"Hybrid:        {hybrid_pnl*100:>8.2f}%")
    print(f"Improvement:   {((hybrid_pnl/vwap_pnl - 1)*100) if vwap_pnl > 0 else 0:>7.0f}% better than VWAP")

if __name__ == "__main__":
    main()
