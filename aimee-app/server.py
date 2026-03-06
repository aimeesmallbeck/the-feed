#!/usr/bin/env python3
"""
Aimee Voice App Server
WebSocket bridge between frontend and OpenClaw AI via API
"""

import asyncio
import websockets
import aiohttp
import json
import sys
from pathlib import Path
from datetime import datetime

# Configuration
OPENCLAW_GATEWAY_URL = "http://localhost:18789"  # Default OpenClaw gateway port
AGENT_NAME = "main"  # Use the main agent session
ELEVENLABS_API_KEY = "sk_5dfb578c2eb044930fef041f356512f918ddd2d9f386d0a9"
ELEVENLABS_VOICE_ID = "XB0fDUnXU5powFXDhCwa"  # Bella voice

# Connected clients
clients = {}

async def handle_client(websocket, path):
    """Handle WebSocket client connection"""
    client_id = id(websocket)
    clients[client_id] = {
        'websocket': websocket,
        'session_id': None,
        'history': []
    }
    
    print(f"🟢 Client {client_id} connected")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            
            if data.get('type') == 'message':
                await handle_message(client_id, data)
                
    except websockets.exceptions.ConnectionClosed:
        print(f"🔴 Client {client_id} disconnected")
    finally:
        if client_id in clients:
            del clients[client_id]

async def handle_message(client_id, data):
    """Process user message and get AI response via API"""
    client = clients[client_id]
    user_text = data.get('text', '')
    session_id = data.get('session_id', f"session_{client_id}")
    
    print(f"📩 [{session_id}] User: {user_text}")
    
    # Add to history
    client['history'].append({'role': 'user', 'content': user_text})
    
    try:
        # Get AI response via API bridge
        response = await get_ai_response_api(user_text, client['history'])
        
        # Format for voice + details
        voice_text, details_html = format_response(response)
        
        # Generate voice using ElevenLabs
        print(f"🎙️  Generating voice for: {voice_text[:50]}...")
        audio_base64 = await generate_voice(voice_text)
        
        # Add to history
        client['history'].append({'role': 'assistant', 'content': response})
        
        # Send to client
        message_data = {
            'type': 'response',
            'voice_text': voice_text,
            'details_html': details_html,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Include audio if generation succeeded
        if audio_base64:
            message_data['audio'] = audio_base64
            message_data['audio_format'] = 'mp3'
        
        await client['websocket'].send(json.dumps(message_data))
        
        print(f"📤 [{session_id}] Response sent")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Fallback to local response if API fails
        response = get_local_response(user_text)
        voice_text, details_html = format_response(response)
        await client['websocket'].send(json.dumps({
            'type': 'response',
            'voice_text': voice_text,
            'details_html': details_html,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'note': '(API unavailable - using local response)'
        }))

async def get_ai_response_api(text, history):
    """Get response from OpenClaw gateway via HTTP API"""
    # NOTE: This is a placeholder for the actual OpenClaw API endpoint
    # The real implementation would depend on OpenClaw's exposed API
    
    async with aiohttp.ClientSession() as session:
        try:
            # Try to send to OpenClaw gateway
            payload = {
                'message': text,
                'agent': AGENT_NAME,
                'history': history[-10:]  # Last 10 messages for context
            }
            
            async with session.post(
                f"{OPENCLAW_GATEWAY_URL}/api/v1/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get('response', 'No response from AI')
                else:
                    raise Exception(f"API returned {resp.status}")
                    
        except aiohttp.ClientConnectorError:
            print("⚠️  OpenClaw gateway not reachable, using local fallback")
            return get_local_response(text)
        except Exception as e:
            print(f"⚠️  API error: {e}, using local fallback")
            return get_local_response(text)

def get_local_response(text):
    """Local fallback responses when API is unavailable"""
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
    """Format AI response into voice text and HTML details"""
    lines = response.strip().split('\n')
    
    # First line or two becomes voice text
    voice_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-') and not line.startswith('*'):
            voice_lines.append(line)
            if len(voice_lines) >= 2:
                break
    
    voice_text = ' '.join(voice_lines) if voice_lines else "Here's what I found."
    
    # Convert markdown to HTML for details
    html = markdown_to_html(response)
    
    return voice_text, html

def markdown_to_html(text):
    """Simple markdown to HTML converter"""
    html = text
    
    # Headers
    while '**' in html:
        html = html.replace('**', '<strong>', 1)
        if '**' in html:
            html = html.replace('**', '</strong>', 1)
    
    # Convert lists
    lines = html.split('\n')
    result = []
    in_list = False
    
    for line in lines:
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                result.append('<ul style="margin-left: 20px; margin-top: 10px;">')
                in_list = True
            item = line.strip()[2:]
            result.append(f'<li>{item}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            if line.strip():
                result.append(f'<p>{line}</p>')
    
    if in_list:
        result.append('</ul>')
    
    return '\n'.join(result)

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
                    # Convert to base64 for sending over WebSocket
                    import base64
                    return base64.b64encode(audio_data).decode('utf-8')
                else:
                    print(f"⚠️ ElevenLabs error: {resp.status}")
                    return None
        except Exception as e:
            print(f"⚠️ ElevenLabs error: {e}")
            return None

async def main():
    """Start WebSocket server"""
    print("🚀 Aimee Voice Server starting...")
    print(f"📡 WebSocket: ws://localhost:8765")
    print(f"🔗 OpenClaw Gateway: {OPENCLAW_GATEWAY_URL}")
    print("\n⚠️  Note: API bridge configured. Will try OpenClaw gateway, fallback to local responses if unavailable.")
    
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
