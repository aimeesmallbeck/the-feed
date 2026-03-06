#!/usr/bin/env python3
"""
VWAP + Momentum Day Trading Strategy
Crypto Backtester (BTC/ETH on Binance)

Core logic:
- Long when price breaks above VWAP with RSI > 30 and volume spike
- Short when price breaks below VWAP with RSI < 70 and volume spike
- Risk-based position sizing (1% risk per trade)
- ATR-based stop losses
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import json


@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime]
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    exit_price: float
    position_size: float
    stop_loss: float
    take_profit: float
    pnl: float
    pnl_pct: float
    reason: str  # 'STOP' or 'TARGET' or 'TIME'


class VWAPStrategy:
    def __init__(
        self,
        account_size: float = 10000.0,
        risk_per_trade: float = 0.01,  # 1%
        atr_multiplier: float = 2.0,
        reward_ratio: float = 3.0,
        volume_threshold: float = 1.5,
        rsi_period: int = 14,
        atr_period: int = 14,
        time_stop_bars: int = 5,
    ):
        self.account_size = account_size
        self.risk_per_trade = risk_per_trade
        self.atr_multiplier = atr_multiplier
        self.reward_ratio = reward_ratio
        self.volume_threshold = volume_threshold
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.time_stop_bars = time_stop_bars
        
        self.trades: List[Trade] = []
        self.current_position = None
        self.entry_bar = 0
        
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate VWAP (Volume Weighted Average Price)"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
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
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def calculate_position_size(self, price: float, stop_distance: float) -> float:
        """Calculate position size based on risk"""
        risk_amount = self.account_size * self.risk_per_trade
        position_size = risk_amount / stop_distance
        return position_size
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        df = df.copy()
        
        # Calculate indicators
        df['vwap'] = self.calculate_vwap(df)
        df['rsi'] = self.calculate_rsi(df['close'], self.rsi_period)
        df['atr'] = self.calculate_atr(df, self.atr_period)
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        # Price relative to VWAP
        df['above_vwap'] = df['close'] > df['vwap']
        df['below_vwap'] = df['close'] < df['vwap']
        
        # VWAP crossovers
        df['vwap_cross_up'] = (df['close'] > df['vwap']) & (df['close'].shift(1) <= df['vwap'].shift(1))
        df['vwap_cross_down'] = (df['close'] < df['vwap']) & (df['close'].shift(1) >= df['vwap'].shift(1))
        
        # Volume spike
        df['volume_spike'] = df['volume'] > (df['volume_ma'] * self.volume_threshold)
        
        # RSI conditions
        df['rsi_oversold'] = df['rsi'] < 30
        df['rsi_overbought'] = df['rsi'] > 70
        df['rsi_rising'] = df['rsi'] > df['rsi'].shift(1)
        df['rsi_falling'] = df['rsi'] < df['rsi'].shift(1)
        
        # Entry signals
        df['long_signal'] = (
            df['vwap_cross_up'] &
            df['volume_spike'] &
            (df['rsi'] > 30) &  # Not oversold
            df['rsi_rising']
        )
        
        df['short_signal'] = (
            df['vwap_cross_down'] &
            df['volume_spike'] &
            (df['rsi'] < 70) &  # Not overbought
            df['rsi_falling']
        )
        
        return df
    
    def run_backtest(self, df: pd.DataFrame) -> dict:
        """Run backtest on historical data"""
        df = self.generate_signals(df)
        self.trades = []
        self.current_position = None
        
        for i in range(len(df)):
            if i < max(self.rsi_period, self.atr_period, 20):
                continue
                
            row = df.iloc[i]
            
            # Check for exits if in position
            if self.current_position:
                bars_in_trade = i - self.entry_bar
                
                if self.current_position['direction'] == 'LONG':
                    # Check stop loss
                    if row['low'] <= self.current_position['stop_loss']:
                        self.close_position(
                            df.index[i], 
                            self.current_position['stop_loss'],
                            'STOP',
                            row
                        )
                    # Check take profit
                    elif row['high'] >= self.current_position['take_profit']:
                        self.close_position(
                            df.index[i],
                            self.current_position['take_profit'],
                            'TARGET',
                            row
                        )
                    # Time stop
                    elif bars_in_trade >= self.time_stop_bars:
                        self.close_position(
                            df.index[i],
                            row['close'],
                            'TIME',
                            row
                        )
                    # Short signal (reverse)
                    elif row['short_signal']:
                        self.close_position(df.index[i], row['close'], 'REVERSE', row)
                        self.open_position('SHORT', row, i)
                        
                elif self.current_position['direction'] == 'SHORT':
                    # Check stop loss
                    if row['high'] >= self.current_position['stop_loss']:
                        self.close_position(
                            df.index[i],
                            self.current_position['stop_loss'],
                            'STOP',
                            row
                        )
                    # Check take profit
                    elif row['low'] <= self.current_position['take_profit']:
                        self.close_position(
                            df.index[i],
                            self.current_position['take_profit'],
                            'TARGET',
                            row
                        )
                    # Time stop
                    elif bars_in_trade >= self.time_stop_bars:
                        self.close_position(
                            df.index[i],
                            row['close'],
                            'TIME',
                            row
                        )
                    # Long signal (reverse)
                    elif row['long_signal']:
                        self.close_position(df.index[i], row['close'], 'REVERSE', row)
                        self.open_position('LONG', row, i)
            
            # Check for new entries if flat
            else:
                if row['long_signal']:
                    self.open_position('LONG', row, i)
                elif row['short_signal']:
                    self.open_position('SHORT', row, i)
        
        # Close any open position at the end
        if self.current_position:
            self.close_position(
                df.index[-1],
                df['close'].iloc[-1],
                'END',
                df.iloc[-1]
            )
        
        return self.generate_report()
    
    def open_position(self, direction: str, row: pd.Series, bar_idx: int):
        """Open a new position"""
        entry_price = row['close']
        atr = row['atr']
        stop_distance = atr * self.atr_multiplier
        
        if direction == 'LONG':
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + (stop_distance * self.reward_ratio)
        else:
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - (stop_distance * self.reward_ratio)
        
        position_size = self.calculate_position_size(entry_price, stop_distance)
        
        self.current_position = {
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'entry_time': row.name,
            'stop_distance': stop_distance,
        }
        self.entry_bar = bar_idx
    
    def close_position(self, exit_time, exit_price, reason: str, row: pd.Series):
        """Close current position and record trade"""
        if not self.current_position:
            return
            
        pos = self.current_position
        
        if pos['direction'] == 'LONG':
            pnl = (exit_price - pos['entry_price']) * pos['position_size']
            pnl_pct = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
        else:
            pnl = (pos['entry_price'] - exit_price) * pos['position_size']
            pnl_pct = (pos['entry_price'] - exit_price) / pos['entry_price'] * 100
        
        trade = Trade(
            entry_time=pos['entry_time'],
            exit_time=exit_time,
        direction=pos['direction'],
            entry_price=pos['entry_price'],
            exit_price=exit_price,
            position_size=pos['position_size'],
            stop_loss=pos['stop_loss'],
            take_profit=pos['take_profit'],
            pnl=pnl,
            pnl_pct=pnl_pct,
            reason=reason
        )
        
        self.trades.append(trade)
        self.account_size += pnl
        self.current_position = None
    
    def generate_report(self) -> dict:
        """Generate backtest performance report"""
        if not self.trades:
            return {"error": "No trades generated"}
        
        trades_df = pd.DataFrame([
            {
                'entry_time': t.entry_time,
                'exit_time': t.exit_time,
                'direction': t.direction,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'pnl': t.pnl,
                'pnl_pct': t.pnl_pct,
                'reason': t.reason,
            }
            for t in self.trades
        ])
        
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        
        total_trades = len(trades_df)
        win_rate = len(wins) / total_trades if total_trades > 0 else 0
        
        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0
        
        profit_factor = abs(wins['pnl'].sum() / losses['pnl'].sum()) if losses['pnl'].sum() != 0 else float('inf')
        
        # Calculate max drawdown
        cumulative = trades_df['pnl'].cumsum()
        running_max = cumulative.expanding().max()
        drawdown = cumulative - running_max
        max_drawdown = drawdown.min()
        
        # Calculate Sharpe-like metric (simplified)
        returns = trades_df['pnl_pct']
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0
        
        report = {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': trades_df['pnl'].sum(),
            'avg_trade': trades_df['pnl'].mean(),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'sharpe': sharpe,
            'final_balance': self.account_size,
            'return_pct': (self.account_size - 10000) / 10000 * 100,
            'trades': trades_df.to_dict('records'),
            'exit_reasons': trades_df['reason'].value_counts().to_dict(),
        }
        
        return report


if __name__ == '__main__':
    # Example usage
    print("VWAP Strategy Backtester")
    print("=" * 50)
    print("\nTo run a backtest:")
    print("1. Load your data as a DataFrame with columns: open, high, low, close, volume")
    print("2. Create strategy: strategy = VWAPStrategy(account_size=10000)")
    print("3. Run backtest: results = strategy.run_backtest(df)")
    print("4. Results include win rate, profit factor, drawdown, etc.")
