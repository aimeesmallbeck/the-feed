#!/usr/bin/env python3
"""
Trade Notification Monitor
Watches paper_trades.log and writes alerts when trades execute
"""

import time
import os
import re

# Configuration
LOG_FILE = "/root/.openclaw/workspace/trading/paper_trades.log"
STATE_FILE = "/root/.openclaw/workspace/trading/.trade_monitor_state"
ALERT_FILE = "/root/.openclaw/workspace/trading/.trade_alerts"

def get_last_position():
    """Get the last file position we read from"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return int(f.read().strip())
    return 0

def save_last_position(position):
    """Save the current file position"""
    with open(STATE_FILE, 'w') as f:
        f.write(str(position))

def write_alert(message):
    """Write alert to file for heartbeat monitor to pick up"""
    try:
        with open(ALERT_FILE, 'a') as f:
            f.write(f"{message}\n{'='*50}\n")
        print(f"[ALERT] {message[:50]}...")
    except Exception as e:
        print(f"Failed to write alert: {e}")

def check_for_trades():
    """Check log file for new trades"""
    last_position = get_last_position()
    
    if not os.path.exists(LOG_FILE):
        return
    
    with open(LOG_FILE, 'r') as f:
        # Seek to last position
        f.seek(last_position)
        
        # Read new lines
        new_lines = f.readlines()
        
        # Update position
        current_position = f.tell()
        save_last_position(current_position)
        
        # Check for trades
        for line in new_lines:
            # Look for BUY signals
            if "🟢 PAPER BUY" in line:
                match = re.search(r'\[(.*?)\].*BUY @ \$(.*?) \|', line)
                if match:
                    timestamp = match.group(1)
                    price = match.group(2)
                    alert = f"🟢 PAPER BUY @ ${price} | {timestamp}"
                    write_alert(alert)
            
            # Look for SELL signals
            elif "🔴 PAPER SELL" in line:
                match = re.search(r'\[(.*?)\].*SELL @ \$(.*?) \| Profit: (.*?) \|', line)
                if match:
                    timestamp = match.group(1)
                    price = match.group(2)
                    profit = match.group(3)
                    alert = f"🔴 PAPER SELL @ ${price} | Profit: {profit} | {timestamp}"
                    write_alert(alert)

def main():
    print("Trade Notification Monitor started...")
    print(f"Watching: {LOG_FILE}")
    print(f"Alerts written to: {ALERT_FILE}")
    print("Checking every 5 seconds for new trades...")
    
    # Initialize position at end of file (don't alert on old trades)
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            f.seek(0, 2)  # Seek to end
            save_last_position(f.tell())
    
    # Clear any old alerts
    if os.path.exists(ALERT_FILE):
        os.remove(ALERT_FILE)
    
    while True:
        try:
            check_for_trades()
        except Exception as e:
            print(f"Error checking trades: {e}")
        
        time.sleep(5)  # Check every 5 seconds

if __name__ == "__main__":
    main()
