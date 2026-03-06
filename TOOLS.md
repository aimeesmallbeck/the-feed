# TOOLS.md

## Telegram Setup

**Bot Token:** `8408186208:AAEF13uGjhHjIEMnyO4ogLqnUb1ZrT_Q3jw`
**Backup:** Stored in `.env` file in workspace

### Restore Telegram (if it breaks again)
```bash
openclaw channels add --channel telegram --token "8408186208:AAEF13uGjhHjIEMnyO4ogLqnUb1ZrT_Q3jw"
openclaw doctor --fix
```

### First-time pairing (new device)
If you see "access not configured" with a pairing code, approve it:
```bash
openclaw pairing approve telegram <PAIRING_CODE>
```

**Your approved Telegram user ID:** `7660866897`

### Check status
```bash
openclaw channels list
openclaw channels status
```

---

*Last verified working: 2026-03-04*
