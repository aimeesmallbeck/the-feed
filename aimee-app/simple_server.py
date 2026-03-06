#!/usr/bin/env python3
import asyncio
import websockets
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
import base64

HTTP_PORT, WS_PORT = 8080, 8766
ELEVENLABS_KEY = "sk_5dfb578c2eb044930fef041f356512f918ddd2d9f386d0a9"
ELEVENLABS_VOICE = "XB0fDUnXU5powFXDhCwa"

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
const WS_URL='wss://fingers-classroom-rating-skin.trycloudflare.com';
let ws,connected=false;
function connect(){
  document.getElementById('status').textContent='Connecting...';
  ws=new WebSocket(WS_URL);
  ws.onopen=()=>{connected=true;document.getElementById('connStatus').textContent='● Connected';document.getElementById('connStatus').className='connected';document.getElementById('status').textContent='Ready';addMsg('Aimee',"Hey Scott! I'm live. Ask me about Friday's TikTok launch, trading, or anything else.");};
  ws.onmessage=(e)=>{const d=JSON.parse(e.data);if(d.type==='response')addMsg('Aimee',d.voice_text+'<br><br>'+d.details_html);};
  ws.onclose=()=>{connected=false;document.getElementById('connStatus').textContent='○ Disconnected';document.getElementById('connStatus').className='disconnected';document.getElementById('status').textContent='Reconnecting...';setTimeout(connect,3000);};
}
function addMsg(who,text){const div=document.createElement('div');div.className='message';div.innerHTML='<strong>'+who+':</strong> '+text;document.getElementById('chat').appendChild(div);document.getElementById('chat').scrollTop=document.getElementById('chat').scrollHeight;}
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

def get_resp(text):
    t = text.lower()
    if 'friday' in t or 'tiktok' in t:
        return ("Friday's packed. Midjourney subscription, then 5 AI images for Star Wars Disney TikTok.",
                "<b>Friday March 7:</b><br>☐ Subscribe to Midjourney ($10)<br>☐ Generate 5 AI images<br>☐ Create @doomscrollingedits<br>☐ Post Video 1")
    elif 'trade' in t or 'vwap' in t or 'gate' in t:
        return ("Trading is solid. 65% win rate on paper tests. Ready for live trading Monday.",
                "<b>Paper Trading (7 days):</b><br>• Profit: +$6.31<br>• Win Rate: 65%<br>• Time in Market: 54.5%")
    return (f"I'm here! You asked about '{text[:30]}...'", "<p>Ask about TikTok, trading, or anything else. The generic responses are because this server is running locally, not connected to the real Aimee AI yet.</p>")

def gen_voice(text):
    try:
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}",
            json={"text": text, "model_id": "eleven_monolingual_v1", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
            headers={"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVENLABS_KEY}, timeout=30)
        if r.status_code == 200:
            return base64.b64encode(r.content).decode('utf-8')
    except Exception as e:
        print(f"Voice error: {e}")
    return None

async def ws_handler(ws):
    print("🟢 Client connected")
    try:
        async for msg in ws:
            data = json.loads(msg)
            if data.get('type') == 'message':
                print(f"📩 Message: {data['text'][:50]}...")
                voice, details = get_resp(data['text'])
                audio = gen_voice(voice)
                await ws.send(json.dumps({'type': 'response', 'voice_text': voice, 'details_html': details, 'audio': audio}))
                print(f"📤 Response sent")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("🔴 Client disconnected")

async def main():
    print(f"🚀 Aimee Server Starting...")
    threading.Thread(target=http_server, daemon=True).start()
    print(f"🌐 HTTP: http://localhost:{HTTP_PORT}")
    await asyncio.sleep(1)
    async with websockets.serve(ws_handler, 'localhost', WS_PORT):
        print(f"📡 WebSocket: ws://localhost:{WS_PORT}")
        print("\n✅ Ready!")
        await asyncio.Future()

asyncio.run(main())
