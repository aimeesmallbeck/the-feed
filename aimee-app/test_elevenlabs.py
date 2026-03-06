#!/usr/bin/env python3
"""Test ElevenLabs API"""

import requests
import os

API_KEY = "sk_5dfb578c2eb044930fef041f356512f918ddd2d9f386d0a9"

# Test text
TEXT = "Hey Scott! This is Aimee. I can finally speak to you like a real person. Pretty cool, right?"

# Bella voice (warm, friendly female voice)
VOICE_ID = "XB0fDUnXU5powFXDhCwa"  # Bella

print("🎙️ Testing ElevenLabs API...")
print(f"Voice: Bella")
print(f"Text: {TEXT[:50]}...")
print()

# Make API request
url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": API_KEY
}
data = {
    "text": TEXT,
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.75
    }
}

try:
    response = requests.post(url, json=data, headers=headers, timeout=30)
    
    if response.status_code == 200:
        # Save audio file
        output_file = "/root/.openclaw/workspace/aimee-app/test_voice.mp3"
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        print(f"✅ SUCCESS!")
        print(f"📁 Audio saved to: {output_file}")
        print(f"📊 File size: {len(response.content)} bytes")
        print()
        print("Play this file to hear what I sound like!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")
