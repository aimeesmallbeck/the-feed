#!/usr/bin/env python3
"""
VWAP Momentum Backtester for Crypto
Strategy: VWAP bounce with RSI confirmation
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import json

@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    side: str  # 'long' or 'short'
    size: float
    pnl: Optional[float]
    pnl_pct: Optional[float]
    exit_reason: Optional[str]

@dataclass
class BacktestResult:
    total_return_pct: float
    win_rate: float
    profit_factor: float
    max_drawdown_pct: float
    sharpe_ratio: float
    total_trades: int
    avg_trade_return: float
    trades: List[Trade]

class VWAPStrategy:
    def __init__(self, 
                 rsi_period: int = 14,
                 rsi_oversold: int = 30,
                 rsi_overbought: int = 70,
                 volume_threshold: float = 1.5,
                 atr_period: int = 14,
                 risk_per_trade: float = 0.01,
                 profit_target_r: float = 3.0,
                 time_stop_minutes: int = 5):
        
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.volume_threshold = volume_threshold
        self.atr_period = atr_period
        self.risk_per_trade = risk_per_trade
        self.profit_target_r = profit_target_r
        self.time_stop_minutes = time_stop_minutes
        
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate VWAP manually (rolling since session start)"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        volume = df['volume']
        
        # Cumulative VWAP (reset daily for crypto 24/7, use rolling 24h window)
        cum_tp_vol = (typical_price * volume).rolling(window=1440, min_periods=1).sum()  # ~24h in 1m candles
        cum_vol = volume.rolling(window=1440, min_periods=1).sum()
        
        return cum_tp_vol / cum_vol
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period, min_periods=1).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(window=self.atr_period, min_periods=1).mean()
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        df = df.copy()
        df['vwap'] = self.calculate_vwap(df)
        df['rsi'] = self.calculate_rsi(df['close'])
        df['atr'] = self.calculate_atr(df)
        
        # Volume moving average
        df['volume_ma'] = df['volume'].rolling(window=20, min_periods=1).mean()
        df['volume_spike'] = df['volume'] > (df['volume_ma'] * self.volume_threshold)
        
        # Signal conditions
        df['below_vwap'] = df['close'] < df['vwap']
        df['above_vwap'] = df['close'] > df['vwap']
        df['cross_above_vwap'] = df['below_vwap'].shift(1) & df['above_vwap']
        df['cross_below_vwap'] = df['above_vwap'].shift(1) & df['below_vwap']
        
        # RSI conditions
        df['rsi_rising'] = df['rsi'] > df['rsi'].shift(1)
        df['rsi_falling'] = df['rsi'] < df['rsi'].shift(1)
        df['rsi_oversold'] = df['rsi'] < self.rsi_oversold
        df['rsi_overbought'] = df['rsi'] > self.rsi_overbought
        
        # Entry signals
        df['long_signal'] = (
            df['below_vwap'] & 
            df['rsi_oversold'] & 
            df['rsi_rising'] & 
            df['volume_spike'] & 
            df['cross_above_vwap']
        )
        
        df['short_signal'] = (
            df['above_vwap'] & 
            df['rsi_overbought'] & 
            df['rsi_falling'] & 
            df['volume_spike'] & 
            df['cross_below_vwap']
        )
        
        return df
    
    def backtest(self, df: pd.DataFrame, initial_capital: float = 10000) -> BacktestResult:
        """Run backtest simulation"""
        df = self.generate_signals(df)
        
        trades: List[Trade] = []
        position: Optional[str] = None
        entry_price: float = 0
        entry_time: Optional[datetime] = None
        entry_size: float = 0
        stop_loss: float = 0
        take_profit: float = 0
        
        capital = initial_capital
        equity_curve = [capital]
        
        for idx, row in df.iterrows():
            current_price = row['close']
            current_time = idx if isinstance(idx, datetime) else pd.to_datetime(idx)
            
            # Check if position is open
            if position:
                # Calculate unrealized PnL
                if position == 'long':
                    unrealized_pct = (current_price - entry_price) / entry_price
                else:
                    unrealized_pct = (entry_price - current_price) / entry_price
                
                # Check exits
                exit_triggered = False
                exit_reason = None
                
                # Stop loss
                if position == 'long' and current_price <= stop_loss:
                    exit_triggered = True
                    exit_reason = 'stop_loss'
                elif position == 'short' and current_price >= stop_loss:
                    exit_triggered = True
                    exit_reason = 'stop_loss'
                
                # Take profit
                elif position == 'long' and current_price >= take_profit:
                    exit_triggered = True
                    exit_reason = 'take_profit'
                elif position == 'short' and current_price <= take_profit:
                    exit_triggered = True
                    exit_reason = 'take_profit'
                
                # Time stop
                elif entry_time and (current_time - entry_time).total_seconds() / 60 > self.time_stop_minutes:
                    exit_triggered = True
                    exit_reason = 'time_stop'
                
                if exit_triggered:
                    # Close position
                    if position == 'long':
                        pnl = (current_price - entry_price) * entry_size
                    else:
                        pnl = (entry_price - current_price) * entry_size
                    
                    pnl_pct = pnl / (entry_price * entry_size)
                    capital += pnl
                    
                    trades.append(Trade(
                        entry_time=entry_time,
                        exit_time=current_time,
                        entry_price=entry_price,
                        exit_price=current_price,
                        side=position,
                        size=entry_size,
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        exit_reason=exit_reason
                    ))
                    
                    position = None
                    entry_price = 0
                    entry_time = None
                    entry_size = 0
            
            # Check for new entries (only if no position)
            elif not position:
                atr = row['atr']
                
                if row['long_signal'] and atr > 0:
                    position = 'long'
                    entry_price = current_price
                    entry_time = current_time
                    
                    # Risk-based position sizing
                    stop_dist = 2 * atr
                    risk_amount = capital * self.risk_per_trade
                    entry_size = risk_amount / stop_dist
                    
                    stop_loss = entry_price - stop_dist
                    take_profit = entry_price + (stop_dist * self.profit_target_r)
                    
                elif row['short_signal'] and atr > 0:
                    position = 'short'
                    entry_price = current_price
                    entry_time = current_time
                    
                    stop_dist = 2 * atr
                    risk_amount = capital * self.risk_per_trade
                    entry_size = risk_amount / stop_dist
                    
                    stop_loss = entry_price + stop_dist
                    take_profit = entry_price - (stop_dist * self.profit_target_r)
            
            equity_curve.append(capital)
        
        # Close any open position at end
        if position:
            final_price = df['close'].iloc[-1]
            if position == 'long':
                pnl = (final_price - entry_price) * entry_size
            else:
                pnl = (entry_price - final_price) * entry_size
            
            pnl_pct = pnl / (entry_price * entry_size)
            capital += pnl
            
            trades.append(Trade(
                entry_time=entry_time,
                exit_time=df.index[-1],
                entry_price=entry_price,
                exit_price=final_price,
                side=position,
                size=entry_size,
                pnl=pnl,
                pnl_pct=pnl_pct,
                exit_reason='end_of_data'
            ))
        
        # Calculate metrics
        if len(trades) == 0:
            return BacktestResult(
                total_return_pct=0,
                win_rate=0,
                profit_factor=0,
                max_drawdown_pct=0,
                sharpe_ratio=0,
                total_trades=0,
                avg_trade_return=0,
                trades=[]
            )
        
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl and t.pnl <= 0]
        
        gross_profit = sum(t.pnl for t in winning_trades if t.pnl)
        gross_loss = abs(sum(t.pnl for t in losing_trades if t.pnl))
        
        total_return_pct = ((capital - initial_capital) / initial_capital) * 100
        win_rate = len(winning_trades) / len(trades) * 100
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Max drawdown
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown_pct = abs(drawdown.min()) * 100
        
        # Sharpe ratio (simplified, assuming daily return)
        returns = pd.Series([t.pnl_pct for t in trades if t.pnl_pct]).dropna()
        sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if len(returns) > 1 and returns.std() > 0 else 0
        
        avg_trade_return = sum(t.pnl_pct for t in trades if t.pnl_pct) / len(trades) * 100
        
        return BacktestResult(
            total_return_pct=total_return_pct,
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            total_trades=len(trades),
            avg_trade_return=avg_trade_return,
            trades=trades
        )

def fetch_data(symbol: str, start: datetime, end: datetime, interval: str = "1m") -> pd.DataFrame:
    """Fetch crypto data from yfinance"""
    # For crypto on yfinance, use format like BTC-USD
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, interval=interval)
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    return df

def run_backtest(symbol: str = "BTC-USD", days: int = 30):
    """Run complete backtest"""
    print(f"📊 Running VWAP Strategy Backtest for {symbol}")
    print("=" * 50)
    
    # Fetch data
    end = datetime.now()
    start = end - timedelta(days=days)
    
    print(f"Fetching {days} days of data...")
    try:
        df = fetch_data(symbol, start, end)
        print(f"✓ Got {len(df)} candles")
    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        return
    
    if len(df) < 100:
        print("⚠ Not enough data for meaningful backtest")
        return
    
    # Run backtest
    strategy = VWAPStrategy()
    result = strategy.backtest(df)
    
    # Print results
    print(f"\n📈 RESULTS")
    print("-" * 50)
    print(f"Total Return:     {result.total_return_pct:+.2f}%")
    print(f"Win Rate:         {result.win_rate:.1f}%")
    print(f"Profit Factor:    {result.profit_factor:.2f}")
    print(f"Max Drawdown:     {result.max_drawdown_pct:.2f}%")
    print(f"Sharpe Ratio:     {result.sharpe_ratio:.2f}")
    print(f"Total Trades:     {result.total_trades}")
    print(f"Avg Trade Return: {result.avg_trade_return:+.2f}%")
    
    # Exit analysis
    if result.trades:
        exit_reasons = {}
        for t in result.trades:
            reason = t.exit_reason or 'unknown'
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        print(f"\n🔚 Exit Distribution:")
        for reason, count in exit_reasons.items():
            print(f"  {reason}: {count}")
    
    # Recent trades
    print(f"\n🔍 Last 5 Trades:")
    for i, t in enumerate(result.trades[-5:], 1):
        pnl_str = f"${t.pnl:.2f}" if t.pnl else "N/A"
        print(f"  {i}. {t.side} | {t.entry_time.strftime('%m/%d %H:%M')} → {t.exit_time.strftime('%H:%M')} | "
              f"{t.pnl_pct:+.2f}% ({pnl_str}) | {t.exit_reason}")
    
    return result

if __name__ == "__main__":
    # Run on BTC last 30 days
    result = run_backtest("BTC-USD", days=30)
