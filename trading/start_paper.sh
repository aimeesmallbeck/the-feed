#!/bin/bash
# Start paper trading with optimized parameters

cd ~/workspace/trading

echo "Starting Binance paper trader with MCMC optimized parameters..."
python3 paper_trade_binance.py > logs/binance_paper_$(date +%Y%m%d).log 2>&1 &
BINANCE_PID=$!
echo $BINANCE_PID > pids/binance_paper.pid
echo "Binance paper trader started (PID: $BINANCE_PID)"

echo "Starting Gate.io paper trader with MCMC optimized parameters..."
python3 paper_trade_gateio.py > logs/gateio_paper_$(date +%Y%m%d).log 2>&1 &
GATEIO_PID=$!
echo $GATEIO_PID > pids/gateio_paper.pid
echo "Gate.io paper trader started (PID: $GATEIO_PID)"

echo ""
echo "Paper trading is now running!"
echo "Check status with: ./status.sh"
echo "View logs: tail -f ~/workspace/trading/logs/*.log"
