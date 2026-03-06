#!/usr/bin/env python3
"""
Paper Trading Runner for VWAP Strategy
Simulates real-time trading without real money
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from vwap_strategy import VWAPStrategy


class PaperTrader:
    def __init__(self, 
                 symbol="BTCUSDT",
                 initial_balance=1000.0,
                 entry_bias=0.0023,
                 exit_bias=0.0028,
                 data_file=None):
        
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.strategy = VWAPStrategy(
            entry_bias=entry_bias,
            exit_bias=exit_bias
        )
        
        self.position_value = 0.0
        self.position_qty = 0.0
        self.pnl_history = []
        self.equity_curve = [initial_balance]
        
        # Time in market tracking
        self.position_entry_time = None
        self.total_time_in_market = 0  # in minutes
        self.simulation_start_time = None
        self.simulation_end_time = None
        
        # Set up logging
        self.trade_log_file = Path(__file__).parent / f"trades_{symbol}_{datetime.now().strftime('%Y%m%d')}.csv"
        self.stats_file = Path(__file__).parent / f"stats_{symbol}_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Load data if provided
        self.data = None
        self.current_idx = 0
        if data_file and Path(data_file).exists():
            self.data = pd.read_csv(data_file, index_col=0, parse_dates=True)
            print(f"📊 Loaded {len(self.data)} historical data points from {data_file}")
        
        print(f"🚀 Paper Trading Initialized")
        print(f"   Symbol: {symbol}")
        print(f"   Entry Bias: {entry_bias*100:.2f}%")
        print(f"   Exit Bias: {exit_bias*100:.2f}%")
        print(f"   Initial Balance: ${initial_balance:,.2f}\n")
    
    def simulate_tick(self, price, vwap, timestamp=None):
        """Simulate one market tick"""
        ts = timestamp or datetime.now()
        
        # Track simulation time
        if self.simulation_start_time is None:
            self.simulation_start_time = ts
        self.simulation_end_time = ts
        
        signal = self.strategy.update(ts, price, vwap)
        
        if signal == 'BUY':
            # Buy in paper trading
            qty = self.strategy.position_size / price
            self.position_qty = qty
            self.position_value = self.strategy.position_size
            self.balance -= self.position_value
            self.position_entry_time = ts
            
            print(f"🟢 BUY  @ ${price:,.2f} | VWAP: ${vwap:,.2f} | Qty: {qty:.6f}")
            self._log_trade('BUY', price, vwap, qty)
            
        elif signal == 'SELL':
            # Sell in paper trading
            sell_value = self.position_qty * price
            profit = sell_value - self.position_value
            self.balance += sell_value
            
            # Track time in market for this trade
            if self.position_entry_time is not None:
                trade_duration = (ts - self.position_entry_time).total_seconds() / 60  # minutes
                self.total_time_in_market += trade_duration
            
            trade_info = self.strategy.trades[-1]
            is_sl = trade_info.get('stop_loss', False)
            sl_tag = " [STOP LOSS]" if is_sl else ""
            
            pct = (sell_value - self.position_value) / self.position_value * 100
            print(f"🔴 SELL @ ${price:,.2f} | PnL: ${profit:+.2f} ({pct:+.2f}%){sl_tag}")
            self._log_trade('SELL', price, vwap, self.position_qty, profit, is_sl)
            
            self.position_qty = 0
            self.position_value = 0
            self.position_entry_time = None
            
        # Update equity
        total_value = self.balance + (self.position_qty * price if self.position_qty > 0 else 0)
        self.equity_curve.append(total_value)
        self.pnl_history.append(total_value - self.initial_balance)
        
        return signal
    
    def _log_trade(self, action, price, vwap, qty, profit=None, stop_loss=False):
        """Log trade to CSV"""
        import csv
        
        row = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'symbol': self.symbol,
            'price': price,
            'vwap': vwap,
            'qty': qty,
            'balance': self.balance,
            'profit': profit or 0,
            'stop_loss': stop_loss
        }
        
        file_exists = self.trade_log_file.exists()
        with open(self.trade_log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    
    def run_simulation(self, speed_factor=1.0):
        """Run paper trading on historical data"""
        if self.data is None:
            print("❌ No data loaded. Cannot run simulation.")
            return
        
        print("🎲 Starting historical simulation...\n")
        
        for i, row in self.data.iterrows():
            price = row['close']
            vwap = row['vwap']
            self.simulate_tick(price, vwap, i)
            
        self._print_summary()
        self._save_stats()
    
    def _print_summary(self):
        """Print trading summary"""
        stats = self.strategy.get_stats()
        final_value = self.equity_curve[-1] if self.equity_curve else self.initial_balance
        total_pnl = final_value - self.initial_balance
        total_pnl_pct = (total_pnl / self.initial_balance) * 100
        
        # Calculate time in market stats
        if self.simulation_start_time and self.simulation_end_time:
            total_simulation_minutes = (self.simulation_end_time - self.simulation_start_time).total_seconds() / 60
            time_in_market_pct = (self.total_time_in_market / total_simulation_minutes * 100) if total_simulation_minutes > 0 else 0
        else:
            total_simulation_minutes = 0
            time_in_market_pct = 0
        
        # Format time for display
        hours_in_market = self.total_time_in_market / 60
        days_in_market = hours_in_market / 24
        
        print("\n" + "="*50)
        print("📊 PAPER TRADING SUMMARY")
        print("="*50)
        print(f"Start Balance:  ${self.initial_balance:,.2f}")
        print(f"Final Balance:  ${final_value:,.2f}")
        print(f"Total PnL:      ${total_pnl:+.2f} ({total_pnl_pct:+.2f}%)")
        print(f"Total Trades:   {stats['total_trades']}")
        print(f"Win Rate:       {stats['win_rate']:.1f}%")
        print(f"Avg Profit:     {stats['avg_profit']:.3f}%")
        print(f"Max Profit:     {stats['max_profit']:.3f}%")
        print(f"Max Loss:       {stats['max_loss']:.3f}%")
        print("-"*50)
        print(f"⏱️ TIME IN MARKET:")
        print(f"   Total: {self.total_time_in_market:.0f} min ({hours_in_market:.1f} hrs, {days_in_market:.2f} days)")
        print(f"   Percentage: {time_in_market_pct:.1f}%")
        print(f"   Cash Time: {100-time_in_market_pct:.1f}%")
        print("="*50)
    
    def _save_stats(self):
        """Save statistics to JSON"""
        # Calculate time stats
        if self.simulation_start_time and self.simulation_end_time:
            total_simulation_minutes = (self.simulation_end_time - self.simulation_start_time).total_seconds() / 60
            time_in_market_pct = (self.total_time_in_market / total_simulation_minutes * 100) if total_simulation_minutes > 0 else 0
        else:
            total_simulation_minutes = 0
            time_in_market_pct = 0
        
        stats = {
            'symbol': self.symbol,
            'start_time': self.data.index[0].isoformat() if hasattr(self.data, 'index') else str(datetime.now()),
            'end_time': self.data.index[-1].isoformat() if hasattr(self.data, 'index') else str(datetime.now()),
            'initial_balance': self.initial_balance,
            'final_balance': self.equity_curve[-1],
            'total_pnl': self.equity_curve[-1] - self.initial_balance,
            'total_trades': self.strategy.get_stats()['total_trades'],
            'win_rate': self.strategy.get_stats()['win_rate'],
            'avg_profit': self.strategy.get_stats()['avg_profit'],
            'time_in_market': {
                'minutes': self.total_time_in_market,
                'hours': self.total_time_in_market / 60,
                'days': self.total_time_in_market / 60 / 24,
                'percentage': time_in_market_pct,
                'cash_percentage': 100 - time_in_market_pct
            },
            'equity_curve': self.equity_curve
        }
        
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        print(f"📁 Stats saved to: {self.stats_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='VWAP Paper Trading')
    parser.add_argument('--symbol', default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--data', help='Path to CSV data file')
    parser.add_argument('--entry-bias', type=float, default=0.0023, help='Entry bias (e.g. 0.0023 for 0.23%)')
    parser.add_argument('--exit-bias', type=float, default=0.0028, help='Exit bias (e.g. 0.0028 for 0.28%)')
    parser.add_argument('--balance', type=float, default=1000.0, help='Initial balance')
    
    args = parser.parse_args()
    
    # Find most recent synthetic data if not specified
    if not args.data:
        data_dir = Path(__file__).parent / 'data'
        data_files = sorted(data_dir.glob('synthetic_*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
        if data_files:
            args.data = str(data_files[0])
            print(f"📝 Using latest data: {args.data}")
    
    trader = PaperTrader(
        symbol=args.symbol,
        data_file=args.data,
        initial_balance=args.balance,
        entry_bias=args.entry_bias,
        exit_bias=args.exit_bias
    )
    
    trader.run_simulation()


if __name__ == '__main__':
    main()
