"""
VWAP Mean Reversion Strategy
Based on MCMC optimization results
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class VWAPStrategy:
    """
    VWAP Mean Reversion Strategy
    
    Buy when price drops below VWAP by entry_bias
    Sell when price rises above VWAP by exit_bias
    """
    # Optimized from MCMC: entry=0.23%, exit=0.28%
    entry_bias: float = 0.0023  # 0.23%
    exit_bias: float = 0.0028   # 0.28%
    
    # Risk management
    position_size: float = 100.0  # USDT per trade
    stop_loss: float = 0.015      # 1.5% max loss
    
    def __post_init__(self):
        self.position = 0  # -1 = short, 0 = flat, 1 = long
        self.entry_price = 0.0
        self.trades = []
        
    def update(self, timestamp, price, vwap):
        """Process new price and VWAP data"""
        signal = None
        
        # Calculate distance from VWAP
        distance = (price - vwap) / vwap
        
        # Entry logic - go long when price drops below VWAP
        if self.position == 0 and distance < -self.entry_bias:
            signal = 'BUY'
            self.position = 1
            self.entry_price = price
            self.trades.append({
                'timestamp': timestamp,
                'action': 'BUY',
                'price': price,
                'vwap': vwap,
                'distance': distance
            })
        
        # Exit logic - sell when price rises above VWAP
        elif self.position == 1:
            # Profit target hit
            if distance > self.exit_bias:
                signal = 'SELL'
                profit = (price - self.entry_price) / self.entry_price
                self.position = 0
                self.trades.append({
                    'timestamp': timestamp,
                    'action': 'SELL',
                    'price': price,
                    'vwap': vwap,
                    'profit_pct': profit * 100
                })
            # Stop loss hit
            elif (self.entry_price - price) / self.entry_price > self.stop_loss:
                signal = 'SELL'
                profit = (price - self.entry_price) / self.entry_price
                self.position = 0
                self.trades.append({
                    'timestamp': timestamp,
                    'action': 'SELL',
                    'price': price,
                    'vwap': vwap,
                    'profit_pct': profit * 100,
                    'stop_loss': True
                })
        
        return signal
    
    def calculate_vwap(self, df, period=20):
        """Calculate VWAP for given period"""
        df = df.copy()
        df['vwap'] = (df['close'] * df['volume']).rolling(period).sum() / df['volume'].rolling(period).sum()
        return df['vwap'].iloc[-1]
    
    def get_stats(self):
        """Get current trading statistics"""
        closed_trades = [t for t in self.trades if t['action'] == 'SELL']
        if not closed_trades:
            return {'total_trades': 0, 'win_rate': 0, 'avg_profit': 0}
        
        profits = [t['profit_pct'] for t in closed_trades]
        wins = sum(1 for p in profits if p > 0)
        
        return {
            'total_trades': len(closed_trades),
            'win_rate': (wins / len(closed_trades)) * 100,
            'avg_profit': np.mean(profits),
            'total_profit': sum(profits),
            'max_profit': max(profits),
            'max_loss': min(profits)
        }
