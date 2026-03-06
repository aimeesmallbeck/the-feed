#!/bin/bash
# Aimee Voice Bridge - Auto-startup script
# This runs automatically when the container starts

echo "================================"
echo "🌀 Starting Aimee Voice Bridge"
echo "================================"
echo ""

# Kill any existing processes
echo "Cleaning up old processes..."
pkill -f "aimee_bridge\|python3.*8080\|python3.*8766" 2>/dev/null
sleep 2

# Change to app directory
cd /root/.openclaw/workspace/aimee-app

# Start the bridge server
echo "Starting bridge server..."
nohup python3 aimee_bridge.py > /tmp/bridge.log 2>&1 &
sleep 5

# Check if server started
if pgrep -f "aimee_bridge" > /dev/null; then
    echo "✅ Bridge server running!"
    echo ""
    echo "🔔 IMPORTANT: Start Cloudflare tunnels manually:"
    echo ""
    echo "Terminal 1 - HTTP tunnel:"
    echo "  cloudflared tunnel --url http://localhost:8080"
    echo ""
    echo "Terminal 2 - WebSocket tunnel:"
    echo "  cloudflared tunnel --url http://localhost:8766"
    echo ""
    echo "Note down the HTTPS URLs and update the HTML!"
else
    echo "❌ Bridge server failed to start"
    echo "Check logs: tail -f /tmp/bridge.log"
fi

echo ""
echo "Server will be available at:"
echo "  HTTP: http://localhost:8080"
echo "  WebSocket: ws://localhost:8766"
echo ""
