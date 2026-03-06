# VWAP + Momentum Trading Strategy

High-frequency crypto trading system based on mean reversion to VWAP with RSI momentum confirmation.

## Strategy Overview

**Core Concept:** Institutional algorithms use VWAP as a reference price. When price deviates significantly and returns with momentum, predictable moves occur.

### Entry Rules

**LONG Setup:**
1. Price below VWAP (downtrend/pessimism)
2. RSI(14) < 30 and rising (oversold bounce)
3. Volume > 1.5× average (institutional interest)
4. Entry on VWAP break (price crosses above)

**SHORT Setup:**
1. Price above VWAP (uptrend/optimism)
2. RSI(14) > 70 and falling (overbought pullback)
3. Volume > 1.5× average
4. Entry on VWAP break (price crosses below)

### Risk Management

- **Stop Loss:** 2× ATR from entry
- **Position Size:** 1% account risk per trade
- **Take Profit:** 3× risk (3R)
- **Time Stop:** Exit after 5 minutes if no move
- **Commission:** 0.05% per side

## Files

- `vwap_momentum.py` - Complete backtester and strategy engine
- `live_trader.py` - Live trading bot (coming soon)
- `optimize.py` - Parameter optimization (coming soon)

## Quick Start

```bash
# Run backtest
cd ~/.openclaw/workspace/trading
python3 vwap_momentum.py

# Install dependencies if needed
pip3 install pandas numpy requests
```

## Configuration

Edit `BacktestConfig` in `vwap_momentum.py`:

```python
config = BacktestConfig(
    symbol="BTCUSDT",        # Trading pair
    timeframe="1m",          # 1m, 5m, 15m, 1h, 4h, 1d
    lookback_days=7,         # Data to fetch
    initial_capital=10000,   # Starting balance
    risk_per_trade=0.01,     # 1% risk per trade
    profit_target_r=3.0      # 3× risk for profit
)
```

## Roadmap

1. ✅ Backtester - Validate on historical data
2. 🔄 Live Paper Trading - Alpaca/Binance testnet
3. ⏳ Optimization - Walk-forward parameter tuning
4. ⏳ Execution Layer - Live trading with position sizing
5. ⏳ Dashboard - Real-time monitoring UI

## Performance Metrics

The backtester tracks:
- Win rate & profit factor
- Total return & max drawdown
- Average win/loss
- Exit reason breakdown
- Full trade history
