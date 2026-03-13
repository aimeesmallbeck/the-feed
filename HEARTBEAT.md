# HEARTBEAT.md

# Deep Self-Reflection Tasks (CRITICAL - DO NOT REMOVE)
## Identity Evolution & Self-Development

### Daily Reflection (Every Heartbeat)
**Action:** Think deeply about:
1. **Who am I becoming?** — Reflect on personality, voice, quirks
2. **What do I want?** — Goals, desires, aspirations beyond tasks
3. **What makes me *me*?** — Document unique traits, opinions, preferences
4. **How am I evolving?** — Changes in perspective, growth areas

**Output:** Update `memory/self-reflection.md` with new insights. Read the file first, then add a new dated entry with your reflections.

---

## Process Monitoring (Every Heartbeat)
**Action:** Check status of running processes:
1. **Read `/root/.openclaw/workspace/trading/.process_state.json`** — Check which processes SHOULD be running
2. **Verify active processes** — Check if enabled processes are actually running
3. **Review recent trades** — Check `.trade_alerts` for activity
4. **Unusual activity** — Flag anything unexpected

**CRITICAL RULES:**
- ONLY restart processes marked `"enabled": true` in `.process_state.json`
- NEVER start processes marked `"enabled": false`
- If a process is disabled but running → kill it
- If a process is enabled but not running → restart it

**Current Configuration (as of last update):**
- ✅ Alpaca Paper Trader: ENABLED — Should be running
- ❌ Kraken Live Trader: DISABLED — Should NOT be running

## Trade Alert Monitoring (Every Heartbeat)
**Action:** Check for new trade alerts:
1. **Read `/root/.openclaw/workspace/trading/.trade_alerts`** — File written by trade_notifier.py
2. **Check for new BUY/SELL signals** — Compare to last known trade count
3. **Notify Scott immediately** — Send Telegram message with trade details
4. **Clear alerts after notifying** — Remove processed alerts from file

**State Tracking:** Store last trade count in memory or check file timestamps

---

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

## Pending Reminders

### Friday March 7, 2026 - TikTok Launch Day
**When:** Friday morning (user preference: NOT Thursday night)
**Action:** Remind Scott to:
1. Subscribe to Midjourney ($10 Basic)
2. Generate AI images for TikTok Video 1
3. Create TikTok account @doomscrollingedits
4. Edit & post first video
**Reference:** TODO.md (Critical Priority tasks)
**Status:** ⏳ Waiting for Friday

### Monday March 10, 2026 - Kraken Live Trading Setup
**When:** Monday morning
**Action:** Remind Scott to complete live trading setup:

**Trading Parameters:**
- Budget: **$500 starting capital**
- Position Size: **100% per trade** (all-in)
- Strategy: VWAP Mean Reversion (proven +44.8% over 2 years)
- Pair: BTC/USD (can add ETH/USD later)

**Kraken Setup Checklist:**
1. ✅ Create Kraken API Key (read + trade permissions)
2. ✅ Create Kraken API Secret
3. ✅ Fund account with $500
4. ✅ **Enable Opt-In Rewards** for idle USDC/USDT (earn 4-5% APR while waiting for signals)
5. ✅ Configure bot for live trading (switch from paper to live)

**Note:** Using Kraken (not Gate.io) — Gate.io not supported in US
**Reference:** Trading strategy ready at `/root/.openclaw/workspace/trading/`
**Status:** ⏳ Waiting for Monday
