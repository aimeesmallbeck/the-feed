# API Keys Storage

## Location
`~/.api_keys/alpaca.env`

## Security
- Directory permissions: `700` (owner only)
- File permissions: `600` (owner read/write only)
- **NEVER commit to GitHub** — container-only storage

## Contents
```
ALPACA_API_KEY=PK5UNZ6EON5ERBEKQAPQELZXCI
ALPACA_SECRET_KEY=8ZfhquxKRa4FJqUHYJdbCjpCTpBDgoiQ33dQFiGPk9pY
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

## Usage in Scripts
```python
import os
from pathlib import Path

# Load from secure location
env_path = Path.home() / '.api_keys' / 'alpaca.env'
with open(env_path) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value
```

## Backup
If keys are lost, regenerate from Alpaca dashboard. These are paper trading keys — no real money at risk.
