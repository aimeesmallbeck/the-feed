#!/usr/bin/env python3
"""
VWAP + Momentum Backtester for BTC/USD
Strategy: Mean-reversion to VWAP with momentum confirmation
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============== CONFIG ==============
SYMBOL = 'BTC-USD'  # Can change to ETH-USD, SPY, etc.
TIMEFRAME = '1m'    # 1m, 5m, 1h
LOOKBACK_DAYS = 30  # Days of data to fetch

# Strategy Parameters
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
VOLUME_MULTIPLIER = 1.5
VOL_PERIOD = 20
ATR_PERIOD = 14

# Risk Management
RISK_PER_TRADE = 0.01  # 1% of account
ATR_MULTIPLIER_SL = 2.0  # Stop loss = 2x ATR
PROFIT_TARGET_R = 3.0  # 3R profit target
MAX_HOLD_BARS = 5  # Time stop after N bars

# Account
STARTING_CAPITAL = 10000

# ============== INDICATORS ==============

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_vwap(df):
    """Calculate Volume-Weighted Average Price"""
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    return vwap

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

# ============== BACKTESTER ==============

class VWAPBacktester:
    def __init__(self, df, starting_capital=10000):
        self.df = df.copy()
        self.capital = starting_capital
        self.initial_capital = starting_capital
        self.position = None
        self.trades = []
        self.equity_curve = []
        
    def calculate_signals(self):
        """Calculate all indicators and signals"""
        df = self.df
        
        # Indicators
        df['RSI'] = calculate_rsi(df['Close'], RSI_PERIOD)
        df['VWAP'] = calculate_vwap(df)
        df['ATR'] = calculate_atr(df, ATR_PERIOD)
        df['Vol_MA'] = df['Volume'].rolling(VOL_PERIOD).mean()
        df['Volume_Spike'] = df['Volume'] > (df['Vol_MA'] * VOLUME_MULTIPLIER)
        
        # Price vs VWAP
        df['Above_VWAP'] = df['Close'] > df['VWAP']
        df['Below_VWAP'] = df['Close'] < df['VWAP']
        
        # RSI conditions
        df['RSI_Oversold'] = df['RSI'] < RSI_OVERSOLD
        df['RSI_Overbought'] = df['RSI'] > RSI_OVERBOUGHT
        df['RSI_Rising'] = df['RSI'] > df['RSI'].shift(1)
        df['RSI_Falling'] = df['RSI'] < df['RSI'].shift(1)
        
        # VWAP cross signals
        df['Cross_Above_VWAP'] = (df['Close'] > df['VWAP']) & (df['Close'].shift(1) <= df['VWAP'].shift(1))
        df['Cross_Below_VWAP'] = (df['Close'] < df['VWAP']) & (df['Close'].shift(1) >= df['VWAP'].shift(1))
        
        # Entry signals
        df['Long_Signal'] = (
            df['Below_VWAP'] &  # Price below VWAP
            df['RSI_Oversold'] &  # Oversold
            df['RSI_Rising'] &  # RSI turning up
            df['Volume_Spike'] &  # Volume confirmation
            df['Cross_Above_VWAP']  # Breaking back above VWAP
        )
        
        df['Short_Signal'] = (
            df['Above_VWAP'] &  # Price above VWAP
            df['RSI_Overbought'] &  # Overbought
            df['RSI_Falling'] &  # RSI turning down
            df['Volume_Spike'] &  # Volume confirmation
            df['Cross_Below_VWAP']  # Breaking back below VWAP
        )
        
        self.df = df
        
    def run_backtest(self):
        """Run the backtest simulation"""
        df = self.df
        
        for i in range(len(df)):
            current = df.iloc[i]
            
            # Skip if not enough data
            if pd.isna(current['ATR']) or pd.isna(current['VWAP']):
                self.equity_curve.append(self.capital)
                continue
            
            # Check for exit if in position
            if self.position:
                exit_reason = self.check_exit(current, i)
                if exit_reason:
                    self.close_position(current, exit_reason, i)
                    self.position = None
            
            # Check for entry if not in position
            if not self.position:
                if current['Long_Signal']:
                    self.enter_position(current, 'LONG', i)
                elif current['Short_Signal']:
                    self.enter_position(current, 'SHORT', i)
            
            # Track equity
            if self.position:
                unrealized_pnl = self.calculate_unrealized_pnl(current)
                self.equity_curve.append(self.capital + unrealized_pnl)
            else:
                self.equity_curve.append(self.capital)
        
        # Close any open position at end
        if self.position:
            self.close_position(df.iloc[-1], 'END_OF_DATA', len(df)-1)
    
    def enter_position(self, bar, direction, idx):
        """Enter a new position"""
        price = bar['Close']
        atr = bar['ATR']
        
        # Position sizing: Risk 1% per trade
        risk_amount = self.capital * RISK_PER_TRADE
        stop_distance = atr * ATR_MULTIPLIER_SL
        
        if direction == 'LONG':
            stop_price = price - stop_distance
            take_profit = price + (stop_distance * PROFIT_TARGET_R)
        else:
            stop_price = price + stop_distance
            take_profit = price - (stop_distance * PROFIT_TARGET_R)
        
        # Calculate position size
        position_size = risk_amount / stop_distance if stop_distance > 0 else 0
        
        self.position = {
            'direction': direction,
            'entry_price': price,
            'entry_idx': idx,
            'stop_price': stop_price,
            'take_profit': take_profit,
            'position_size': position_size,
            'risk_amount': risk_amount
        }
    
    def check_exit(self, bar, idx):
        """Check if position should be closed"""
        pos = self.position
        price = bar['Close']
        bars_held = idx - pos['entry_idx']
        
        if pos['direction'] == 'LONG':
            if price <= pos['stop_price']:
                return 'STOP_LOSS'
            if price >= pos['take_profit']:
                return 'TAKE_PROFIT'
        else:
            if price >= pos['stop_price']:
                return 'STOP_LOSS'
            if price <= pos['take_profit']:
                return 'TAKE_PROFIT'
        
        if bars_held >= MAX_HOLD_BARS:
            return 'TIME_STOP'
        
        return None
    
    def calculate_unrealized_pnl(self, bar):
        """Calculate unrealized P&L"""
        pos = self.position
        price = bar['Close']
        
        if pos['direction'] == 'LONG':
            return (price - pos['entry_price']) * pos['position_size']
        else:
            return (pos['entry_price'] - price) * pos['position_size']
    
    def close_position(self, bar, reason, idx):
        """Close position and record trade"""
        pos = self.position
        exit_price = bar['Close']
        
        if pos['direction'] == 'LONG':
            pnl = (exit_price - pos['entry_price']) * pos['position_size']
        else:
            pnl = (pos['entry_price'] - exit_price) * pos['position_size']
        
        self.capital += pnl
        
        trade = {
            'entry_idx': pos['entry_idx'],
            'exit_idx': idx,
            'direction': pos['direction'],
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'pnl': pnl,
            'exit_reason': reason,
            'risk': pos['risk_amount'],
            'r_multiple': pnl / pos['risk_amount'] if pos['risk_amount'] > 0 else 0
        }
        self.trades.append(trade)
    
    def get_results(self):
        """Calculate and return performance metrics"""
        if not self.trades:
            return {'error': 'No trades executed'}
        
        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame({'equity': self.equity_curve})
        
        # Basic stats
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] <= 0])
        win_rate = (winning_trades / total_trades) * 100
        
        # P&L stats
        total_pnl = trades_df['pnl'].sum()
        gross_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        gross_loss = trades_df[trades_df['pnl'] < 0]['pnl'].sum()
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
        
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        # R-multiples
        avg_r = trades_df['r_multiple'].mean()
        
        # Drawdown
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
        max_drawdown = equity_df['drawdown'].min() * 100
        
        # Returns
        total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        # Exit reasons
        exit_stats = trades_df['exit_reason'].value_counts().to_dict()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return_pct': total_return,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_r_multiple': avg_r,
            'max_drawdown_pct': max_drawdown,
            'final_capital': self.capital,
            'exit_reasons': exit_stats
        }

# ============== MAIN ==============

def main():
    print("=" * 60)
    print("VWAP + MOMENTUM BACKTESTER")
    print("=" * 60)
    print(f"\nFetching {SYMBOL} data ({LOOKBACK_DAYS} days, {TIMEFRAME} candles)...")
    
    # Fetch data
    try:
        ticker = yf.Ticker(SYMBOL)
        # For 1m data, yfinance limits to 7 days. Use 1h for more history.
        if TIMEFRAME == '1m':
            print("Note: 1m data limited to 7 days by Yahoo Finance. Using 1h instead for longer backtest.")
            df = ticker.history(period="30d", interval="1h")
        else:
            df = ticker.history(period=f"{LOOKBACK_DAYS}d", interval=TIMEFRAME)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
    
    if df.empty:
        print("No data retrieved. Check symbol and try again.")
        return
    
    print(f"Data loaded: {len(df)} candles")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print(f"Starting capital: ${STARTING_CAPITAL:,.2f}")
    
    # Run backtest
    print("\nCalculating indicators and running backtest...")
    backtester = VWAPBacktester(df, STARTING_CAPITAL)
    backtester.calculate_signals()
    backtester.run_backtest()
    
    # Results
    results = backtester.get_results()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if 'error' in results:
        print(f"Error: {results['error']}")
        return
    
    print(f"\n📊 TRADE STATISTICS:")
    print(f"  Total Trades:      {results['total_trades']}")
    print(f"  Winning Trades:    {results['winning_trades']}")
    print(f"  Losing Trades:     {results['losing_trades']}")
    print(f"  Win Rate:          {results['win_rate']:.1f}%")
    
    print(f"\n💰 P&L STATISTICS:")
    print(f"  Total Return:      {results['total_return_pct']:.2f}%")
    print(f"  Total P&L:         ${results['total_pnl']:,.2f}")
    print(f"  Final Capital:     ${results['final_capital']:,.2f}")
    print(f"  Profit Factor:     {results['profit_factor']:.2f}")
    print(f"  Avg Win:           ${results['avg_win']:,.2f}")
    print(f"  Avg Loss:          ${results['avg_loss']:,.2f}")
    print(f"  Expected Value:    ${(results['avg_win'] * results['win_rate']/100 + results['avg_loss'] * (100-results['win_rate'])/100):,.2f}")
    
    print(f"\n📈 RISK METRICS:")
    print(f"  Avg R-Multiple:    {results['avg_r_multiple']:.2f}R")
    print(f"  Max Drawdown:      {results['max_drawdown_pct']:.2f}%")
    
    print(f"\n🚪 EXIT REASONS:")
    for reason, count in results['exit_reasons'].items():
        print(f"  {reason}: {count}")
    
    # Recent trade log
    print(f"\n📝 LAST 5 TRADES:")
    trades_df = pd.DataFrame(backtester.trades)
    if not trades_df.empty:
        for idx in range(max(0, len(trades_df)-5), len(trades_df)):
            t = trades_df.iloc[idx]
            emoji = "✅" if t['pnl'] > 0 else "❌"
            print(f"  {emoji} {t['direction']} | Entry: ${t['entry_price']:.2f} | Exit: ${t['exit_price']:.2f} | P&L: ${t['pnl']:.2f} | {t['exit_reason']}")
    
    print("\n" + "=" * 60)
    print("Backtest Complete")
    print("=" * 60)
    
    # Save results
    trades_df.to_csv('/home/agent/.openclaw/workspace/trading/backtest_trades.csv', index=False)
    print(f"\n✓ Trade history saved to: backtest_trades.csv")

if __name__ == '__main__':
    main()
