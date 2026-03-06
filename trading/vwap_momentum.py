#!/usr/bin/env python3
"""
VWAP + Momentum Backtester for Crypto
Strategy: Mean reversion to VWAP with RSI confirmation
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import requests
import json


@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime] = None
    entry_price: float = 0.0
    exit_price: float = 0.0
    direction: str = ""  # 'long' or 'short'
    size: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""
    
    @property
    def is_open(self) -> bool:
        return self.exit_time is None


@dataclass
class BacktestConfig:
    symbol: str = "BTCUSDT"
    timeframe: str = "1m"
    lookback_days: int = 30
    initial_capital: float = 10000.0
    risk_per_trade: float = 0.01  # 1% risk
    vwap_period: int = 20
    rsi_period: int = 14
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    volume_threshold: float = 1.5
    atr_period: int = 14
    atr_multiplier: float = 2.0
    profit_target_r: float = 3.0
    time_stop_minutes: int = 5
    commission_rate: float = 0.0005  # 0.05%


class DataLoader:
    """Fetch historical crypto data from Binance"""
    
    BASE_URL = "https://api.binance.com/api/v3/klines"
    
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d"
    }
    
    def fetch_klines(self, symbol: str, interval: str, limit: int = 1000) -> pd.DataFrame:
        """Fetch kline/candlestick data from Binance"""
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades_count',
                'taker_buy_volume', 'taker_buy_quote_volume', 'ignore'
            ])
            
            # Convert types
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume', 'quote_volume']]
            
            return df
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()
    
    def fetch_backtest_data(self, symbol: str, interval: str, days: int) -> pd.DataFrame:
        """Fetch enough data for backtesting"""
        # Calculate how many candles we need
        candles_per_day = 1440 if interval == "1m" else 288 if interval == "5m" else 96 if interval == "15m" else 24
        total_candles = candles_per_day * days
        
        # Binance limits to 1000 candles per request, so we may need multiple requests
        all_data = []
        remaining = total_candles
        
        while remaining > 0:
            limit = min(1000, remaining)
            df = self.fetch_klines(symbol, interval, limit)
            if df.empty:
                break
            all_data.append(df)
            remaining -= len(df)
            
        if not all_data:
            return pd.DataFrame()
            
        combined = pd.concat(all_data)
        combined = combined[~combined.index.duplicated(keep='first')]
        combined.sort_index(inplace=True)
        
        return combined


class Indicators:
    """Technical indicator calculations"""
    
    @staticmethod
    def vwap(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Volume Weighted Average Price
        VWAP = cumulative(volume * typical_price) / cumulative(volume)
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).rolling(window=period).sum() / df['volume'].rolling(window=period).sum()
        return vwap
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(period).mean()
        return atr
    
    @staticmethod
    def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
        """Simple moving average of volume"""
        return volume.rolling(window=period).mean()


class VWAPMomentumStrategy:
    """
    VWAP + Momentum Strategy
    
    Rules:
    1. Price must be on opposite side of VWAP (downtrend for longs, uptrend for shorts)
    2. RSI confirms oversold/overbought condition
    3. Volume spike confirms interest
    4. Entry on VWAP break with momentum
    5. Stop loss at 2× ATR
    6. Take profit at 3× risk (3R)
    7. Time stop after 5 minutes if no move
    """
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.data: pd.DataFrame = pd.DataFrame()
        self.trades: List[Trade] = []
        self.current_trade: Optional[Trade] = None
        self.equity_curve: List[float] = []
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all indicators to dataframe"""
        df = df.copy()
        
        # VWAP
        df['vwap'] = Indicators.vwap(df, self.config.vwap_period)
        
        # RSI
        df['rsi'] = Indicators.rsi(df['close'], self.config.rsi_period)
        
        # ATR for stop loss
        df['atr'] = Indicators.atr(df, self.config.atr_period)
        
        # Volume moving average
        df['volume_sma'] = Indicators.volume_sma(df['volume'], self.config.vwap_period)
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Price vs VWAP
        df['price_to_vwap'] = df['close'] / df['vwap'] - 1
        
        # RSI momentum (rising/falling)
        df['rsi_slope'] = df['rsi'].diff(3)  # 3-period slope
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        df = self.calculate_indicators(df)
        
        # Long signal conditions
        df['long_setup'] = (
            (df['close'] < df['vwap']) &  # Price below VWAP
            (df['rsi'] < self.config.rsi_oversold) &  # Oversold
            (df['rsi_slope'] > 0) &  # RSI rising
            (df['volume_ratio'] > self.config.volume_threshold)  # Volume spike
        )
        
        df['long_entry'] = (
            df['long_setup'].shift(1) &  # Setup in previous candle
            (df['close'] > df['vwap'])  # Break above VWAP
        )
        
        # Short signal conditions
        df['short_setup'] = (
            (df['close'] > df['vwap']) &  # Price above VWAP
            (df['rsi'] > self.config.rsi_overbought) &  # Overbought
            (df['rsi_slope'] < 0) &  # RSI falling
            (df['volume_ratio'] > self.config.volume_threshold)  # Volume spike
        )
        
        df['short_entry'] = (
            df['short_setup'].shift(1) &  # Setup in previous candle
            (df['close'] < df['vwap'])  # Break below VWAP
        )
        
        return df
    
    def calculate_position_size(self, price: float, stop_price: float, equity: float) -> float:
        """Calculate position size based on risk"""
        risk_amount = equity * self.config.risk_per_trade
        price_distance = abs(price - stop_price)
        
        if price_distance == 0:
            return 0
            
        position_size = risk_amount / price_distance
        return position_size
    
    def run_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        """Run full backtest simulation"""
        self.data = self.generate_signals(data)
        self.trades = []
        self.equity_curve = []
        
        equity = self.config.initial_capital
        current_trade: Optional[Trade] = None
        
        for idx, row in self.data.iterrows():
            self.equity_curve.append(equity)
            
            # Manage open trade
            if current_trade is not None:
                exit_price = None
                exit_reason = None
                
                # Check stop loss
                if current_trade.direction == 'long':
                    if row['low'] <= current_trade.stop_loss:
                        exit_price = current_trade.stop_loss
                        exit_reason = 'stop_loss'
                    elif row['high'] >= current_trade.take_profit:
                        exit_price = current_trade.take_profit
                        exit_reason = 'take_profit'
                else:  # short
                    if row['high'] >= current_trade.stop_loss:
                        exit_price = current_trade.stop_loss
                        exit_reason = 'stop_loss'
                    elif row['low'] <= current_trade.take_profit:
                        exit_price = current_trade.take_profit
                        exit_reason = 'take_profit'
                
                # Check time stop
                time_in_trade = (idx - current_trade.entry_time).total_seconds() / 60
                if exit_price is None and time_in_trade >= self.config.time_stop_minutes:
                    exit_price = row['close']
                    exit_reason = 'time_stop'
                
                # Close trade if exit condition met
                if exit_price is not None:
                    current_trade.exit_time = idx
                    current_trade.exit_price = exit_price
                    
                    # Calculate P&L
                    if current_trade.direction == 'long':
                        pnl = (exit_price - current_trade.entry_price) * current_trade.size
                    else:
                        pnl = (current_trade.entry_price - exit_price) * current_trade.size
                    
                    # Subtract commission (entry + exit)
                    commission = (current_trade.entry_price + exit_price) * current_trade.size * self.config.commission_rate
                    current_trade.pnl = pnl - commission
                    current_trade.pnl_pct = (current_trade.pnl / equity) * 100
                    current_trade.exit_reason = exit_reason
                    
                    equity += current_trade.pnl
                    self.trades.append(current_trade)
                    current_trade = None
            
            # Check for new entry (only if no open trade)
            if current_trade is None:
                if row['long_entry'] and not pd.isna(row['atr']) and row['atr'] > 0:
                    stop_distance = row['atr'] * self.config.atr_multiplier
                    entry_price = row['close']
                    stop_price = entry_price - stop_distance
                    
                    position_size = self.calculate_position_size(entry_price, stop_price, equity)
                    
                    if position_size > 0:
                        current_trade = Trade(
                            entry_time=idx,
                            entry_price=entry_price,
                            direction='long',
                            size=position_size,
                            stop_loss=stop_price,
                            take_profit=entry_price + (stop_distance * self.config.profit_target_r)
                        )
                
                elif row['short_entry'] and not pd.isna(row['atr']) and row['atr'] > 0:
                    stop_distance = row['atr'] * self.config.atr_multiplier
                    entry_price = row['close']
                    stop_price = entry_price + stop_distance
                    
                    position_size = self.calculate_position_size(entry_price, stop_price, equity)
                    
                    if position_size > 0:
                        current_trade = Trade(
                            entry_time=idx,
                            entry_price=entry_price,
                            direction='short',
                            size=position_size,
                            stop_loss=stop_price,
                            take_profit=entry_price - (stop_distance * self.config.profit_target_r)
                        )
        
        # Close any open trade at the end
        if current_trade is not None:
            last_price = self.data.iloc[-1]['close']
            current_trade.exit_time = self.data.index[-1]
            current_trade.exit_price = last_price
            
            if current_trade.direction == 'long':
                pnl = (last_price - current_trade.entry_price) * current_trade.size
            else:
                pnl = (current_trade.entry_price - last_price) * current_trade.size
            
            commission = (current_trade.entry_price + last_price) * current_trade.size * self.config.commission_rate
            current_trade.pnl = pnl - commission
            current_trade.pnl_pct = (current_trade.pnl / equity) * 100
            current_trade.exit_reason = 'end_of_data'
            
            equity += current_trade.pnl
            self.trades.append(current_trade)
        
        self.data['equity'] = self.equity_curve + [equity] * (len(self.data) - len(self.equity_curve))
        
        return self.data
    
    def get_performance_report(self) -> Dict:
        """Generate performance metrics"""
        if not self.trades:
            return {"error": "No trades executed"}
        
        closed_trades = [t for t in self.trades if not t.is_open]
        if not closed_trades:
            return {"error": "No closed trades"}
        
        pnls = [t.pnl for t in closed_trades]
        pnls_pct = [t.pnl_pct for t in closed_trades]
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl <= 0]
        
        final_equity = self.config.initial_capital + sum(pnls)
        total_return = (final_equity / self.config.initial_capital - 1) * 100
        
        # Calculate max drawdown
        equity_curve = [self.config.initial_capital]
        for pnl in pnls:
            equity_curve.append(equity_curve[-1] + pnl)
        
        peak = equity_curve[0]
        max_dd = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        
        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(closed_trades) * 100,
            "total_pnl_usd": sum(pnls),
            "total_return_pct": total_return,
            "avg_trade_pnl": np.mean(pnls),
            "avg_win": np.mean([t.pnl for t in winning_trades]) if winning_trades else 0,
            "avg_loss": np.mean([t.pnl for t in losing_trades]) if losing_trades else 0,
            "profit_factor": abs(sum([t.pnl for t in winning_trades]) / sum([t.pnl for t in losing_trades])) if losing_trades and sum([t.pnl for t in losing_trades]) != 0 else float('inf'),
            "max_drawdown_pct": max_dd * 100,
            "final_equity": final_equity,
            "long_trades": len([t for t in closed_trades if t.direction == 'long']),
            "short_trades": len([t for t in closed_trades if t.direction == 'short']),
            "exit_reasons": {
                "stop_loss": len([t for t in closed_trades if t.exit_reason == 'stop_loss']),
                "take_profit": len([t for t in closed_trades if t.exit_reason == 'take_profit']),
                "time_stop": len([t for t in closed_trades if t.exit_reason == 'time_stop']),
                "end_of_data": len([t for t in closed_trades if t.exit_reason == 'end_of_data'])
            }
        }


def run_backtest_example():
    """Example usage"""
    print("="*60)
    print("VWAP + MOMENTUM BACKTESTER")
    print("="*60)
    
    # Configuration
    config = BacktestConfig(
        symbol="BTCUSDT",
        timeframe="1m",
        lookback_days=7,  # Last 7 days for quick test
        initial_capital=10000,
        risk_per_trade=0.01,
        rsi_oversold=30,
        rsi_overbought=70,
        profit_target_r=3.0,
        time_stop_minutes=5
    )
    
    print(f"\nConfiguration:")
    print(f"  Symbol: {config.symbol}")
    print(f"  Timeframe: {config.timeframe}")
    print(f"  Initial Capital: ${config.initial_capital:,.2f}")
    print(f"  Risk per Trade: {config.risk_per_trade*100}%")
    print(f"  Profit Target: {config.profit_target_r}R")
    
    # Load data
    print(f"\nFetching data from Binance...")
    loader = DataLoader()
    data = loader.fetch_backtest_data(config.symbol, config.timeframe, config.lookback_days)
    
    if data.empty:
        print("Failed to fetch data. Check internet connection.")
        return
    
    print(f"  Loaded {len(data)} candles")
    print(f"  Date range: {data.index[0]} to {data.index[-1]}")
    print(f"  Price range: ${data['low'].min():,.2f} - ${data['high'].max():,.2f}")
    
    # Run backtest
    print(f"\nRunning backtest...")
    strategy = VWAPMomentumStrategy(config)
    results = strategy.run_backtest(data)
    
    # Get performance
    report = strategy.get_performance_report()
    
    if "error" in report:
        print(f"Error: {report['error']}")
        return
    
    # Print results
    print(f"\n{'='*60}")
    print("PERFORMANCE REPORT")
    print("="*60)
    print(f"Total Trades:     {report['total_trades']}")
    print(f"Win Rate:         {report['win_rate']:.1f}%")
    print(f"Profit Factor:    {report['profit_factor']:.2f}")
    print(f"Total Return:     {report['total_return_pct']:+.2f}%")
    print(f"Total P&L:        ${report['total_pnl_usd']:+.2f}")
    print(f"Final Equity:     ${report['final_equity']:,.2f}")
    print(f"Max Drawdown:     {report['max_drawdown_pct']:.2f}%")
    print(f"\nTrade Breakdown:")
    print(f"  Long Trades:    {report['long_trades']}")
    print(f"  Short Trades:   {report['short_trades']}")
    print(f"  Avg Win:        ${report['avg_win']:+.2f}")
    print(f"  Avg Loss:       ${report['avg_loss']:+.2f}")
    print(f"\nExit Reasons:")
    for reason, count in report['exit_reasons'].items():
        print(f"  {reason}: {count}")
    
    # Print recent trades
    print(f"\n{'='*60}")
    print("RECENT TRADES")
    print("="*60)
    for i, trade in enumerate(strategy.trades[-5:]):
        print(f"\nTrade {i+1}: {trade.direction.upper()}")
        print(f"  Entry:  {trade.entry_time} @ ${trade.entry_price:,.2f}")
        print(f"  Exit:   {trade.exit_time} @ ${trade.exit_price:,.2f}")
        print(f"  P&L:    ${trade.pnl:+.2f} ({trade.pnl_pct:+.2f}%)")
        print(f"  Reason: {trade.exit_reason}")
    
    return strategy, report


if __name__ == "__main__":
    run_backtest_example()
