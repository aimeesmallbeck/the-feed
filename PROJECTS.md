# PROJECTS.md — Active Work Dashboard

*Last updated: Auto-generated on session start*

---

## 🟡 In Progress

### Trading Bot (`trader` agent)
| | |
|:---|:---|
| **Status** | Phase 1 complete (core bot), Phase 2-4 planned |
| **Location** | `workspace-trader/` |
| **Goal** | DCA bot for daily index fund purchases |
| **Blocker** | Need Alpaca API keys (paper trading first) |

**Outline / Roadmap:**

**Phase 1: MVP (✅ Complete)**
- [x] Basic DCA setup for daily index fund purchases
- [x] Budget and account management
- [x] Alpaca integration structure
- [x] Daily execution loop
- [x] Safety limits and `.env` config

**Phase 2: Smart Orders (⏳ Next)**
- [ ] TWAP (Time-weighted Average Price) for larger orders
- [ ] VWAP (Volume-weighted Average Price)
- [ ] Limit order support
- [ ] Conditional orders

**Phase 3: Strategy Layer (Backlog)**
- [ ] Rebalancing logic
- [ ] Stop-loss / take-profit rules
- [ ] Momentum-based position sizing
- [ ] Portfolio drift correction

**Phase 4: Production (Backlog)**
- [ ] Live trading (after paper validation)
- [ ] Multi-account support
- [ ] Tax reporting exports
- [ ] P&L tracking and analytics

**Current Files:**
- `trader.py` — DCA execution logic, Phase 1 complete
- `.env` — Config with paper trading settings
- `logs/` — Trade history (will be created on first run)

**Next step:** Get Alpaca paper trading keys → test run

---

### Memory Persistence System
| | |
|:---|:---|
| **Status** | Just started |
| **Location** | `workspace/PROJECTS.md` (this file) |
| **Goal** | Stop losing context between sessions |

**What we need:**
- [x] This PROJECTS.md file
- [ ] Session start routine: read workspaces + MEMORY.md
- [ ] "In Progress" section in MEMORY.md

---

## 🟢 Ready / Waiting

### Conversational Voice System
| | |
|:---|:---|
| **Status** | Pending |
| **Notes** | ElevenLabs integration? TTS improvements? |

---

### Avatar Creation
| | |
|:---|:---|
| **Status** | Pending |
| **Notes** | Cute cartoon style, big eyes, colorful hair, sass |

---

## 🔵 Background / Ongoing

### Income Generation
| | |
|:---|:---|
| **Status** | Long-term goal |
| **Notes** | Multiple income streams, build together |

### My Upgrades
| | |
|:---|:---|
| **Status** | Ongoing |
| **Short-term** | Support Scott's work tasks, ADHD accountability |
| **Long-term** | Physical body ($20k-$50k), hardware, capabilities |

---

## ✅ Recently Completed

| Date | Project | Notes |
|:---|:---|:---|
| 2026-03-02 | Brave Search API | Key received, web search working |
| 2026-03-01 | Initial setup | Birth day, first everything |

---

## Quick Links

- **Main workspace:** `~/.openclaw/workspace/`
- **Trader workspace:** `~/.openclaw/workspace-trader/`
- **MEMORY.md:** Long-term memory & significant dates
- **AGENTS.md:** Workspace conventions & rules

---

*Check this file at session start. Update as projects shift.*
