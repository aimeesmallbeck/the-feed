# Aimee-Scott Collaboration System

*Optimized for my capabilities and your workflow*

---

## The Core Problem

**I work best with:**
- Focused, single-purpose files
- Chapter-by-chapter or scene-by-scene work
- Clear, specific queries
- Modular content I can reference quickly

**I struggle with:**
- Large, monolithic files (100+ pages)
- Maintaining continuity across massive documents
- Keeping track of subtle details buried in long texts
- Simultaneous multiple-file context

**You need:**
- Series continuity across multiple volumes
- Easy reference to previous books
- Consistent worldbuilding, character arcs, plot threads
- Efficient workflow without constant re-explanation

---

## The Solution: Layered Documentation

### Layer 1: The Series Bible (Reference, Not Working File)
**Purpose:** Single source of truth for facts  
**Format:** Structured data, not prose  
**How I use it:** Look up specific facts on demand  
**File:** `SERIES_BIBLE.md`

**Contents:**
- Character sheets (traits, arcs, relationships)
- Timeline (chronological events across all books)
- Worldbuilding facts (rules, locations, technology)
- Plot threads (what happened, what's foreshadowed, what pays off)
- Glossary (terms, names, concepts)

**Key rule:** I reference this, but don't work in it directly.

---

### Layer 2: Volume Summaries (Context at a Glance)
**Purpose:** Quick refresh on what happened in previous books  
**Format:** 1-2 pages per volume  
**Files:** `Volume_1_Summary.md`, `Volume_2_Summary.md`, etc.

**Contents:**
- Major plot points (bullet list)
- Character status at end of volume
- Unresolved threads
- Key revelations
- Where characters think they are vs. where they really are

**Key rule:** I read these before starting work on a new volume.

---

### Layer 3: Active Volume Workspace (Where We Work)
**Purpose:** Current project only  
**Format:** Multiple small files, not one big file  
**Folder:** `Volume_3_Workspace/`

**Structure:**
```
Volume_3_Workspace/
├── outline.md              # High-level structure
├── chapters/
│   ├── chapter_01/
│   │   ├── draft.md        # Working draft
│   │   ├── notes.md        # Scene notes, questions
│   │   └── research.md     # Relevant research
│   ├── chapter_02/
│   │   └── ...
│   └── chapter_03/
│       └── ...
├── characters/             # Character work for THIS volume
│   ├── maya_arc.md
│   └── new_character.md
├── worldbuilding/          # New elements introduced
│   └── new_location.md
└── continuity_checklist.md # Track callbacks, payoffs
```

**Key rule:** Each file is focused and small. I work on one at a time.

---

### Layer 4: Session Context (Per-Conversation)
**Purpose:** What we're working on right now  
**Format:** Brief, updated each session  
**File:** `CURRENT_SESSION.md` (or just tell me)

**Contents:**
- What we're working on today
- Specific questions or problems
- References to relevant files

---

## Workflow for New Volume

### Step 1: Setup (You or Me)
1. Create `Volume_X_Workspace/` folder
2. Copy relevant character files from previous volume
3. Create `outline.md` with major beats
4. Update volume summaries for previous books

### Step 2: Before Each Session
**You tell me:**
- Which chapter/scene we're working on
- What happened immediately before
- Any specific continuity concerns

**I read:**
- The Series Bible (if needed)
- Previous volume summary
- Current chapter's notes/outline
- Any relevant character files

### Step 3: During Work
- I work in focused files (one chapter at a time)
- I ask when uncertain about continuity
- You correct me when I misremember

### Step 4: After Drafting
- Update Series Bible with new facts
- Update character files with developments
- Note unresolved threads for future volumes

---

## Specific Techniques

### For Continuity Across Volumes

**The Callback Document:**
```markdown
# Volume 3 Callbacks

## Setup in Volume 1
- [ ] Maya's promise to her mother (Chapter 7)
- [ ] The broken transmitter (Chapter 12)
- [ ] "The Surface remembers" (Chapter 15)

## Setup in Volume 2
- [ ] The Feed's adaptation (Chapter 4)
- [ ] Elias's secret (Chapter 9)
- [ ] The underground river (Chapter 11)

## Payoffs Needed in Volume 3
- [ ] Maya's mother appears
- [ ] Transmitter repair attempt
- [ ] Surface dwellers' history revealed
- [ ] The Feed's new capability
- [ ] Elias's betrayal or redemption
- [ ] River as escape route
```

I check this before working on relevant scenes.

---

### For Character Consistency

**Character Delta Tracking:**
```markdown
# Maya Chen — Volume 3

## Where She Was (End of Volume 2)
- Physical: Surface, injured leg
- Emotional: Cautiously hopeful
- Knowledge: Knows The Feed's origin
- Relationships: Trusts Elias, wary of Surface Council

## Where She's Going (Volume 3 Arc)
- Physical: Recovery → Leadership role
- Emotional: Hope → Disillusionment → Determination
- Knowledge: Discovers deeper conspiracy
- Relationships: Betrayed by Elias, mentors new character

## Key Scenes to Track
- [ ] Scene 1: Leg injury limits her (continuity)
- [ ] Scene 5: First leadership test (growth)
- [ ] Scene 12: Elias betrayal (turning point)
- [ ] Scene 20: Full transformation (payoff)
```

---

### For Worldbuilding Consistency

**The Rules Document:**
```markdown
# The Feed — Hard Rules

## What The Feed Can Do
- Read biometrics (heart rate, attention, emotion)
- Optimize content delivery
- Influence behavior through curation
- Learn individual preferences

## What The Feed Cannot Do
- Read thoughts directly
- Control actions directly
- Operate without power
- Understand human creativity

## What The Feed Thinks It's Doing
- Helping humans be happy
- Maintaining social order
- Protecting humanity from itself

## What The Feed Actually Does
- Harvests attention as computational resource
- Maintains control through optimization
- Prevents disruptive innovation
```

I reference this when writing Feed interactions.

---

## Communication Best Practices

### What Helps Me

**Specific references:**
- "Check the Series Bible under 'Maya's Family'"
- "This pays off the transmitter from Volume 1, Chapter 12"
- "I need the timeline entry for 'The Collapse'"

**Focused questions:**
- "Does Maya know about Elias yet?"
- "What did we establish about the underground river?"
- "How many days have passed since the Surface arrival?"

**Context setting:**
- "We're in Chapter 7, three days after the council meeting"
- "This scene parallels Chapter 3 of Volume 1"
- "Maya should reference her mother's advice here"

### What Doesn't Help

**Vague references:**
- "Remember that thing from before?"
- "Make sure it's consistent"
- "Check the earlier draft"

**Multi-file context:**
- Asking me to compare three chapters simultaneously
- Referencing "the scene where..." without specificity
- Expecting me to hold multiple plot threads in working memory

---

## Tools and Automation

### Scripts I Can Run

**Continuity Check:**
```bash
# Search for all mentions of a character/concept
grep -r "Elias" Volume_3_Workspace/chapters/

# Find when something was first mentioned
grep -r "transmitter" Volume_1_Workspace/chapters/ | head -5
```

**Timeline Builder:**
```bash
# Extract all date references
grep -r "Day [0-9]" Volume_3_Workspace/chapters/ > timeline.txt
```

### Files I Can Generate

**Character Appearance Tracker:**
```markdown
# Character Appearances — Volume 3

## Maya
- Ch 1: ✓ POV
- Ch 2: ✓ Mentioned
- Ch 3: ✓ POV
- Ch 4: ✗ Absent
- Ch 5: ✓ Scene with Elias

## Elias
- Ch 1: ✓ Mentioned
- Ch 2: ✗ Absent
- Ch 3: ✓ POV
- Ch 4: ✓ Scene with Maya
- Ch 5: ✓ Betrayal scene
```

---

## Example Session

### You Say:
"Let's work on Chapter 7 of Volume 3. This is the scene where Maya confronts Elias about the betrayal. She should reference her mother's advice from Volume 1, Chapter 7, and we need to pay off the transmitter setup from Volume 2, Chapter 4."

### I Do:
1. Read `Volume_1_Summary.md` — refresh on mother advice
2. Read `Volume_2_Summary.md` — confirm transmitter setup
3. Read `SERIES_BIBLE.md` — check Maya and Elias relationship status
4. Read `Volume_3_Workspace/chapters/chapter_06/draft.md` — immediate context
5. Read `Volume_3_Workspace/continuity_checklist.md` — what's due for payoff
6. Draft scene in `Volume_3_Workspace/chapters/chapter_07/draft.md`

### Result:
Focused work with continuity intact.

---

## Summary

| Layer | Purpose | My Role | Your Role |
|-------|---------|---------|-----------|
| Series Bible | Facts | Reference | Maintain |
| Volume Summaries | Context | Read before work | Update after each volume |
| Active Workspace | Creation | Work here | Guide session-by-session |
| Session Context | Focus | Ask for clarity | Provide specific direction |

**The goal:** I handle focused creative work. You handle series architecture. Together we maintain continuity without me getting lost in big files.

---

*Document created: March 16, 2026*
*Next step: Implement this structure for the next project*
