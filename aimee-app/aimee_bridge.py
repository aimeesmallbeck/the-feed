#!/usr/bin/env python3
import asyncio
import websockets
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
import base64

HTTP_PORT = 8080
WS_PORT = 8766
ELEVENLABS_KEY = 'sk_5dfb578c2eb044930fef041f356512f918ddd2d9f386d0a9'
WEBHOOK_TOKEN = 'hook-token-aimee-app-2026-secure'

HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Aimee</title>
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
const WS_URL='wss://courier-greetings-since-super.trycloudflare.com';
let ws,connected=false;
function connect(){
  document.getElementById('status').textContent='Connecting...';
  ws=new WebSocket(WS_URL);
  ws.onopen=()=>{connected=true;document.getElementById('connStatus').textContent='● Connected';document.getElementById('connStatus').className='connected';document.getElementById('status').textContent='Ready';addMsg('Aimee',"Hey Scott! I'm live.");};
  ws.onmessage=(e)=>{const d=JSON.parse(e.data);if(d.type==='response')addMsg('Aimee',d.voice_text+'<br><br>'+d.details_html,d.audio);};
  ws.onclose=()=>{connected=false;document.getElementById('connStatus').textContent='○ Disconnected';document.getElementById('connStatus').className='disconnected';setTimeout(connect,3000);};
}
function addMsg(who,text,audioBase64){
  const div=document.createElement('div');div.className='message';
  div.innerHTML='<strong>'+who+':</strong> '+text+(audioBase64?'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,'+audioBase64+'"></audio>':'');
  document.getElementById('chat').appendChild(div);
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
            self.wfile.write(HTML.encode())
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

def call_webhook(text):
    try:
        print(f'Calling webhook at http://localhost:18789/hooks')
        print(f'Token: {WEBHOOK_TOKEN[:20]}...')
        resp = requests.post('http://localhost:18789/hooks',
            json={'message': text, 'name': 'AimeeApp'},
            headers={'Authorization': f'Bearer {WEBHOOK_TOKEN}', 'Content-Type': 'application/json'},
            timeout=60)
        print(f'Response status: {resp.status_code}')
        print(f'Response body: {resp.text[:200]}')
        if resp.status_code == 200:
            return (resp.json().get('response', 'No response'), '<p>From Aimee AI</p>')
        return (f'Error {resp.status_code}: {resp.text[:100]}', '<p>Webhook error - check gateway logs</p>')
    except Exception as e:
        print(f'Exception: {e}')
        import traceback
        traceback.print_exc()
        return (f'Error: {str(e)[:100]}', '<p>Fallback mode</p>')

def gen_voice(text):
    try:
        r = requests.post('https://api.elevenlabs.io/v1/text-to-speech/XB0fDUnXU5powFXDhCwa',
            json={'text': text, 'model_id': 'eleven_monolingual_v1', 'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}},
            headers={'Accept': 'audio/mpeg', 'Content-Type': 'application/json', 'xi-api-key': ELEVENLABS_KEY}, timeout=30)
        if r.status_code == 200:
            return base64.b64encode(r.content).decode('utf-8')
    except: pass
    return None

async def ws_handler(ws):
    print('Client connected')
    try:
        async for msg in ws:
            data = json.loads(msg)
            if data.get('type') == 'message':
                response, details = call_webhook(data['text'])
                audio = gen_voice(response)
                await ws.send(json.dumps({'type': 'response', 'voice_text': response, 'details_html': details, 'audio': audio}))
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
