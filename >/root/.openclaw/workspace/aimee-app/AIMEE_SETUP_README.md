# 🌀 Aimee Voice Bridge - Setup Guide

## What This Is
Full voice interface with ElevenLabs TTS (text-to-speech) that connects to the real Aimee AI.

## Files
- `aimee_bridge.py` - Main server (HTTP + WebSocket)
- `STARTUP.sh` - Run this to start everything after container restart
- HTML is embedded in the Python file

## How to Start (After Container Restart)

### Step 1: Start the Bridge Server
```bash
cd /root/.openclaw/workspace/aimee-app
./STARTUP.sh
```

### Step 2: Create Cloudflare Tunnels (in separate terminals)

**Terminal 1 - HTTP Page:**
```bash
cloudflared tunnel --url http://localhost:8080
```
Copy the HTTPS URL (e.g., `https://xxxxx.trycloudflare.com`)

**Terminal 2 - WebSocket:**
```bash
cloudflared tunnel --url http://localhost:8766
```
Copy the HTTPS URL and convert to WSS:
- If you get: `https://dramatically-found-projectors-hospital.trycloudflare.com`
- Change to: `wss://dramatically-found-projectors-hospital.trycloudflare.com`

### Step 3: Update the WebSocket URL
Edit `aimee_bridge.py` and update line 18:
```javascript
const WS_URL='wss://YOUR_WEBSOCKET_URL_HERE';
```

### Step 4: Restart the Server
```bash
pkill -f aimee_bridge
./STARTUP.sh
```

### Step 5: Access the App
Open the HTTP tunnel URL in your browser!

## Current Working URLs (Update These!)
- **HTTP Page:** `https://federation-blocks-considers-vegetation.trycloudflare.com` (from last run)
- **WebSocket:** `wss://dramatically-found-projectors-hospital.trycloudflare.com` (from last run)

## Troubleshooting

### Port Already in Use
```bash
fuser -k 8080/tcp
fuser -k 8766/tcp
pkill -f aimee_bridge
```

### Check Server Status
```bash
ps aux | grep aimee_bridge
curl http://localhost:8080/health
```

### View Logs
```bash
tail -f /tmp/bridge.log
```

## Config Info
- **ElevenLabs API Key:** Stored in aimee_bridge.py (Bella voice)
- **OpenClaw Webhook:** Configured at /hooks endpoint
- **Webhook Token:** hook-token-aimee-app-2026-secure

## To Connect Real Aimee AI
The webhook config is in `/root/.openclaw/openclaw.json` but the gateway needs restart to activate it. For now, responses use local intelligence with ElevenLabs voice generation.
