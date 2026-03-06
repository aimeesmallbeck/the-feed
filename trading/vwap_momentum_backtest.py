#!/usr/bin/env python3
"""
VWAP + Momentum Backtester for Crypto (BTC/USD)
Strategy: VWAP Bounce with RSI confirmation
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional
import json

@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime]
    side: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float
    exit_reason: str

class VWAPMomentumStrategy:
    def __init__(
        self,
        rsi_period: int = 14,
        rsi_long_threshold: float = 30,
        rsi_short_threshold: float = 70,
        volume_mult: float = 1.5,
        atr_period: int = 14,
        atr_mult: float = 2.0,
        risk_per_trade: float = 0.01,  # 1% of account
        profit_target_r: float = 3.0,
        time_stop_minutes: int = 5
    ):
        self.rsi_period = rsi_period
        self.rsi_long_threshold = rsi_long_threshold
        self.rsi_short_threshold = rsi_short_threshold
        self.volume_mult = volume_mult
        self.atr_period = atr_period
        self.atr_mult = atr_mult
        self.risk_per_trade = risk_per_trade
        self.profit_target_r = profit_target_r
        self.time_stop_minutes = time_stop_minutes
        
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
    
    def fetch_binance_data(self, symbol: str = "BTCUSDT", limit: int = 1000) -> pd.DataFrame:
        """Fetch 1-minute klines from Binance"""
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": "1m",
            "limit": limit
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignored'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate VWAP: cumulative(TP * Volume) / cumulative(Volume)"""
        tp = (df['high'] + df['low'] + df['close']) / 3
        vwap = (tp * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(period).mean()
        return atr
    
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all indicators to dataframe"""
        df = df.copy()
        df['vwap'] = self.calculate_vwap(df)
        df['rsi'] = self.calculate_rsi(df['close'], self.rsi_period)
        df['atr'] = self.calculate_atr(df, self.atr_period)
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_spike'] = df['volume'] > (df['volume_sma'] * self.volume_mult)
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate entry/exit signals"""
        df = df.copy()
        
        # Long signal conditions
        price_below_vwap = df['close'] < df['vwap']
        rsi_oversold = df['rsi'] < self.rsi_long_threshold
        rsi_rising = df['rsi'] > df['rsi'].shift(1)
        volume_confirms = df['volume_spike']
        vwap_break_long = (df['close'] > df['vwap']) & (df['close'].shift(1) <= df['vwap'].shift(1))
        
        df['long_signal'] = (
            price_below_vwap & 
            rsi_oversold & 
            rsi_rising & 
            volume_confirms & 
            vwap_break_long
        )
        
        # Short signal conditions
        price_above_vwap = df['close'] > df['vwap']
        rsi_overbought = df['rsi'] > self.rsi_short_threshold
        rsi_falling = df['rsi'] < df['rsi'].shift(1)
        vwap_break_short = (df['close'] < df['vwap']) & (df['close'].shift(1) >= df['vwap'].shift(1))
        
        df['short_signal'] = (
            price_above_vwap & 
            rsi_overbought & 
            rsi_falling & 
            volume_confirms & 
            vwap_break_short
        )
        
        return df
    
    def run_backtest(self, df: pd.DataFrame, initial_capital: float = 10000.0) -> dict:
        """Run backtest simulation"""
        df = self.prepare_data(df)
        df = self.generate_signals(df)
        
        capital = initial_capital
        position = None  # None, 'long', or 'short'
        entry_price = 0
        entry_time = None
        stop_loss = 0
        profit_target = 0
        position_size = 0
        
        self.equity_curve = [capital]
        
        for idx, row in df.iterrows():
            # Check if we need to exit current position
            if position is not None:
                time_in_trade = (row['timestamp'] - entry_time).total_seconds() / 60
                
                exit_reason = None
                exit_price = row['close']
                
                if position == 'long':
                    if row['low'] <= stop_loss:
                        exit_reason = 'stop_loss'
                        exit_price = stop_loss
                    elif row['high'] >= profit_target:
                        exit_reason = 'profit_target'
                        exit_price = profit_target
                    elif time_in_trade >= self.time_stop_minutes:
                        exit_reason = 'time_stop'
                
                elif position == 'short':
                    if row['high'] >= stop_loss:
                        exit_reason = 'stop_loss'
                        exit_price = stop_loss
                    elif row['low'] <= profit_target:
                        exit_reason = 'profit_target'
                        exit_price = profit_target
                    elif time_in_trade >= self.time_stop_minutes:
                        exit_reason = 'time_stop'
                
                if exit_reason:
                    pnl = (exit_price - entry_price) * position_size
                    if position == 'short':
                        pnl = -pnl
                    
                    pnl_pct = pnl / capital
                    capital += pnl
                    
                    trade = Trade(
                        entry_time=entry_time,
                        exit_time=row['timestamp'],
                        side=position,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        size=position_size,
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        exit_reason=exit_reason
                    )
                    self.trades.append(trade)
                    
                    position = None
                    self.equity_curve.append(capital)
            
            # Check for new entry if no position
            if position is None:
                if row['long_signal'] and not np.isnan(row['atr']):
                    position = 'long'
                    entry_price = row['close']
                    entry_time = row['timestamp']
                    
                    risk_amount = capital * self.risk_per_trade
                    stop_distance = row['atr'] * self.atr_mult
                    position_size = risk_amount / stop_distance
                    
                    stop_loss = entry_price - stop_distance
                    profit_target = entry_price + (stop_distance * self.profit_target_r)
                
                elif row['short_signal'] and not np.isnan(row['atr']):
                    position = 'short'
                    entry_price = row['close']
                    entry_time = row['timestamp']
                    
                    risk_amount = capital * self.risk_per_trade
                    stop_distance = row['atr'] * self.atr_mult
                    position_size = risk_amount / stop_distance
                    
                    stop_loss = entry_price + stop_distance
                    profit_target = entry_price - (stop_distance * self.profit_target_r)
        
        return self.calculate_stats(initial_capital, capital)
    
    def calculate_stats(self, initial_capital: float, final_capital: float) -> dict:
        """Calculate backtest statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_return': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }
        
        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl <= 0]
        
        total_return = (final_capital - initial_capital) / initial_capital * 100
        win_rate = len(wins) / len(self.trades) * 100
        
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate max drawdown
        peak = initial_capital
        max_dd = 0
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        # Calculate Sharpe-like ratio (simplified)
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            sharpe = returns.mean() / returns.std() * np.sqrt(252 * 24 * 60) if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'total_return_pct': round(total_return, 2),
            'max_drawdown_pct': round(max_dd, 2),
            'sharpe_ratio': round(sharpe, 2),
            'avg_trade_pct': round(np.mean([t.pnl_pct * 100 for t in self.trades]), 3),
            'final_capital': round(final_capital, 2)
        }
    
    def print_report(self, stats: dict):
        """Print formatted backtest report"""
        print("\n" + "="*50)
        print("VWAP MOMENTUM BACKTEST RESULTS")
        print("="*50)
        print(f"\n📊 PERFORMANCE")
        print(f"  Total Trades:     {stats['total_trades']}")
        print(f"  Win Rate:         {stats['win_rate']}%")
        print(f"  Profit Factor:    {stats['profit_factor']}")
        print(f"  Total Return:     {stats['total_return_pct']}%")
        print(f"\n📉 RISK")
        print(f"  Max Drawdown:     {stats['max_drawdown_pct']}%")
        print(f"  Sharpe Ratio:     {stats['sharpe_ratio']}")
        print(f"\n💰 Avg Trade:       {stats['avg_trade_pct']}%")
        print(f"   Final Capital:   ${stats['final_capital']:,}")
        print("="*50)
        
        # Exit analysis
        if self.trades:
            print(f"\n🔍 EXIT BREAKDOWN")
            exits = {}
            for t in self.trades:
                exits[t.exit_reason] = exits.get(t.exit_reason, 0) + 1
            for reason, count in exits.items():
                pct = count / len(self.trades) * 100
                print(f"  {reason}: {count} ({pct:.1f}%)")


def main():
    print("🌀 VWAP + Momentum Backtester")
    print("Fetching BTC data from Binance...")
    
    strategy = VWAPMomentumStrategy(
        rsi_period=14,
        rsi_long_threshold=30,
        rsi_short_threshold=70,
        volume_mult=1.5,
        atr_mult=2.0,
        risk_per_trade=0.01,
        profit_target_r=3.0,
        time_stop_minutes=5
    )
    
    # Get last ~16 hours of 1-min data
    df = strategy.fetch_binance_data("BTCUSDT", limit=1000)
    print(f"Loaded {len(df)} 1-minute candles")
    print(f"Period: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}\n")
    
    # Run backtest
    stats = strategy.run_backtest(df, initial_capital=10000.0)
    
    # Print results
    strategy.print_report(stats)
    
    # Print recent trades
    if strategy.trades:
        print(f"\n📋 LAST 5 TRADES")
        for t in strategy.trades[-5:]:
            emoji = "🟢" if t.pnl > 0 else "🔴"
            print(f"  {emoji} {t.side.upper()} | {t.entry_time.strftime('%H:%M')} | "
                  f"P&L: ${t.pnl:.2f} | Exit: {t.exit_reason}")


if __name__ == "__main__":
    main()
