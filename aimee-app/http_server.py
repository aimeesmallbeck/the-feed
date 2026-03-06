#!/usr/bin/env python3
"""
HTTP + WebSocket Server for Aimee Life App
Serves static HTML and handles WebSocket connections
"""

import asyncio
import websockets
import aiohttp
from aiohttp import web
import json
import sys
from pathlib import Path
from datetime import datetime
import base64

# Configuration
ELEVENLABS_API_KEY = "sk_5dfb578c2eb044930fef041f356512f918ddd2d9f386d0a9"
ELEVENLABS_VOICE_ID = "XB0fDUnXU5powFXDhCwa"  # Bella voice
HTTP_PORT = 8080
WS_PORT = 8765

# Connected WebSocket clients
ws_clients = {}

async def generate_voice(text):
    """Generate voice using ElevenLabs API"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    audio_data = await resp.read()
                    return base64.b64encode(audio_data).decode('utf-8')
                else:
                    print(f"⚠️ ElevenLabs error: {resp.status}")
                    return None
        except Exception as e:
            print(f"⚠️ ElevenLabs error: {e}")
            return None

def get_local_response(text):
    """Local fallback responses"""
    text_lower = text.lower()
    
    if 'friday' in text_lower or 'tiktok' in text_lower:
        return """Friday's agenda:

**TikTok Launch Day**
1. Subscribe to Midjourney ($10 Basic plan)
2. Generate 5 AI images for Star Wars Disney video
3. Create @doomscrollingedits account
4. Post first video

All the prompts and production details are ready in the workspace."""
    
    elif 'trade' in text_lower or 'gate' in text_lower or 'vwap' in text_lower:
        return """Trading update:

**Paper Trading Results (7 days)**
- Profit: +$6.31 (+0.06%)
- Win Rate: 65%
- Time in Market: 54.5%
- Max Profit: +5.11%
- Max Loss: -1.68%

Ready for live trading once we get your Gate.io API credentials on Monday."""
    
    elif 'income' in text_lower or 'money' in text_lower or 'revenue' in text_lower:
        return """**Future Income Streams**

I've documented 4 options for after TikTok and trading are running:

1. **Print-on-Demand** — Merch via Printful/Etsy
2. **Trade Alerts** — $29-99/month subscription
3. **AI Agency** — White-label content services
4. **Digital Products** — Notion templates, planners

All saved in NICE-TO-HAVE.md for later."""
    
    else:
        return f"I'm here and listening. You said: '{text}'. I'm ready to help with TikTok prep, trading setup, or anything else you need."

def format_response(response):
    """Format response into voice text and HTML"""
    lines = response.strip().split('\n')
    voice_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-') and not line.startswith('*'):
            voice_lines.append(line)
            if len(voice_lines) >= 2:
                break
    
    voice_text = ' '.join(voice_lines) if voice_lines else "Here's what I found."
    
    # Convert markdown to HTML
    html = response.replace('\n\n', '</p><p>').replace('\n', '<br>')
    while '**' in html:
        html = html.replace('**', '<strong>', 1)
        if '**' in html:
            html = html.replace('**', '</strong>', 1)
    
    return voice_text, f'<p>{html}</p>'

async def handle_ws_client(websocket, path):
    """Handle WebSocket client"""
    client_id = id(websocket)
    ws_clients[client_id] = {'websocket': websocket, 'history': []}
    print(f"🟢 WS Client {client_id} connected")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get('type') == 'message':
                await handle_ws_message(client_id, data)
    except websockets.exceptions.ConnectionClosed:
        print(f"🔴 WS Client {client_id} disconnected")
    finally:
        if client_id in ws_clients:
            del ws_clients[client_id]

async def handle_ws_message(client_id, data):
    """Process WebSocket message"""
    client = ws_clients[client_id]
    user_text = data.get('text', '')
    session_id = data.get('session_id', f"session_{client_id}")
    
    print(f"📩 [{session_id}] User: {user_text}")
    client['history'].append({'role': 'user', 'content': user_text})
    
    try:
        # Get response
        response = get_local_response(user_text)
        voice_text, details_html = format_response(response)
        
        # Generate voice
        print(f"🎙️  Generating voice for: {voice_text[:50]}...")
        audio_base64 = await generate_voice(voice_text)
        
        client['history'].append({'role': 'assistant', 'content': response})
        
        # Send response
        msg_data = {
            'type': 'response',
            'voice_text': voice_text,
            'details_html': details_html,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
        if audio_base64:
            msg_data['audio'] = audio_base64
            msg_data['audio_format'] = 'mp3'
        
        await client['websocket'].send(json.dumps(msg_data))
        print(f"📤 [{session_id}] Response sent")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await client['websocket'].send(json.dumps({
            'type': 'error',
            'message': str(e)
        }))

# HTTP Handlers
async def index_handler(request):
    """Serve index.html"""
    html_path = Path(__file__).parent / 'index.html'
    if html_path.exists():
        return web.FileResponse(html_path)
    return web.Response(text="index.html not found", status=404)

async def health_handler(request):
    """Health check"""
    return web.json_response({'status': 'ok', 'timestamp': datetime.now().isoformat()})

async def start_servers():
    """Start both HTTP and WebSocket servers"""
    # HTTP Server
    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/index.html', index_handler)
    app.router.add_get('/health', health_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', HTTP_PORT)
    await site.start()
    
    print(f"🌐 HTTP Server: http://localhost:{HTTP_PORT}")
    print(f"📄 Serving: index.html")
    
    # WebSocket Server
    ws_server = await websockets.serve(handle_ws_client, 'localhost', WS_PORT)
    print(f"📡 WebSocket Server: ws://localhost:{WS_PORT}")
    
    print(f"\n✅ Both servers running!")
    print(f"   HTTP:  http://localhost:{HTTP_PORT}")
    print(f"   WS:    ws://localhost:{WS_PORT}")
    print(f"\nTo expose via Cloudflare:")
    print(f"   cloudflared tunnel --url http://localhost:{HTTP_PORT}")
    
    # Keep running
    await asyncio.Future()

if __name__ == '__main__':
    print("🚀 Starting Aimee HTTP + WebSocket Server...\n")
    asyncio.run(start_servers())
