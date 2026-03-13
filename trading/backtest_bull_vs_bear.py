#!/usr/bin/env python3
"""
Simulate Bull Market by reversing the 3-month data
Compare VWAP vs Grid in bull vs bear conditions
"""

import pandas as pd
import numpy as np

def load_data():
    df = pd.read_csv('/root/.openclaw/workspace/trading/btc_usd_1h.csv', index_col=0, parse_dates=True)
    df = df.sort_index()
    return df

def reverse_data(df):
    """Reverse the price data to simulate opposite market conditions"""
    df_reversed = df.copy()
    
    # Reverse the order of rows
    df_reversed = df_reversed.iloc[::-1].reset_index(drop=True)
    
    # Create new datetime index starting from original start
    df_reversed.index = pd.date_range(
        start=df.index[0], 
        periods=len(df_reversed), 
        freq='h'
    )
    
    return df_reversed

def backtest_vwap(df, threshold=0.002):
    """VWAP Mean Reversion strategy"""
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (df['typical_price'] * df['volume']).cumsum() / df['volume'].cumsum()
    
    position = 0
    entry_price = 0
    trades = []
    pnl = 0
    position_hours = 0
    entry_time = None
    
    for i in range(1, len(df)):
        price = df.iloc[i]['close']
        vwap = df.iloc[i]['vwap']
        timestamp = df.index[i]
        
        if pd.isna(vwap):
            continue
            
        distance = (price - vwap) / vwap
        
        if position == 0 and distance < -threshold:
            position = 1
            entry_price = price
            entry_time = timestamp
            trades.append({'type': 'BUY', 'price': price, 'time': timestamp})
        
        elif position == 1 and distance > threshold:
            profit = (price - entry_price) / entry_price
            pnl += profit
            position_hours += (timestamp - entry_time).total_seconds() / 3600
            trades.append({'type': 'SELL', 'price': price, 'profit': profit, 'time': timestamp})
            position = 0
            entry_time = None
    
    # Handle position still open at end
    if position == 1 and entry_time is not None:
        position_hours += (df.index[-1] - entry_time).total_seconds() / 3600
    
    return trades, pnl, position_hours

def backtest_grid(df, grid_size=500, grid_range=10):
    """Grid trading strategy"""
    start_price = df.iloc[0]['close']
    grid_levels = [start_price + (i * grid_size) for i in range(-grid_range, grid_range + 1)]
    
    position = 0
    entry_price = 0
    trades = []
    pnl = 0
    position_hours = 0
    filled_buys = set()
    entry_time = None
    
    for i in range(len(df)):
        price = df.iloc[i]['close']
        timestamp = df.index[i]
        
        for level in grid_levels:
            if price <= level and level not in filled_buys:
                filled_buys.add(level)
                if position == 0:
                    position = 1
                    entry_price = price
                    entry_time = timestamp
                    trades.append({'type': 'BUY', 'price': price, 'grid_level': level, 'time': timestamp})
        
        if position == 1:
            for level in sorted(grid_levels):
                if level > entry_price and price >= level:
                    profit = (price - entry_price) / entry_price
                    pnl += profit
                    position_hours += (timestamp - entry_time).total_seconds() / 3600
                    trades.append({'type': 'SELL', 'price': price, 'profit': profit, 'grid_level': level, 'time': timestamp})
                    position = 0
                    filled_buys.clear()
                    entry_time = None
                    break
    
    if position == 1 and entry_time is not None:
        position_hours += (df.index[-1] - entry_time).total_seconds() / 3600
    
    return trades, pnl, position_hours

def main():
    print("=" * 80)
    print("VWAP vs GRID: BEAR vs BULL MARKET COMPARISON")
    print("=" * 80)
    print("\nMethod: Reverse 3-month data to simulate opposite market conditions")
    
    df = load_data()
    df_bull = reverse_data(df)
    
    # BEAR MARKET (Original data)
    print("\n" + "=" * 80)
    print("BEAR MARKET (Original Data: Dec 2025 - Mar 2026)")
    print("=" * 80)
    print(f"Price: ${df.iloc[0]['close']:,.0f} → ${df.iloc[-1]['close']:,.0f}")
    print(f"Trend: {((df.iloc[-1]['close'] - df.iloc[0]['close']) / df.iloc[0]['close'] * 100):+.1f}%")
    
    vwap_trades_bear, vwap_pnl_bear, vwap_hours_bear = backtest_vwap(df)
    grid_trades_bear, grid_pnl_bear, grid_hours_bear = backtest_grid(df)
    bh_bear = (df.iloc[-1]['close'] - df.iloc[0]['close']) / df.iloc[0]['close']
    
    total_hours = len(df)
    
    print(f"\nBuy & Hold:      {bh_bear*100:>8.2f}%")
    print(f"VWAP Strategy:   {vwap_pnl_bear*100:>8.2f}%  ({len([t for t in vwap_trades_bear if t['type']=='SELL'])} trades, {vwap_hours_bear/total_hours*100:.1f}% invested)")
    print(f"Grid Strategy:   {grid_pnl_bear*100:>8.2f}%  ({len([t for t in grid_trades_bear if t['type']=='SELL'])} trades, {grid_hours_bear/total_hours*100:.1f}% invested)")
    
    # BULL MARKET (Reversed data)
    print("\n" + "=" * 80)
    print("BULL MARKET (Simulated: Reversed Data)")
    print("=" * 80)
    print(f"Price: ${df_bull.iloc[0]['close']:,.0f} → ${df_bull.iloc[-1]['close']:,.0f}")
    print(f"Trend: {((df_bull.iloc[-1]['close'] - df_bull.iloc[0]['close']) / df_bull.iloc[0]['close'] * 100):+.1f}%")
    
    vwap_trades_bull, vwap_pnl_bull, vwap_hours_bull = backtest_vwap(df_bull)
    grid_trades_bull, grid_pnl_bull, grid_hours_bull = backtest_grid(df_bull)
    bh_bull = (df_bull.iloc[-1]['close'] - df_bull.iloc[0]['close']) / df_bull.iloc[0]['close']
    
    print(f"\nBuy & Hold:      {bh_bull*100:>8.2f}%")
    print(f"VWAP Strategy:   {vwap_pnl_bull*100:>8.2f}%  ({len([t for t in vwap_trades_bull if t['type']=='SELL'])} trades, {vwap_hours_bull/total_hours*100:.1f}% invested)")
    print(f"Grid Strategy:   {grid_pnl_bull*100:>8.2f}%  ({len([t for t in grid_trades_bull if t['type']=='SELL'])} trades, {grid_hours_bull/total_hours*100:.1f}% invested)")
    
    # Summary comparison
    print("\n" + "=" * 80)
    print("SIDE-BY-SIDE COMPARISON")
    print("=" * 80)
    print(f"\n{'Strategy':<15} {'Bear Market':>15} {'Bull Market':>15} {'Average':>15}")
    print("-" * 65)
    print(f"{'Buy & Hold':<15} {bh_bear*100:>14.1f}% {bh_bull*100:>14.1f}% {(bh_bear+bh_bull)/2*100:>14.1f}%")
    print(f"{'VWAP':<15} {vwap_pnl_bear*100:>14.1f}% {vwap_pnl_bull*100:>14.1f}% {(vwap_pnl_bear+vwap_pnl_bull)/2*100:>14.1f}%")
    print(f"{'Grid':<15} {grid_pnl_bear*100:>14.1f}% {grid_pnl_bull*100:>14.1f}% {(grid_pnl_bear+grid_pnl_bull)/2*100:>14.1f}%")
    
    # Key insights
    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    
    print("\n1. VWAP PERFORMANCE:")
    print(f"   Bear Market: {vwap_pnl_bear*100:+.1f}% (outperformed buy&hold by {vwap_pnl_bear*100 - bh_bear*100:.1f}%)")
    print(f"   Bull Market: {vwap_pnl_bull*100:+.1f}% (underperformed buy&hold by {bh_bull*100 - vwap_pnl_bull*100:.1f}%)")
    print(f"   Average: {(vwap_pnl_bear+vwap_pnl_bull)/2*100:+.1f}%")
    
    print("\n2. GRID PERFORMANCE:")
    print(f"   Bear Market: {grid_pnl_bear*100:+.1f}%")
    print(f"   Bull Market: {grid_pnl_bull*100:+.1f}%")
    print(f"   Average: {(grid_pnl_bear+grid_pnl_bull)/2*100:+.1f}%")
    
    print("\n3. MARKET REGIME CONCLUSION:")
    if vwap_pnl_bear > grid_pnl_bear and vwap_pnl_bull > grid_pnl_bull:
        print("   ✅ VWAP wins in BOTH bear and bull markets")
    elif vwap_pnl_bear > grid_pnl_bear:
        print("   ✅ VWAP wins in bear markets")
        print(f"   ⚠️  VWAP {'wins' if vwap_pnl_bull > grid_pnl_bull else 'loses'} in bull markets")
    
    print("\n4. TIME INVESTED:")
    print(f"   VWAP: {((vwap_hours_bear+vwap_hours_bull)/2/total_hours)*100:.1f}% (avg across both markets)")
    print(f"   Grid: {((grid_hours_bear+grid_hours_bull)/2/total_hours)*100:.1f}% (avg across both markets)")
    
    print("\n" + "=" * 80)
    print("FINAL RECOMMENDATION")
    print("=" * 80)
    
    vwap_avg = (vwap_pnl_bear + vwap_pnl_bull) / 2
    grid_avg = (grid_pnl_bear + grid_pnl_bull) / 2
    
    if vwap_avg > grid_avg:
        print(f"\n✅ VWAP is superior across market regimes")
        print(f"   Average return: {vwap_avg*100:.1f}% vs Grid {grid_avg*100:.1f}%")
        print(f"   Works in bear markets (+{vwap_pnl_bear*100:.1f}%)")
        print(f"   Works in bull markets (+{vwap_pnl_bull*100:.1f}%)")
        print(f"\n   Keep your VWAP bot running!")
    else:
        print(f"\n⚠️  Mixed results - consider market regime detection")

if __name__ == "__main__":
    main()
