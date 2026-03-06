#!/usr/bin/env python3
"""
VWAP + Momentum Strategy Backtester for BTC
High-frequency day trading on crypto markets
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import json

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    import subprocess
    subprocess.check_call(["pip", "install", "yfinance", "-q"])
    import yfinance as yf


@dataclass
class Trade:
    """Single trade record"""
    entry_time: datetime
    exit_time: Optional[datetime]
    side: str  # 'long' or 'short'
    entry_price: float
    exit_price: Optional[float]
    size: float
    stop_loss: float
    take_profit: float
    pnl: float = 0.0
    pnl_pct: float = 0.0
    status: str = 'open'  # 'open', 'closed', 'stopped'


@dataclass
class Signal:
    """Trading signal from strategy"""
    timestamp: datetime
    side: str
    price: float
    vwap: float
    rsi: float
    volume_ratio: float
    atr: float


class VWAPMomentumStrategy:
    """
    VWAP Bounce Strategy for BTC day trading
    - Long: Price < VWAP + oversold RSI + volume spike, wait for VWAP break
    - Short: Price > VWAP + overbought RSI + volume spike, wait for VWAP break
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        volume_ma_period: int = 20,
        volume_threshold: float = 1.5,
        atr_period: int = 14,
        stop_atr_mult: float = 2.0,
        profit_target_atr_mult: float = 3.0,
        max_hold_bars: int = 5,
        risk_per_trade: float = 0.01  # 1% of equity
    ):
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.volume_ma_period = volume_ma_period
        self.volume_threshold = volume_threshold
        self.atr_period = atr_period
        self.stop_atr_mult = stop_atr_mult
        self.profit_target_atr_mult = profit_target_atr_mult
        self.max_hold_bars = max_hold_bars
        self.risk_per_trade = risk_per_trade
        
        # State
        self.position: Optional[Trade] = None
        self.signals: List[Signal] = []
        self.trades: List[Trade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VWAP, RSI, ATR, and volume indicators"""
        df = df.copy()
        
        # VWAP calculation
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        cumulative_tp_vol = (typical_price * df['volume']).cumsum()
        cumulative_vol = df['volume'].cumsum()
        df['vwap'] = cumulative_tp_vol / cumulative_vol
        
        # Price vs VWAP
        df['price_vs_vwap'] = (df['close'] - df['vwap']) / df['vwap'] * 100
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Volume MA and ratio
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=self.atr_period).mean()
        
        # VWAP Cross signals
        df['above_vwap'] = df['close'] > df['vwap']
        df['vwap_cross_up'] = (~df['above_vwap'].shift(1).fillna(False)) & df['above_vwap']
        df['vwap_cross_down'] = (df['above_vwap'].shift(1).fillna(False)) & (~df['above_vwap'])
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate entry signals based on strategy rules"""
        df = self.calculate_indicators(df)
        
        # Long setup conditions
        setup_long = (
            (df['close'] < df['vwap']) &  # Below VWAP
            (df['rsi'] < self.rsi_oversold) &  # Oversold
            (df['volume_ratio'] > self.volume_threshold)  # Volume spike
        )
        
        # Long entry: VWAP break after setup
        df['signal_long'] = setup_long.shift(1).fillna(False) & df['vwap_cross_up']
        
        # Short setup conditions
        setup_short = (
            (df['close'] > df['vwap']) &  # Above VWAP
            (df['rsi'] > self.rsi_overbought) &  # Overbought
            (df['volume_ratio'] > self.volume_threshold)  # Volume spike
        )
        
        # Short entry: VWAP break after setup
        df['signal_short'] = setup_short.shift(1).fillna(False) & df['vwap_cross_down']
        
        return df
    
    def calculate_position_size(self, equity: float, price: float, atr: float) -> float:
        """Calculate position size based on risk"""
        risk_amount = equity * self.risk_per_trade
        stop_distance = atr * self.stop_atrMult
        
        if stop_distance <= 0 or price <= 0:
            return 0
            
        # Position size in base currency (BTC)
        position_size = risk_amount / stop_distance
        return position_size
    
    def run_backtest(self, df: pd.DataFrame, initial_equity: float = 10000.0) -> Dict:
        """Run full backtest simulation"""
        df = self.generate_signals(df)
        
        equity = initial_equity
        self.equity_curve = [(df.index[0], equity)]
        
        entry_bar_count = 0  # Track how long we've been in position
        
        for i in range(1, len(df)):
            current = df.iloc[i]
            timestamp = df.index[i]
            
            # Update equity tracking (mark-to-market)
            if self.position and self.position.status == 'open':
                if self.position.side == 'long':
                    unrealized_pnl = (current['close'] - self.position.entry_price) * self.position.size
                else:
                    unrealized_pnl = (self.position.exit_price - current['close']) * self.position.size
                current_equity = equity + unrealized_pnl
            else:
                current_equity = equity
                
            self.equity_curve.append((timestamp, current_equity))
            
            # Check exit conditions if in position
            if self.position and self.position.status == 'open':
                entry_bar_count += 1
                
                exit_reason = None
                exit_price = None
                
                # Check stop loss
                if self.position.side == 'long':
                    if current['low'] <= self.position.stop_loss:
                        exit_price = self.position.stop_loss
                        exit_reason = 'stopped'
                    elif current['high'] >= self.position.take_profit:
                        exit_price = self.position.take_profit
                        exit_reason = 'profit_target'
                    elif entry_bar_count >= self.max_hold_bars:
                        exit_price = current['close']
                        exit_reason = 'time_stop'
                else:  # short
                    if current['high'] >= self.position.stop_loss:
                        exit_price = self.position.stop_loss
                        exit_reason = 'stopped'
                    elif current['low'] <= self.position.take_profit:
                        exit_price = self.position.take_profit
                        exit_reason = 'profit_target'
                    elif entry_bar_count >= self.max_hold_bars:
                        exit_price = current['close']
                        exit_reason = 'time_stop'
                
                # Close position
                if exit_reason:
                    self.position.exit_time = timestamp
                    self.position.exit_price = exit_price
                    
                    if self.position.side == 'long':
                        self.position.pnl = (exit_price - self.position.entry_price) * self.position.size
                    else:
                        self.position.pnl = (self.position.entry_price - exit_price) * self.position.size
                    
                    self.position.pnl_pct = self.position.pnl / (self.position.entry_price * self.position.size) * 100
                    self.position.status = exit_reason
                    
                    equity += self.position.pnl
                    self.trades.append(self.position)
                    self.position = None
                    entry_bar_count = 0
            
            # Check entry conditions if not in position
            elif self.position is None:
                if current['signal_long']:
                    atr = current['atr']
                    position_size = self.calculate_position_size(equity, current['close'], atr)
                    
                    if position_size > 0:
                        self.position = Trade(
                            entry_time=timestamp,
                            exit_time=None,
                            side='long',
                            entry_price=current['close'],
                            exit_price=None,
                            size=position_size,
                            stop_loss=current['close'] - (atr * self.stop_atr_mult),
                            take_profit=current['close'] + (atr * self.profit_target_atr_mult),
                            status='open'
                        )
                        entry_bar_count = 0
                        
                elif current['signal_short']:
                    atr = current['atr']
                    position_size = self.calculate_position_size(equity, current['close'], atr)
                    
                    if position_size > 0:
                        self.position = Trade(
                            entry_time=timestamp,
                            exit_time=None,
                            side='short',
                            entry_price=current['close'],
                            exit_price=None,
                            size=position_size,
                            stop_loss=current['close'] + (atr * self.stop_atr_mult),
                            take_profit=current['close'] - (atr * self.profit_target_atr_mult),
                            status='open'
                        )
                        entry_bar_count = 0
        
        # Close any open position at end of data
        if self.position and self.position.status == 'open':
            final_price = df['close'].iloc[-1]
            self.position.exit_time = df.index[-1]
            self.position.exit_price = final_price
            
            if self.position.side == 'long':
                self.position.pnl = (final_price - self.position.entry_price) * self.position.size
            else:
                self.position.pnl = (self.position.entry_price - final_price) * self.position.size
            
            self.position.pnl_pct = self.position.pnl / (self.position.entry_price * self.position.size) * 100
            self.position.status = 'end_of_data'
            
            equity += self.position.pnl
            self.trades.append(self.position)
        
        return self.calculate_metrics(equity, initial_equity)
    
    def calculate_metrics(self, final_equity: float, initial_equity: float) -> Dict:
        """Calculate comprehensive backtest metrics"""
        if not self.trades:
            return {
                'total_return_pct': 0,
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'max_drawdown_pct': 0
            }
        
        profits = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl <= 0]
        
        winning_trades = len(profits)
        losing_trades = len(losses)
        total_trades = len(self.trades)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_profit = sum(profits)
        total_loss = abs(sum(losses))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Calculate max drawdown
        equity_values = [e[1] for e in self.equity_curve]
        peak = equity_values[0]
        max_dd = 0
        
        for eq in equity_values:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        # Simple Sharpe (assuming 0% risk-free rate)
        equity_series = pd.Series(equity_values)
        returns = equity_series.pct_change().dropna()
        sharpe = returns.mean() / returns.std() * np.sqrt(252 * 24 * 60) if returns.std() > 0 else 0  # Annualized for minute data
        
        avg_win = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0
        
        return {
            'initial_equity': initial_equity,
            'final_equity': final_equity,
            'total_return_pct': (final_equity - initial_equity) / initial_equity * 100,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown_pct': max_dd,
            'sharpe_ratio': sharpe,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': max(profits) if profits else 0,
            'largest_loss': min(losses) if losses else 0,
        }
    
    def print_report(self, metrics: Dict):
        """Print formatted backtest report"""
        print("\n" + "=" * 60)
        print("VWAP + MOMENTUM BACKTEST RESULTS")
        print("=" * 60)
        print(f"Initial Equity:     ${metrics['initial_equity']:,.2f}")
        print(f"Final Equity:       ${metrics['final_equity']:,.2f}")
        print(f"Total Return:       {metrics['total_return_pct']:+.2f}%")
        print(f"Max Drawdown:       {metrics['max_drawdown_pct']:.2f}%")
        print(f"Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}")
        print("\n--- Trade Statistics ---")
        print(f"Total Trades:       {metrics['total_trades']}")
        print(f"Win Rate:           {metrics['win_rate']*100:.1f}%")
        print(f"Profit Factor:      {metrics['profit_factor']:.2f}")
        print(f"Avg Win:            ${metrics['avg_win']:+.2f}")
        print(f"Avg Loss:           ${metrics['avg_loss']:+.2f}")
        print(f"Largest Win:        ${metrics['largest_win']:,.2f}")
        print(f"Largest Loss:       ${metrics['largest_loss']:,.2f}")
        print("=" * 60)


def fetch_btc_data(period: str = "60d", interval: str = "1m") -> pd.DataFrame:
    """Fetch BTC-USD data from Yahoo Finance"""
    print(f"Fetching BTC data: {period} @ {interval} resolution...")
    
    # For crypto, use BTC-USD ticker
    ticker = yf.Ticker("BTC-USD")
    
    # yfinance has limits on intraday data
    df = ticker.history(period=period, interval=interval)
    
    if df.empty:
        print("Error: No data returned. Trying alternative interval...")
        # Fall back to 5m
        df = ticker.history(period=period, interval="5m")
    
    print(f"Loaded {len(df)} bars")
    return df


def main():
    """Main execution"""
    print("VWAP + Momentum Strategy Backtester")
    print("=" * 40)
    
    # Fetch data
    df = fetch_btc_data(period="60d", interval="5m")  # 5min for stability
    
    if df.empty:
        print("Failed to fetch data")
        return
    
    # Initialize strategy
    strategy = VWAPMomentumStrategy(
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70,
        volume_threshold=1.5,
        stop_atr_mult=2.0,
        profit_target_atr_mult=3.0,
        max_hold_bars=5,
        risk_per_trade=0.01
    )
    
    # Run backtest
    print("\nRunning backtest...")
    metrics = strategy.run_backtest(df, initial_equity=10000.0)
    
    # Print results
    strategy.print_report(metrics)
    
    # Print last 5 trades
    print("\n--- Recent Trades ---")
    for trade in strategy.trades[-5:]:
        print(f"{trade.side.upper():>5} | {trade.entry_time.strftime('%m/%d %H:%M')} | "
              f"Entry: ${trade.entry_price:,.2f} | Exit: ${trade.exit_price:,.2f} | "
              f"PnL: ${trade.pnl:+.2f} | {trade.status}")


if __name__ == "__main__":
    main()
