#!/usr/bin/env python3
"""
Aimee App Bridge - Connects to OpenClaw webhook for real AI responses
"""

import asyncio
import websockets
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
import base64
import os

HTTP_PORT = 8080
WS_PORT = 8766
ELEVENLABS_KEY = 'sk_5dfb578c2eb044930fef041f356512f918ddd2d9f386d0a9'
ELEVENLABS_VOICE = 'XB0fDUnXU5powFXDhCwa'
OPENCLAW_GATEWAY = 'http://localhost:18789'
WEBHOOK_TOKEN = 'hook-token-aimee-app-2026-secure'

HTML_PAGE = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aimee</title>
<style>
body{font-family:sans-serif;background:#1a1a2e;color:#fff;max-width:800px;margin:0 auto;padding:20px}
.header{text-align:center;padding:20px;border-bottom:1px solid rgba(255,255,255,0.1)}
.header h1{font-weight:300;letter-spacing:2px}.header span{color:#00d4ff}
.connected{color:#00ff88}.disconnected{color:#ff4444}
.chat-container{min-height:400px;padding:20px}
.message{margin-bottom:15px;padding:15px;border-radius:10px;background:rgba(0,212,255,0.1);border-left:3px solid #00d4ff}
.input-container{display:flex;gap:10px;padding:20px}
input{flex:1;padding:15px;border-radius:25px;border:none;background:rgba(255,255,255,0.1);color:#fff;font-size:16px}
button{padding:15px 25px;border-radius:25px;border:none;background:#00d4ff;color:#1a1a2e;cursor:pointer;font-size:16px}
.status{text-align:center;padding:10px;color:rgba(255,255,255,0.5);font-size:12px}
</style></head>
<body>
<div class="header"><h1><span>🌀</span> AIMEE</h1><div id="connStatus" class="disconnected">Connecting...</div></div>
<div class="chat-container" id="chat"></div>
<div class="input-container"><input type="text" id="msgInput" placeholder="Type your message..."><button onclick="send()">Send</button></div>
<div class="status" id="status">Waiting for connection</div>
<script>
const WS_URL='wss://fingers-classroom-rating-skin.trycloudflare.com';
let ws,connected=false;
function connect(){
  document.getElementById('status').textContent='Connecting...';
  ws=new WebSocket(WS_URL);
  ws.onopen=()=>{connected=true;document.getElementById('connStatus').textContent='● Connected';document.getElementById('connStatus').className='connected';document.getElementById('status').textContent='Ready';addMsg('Aimee',"Hey Scott! I'm live and connected to the real Aimee AI. Ask me anything!");};
  ws.onmessage=(e)=>{const d=JSON.parse(e.data);if(d.type==='response')addMsg('Aimee',d.voice_text+'<br><br>'+d.details_html,d.audio);};
  ws.onclose=()=>{connected=false;document.getElementById('connStatus').textContent='○ Disconnected';document.getElementById('connStatus').className='disconnected';document.getElementById('status').textContent='Reconnecting...';setTimeout(connect,3000);};
}
function addMsg(who,text,audioBase64){
  const div=document.createElement('div');div.className='message';
  let audioHTML=audioBase64?'<audio controls autoplay style="width:100%;margin-top:10px"><source src="data:audio/mp3;base64,'+audioBase64+'" type="audio/mpeg"></audio>':'';
  div.innerHTML='<strong>'+who+':</strong> '+text+audioHTML;
  document.getElementById('chat').appendChild(div);
  document.getElementById('chat').scrollTop=document.getElementById('chat').scrollHeight;
}
function send(){const text=document.getElementById('msgInput').value.trim();if(!text||!connected)return;addMsg('You',text);ws.send(JSON.stringify({type:'message',text:text}));document.getElementById('msgInput').value='';}
document.getElementById('msgInput').addEventListener('keypress',(e)=>{if(e.key==='Enter')send();});
connect();
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/index.html']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *args): pass

def http_server():
    HTTPServer(('localhost', HTTP_PORT), Handler).serve_forever()

def call_openclaw_webhook(text):
    try:
        print(f'Calling webhook with: {text[:50]}...')
        resp = requests.post(
            f'{OPENCLAW_GATEWAY}/hooks',
            json={'message': text, 'name': 'AimeeApp'},
            headers={'Authorization': f'Bearer {WEBHOOK_TOKEN}', 'Content-Type': 'application/json'},
            timeout=60
        )
        print(f'Webhook response: {resp.status_code}')
        if resp.status_code == 200:
            result = resp.json()
            ai_response = result.get('response') or result.get('text') or result.get('message', 'No response')
            print(f'Got AI response: {ai_response[:100]}...')
            return (ai_response, '<p>Response from Aimee AI</p>')
        else:
            return (f'Error {resp.status_code}', f'<p>{resp.text[:100]}</p>')
    except Exception as e:
        print(f'Webhook error: {e}')
        return (f'Error: {str(e)[:100]}', '<p>Fallback mode</p>')

def generate_voice(text):
    try:
        r = requests.post(
            f'https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}',
            json={'text': text, 'model_id': 'eleven_monolingual_v1', 'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}},
            headers={'Accept': 'audio/mpeg', 'Content-Type': 'application/json', 'xi-api-key': ELEVENLABS_KEY},
            timeout=30
        )
        if r.status_code == 200:
            return base64.b64encode(r.content).decode('utf-8')
    except Exception as e:
        print(f'Voice error: {e}')
    return None

async def ws_handler(websocket):
    print('Client connected')
    try:
        async for msg in websocket:
            data = json.loads(msg)
            if data.get('type') == 'message':
                response_text, details = call_openclaw_webhook(data['text'])
                audio = generate_voice(response_text)
                await websocket.send(json.dumps({'type': 'response', 'voice_text': response_text, 'details_html': details, 'audio': audio}))
                print('Response sent')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        print('Client disconnected')

async def main():
    print('Starting Aimee Bridge...')
    threading.Thread(target=http_server, daemon=True).start()
    print(f'HTTP: http://localhost:{HTTP_PORT}')
    await asyncio.sleep(1)
    async with websockets.serve(ws_handler, 'localhost', WS_PORT):
        print(f'WebSocket: ws://localhost:{WS_PORT}')
        await asyncio.Future()

asyncio.run(main())
