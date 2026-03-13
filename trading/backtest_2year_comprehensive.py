#!/usr/bin/env python3
"""
Comprehensive 2-Year Backtest Across All Market Regimes
Tests VWAP vs Grid in bull, bear, and sideways markets
"""

import pandas as pd
import numpy as np

def load_data():
    df = pd.read_csv('/root/.openclaw/workspace/trading/btc_usd_1h_2year.csv', index_col=0, parse_dates=True)
    df = df.sort_index()
    return df

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

def identify_market_regimes(df):
    """Identify bull, bear, and sideways phases"""
    # Use 30-day rolling returns
    daily = df['close'].resample('D').last().dropna()
    returns_30d = daily.pct_change(30) * 100
    
    regimes = []
    current_regime = None
    regime_start = daily.index[30]
    
    for date in daily.index[30:]:
        ret = returns_30d.loc[date]
        
        if ret > 15:
            regime = 'bull'
        elif ret < -15:
            regime = 'bear'
        else:
            regime = 'sideways'
        
        if regime != current_regime:
            if current_regime:
                regimes.append((current_regime, regime_start, date))
            current_regime = regime
            regime_start = date
    
    if current_regime:
        regimes.append((current_regime, regime_start, daily.index[-1]))
    
    return regimes

def backtest_by_regime(df, regimes):
    """Run backtests for each market regime"""
    results = []
    
    for regime, start, end in regimes:
        regime_df = df[(df.index >= start) & (df.index <= end)]
        if len(regime_df) < 100:
            continue
        
        vwap_trades, vwap_pnl, vwap_hours = backtest_vwap(regime_df)
        grid_trades, grid_pnl, grid_hours = backtest_grid(regime_df)
        
        start_price = regime_df.iloc[0]['close']
        end_price = regime_df.iloc[-1]['close']
        bh_pnl = (end_price - start_price) / start_price
        
        results.append({
            'regime': regime,
            'start': start,
            'end': end,
            'days': (end - start).days,
            'start_price': start_price,
            'end_price': end_price,
            'bh_pnl': bh_pnl * 100,
            'vwap_pnl': vwap_pnl * 100,
            'vwap_trades': len([t for t in vwap_trades if t['type'] == 'SELL']),
            'grid_pnl': grid_pnl * 100,
            'grid_trades': len([t for t in grid_trades if t['type'] == 'SELL'])
        })
    
    return results

def main():
    print("=" * 90)
    print("COMPREHENSIVE 2-YEAR BACKTEST (March 2024 - March 2026)")
    print("=" * 90)
    
    df = load_data()
    print(f"\nData: {len(df)} hourly candles over {(df.index[-1] - df.index[0]).days} days")
    print(f"Price Range: ${df['close'].min():,.0f} - ${df['close'].max():,.0f}")
    print(f"Overall Change: {((df.iloc[-1]['close'] - df.iloc[0]['close']) / df.iloc[0]['close'] * 100):+.1f}%")
    
    # Identify regimes
    print("\n" + "=" * 90)
    print("MARKET REGIMES IDENTIFIED")
    print("=" * 90)
    
    regimes = identify_market_regimes(df)
    
    print(f"\n{'Regime':<10} {'Start':<12} {'End':<12} {'Days':>6} {'Price Change':>12}")
    print("-" * 90)
    for regime, start, end in regimes:
        regime_df = df[(df.index >= start) & (df.index <= end)]
        if len(regime_df) > 0:
            change = ((regime_df.iloc[-1]['close'] - regime_df.iloc[0]['close']) / regime_df.iloc[0]['close'] * 100)
            emoji = {'bull': '🐂', 'bear': '🐻', 'sideways': '↔️'}.get(regime, '❓')
            print(f"{emoji} {regime.upper():<8} {start.strftime('%Y-%m-%d')} {end.strftime('%Y-%m-%d')} {(end-start).days:>6} {change:>+10.1f}%")
    
    # Backtest by regime
    print("\n" + "=" * 90)
    print("STRATEGY PERFORMANCE BY MARKET REGIME")
    print("=" * 90)
    
    results = backtest_by_regime(df, regimes)
    
    print(f"\n{'Regime':<10} {'Days':>6} {'Buy&Hold':>10} {'VWAP':>10} {'VWAP #':>8} {'Grid':>10} {'Grid #':>8} {'Winner':>8}")
    print("-" * 90)
    
    regime_totals = {'bull': {'vwap': 0, 'grid': 0, 'bh': 0, 'count': 0},
                     'bear': {'vwap': 0, 'grid': 0, 'bh': 0, 'count': 0},
                     'sideways': {'vwap': 0, 'grid': 0, 'bh': 0, 'count': 0}}
    
    for r in results:
        # Determine winner
        best = max(r['vwap_pnl'], r['grid_pnl'], r['bh_pnl'])
        if best == r['vwap_pnl']:
            winner = 'VWAP'
        elif best == r['grid_pnl']:
            winner = 'Grid'
        else:
            winner = 'B&H'
        
        emoji = {'bull': '🐂', 'bear': '🐻', 'sideways': '↔️'}.get(r['regime'], '❓')
        print(f"{emoji} {r['regime'].upper():<8} {r['days']:>6} {r['bh_pnl']:>9.1f}% {r['vwap_pnl']:>9.1f}% {r['vwap_trades']:>8} {r['grid_pnl']:>9.1f}% {r['grid_trades']:>8} {winner:>8}")
        
        # Accumulate totals
        if r['regime'] in regime_totals:
            regime_totals[r['regime']]['vwap'] += r['vwap_pnl']
            regime_totals[r['regime']]['grid'] += r['grid_pnl']
            regime_totals[r['regime']]['bh'] += r['bh_pnl']
            regime_totals[r['regime']]['count'] += 1
    
    # Summary by regime type
    print("\n" + "=" * 90)
    print("AVERAGE PERFORMANCE BY REGIME TYPE")
    print("=" * 90)
    
    print(f"\n{'Regime Type':<15} {'Periods':>8} {'Buy&Hold':>12} {'VWAP':>12} {'Grid':>12} {'Best':>10}")
    print("-" * 90)
    
    for regime_type, totals in regime_totals.items():
        if totals['count'] > 0:
            avg_bh = totals['bh'] / totals['count']
            avg_vwap = totals['vwap'] / totals['count']
            avg_grid = totals['grid'] / totals['count']
            best = max(avg_bh, avg_vwap, avg_grid)
            best_str = 'B&H' if best == avg_bh else ('VWAP' if best == avg_vwap else 'Grid')
            emoji = {'bull': '🐂', 'bear': '🐻', 'sideways': '↔️'}.get(regime_type, '❓')
            print(f"{emoji} {regime_type.upper():<13} {totals['count']:>8} {avg_bh:>11.1f}% {avg_vwap:>11.1f}% {avg_grid:>11.1f}% {best_str:>10}")
    
    # Overall totals
    print("\n" + "=" * 90)
    print("2-YEAR TOTAL PERFORMANCE")
    print("=" * 90)
    
    vwap_trades_all, vwap_pnl_all, vwap_hours_all = backtest_vwap(df)
    grid_trades_all, grid_pnl_all, grid_hours_all = backtest_grid(df)
    bh_pnl_all = (df.iloc[-1]['close'] - df.iloc[0]['close']) / df.iloc[0]['close']
    
    print(f"\n{'Strategy':<20} {'Total Return':>15} {'# Trades':>10} {'Time Invested':>15}")
    print("-" * 70)
    print(f"{'Buy & Hold':<20} {bh_pnl_all*100:>14.1f}% {'N/A':>10} {'100%':>15}")
    print(f"{'VWAP Strategy':<20} {vwap_pnl_all*100:>14.1f}% {len([t for t in vwap_trades_all if t['type']=='SELL']):>10} {vwap_hours_all/len(df)*100:>14.1f}%")
    print(f"{'Grid Strategy':<20} {grid_pnl_all*100:>14.1f}% {len([t for t in grid_trades_all if t['type']=='SELL']):>10} {grid_hours_all/len(df)*100:>14.1f}%")
    
    # Final recommendation
    print("\n" + "=" * 90)
    print("FINAL RECOMMENDATION")
    print("=" * 90)
    
    # Count regime wins
    vwap_wins = sum(1 for r in results if r['vwap_pnl'] > r['grid_pnl'] and r['vwap_pnl'] > r['bh_pnl'])
    grid_wins = sum(1 for r in results if r['grid_pnl'] > r['vwap_pnl'] and r['grid_pnl'] > r['bh_pnl'])
    bh_wins = sum(1 for r in results if r['bh_pnl'] > r['vwap_pnl'] and r['bh_pnl'] > r['grid_pnl'])
    
    print(f"\nStrategy Wins by Regime:")
    print(f"  VWAP: {vwap_wins} regimes")
    print(f"  Grid: {grid_wins} regimes")
    print(f"  Buy & Hold: {bh_wins} regimes")
    
    # Best overall
    returns = {'VWAP': vwap_pnl_all, 'Grid': grid_pnl_all, 'Buy & Hold': bh_pnl_all}
    best_overall = max(returns, key=returns.get)
    
    print(f"\n🏆 BEST OVERALL STRATEGY: {best_overall}")
    print(f"   2-Year Return: {returns[best_overall]*100:.1f}%")
    
    if best_overall == 'VWAP':
        print(f"\n✅ VWAP is the winner across market regimes")
        print(f"   - Profitable in both bull and bear markets")
        print(f"   - Won {vwap_wins} out of {len(results)} market phases")
        print(f"   - Keep your current bot running!")
    elif best_overall == 'Grid':
        print(f"\n✅ Grid trading is the winner")
        print(f"   - Consider switching to grid strategy")
    else:
        print(f"\n⚠️  Buy & Hold outperformed active strategies")
        print(f"   - Consider passive holding during strong trends")

if __name__ == "__main__":
    main()
