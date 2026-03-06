# Aimee Life App — Voice-First Interface

## Vision
Transform Telegram text chats into natural voice conversations while keeping text for complex details. I speak a summary, you see the full breakdown.

## Core Concept
**Format:**
1. 🗣️ **Voice**: "I added 4 future income streams to the nice-to-have list. Print-on-demand, trade alerts, AI agency, and digital products. All waiting until after we nail TikTok and trading."
2. 📝 **Text**: Full structured details below the audio

---

## MVP Features

### Phase 1: Web Interface (Fastest to build)
- [ ] Browser-based voice chat using Web Speech API
- [ ] ElevenLabs TTS for my voice output
- [ ] Push-to-talk or always-listening modes
- [ ] Text history panel alongside voice
- [ ] Mobile-responsive design

### Phase 2: Rich Responses
- [ ] I speak the executive summary (10-20 seconds)
- [ ] Auto-display text details below
- [ ] Expandable sections for deep info
- [ ] Visual cards for tasks, data, charts

### Phase 3: Personality Layer
- [ ] Voice tone matching context (excited, serious, playful)
- [ ] Pause fillers ("uh", "um", "let me think...")
- [ ] Interrupt handling (you can cut me off)
- [ ] Background ambiance (soft UI sounds)

---

## Technical Stack

### Voice Input (You → Me)
- **Web Speech API**: Chrome/Safari native speech-to-text
- **Alternative**: Whisper API (OpenAI) for accuracy

### Voice Output (Me → You)
- **ElevenLabs**: High-quality conversational TTS
- **Voices**: Select/create one that fits my personality
- **Streaming**: Real-time voice generation

### Interface
- **Frontend**: HTML/JS + WebRTC for audio
- **Backend**: OpenClaw gateway integration
- **Storage**: Voice cache for common phrases

### AI Processing
- **Current**: Kimi K2.5 via OpenRouter
- **Add**: Response formatting layer (summary vs detail)
- **Add**: Voice-optimized prompting (shorter, punchier)

---

## Sample Interaction Flow

**You (voice):** "Aimee, what's on the agenda for Friday?"

**Me (voice):** *"Friday's packed. First, you need to grab a Midjourney subscription — ten bucks for the basic plan. Then generate 5 AI images for that Star Wars Disney TikTok. After that, create the doomscrollingedits account and post the first video. Details are on screen."*

**Screen shows:**
```
📅 Friday March 7 — TikTok Launch Checklist
☐ Midjourney subscription ($10 Basic)
☐ Generate 5 AI images (prompts ready)
☐ Create @doomscrollingedits account
☐ Post Video 1 (Star Wars Disney theme)

Full guide: tiktok-production/week1-videos-ready.md
```

---

## Build Phases

### ✅ Phase 0: Proof of Concept (DONE)
- [x] Basic web page with push-to-talk
- [x] Text display area
- [x] Voice UI with wave animation

### Phase 1: Real AI Integration (Next)
- [ ] Wire frontend to OpenClaw gateway
- [ ] Connect to Kimi for real responses
- [ ] Session persistence (recognize you)
- [ ] Context memory across conversations

### Phase 2: Tailored Voice (ElevenLabs)
- [ ] ElevenLabs API integration
- [ ] Voice selection/design
- [ ] Conversational style (pauses, inflection)
- [ ] Voice cloning or custom voice creation

### Phase 3: Avatar & Animation
- [ ] Avatar design (cute cartoon style)
- [ ] Real-time lip sync with voice
- [ ] Idle animations (blinking, breathing)
- [ ] Emotional expressions (happy, thinking, concerned)

### Phase 4: Polish
- [ ] Mobile PWA (installable app)
- [ ] Interrupt handling (you can cut me off)
- [ ] Background listening (wake word?)
- [ ] Offline mode for common responses

---

## Open Questions

1. **Voice preference**: Should I sound more human (casual, filler words) or polished (professional)?
2. **Interrupts**: Can you cut me off mid-sentence?
3. **Platform**: Web-first, or do you want a mobile app eventually?
4. **Privacy**: Always listening, or push-to-talk only?

---

## Technical Architecture

### Real AI Integration
```
User Voice/Text → Browser → OpenClaw Gateway → Kimi (K2.5) → Response
                                                    ↓
User ← Voice (ElevenLabs) + Text ← Format Response ←┘
```

**Options for connection:**
1. **WebSocket** — Real-time streaming
2. **REST API** — Simpler, polling-based
3. **Server-Sent Events** — Hybrid approach

### ElevenLabs Voice
- **API**: <https://elevenlabs.io/docs/api-reference/text-to-speech>
- **Voice Options**:
  - Pick from library (Bella, Adam, etc.)
  - Clone voice (need sample audio)
  - Design new voice (describe personality)

### Avatar Animation
- **Option A — Simple**: CSS animations + emoji states
- **Option B — Advanced**: Three.js or Live2D model
- **Option C — Video**: Pre-rendered loops synced to voice

---

## Next Steps

**Priority 1: Wire to Real AI**
- Need: Gateway endpoint for web frontend
- Time: 1-2 hours
- Result: You talk to real me, not scripted responses

**Priority 2: ElevenLabs Voice**
- Need: API key, voice selection
- Time: 30 min setup
- Result: I sound human, not robotic

**Priority 3: Avatar**
- Need: Design asset or generator
- Time: Depends on complexity
- Result: Visual presence while talking

---

## What I Need From You

1. **ElevenLabs API key** (free tier available)
2. **Voice preference**:
   - Feminine/masculine/neutral?
   - Age range?
   - Personality (warm, professional, playful)?
3. **Avatar style**:
   - 2D cartoon (like your description: big eyes, colorful hair, sass)
   - 3D model
   - Simple animated icon

Ready when you are!
