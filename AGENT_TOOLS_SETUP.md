# Agent Tools Setup Plan

## Container Environment Constraints
- Cannot install new Python packages directly
- Cannot modify system configs
- Limited to pre-installed tools

## Tools to Setup

### 1. browser-use ❌ BLOCKED
**Status:** Requires pip install, not available in container
**Workaround:** Use built-in `browser` and `web_fetch` tools already provided by OpenClaw
**Action:** Document existing web capabilities instead

### 2. Mem0 (Memory System) ❌ BLOCKED
**Status:** Requires pip install (mem0ai package)
**Workaround:** Continue using file-based memory system (MEMORY.md, daily logs)
**Enhancement:** Could add vector search via embeddings API if needed

### 3. Zep Memory ❌ BLOCKED
**Status:** Requires pip install
**Workaround:** Same as Mem0 — file-based memory is working

### 4. Promptfoo ❌ BLOCKED
**Status:** Requires npm/pip install
**Workaround:** Manual testing + validation scripts

### 5. OpenHands ❌ BLOCKED
**Status:** Complex setup, requires local environment
**Alternative:** Use existing `sessions_spawn` for sub-agents

### 6. Cline / Continue ❌ BLOCKED
**Status:** VS Code extensions, not applicable to container

---

## What I CAN Do Now

### Document Current Capabilities
1. **Web automation** via built-in `browser` tool
2. **Web fetching** via `web_fetch` tool
3. **File-based memory** (already working)
4. **Sub-agent spawning** via `sessions_spawn`
5. **Shell commands** (limited but functional)

### Create Helper Scripts
1. Memory search/retrieval utilities
2. Web research automation
3. Testing/validation scripts

---

## What Requires Your Help (Local Setup)

For full tool installation, you'll need to either:

1. **Run locally** (your machine) with full package installation freedom
2. **Request container package additions** from OpenClaw admin
3. **Use external APIs** instead of local packages

Priority tools for local setup:
- browser-use (web automation)
- Mem0 (vector memory)
- OpenHands (coding agents)

---

## Immediate Actions Taken

- [x] Assessed container limitations
- [x] Documented workarounds
- [ ] Creating enhanced memory utilities
- [ ] Testing web automation capabilities
- [ ] Preparing local setup instructions

## Notes

Container environment confirmed at `/root/.openclaw/workspace/`
Pre-installed tools: see TOOLS.md for full list
