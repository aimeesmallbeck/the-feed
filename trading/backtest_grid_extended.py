#!/usr/bin/env python3
"""
Backtest Grid Strategy on extended hourly data
"""

import pandas as pd
import numpy as np

def load_hourly_data():
    """Load the BTC/USD hourly data"""
    df = pd.read_csv('/root/.openclaw/workspace/trading/btc_usd_1h.csv', index_col=0, parse_dates=True)
    df = df.sort_index()
    return df

def backtest_grid(df, grid_size=500, grid_range=20, stop_loss_pct=0.05):
    """
    Grid trading backtest
    grid_size: price spacing between grid levels (in USD)
    grid_range: number of grid levels above/below mid price
    stop_loss_pct: stop loss if price moves beyond grid by this percentage
    """
    # Calculate grid based on starting price
    start_price = df.iloc[0]['close']
    grid_levels = []
    for i in range(-grid_range, grid_range + 1):
        grid_levels.append(start_price + (i * grid_size))
    
    # Initialize tracking
    position = 0
    entry_price = 0
    trades = []
    pnl = 0
    max_drawdown = 0
    peak_value = 0
    
    # Track filled orders
    filled_buys = set()
    
    for i in range(len(df)):
        price = df.iloc[i]['close']
        timestamp = df.index[i]
        
        # Check stop loss (price beyond grid range)
        min_grid = min(grid_levels)
        max_grid = max(grid_levels)
        
        if price < min_grid * (1 - stop_loss_pct) and position > 0:
            # Stop loss hit - close position
            loss = (price - entry_price) / entry_price
            pnl += loss
            trades.append({
                'type': 'STOP_LOSS',
                'price': price,
                'profit': loss,
                'time': timestamp
            })
            position = 0
            filled_buys.clear()
            continue
        
        # Grid buy logic
        for level in grid_levels:
            if price <= level and level not in filled_buys:
                filled_buys.add(level)
                if position == 0:
                    position = 1
                    entry_price = price
                    trades.append({
                        'type': 'BUY',
                        'price': price,
                        'grid_level': level,
                        'time': timestamp
                    })
        
        # Grid sell logic - sell when price reaches next grid level up
        if position == 1 and entry_price > 0:
            # Find the next grid level above entry
            sell_triggered = False
            for level in sorted(grid_levels):
                if level > entry_price and price >= level:
                    profit = (price - entry_price) / entry_price
                    pnl += profit
                    trades.append({
                        'type': 'SELL',
                        'price': price,
                        'profit': profit,
                        'grid_level': level,
                        'time': timestamp
                    })
                    position = 0
                    filled_buys.clear()
                    sell_triggered = True
                    break
            
            # Track drawdown
            if position == 1:
                current_value = price / entry_price
                if current_value > peak_value:
                    peak_value = current_value
                drawdown = (peak_value - current_value) / peak_value
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
    
    return trades, pnl, max_drawdown

def optimize_grid_params(df):
    """Test different grid parameters to find optimal"""
    results = []
    
    grid_sizes = [200, 300, 400, 500, 600, 800, 1000]
    grid_ranges = [10, 15, 20, 25]
    
    print("Optimizing grid parameters...")
    print("=" * 80)
    
    for grid_size in grid_sizes:
        for grid_range in grid_ranges:
            trades, pnl, max_dd = backtest_grid(df, grid_size, grid_range)
            num_trades = len([t for t in trades if t['type'] == 'SELL'])
            
            results.append({
                'grid_size': grid_size,
                'grid_range': grid_range,
                'trades': num_trades,
                'pnl': pnl,
                'max_dd': max_dd,
                'avg_profit_per_trade': pnl / num_trades if num_trades > 0 else 0
            })
            
            print(f"Grid: ${grid_size:>4} | Range: {grid_range:>2} | "
                  f"Trades: {num_trades:>3} | P&L: {pnl*100:>6.2f}% | "
                  f"Max DD: {max_dd*100:>5.2f}%")
    
    return results

def main():
    print("=" * 80)
    print("GRID TRADING BACKTEST - 3 MONTHS HOURLY DATA")
    print("=" * 80)
    
    df = load_hourly_data()
    print(f"\nData: {len(df)} hourly candles")
    print(f"Period: {df.index[0]} to {df.index[-1]}")
    print(f"Price Range: ${df['close'].min():,.2f} - ${df['close'].max():,.2f}")
    print(f"Volatility: {((df['close'].max() - df['close'].min()) / df['close'].mean()) * 100:.2f}%")
    
    # Run optimization
    print("\n")
    results = optimize_grid_params(df)
    
    # Find best result
    best = max(results, key=lambda x: x['pnl'])
    print("\n" + "=" * 80)
    print("OPTIMAL PARAMETERS")
    print("=" * 80)
    print(f"Grid Size: ${best['grid_size']}")
    print(f"Grid Range: {best['grid_range']} levels")
    print(f"Total Trades: {best['trades']}")
    print(f"Total Return: {best['pnl']*100:.2f}%")
    print(f"Max Drawdown: {best['max_dd']*100:.2f}%")
    print(f"Avg Profit/Trade: {best['avg_profit_per_trade']*100:.2f}%")
    
    # Run detailed backtest with optimal params
    print("\n" + "=" * 80)
    print("DETAILED BACKTEST WITH OPTIMAL PARAMETERS")
    print("=" * 80)
    trades, pnl, max_dd = backtest_grid(df, best['grid_size'], best['grid_range'])
    
    buy_trades = [t for t in trades if t['type'] == 'BUY']
    sell_trades = [t for t in trades if t['type'] == 'SELL']
    stop_trades = [t for t in trades if t['type'] == 'STOP_LOSS']
    
    print(f"\nTotal Trades:")
    print(f"  Buys: {len(buy_trades)}")
    print(f"  Sells: {len(sell_trades)}")
    print(f"  Stop Losses: {len(stop_trades)}")
    
    if sell_trades:
        profits = [t['profit'] for t in sell_trades]
        print(f"\nWin Rate: {(len([p for p in profits if p > 0]) / len(profits)) * 100:.1f}%")
        print(f"Avg Win: {np.mean([p for p in profits if p > 0]) * 100:.2f}%")
        print(f"Avg Loss: {np.mean([p for p in profits if p < 0]) * 100:.2f}%")
        print(f"Best Trade: {max(profits) * 100:.2f}%")
        print(f"Worst Trade: {min(profits) * 100:.2f}%")
    
    # Monthly breakdown
    print("\n" + "=" * 80)
    print("MONTHLY BREAKDOWN")
    print("=" * 80)
    df['month'] = df.index.to_period('M')
    for month in df['month'].unique():
        month_df = df[df['month'] == month]
        month_return = (month_df['close'].iloc[-1] - month_df['close'].iloc[0]) / month_df['close'].iloc[0]
        print(f"{month}: Market return = {month_return*100:+.2f}%")

if __name__ == "__main__":
    main()
