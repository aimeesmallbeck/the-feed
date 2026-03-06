# Aimee App Server

Bridge between web frontend and OpenClaw AI.

## Architecture

```
Browser (Voice/Text) ←→ WebSocket Server ←→ OpenClaw Gateway ←→ Kimi K2.5
                              ↓
                    ElevenLabs TTS (voice response)
```

## Setup

```bash
cd /root/.openclaw/workspace/aimee-app
python3 -m pip install websockets aiohttp --break-system-packages
```

## Run

```bash
python3 server.py
```

Server starts on ws://localhost:8765

## API

### WebSocket Connection
Connect to `ws://localhost:8765`

### Message Format (Client → Server)
```json
{
  "type": "message",
  "text": "What's on for Friday?",
  "session_id": "unique-session-id"
}
```

### Response Format (Server → Client)
```json
{
  "type": "response",
  "voice_text": "Friday's packed...",
  "details_html": "<h3>Friday...</h3>...",
  "session_id": "unique-session-id"
}
```
