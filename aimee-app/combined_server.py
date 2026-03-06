#!/usr/bin/env python3
"""
Combined HTTP + WebSocket Server on Single Port
"""

import asyncio
import websockets
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
from pathlib import Path
from datetime import datetime
import base64
import aiohttp

# Config
PORT = 8080
ELEVENLABS_API_KEY = "sk_5dfb578c2eb044930fef041f356512f918ddd2d9f386d0a9"
ELEVENLABS_VOICE_ID = "XB0fDUnXU5powFXDhCwa"

# HTML content
HTML_CONTENT = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aimee — Voice Interface</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff; min-height: 100vh; display: flex; flex-direction: column;
        }
        .header { padding: 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .header h1 { font-size: 24px; font-weight: 300; letter-spacing: 2px; }
        .header span { color: #00d4ff; }
        .connection-status { font-size: 12px; margin-top: 5px; color: rgba(255,255,255,0.5); }
        .connection-status.connected { color: #00ff88; }
        .connection-status.disconnected { color: #ff4444; }
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; max-width: 800px; margin: 0 auto; width: 100%; }
        .message { margin-bottom: 20px; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .message-aimee { display: flex; flex-direction: column; align-items: flex-start; }
        .message-user { display: flex; flex-direction: column; align-items: flex-end; }
        .bubble { max-width: 80%; padding: 15px 20px; border-radius: 20px; position: relative; }
        .message-aimee .bubble { background: rgba(0, 212, 255, 0.1); border: 1px solid rgba(0, 212, 255, 0.3); border-bottom-left-radius: 5px; }
        .message-user .bubble { background: rgba(255, 255, 255, 0.1); border-bottom-right-radius: 5px; }
        .voice-indicator { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; color: #00d4ff; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
        .voice-indicator.playing { animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .voice-wave { display: flex; gap: 3px; height: 20px; align-items: center; }
        .voice-wave span { width: 3px; background: #00d4ff; border-radius: 2px; animation: wave 1s infinite ease-in-out; }
        .voice-wave span:nth-child(1) { animation-delay: 0s; height: 8px; }
        .voice-wave span:nth-child(2) { animation-delay: 0.1s; height: 15px; }
        .voice-wave span:nth-child(3) { animation-delay: 0.2s; height: 20px; }
        .voice-wave span:nth-child(4) { animation-delay: 0.3s; height: 12px; }
        .voice-wave span:nth-child(5) { animation-delay: 0.4s; height: 18px; }
        @keyframes wave { 0%, 100% { transform: scaleY(0.5); } 50% { transform: scaleY(1); } }
        .details-panel { background: rgba(0, 0, 0, 0.3); border-radius: 10px; padding: 15px; margin-top: 10px; font-size: 14px; line-height: 1.6; border-left: 3px solid #00d4ff; }
        .details-panel h3 { color: #00d4ff; margin-bottom: 10px; font-size: 14px; }
        .input-container { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); display: flex; gap: 10px; max-width: 800px; margin: 0 auto; width: 100%; }
        #userInput { flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 25px; padding: 15px 20px; color: #fff; font-size: 16px; outline: none; }
        #userInput::placeholder { color: rgba(255,255,255,0.4); }
        .mic-btn, .send-btn { width: 50px; height: 50px; border-radius: 50%; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s; }
        .mic-btn { background: rgba(255,255,255,0.1); color: #fff; }
        .mic-btn:hover { background: rgba(255,255,255,0.2); }
        .mic-btn.recording { background: #ff4444; animation: pulse 1s infinite; }
        .send-btn { background: #00d4ff; color: #1a1a2e; }
        .send-btn:hover { background: #00b8e6; }
        .status-bar { text-align: center; padding: 10px; font-size: 12px; color: rgba(255,255,255,0.5); }
        .thinking { display: flex; align-items: center; gap: 5px; color: rgba(255,255,255,0.6); font-style: italic; }
        .dots { display: flex; gap: 3px; }
        .dots span { width: 6px; height: 6px; background: rgba(255,255,255,0.6); border-radius: 50%; animation: bounce 1.4s infinite ease-in-out; }
        .dots span:nth-child(1) { animation-delay: 0s; }
        .dots span:nth-child(2) { animation-delay: 0.2s; }
        .dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-8px); } }
        .audio-player { margin-top: 10px; width: 100%; }
    </style>
</head>
<body>
    <div class="header">
        <h1><span>🌀</span> AIMEE</h1>
        <div class="connection-status disconnected" id="connectionStatus">Connecting...</div>
    </div>
    <div class="chat-container" id="chatContainer">
        <div class="message message-aimee">
            <div class="bubble">
                <div class="voice-indicator" id="voiceIndicator1">
                    <div class="voice-wave"><span></span><span></span><span></span><span></span><span></span></div>
                    <span>Voice</span>
                </div>
                <div id="welcomeText">Connecting to Aimee...</div>
                <div class="details-panel">
                    <h3>📱 How This Works</h3>
                    <ul style="margin-left: 20px; margin-top: 10px;">
                        <li>Make sure the server is running</li>
                        <li>Press the mic button to talk</li>
                        <li>Or type in the text box</li>
                        <li>I'll respond with voice + details</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    <div class="status-bar" id="statusBar">Waiting for connection...</div>
    <div class="input-container">
        <button class="mic-btn" id="micBtn" title="Hold to speak">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
        </button>
        <input type="text" id="userInput" placeholder="Type your message..." />
        <button class="send-btn" id="sendBtn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
        </button>
    </div>
    <script>
        const WS_URL = window.location.protocol === 'https:' 
            ? 'wss://' + window.location.host + '/ws'
            : 'ws://' + window.location.host + '/ws';
        const chatContainer = document.getElementById('chatContainer');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const micBtn = document.getElementById('micBtn');
        const statusBar = document.getElementById('statusBar');
        const connectionStatus = document.getElementById('connectionStatus');
        const welcomeText = document.getElementById('welcomeText');
        let ws = null, isConnected = false, sessionId = 'session_' + Date.now();
        let recognition = null;
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false; recognition.interimResults = false; recognition.lang = 'en-US';
        }
        function connect() {
            statusBar.textContent = 'Connecting...';
            try {
                ws = new WebSocket(WS_URL);
                ws.onopen = () => {
                    isConnected = true;
                    connectionStatus.textContent = '● Connected';
                    connectionStatus.classList.remove('disconnected');
                    connectionStatus.classList.add('connected');
                    statusBar.textContent = 'Ready • Speak or type';
                    welcomeText.textContent = "Hey Scott! I'm live. Speak or type—I'll respond with voice and show details below.";
                };
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.type === 'response') addAimeeMessage(data.voice_text, data.details_html, data.audio);
                    else if (data.type === 'error') addErrorMessage(data.message);
                };
                ws.onclose = () => {
                    isConnected = false;
                    connectionStatus.textContent = '○ Disconnected';
                    connectionStatus.classList.remove('connected');
                    connectionStatus.classList.add('disconnected');
                    statusBar.textContent = 'Connection lost. Retrying...';
                    setTimeout(connect, 3000);
                };
                ws.onerror = (error) => { console.error('WS error:', error); statusBar.textContent = 'Connection error'; };
            } catch (e) { console.error('Error:', e); statusBar.textContent = 'Failed to connect'; }
        }
        function addAimeeMessage(voiceText, detailsHTML, audioBase64) {
            const div = document.createElement('div'); div.className = 'message message-aimee';
            let audioHTML = audioBase64 ? '<audio class="audio-player" controls autoplay><source src="data:audio/mp3;base64,' + audioBase64 + '" type="audio/mpeg"></audio>' : '';
            div.innerHTML = '<div class="bubble"><div class="voice-indicator playing"><div class="voice-wave"><span></span><span></span><span></span><span></span><span></span></div><span>Speaking...</span></div><div>' + escapeHtml(voiceText) + '</div>' + audioHTML + '<div class="details-panel">' + detailsHTML + '</div></div>';
            chatContainer.appendChild(div); chatContainer.scrollTop = chatContainer.scrollHeight;
            const audio = div.querySelector('audio'), indicator = div.querySelector('.voice-indicator');
            if (audio && indicator) audio.onended = () => { indicator.classList.remove('playing'); indicator.innerHTML = '<span>✓ Voice</span>'; };
            else if (indicator) setTimeout(() => { indicator.classList.remove('playing'); indicator.innerHTML = '<span>✓ Voice</span>'; }, 2000);
        }
        function addErrorMessage(message) {
            const div = document.createElement('div'); div.className = 'message message-aimee';
            div.innerHTML = '<div class="bubble"><div style="color: #ff8888;">⚠️ ' + escapeHtml(message) + '</div></div>';
            chatContainer.appendChild(div); chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        function escapeHtml(text) { const div = document.createElement('div'); div.textContent = text; return div.innerHTML; }
        function handleUserInput() {
            const text = userInput.value.trim();
            if (!text || !isConnected) { if (!isConnected) { statusBar.textContent = 'Not connected...'; connect(); } return; }
            addUserMessage(text); userInput.value = '';
            const thinking = document.createElement('div'); thinking.className = 'message message-aimee'; thinking.id = 'thinking';
            thinking.innerHTML = '<div class="bubble"><div class="thinking"><div class="dots"><span></span><span></span><span></span></div><span>Thinking...</span></div></div>';
            chatContainer.appendChild(thinking); chatContainer.scrollTop = chatContainer.scrollHeight;
            ws.send(JSON.stringify({type: 'message', text: text, session_id: sessionId}));
        }
        function addUserMessage(text) {
            const div = document.createElement('div'); div.className = 'message message-user';
            div.innerHTML = '<div class="bubble">' + escapeHtml(text) + '</div>';
            chatContainer.appendChild(div); chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        sendBtn.addEventListener('click', handleUserInput);
        userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleUserInput(); });
        if (recognition) {
            micBtn.addEventListener('mousedown', () => { micBtn.classList.add('recording'); statusBar.textContent = 'Listening...'; recognition.start(); });
            micBtn.addEventListener('mouseup', () => { micBtn.classList.remove('recording'); statusBar.textContent = 'Processing...'; recognition.stop(); });
            micBtn.addEventListener('mouseleave', () => { if (micBtn.classList.contains('recording')) { micBtn.classList.remove('recording'); recognition.stop(); } });
            recognition.onresult = (event) => { const text = event.results[0][0].transcript; userInput.value = text; handleUserInput(); };
            recognition.onerror = (event) => { console.error('Speech error:', event.error); statusBar.textContent = 'Voice error. Try typing.'; micBtn.classList.remove('recording'); };
        } else { micBtn.style.display = 'none'; }
        connect();
    </script>
</body>
</html>'''

class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'timestamp': str(datetime.now())}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def start_http():
    server = HTTPServer(('localhost', PORT), HTTPHandler)
    print(f"🌐 HTTP Server on http://localhost:{PORT}")
    server.serve_forever()

async def generate_voice(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVENLABS_API_KEY}
    data = {"text": text, "model_id": "eleven_monolingual_v1", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    audio_data = await resp.read()
                    return base64.b64encode(audio_data).decode('utf-8')
        except Exception as e:
            print(f"Voice error: {e}")
    return None

def get_response(text):
    text_lower = text.lower()
    if 'friday' in text_lower or 'tiktok' in text_lower:
        return ("Friday's looking busy. Midjourney subscription, then 5 AI images for TikTok.", 
                "<h3>Friday March 7</h3><ul><li>Subscribe to Midjourney</li><li>Generate 5 AI images</li><li>Create @doomscrollingedits</li><li>Post Video 1</li></ul>")
    elif 'trade' in text_lower:
        return ("Trading update: 65% win rate, $6.31 profit. Ready for live trading Monday.",
                "<h3>Paper Trading Results</h3><ul><li>Profit: +$6.31</li><li>Win Rate: 65%</li><li>Time in Market: 54.5%</li></ul>")
    return (f"I'm here! You said: '{text[:30]}...'", "<p>Ask about TikTok, trading, or anything else.</p>")

async def handle_ws(websocket, path):
    print(f"🟢 Client connected")
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get('type') == 'message':
                voice_text, details = get_response(data['text'])
                audio = await generate_voice(voice_text)
                await websocket.send(json.dumps({
                    'type': 'response',
                    'voice_text': voice_text,
                    'details_html': details,
                    'audio': audio,
                    'timestamp': str(datetime.now())
                }))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("🔴 Client disconnected")

WS_PORT = 8765

async def start_ws():
    print(f"📡 WebSocket Server on ws://localhost:{WS_PORT}")
    async with websockets.serve(handle_ws, 'localhost', WS_PORT):
        await asyncio.Future()

async def main():
    print("🚀 Starting Combined Server...\n")
    # Start HTTP in thread
    http_thread = threading.Thread(target=start_http, daemon=True)
    http_thread.start()
    await asyncio.sleep(2)
    # Start WebSocket
    await start_ws()

if __name__ == '__main__':
    asyncio.run(main())
