# Game Companion – Product Requirements Document (PRD)

**Version:** 4.0  
**Date:** February 7, 2026  
**Author:** Product Team  
**Status:** Approved – Ready for Technical Design  

**Revision History:**
| Version | Date | Changes |
|---------|------|---------|
| 3.0 | Feb 6, 2026 | Initial approved spec — M1–M7 milestones, 3-type stable context (Character Sheets, Playthrough State, Narrative Notes) |
| 4.0 | Feb 7, 2026 | Rewrote §4.3 based on 100-participant user study (see [research-protocol.md](research-protocol.md)). Expanded stable context from 3 types to 5: Entity Sheets, World State, Decision Log, Player Codex, Narrative Threads. Added entity tiers, plan/constraint/rejection tracking, cross-genre examples (BG3, Football Manager, CK3). Updated user flows §6 and milestone table §12 for new terminology. |

---

## 1. Overview

### 1.1 Vision
Game Companion is an AI-powered chat assistant that acts as your knowledgeable, friendly co-pilot across long-running video game playthroughs. It remembers everything about your journey—characters, decisions, struggles—so you never have to re-explain context, even after 60+ hours of gameplay.

### 1.2 Problem Statement
Today, players use general-purpose LLMs (ChatGPT, Claude) to discuss their games. This works for quick questions but breaks down for extended playthroughs:
- **Context window limits** cause the AI to forget earlier conversations
- **No persistence** means starting fresh each session
- **No game-specific search** leads to outdated or incorrect advice
- **Multi-game juggling** is entirely manual

### 1.3 Solution
A locally-run web application with:
- **Persistent memory** – stores and retrieves relevant context from all past conversations per playthrough
- **Web search integration** – fetches accurate, cited game information on demand
- **Multi-playthrough management** – cleanly separates different games and runs
- **Model-agnostic design** – starts with Gemini, extensible to other LLM providers
- **Browser-based UI** – accessible via any modern web browser on the local machine

---

## 2. Target User

**Primary (v1):** The creator – a multi-genre gamer who plays RPGs, fighting games, sports games, and story-driven titles across long sessions.

**Future:** Broad gamer audience seeking a persistent AI companion for any game.

---

## 3. Use Cases (Prioritized)

| Priority | Use Case | Example |
|----------|----------|---------|
| **P1** | Character build advice | "Should I go STR or DEX for a paladin multiclass?" |
| **P2** | Roleplay/storytelling brainstorm | "What would my character say to Shadowheart here?" |
| **P3** | Strategy/walkthrough help | "How do I beat the Nameless King? I keep dying." |
| **P4** | Session journaling | "Summarize what happened in tonight's session." |
| **P5** | World/lore Q&A | "Who is Raphael and why does everyone hate him?" |

**v2:** Narrative story export ("Generate a dramatic retelling of my playthrough")

---

## 4. Functional Requirements

### 4.1 Playthrough Management

| ID | Requirement |
|----|-------------|
| F1.1 | User can create a new playthrough with a custom name (e.g., "BG3 – Dark Urge Run") and an optional game title (e.g., "Baldur's Gate 3"). Game title, when provided, is used for web search context and system prompting. |
| F1.2 | User can rename a playthrough and update its game title at any time |
| F1.3 | User can view a list of all playthroughs, sorted by last played |
| F1.4 | App opens to the most recently active playthrough |
| F1.5 | Playthroughs are completely siloed – no cross-referencing |
| F1.6 | User can delete a playthrough (with confirmation) |
| F1.7 | User can export a playthrough to a ZIP file (metadata, messages, stable context; excludes embeddings) |
| F1.8 | User can import a playthrough from a ZIP file (embeddings regenerated on import) |

### 4.2 Chat Interface

| ID | Requirement |
|----|-------------|
| F2.1 | Minimal chat UI – text input, message history, send button |
| F2.2 | Natural language only (no slash commands in v1) |
| F2.3 | Dark mode by default |
| F2.4 | Mobile-responsive layout (ready for tablet/phone in v2) |
| F2.5 | Chat history persists across app restarts |
| F2.6 | Typing/thinking indicator shown while waiting for LLM response |
| F2.7 | Clear error message shown when user attempts to chat while offline |
| F2.8 | **API Error Handling:** Catch and wrap API errors (rate limits, auth failures, network errors) in user-friendly error dialog. Dialog shows friendly message (e.g., "API rate limit reached. Please wait a moment and try again.") with expandable "Details" section containing full error response for debugging. |

### 4.3 Persistent Memory (RAG)

| ID | Requirement |
|----|-------------|
| F3.1 | All conversations are stored locally per playthrough |
| F3.2 | On each user query, relevant past context is retrieved via vector similarity search |
| F3.3 | Retrieved context is injected into the LLM prompt automatically |
| F3.4 | AI response and context extraction occur in a single LLM call using structured output (function calling) |
| F3.4a | Orchestrator parses structured output; only displays response text to user; context updates are applied silently |
| F3.5 | User is notified via an expandable "📌 Memory updated" indicator when stable context is updated. Indicator shows a short summary of what was saved (e.g., "Saved: Keth reached level 7"). User can expand to see full detail of the context change. |
| F3.6 | User can explicitly pin a message/fact to force-persist it |
| F3.7 | Zero manual curation required – system is fully automatic |
| F3.8 | User can view any stable context via natural language ("Show me Keth's character sheet", "What are my house rules?") |
| F3.9 | User can request updates to stable context ("Update Alfira's spells – she now has Hold Person") |
| F3.10 | User corrections to web-search-sourced information are persisted to stable context (e.g., "That weapon was nerfed in patch 1.07"). AI avoids repeating corrected claims in future responses. |

#### 4.3.1 Stable Context Types

> **Design principle:** Categories are universal containers. The AI fills them with game-appropriate content. The user never defines the schema — the AI adapts it based on the game and conversations.

The system maintains five types of stable context per playthrough:

| Type | What It Captures | Format | Update Mode |
|------|-----------------|--------|-------------|
| **Entity Sheets** | One per tracked entity — who/what they are, their current state, where they're headed, and what the player has decided about them | Structured JSON | Overwrite on change |
| **World State** | Current state of the game world — progression, location, active goals, strategic situation, infrastructure | Structured JSON | Overwrite |
| **Decision Log** | Choices made, their consequences, and their current status | Structured entries | Append; AI prunes resolved/irrelevant entries |
| **Player Codex** | How the player plays — preferences, self-imposed rules, mods, difficulty settings, spoiler boundaries | Structured JSON | Overwrite on change |
| **Narrative Threads** | Themes, relationships, ongoing dynamics, player-authored narratives | Prose/Markdown | Append + AI-curated pruning |

**Why five types, not three:**
- The original three (Character Sheets, Playthrough State, Narrative Notes) collapsed too many distinct needs into too few containers.
- **Player Codex** was extracted because player preferences and house rules are neither character data nor story data — they're meta-gameplay constraints that govern how the AI should behave.
- **Decision Log** was extracted from Narrative Notes because decisions with consequences need structure (what → why → what happened), not free prose.
- User study evidence: see [research-protocol.md](research-protocol.md) §B.10–B.11.

#### 4.3.2 Entity Sheet Schema

An "entity" is anything the player needs the companion to track as a distinct object: a character, a party member, a dynasty, a club, a civilization, a base, a vehicle. The schema is universal — the AI populates game-appropriate fields within fixed top-level categories.

**Fixed top-level structure:**

```json
{
  "name": "...",
  "role": "...",
  "status": "active",
  "identity": {},
  "state": {},
  "plan": {},
  "constraints": [],
  "rejections": [],
  "notes": ""
}
```

| Category | Purpose | Why It's Universal |
|----------|---------|-------------------|
| `name` | Display name of the entity | Every tracked thing has a name |
| `role` | Relationship to the player — protagonist, ally, rival, squad member, team, base, etc. | Every entity has a relationship to the player |
| `status` | Lifecycle state — active, dead, retired, benched, sold, destroyed, succeeded-by | Every entity can enter and exit play |
| `identity` | What the entity *is* — the facts that don't change or rarely change | RPG: race, class, background. Sports: team, position. Strategy: civ, leader. Survival: base location, type |
| `state` | The entity's *current measurable condition* | RPG: level, stats, gear, abilities. Sports: season stats, form. Strategy: territory, resources |
| `plan` | Where the entity is *headed* — goals, targets, development path, and what changed along the way | RPG: target build, planned feats. Sports: development focus. Strategy: expansion plan. Includes change history with reasons |
| `constraints` | Rules the player has set for this entity that the AI must respect | RPG: "no coercive magic." Sports: "pressing style only." Strategy: "peaceful victory." Universal: any player-imposed limit |
| `rejections` | Options explicitly considered and rejected, with reasons | RPG: "no Tavern Brawler — doesn't fit theme." Sports: "rejected 4-3-3, doesn't suit personnel." Prevents re-suggesting |
| `notes` | Free-text — philosophy, personality, player observations, anything that doesn't fit above | Universal catch-all for qualitative context |

**Key changes from v3.0 spec:**
- Renamed "Character Sheets" → "Entity Sheets" — an entity can be a person, a team, a base, a dynasty
- Added `status` — entities have lifecycles (especially in permadeath, dynasty, or roster games)
- Added `plan` — 72% of study participants need future-looking tracking, not just current state. Includes change history so the AI knows *why* the plan shifted
- Added `constraints` — player-imposed rules that the AI must enforce, not just remember
- Added `rejections` — the #1 AI frustration in user study was re-suggesting rejected options
- Merged former `stats`, `progression`, `inventory` into two broader categories: `identity` (stable facts) and `state` (current condition)
- User study evidence: see [research-protocol.md](research-protocol.md) §B.4, §B.10

**Key principle:** The AI infers the appropriate fields within each category from conversation context and the game being played. The user never defines the schema — the AI adapts it.

**Example — RPG (Baldur's Gate 3):**

```json
{
  "name": "Keth",
  "role": "Protagonist",
  "status": "active",
  "identity": {
    "race": "Shadar-kai (Netherese)",
    "background": "Planar Philosopher (Transcendent Order)",
    "class": [{ "name": "Monk", "subclass": "Way of Shadow", "level": 9 },
              { "name": "Rogue", "subclass": "Thief", "level": 5 }]
  },
  "state": {
    "STR": 10, "DEX": 18, "CON": 14, "INT": 8, "WIS": 16, "CHA": 10,
    "keyAbilities": ["Shadow Step", "Uncanny Dodge", "Mage Slayer"],
    "keyMechanics": ["Unarmed Smite mod enabled"]
  },
  "plan": {
    "target": "Monk 11 / Rogue 9",
    "nextMilestone": "Monk 11 — Shadow Strike power spike",
    "history": [
      { "previous": "Monk 14 / Paladin 6 (Vengeance)", "reason": "Rejected divine authority after Alfira's death", "when": "Mid Act 2" }
    ]
  },
  "constraints": [
    "No weapons — body is the instrument of correction",
    "Smite is a sentence, not a DPR habit — reserved for decisive moments",
    "RPG priority over mechanical optimization"
  ],
  "rejections": [
    { "option": "Half-Orc race", "reason": "Power from discipline, not biology" },
    { "option": "Tavern Brawler feat", "reason": "Doesn't fit theme; STR-based" },
    { "option": "Yuan-ti race", "reason": "Risks supremacist overtones" }
  ],
  "notes": "Restraint is the default. Enforcement is the exception. Violence is corrective, not expressive. Professor X-style authority."
}
```

**Example — Sports (Football Manager):**

```json
{
  "name": "AFC Richmond",
  "role": "Player-managed club",
  "status": "active",
  "identity": {
    "league": "English Premier League",
    "reputation": "3.5 star",
    "philosophy": "Pressing, youth-driven"
  },
  "state": {
    "season": "2026-27",
    "leaguePosition": 8,
    "record": "W12 D6 L4",
    "topScorer": "Jamie Tartt (14 goals)"
  },
  "plan": {
    "target": "Top 4 finish within 2 seasons",
    "nextMilestone": "January window — sign a holding midfielder",
    "history": [
      { "previous": "Mid-table consolidation", "reason": "Youth academy producing faster than expected", "when": "Season 2" }
    ]
  },
  "constraints": [
    "No signings over age 28 — building for the future",
    "Pressing style non-negotiable"
  ],
  "rejections": [
    { "option": "4-3-3 formation", "reason": "Doesn't suit double-pivot personnel" }
  ],
  "notes": "Manager wants to build a dynasty, not buy one. Community club ethos."
}
```

**Example — Strategy (Crusader Kings 3):**

```json
{
  "name": "House Sigurdsson",
  "role": "Player dynasty",
  "status": "active",
  "identity": {
    "culture": "Norse",
    "religion": "Reformed Asatru",
    "holdings": "Kingdom of Norway, Duchy of Iceland"
  },
  "state": {
    "currentRuler": "King Harald III (Ambitious, Diligent, Wrathful)",
    "successionLaw": "Scandinavian Elective",
    "heir": "Prince Bjorn (age 14, Strong, Genius)"
  },
  "plan": {
    "target": "Form Empire of Scandinavia within 2 rulers",
    "nextMilestone": "Conquer Denmark before Harald dies",
    "history": [
      { "previous": "Unify Norway only", "reason": "Discovered Bjorn is Genius — dynasty can aim higher", "when": "Year 923" }
    ]
  },
  "constraints": [
    "Never convert away from Asatru",
    "No kinslaying — even for succession convenience"
  ],
  "rejections": [
    { "option": "Feudal conversion", "reason": "Tribal fits our raiding playstyle" }
  ],
  "notes": "Three generations of rulers. Grandmother conquered, father reformed faith, current ruler consolidating."
}
```

**Entity Sheet Tiers:**

Not all entities need the same depth. The AI manages tiered detail levels to stay within context budget:

| Tier | When Used | Typical Size | Example |
|------|-----------|-------------|---------|
| **Full** | Active party members, protagonist, primary entities | ~300–400 tokens | Keth, Alfira, the player's CK3 dynasty |
| **Summary** | Benched/secondary entities, large rosters | ~50–80 tokens | XCOM soldiers, FM youth prospects, inactive companions |
| **Archived** | Dead, removed, or retired entities | ~30–50 tokens | Astarion (removed), Shadowheart (dead), former CK3 rulers |

Archived entities retain enough information for consequence tracking ("Jaheira died → Minsc unavailable") but don't consume full context budget.

#### 4.3.3 World State

World State captures the current condition of the game world. Like entity sheets, the fields within each category are game-adaptive.

**Fixed top-level structure:**

```json
{
  "progression": {},
  "location": {},
  "activeGoals": [],
  "worldConditions": {}
}
```

| Category | Purpose | Example by genre |
|----------|---------|-----------------|
| `progression` | Where the player is in the game's arc | RPG: "Act 2, Shadow-Cursed Lands." Strategy: "Classical Era, Turn 142." Sports: "Season 3, January window." Survival: "Bronze Age, 3 bosses defeated." |
| `location` | Current position in the game world | RPG: "Moonrise Towers." Open world: "Caelid, east of Sellia." Survival: "Ocean biome, 800m depth." |
| `activeGoals` | What the player is currently trying to accomplish | RPG: "Resolve Nightsong quest." Strategy: "Take Damascus before Mongol invasion." Sports: "Sign a CB before deadline." |
| `worldConditions` | State of the world that affects decisions | RPG: "Shadow curse active, need light source." Strategy: "Allied with France, at war with England." Survival: "Copper unlocked, tin not yet found." |

#### 4.3.4 Decision Log

Structured record of meaningful choices, their consequences, and current status. Replaces free-form notes for anything with a cause-and-effect chain.

**Entry format:**

```json
{
  "decision": "Removed Astarion from party",
  "reason": "Unbounded actor — preventative correction",
  "consequences": ["Lost lockpicking specialist", "No Astarion-specific Act 2 content"],
  "status": "permanent",
  "when": "Early Act 1"
}
```

| Field | Purpose |
|-------|---------|
| `decision` | What the player chose |
| `reason` | Why — in the player's own framing |
| `consequences` | Known downstream effects (updated as consequences become apparent) |
| `status` | `active` (still in play), `resolved` (concluded), `permanent` (irreversible) |
| `when` | When in the game this occurred |

The AI prunes resolved decisions that no longer affect gameplay to manage context budget.

#### 4.3.5 Player Codex

Captures *how the player plays* — meta-gameplay preferences, self-imposed rules, mods, and interaction preferences. This is not about the game state; it's about the player's relationship to the game and to the companion.

**Fixed top-level structure:**

```json
{
  "difficulty": {},
  "mods": [],
  "houseRules": [],
  "spoilerBoundary": null,
  "companionPreferences": {}
}
```

| Category | Purpose | Examples |
|----------|---------|---------|
| `difficulty` | Game difficulty settings and adjustments | "Honor Mode, no single-save", "XP curve unlocked, targeting level 6 by Goblin Camp" |
| `mods` | Active mods + mods tried and rejected (with reasons) | Active: "Unarmed Smite — enables smite on fists." Rejected: "Recruit Any NPC — NPCs can't respec, abandoned." |
| `houseRules` | Self-imposed constraints beyond game settings | "No save-scumming except crashes", "Console commands treated as in-world defiance, not cheating" |
| `spoilerBoundary` | What the player has discovered; AI must not reference beyond this | "Completed Act 2, do not reference Act 3", "Reached 800m depth, don't spoil deeper biomes" |
| `companionPreferences` | How the player wants the AI to behave | "RP priority over optimization", "Wants critical pushback, not agreement", "Prefers concise answers" |

#### 4.3.6 Narrative Threads

Free-form prose for themes, dynamics, and ongoing narratives that don't fit into the structured types above. This is the space for qualitative context — the *feel* of the playthrough.

**Example:**

```markdown
## Thematic Anchors
- Power must have accountability
- The Tadpole represents parasitic systems bypassing consent
- Paladin oath = self-imposed limiter, not spiritual aspiration

## Party Dynamics
- Keth and Alfira: mutual restoration — she represents hope reclaimed by will
- Lae'zel: trusted as a force, not yet trusted as a judge
- Halsin: stayed out of stewardship, not obligation

## Player-Authored Narrative (XCOM example)
- Sgt "Big Mike" Torres: survived 14 missions, clutch sniper, named after player's brother
- The "Black Friday Squad" — the B-team that won the impossible terror mission
```

Narrative Threads are AI-curated: the AI appends new observations and prunes content that's no longer relevant. Player-authored content (named XCOM soldiers, CK3 dynasty sagas) is never pruned without player consent.

#### 4.3.7 Stable Context Update Mechanics

| Scenario | System Behavior |
|----------|-----------------|
| Measurable change discussed (level-up, stat change, trade, etc.) | AI updates entity sheet `state` → shows "📌 Memory updated" |
| New goal or plan change | AI updates entity sheet `plan` or World State `activeGoals` |
| New entity introduced (character, base, faction, etc.) | AI creates entity sheet at appropriate tier (full/summary) |
| Entity removed from active play | Sheet `status` changed (dead/retired/benched/sold); moved to archived tier |
| Player rejects an option with reasoning | AI adds to entity's `rejections` array |
| Player states a rule or constraint | AI adds to entity `constraints` or Player Codex `houseRules` |
| Major decision with consequences | AI adds entry to Decision Log |
| Playstyle/philosophy clarification | AI updates entity `notes` or Narrative Threads |
| Story event changes world state | AI updates World State `worldConditions` |
| User explicit request ("Remember this") | AI adds to appropriate context type |
| User correction ("That's wrong — X") | AI corrects the relevant field and confirms |
| Mod installed, removed, or evaluated | AI updates Player Codex `mods` |

#### 4.3.8 Stable Context Interaction Model

Users interact with stable context entirely through natural language:

| User Action | Example | System Response |
|-------------|---------|-----------------|
| View entity | "Show me Keth's character sheet" | Displays formatted entity sheet |
| View party/roster | "What do you remember about my party?" | Summarizes all active entity sheets |
| View decisions | "What major choices have I made?" | Lists Decision Log entries |
| View rules | "What are my house rules?" | Shows Player Codex |
| Explicit update | "Update Alfira — she learned Hold Person instead of Enhance Ability" | Updates entity state, confirms |
| Pin fact | "Remember this: Lae'zel is under evaluation" | Adds to Narrative Threads or entity notes |
| Correction | "That's wrong — Shadowheart is Twilight domain, not Darkness" | Corrects field, confirms |
| Add constraint | "Never suggest Friends cantrip for Alfira" | Adds to Alfira's constraints |
| Add rejection | "I decided against Tavern Brawler — doesn't fit the theme" | Adds to entity rejections |

**Key Principle:** User never has to curate, but always can.

#### 4.3.9 Context Budget

| Context Type | Estimated Tokens | Notes |
|--------------|------------------|-------|
| World State | ~300 | Progression, location, goals, conditions |
| Entity Sheets — full tier (×4 avg) | ~1,600 | ~400 tokens each with plan/constraints/rejections |
| Entity Sheets — summary tier (×4 avg) | ~250 | ~60 tokens each for secondary entities |
| Decision Log | ~400 | ~10 active entries × ~40 tokens |
| Player Codex | ~300 | Difficulty, mods, house rules, preferences |
| Narrative Threads | ~600 | AI-pruned to essentials |
| **Total Stable Context** | **~3,450** | Always included in prompt — this is the primary memory |
| Retrieved RAG chunks | ~2,000 | Supplementary — past conversation recall only (see note below) |
| Web search results | ~2,000 | When search triggered |
| Recent conversation | ~2,000 | Last 5–10 turns |
| **Typical Total Prompt** | **~9,500–10,000** | Well under context limits |

**RAG's role after stable context:** Stable context (Entity Sheets, World State, Decision Log, Player Codex, Narrative Threads) captures all *facts, decisions, and state*. RAG's only unique value is recalling the AI's own past advice and analysis — the *discussion*, not the facts. Use cases: "Summarize what happened last session" (31% of participants), "What did you recommend about multiclassing?" (19%), lore/theory discussions (18%). If RAG returns nothing, the experience degrades (user must re-ask) but doesn't break. If stable context fails, the product is useless. Budget reflects this: stable context gets ~3,450 tokens (always present), RAG gets ~2,000 (supplementary). See [research-protocol.md](research-protocol.md) §B.4, §B.5, §B.8 for evidence.

**Context tier management:** When total stable context approaches budget, the AI demotes less-relevant entities from full → summary tier and prunes resolved Decision Log entries. Player Codex and Narrative Threads with player-authored content are never auto-pruned.

### 4.4 Web Search

| ID | Requirement |
|----|-------------|
| F4.1 | AI has access to web search (Tavily) for game-specific information |
| F4.2 | LLM decides whether web search is needed as part of structured JSON response; orchestrator executes search if flagged (see tech-design-session.md §Orchestration) |
| F4.3 | All external information is cited with source URLs |
| F4.4 | Citations are displayed inline or as footnotes in responses |
| F4.5 | M4 introduces the structured JSON response format (`response` + `web_search` fields) that M5 will extend with `context_deltas` |

### 4.5 LLM Backend

| ID | Requirement |
|----|-------------|
| F5.1 | Gemini is the default model for v1 |
| F5.2 | User provides their own API key (stored securely locally) |
| F5.3 | Design supports adding LLM providers (OpenAI, Claude, local models) in future |
| F5.4 | User can select/change model in settings (extensible for v2) |

### 4.6 Settings

| ID | Requirement |
|----|-------------|
| F6.1 | API key entry/management for Gemini (and Tavily) |
| F6.2 | Model selection (v1: Gemini only; architecture ready for more) |
| F6.3 | Data storage location (informational, local by default) |
| F6.4 | Debug Mode toggle – when enabled, writes changelog.jsonl with all stable context updates |

---

## 5. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NF1 | **Platform:** Web application served locally, accessible via any modern browser |
| NF2 | **Data locality:** All user data (conversations, memory, settings) stored locally on the user's machine |
| NF3 | **Performance:** Response latency ≤ 5s for typical queries (network dependent) |
| NF4 | **Offline behavior:** App launches and shows history offline; chat requires internet connectivity |
| NF5 | **Security:** API keys stored securely and never exposed to the browser or transmitted to third parties |
| NF6 | **Single-user:** Designed for one user on one machine; no authentication required |
| NF7 | **Portability:** No install beyond standard developer tooling; self-contained local server |

---

## 6. User Flows

### 6.1 First-Time Setup
1. User starts the server and opens the web UI in their browser → sees welcome screen
2. Prompted to enter Gemini API key (and web search API key)
   - Each key field includes: a direct link to the provider's API key page, a brief explanation of what the key is for, and estimated cost/free-tier info
   - A "Test Key" button validates the key against the provider and shows success/failure inline
3. Keys validated and stored
4. User taken to "Create your first playthrough" screen
5. User enters playthrough name (e.g., "BG3 – Dark Urge Run") and optional game title (e.g., "Baldur's Gate 3")
6. Chat opens – ready to play

### 6.2 Returning User
1. User opens the web UI in their browser
2. UI opens to last active playthrough's chat
3. If significant time has passed since last session, system displays a brief "Welcome back" summary of last known game state (act, location, party, recent events) drawn from World State and Entity Sheets — not from chat history
4. User can dismiss the summary or ask follow-up questions
5. User continues conversation where they left off

### 6.3 Switching Playthroughs
1. User clicks playthrough name/menu icon
2. Sees list of playthroughs (sorted by recent)
3. Clicks different playthrough → chat switches
4. Option: "New Playthrough" button at top/bottom of list

### 6.4 Typical Chat Interaction
1. User types: "What class should I pick for a sneaky character?"
2. **System:**
   - Recalls relevant context (prior class discussions, character decisions)
   - Searches the web for current game’s class info
   - Generates response using all available context
3. AI responds with build advice, citing sources
4. System detects "User is building a stealth character" → saves to memory
5. User sees response + subtle "📌 Memory updated" indicator

### 6.5 Explicit Pin
1. User types: "My character's name is Tav and she's a half-elf rogue"
2. AI acknowledges
3. User clicks pin icon on the message → "Pin this"
4. Fact force-persisted to stable context
5. Confirmation shown

### 6.6 Viewing Stable Context
1. User types: "Show me Keth's character sheet"
2. AI displays formatted entity sheet with all tracked data
3. User can follow up: "What about Alfira?" or "What major decisions have I made?" or "Show my house rules"

### 6.7 Updating Stable Context
1. User types: "Update Alfira's spells — she swapped Enhance Ability for Hold Person"
2. AI updates the entity sheet's state
3. AI confirms: "Updated Alfira's Level 2 spells. 📌 Memory updated"
4. User can verify: "Show me Alfira's spells now"

### 6.8 Correcting Errors
1. User notices AI referenced wrong information
2. User types: "That's wrong — Shadowheart has 18 WIS, not 16"
3. AI corrects the entity sheet
4. AI confirms: "Corrected Shadowheart's WIS to 18. 📌 Memory updated"

---

## 7. UI Wireframes (Conceptual)

### Main Chat View
```
┌─────────────────────────────────────┐
│ [≡]  BG3 – Dark Urge Run       [⚙]│
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🤖 Based on your preference │   │
│  │ for stealth, I'd recommend  │   │
│  │ a Gloom Stalker Ranger...   │   │
│  │ [Source: bg3.wiki]          │   │
│  │              📌 Memory saved │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 👤 What about multiclassing │   │
│  │ with rogue?                 │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🤖 Great idea! A 3-level    │   │
│  │ Assassin dip gives you...   │   │
│  └─────────────────────────────┘   │
│                                     │
├─────────────────────────────────────┤
│ [   Type a message...         ] [→]│
└─────────────────────────────────────┘
```

### Playthrough Selector (Slide-out or Modal)
```
┌─────────────────────────────────────┐
│  Your Playthroughs                  │
├─────────────────────────────────────┤
│  [+ New Playthrough]                │
├─────────────────────────────────────┤
│  ● BG3 – Dark Urge Run              │
│    Last played: Today               │
├─────────────────────────────────────┤
│  ○ Clair Obscur – First Run         │
│    Last played: Yesterday           │
├─────────────────────────────────────┤
│  ○ Elden Ring – NG+                 │
│    Last played: Jan 28              │
└─────────────────────────────────────┘
```

---

## 8. Out of Scope (v1)

| Feature | Rationale |
|---------|-----------|
| Narrative story export | Complex; deferred to v2 |
| Cloud sync | Requires account system; v2 |
| Multiple LLM providers | Architecture ready, but only Gemini in v1 UI |
| Mobile-native deployment | Web UI is responsive; native mobile apps are v2 |
| Game-specific data imports | Stay generic; rely on web search |
| Voice input/output | Nice-to-have; v2+ |

---

## 9. Success Metrics (Future)

| Metric | Target |
|--------|--------|
| Session retention | User returns within 7 days |
| Context recall accuracy | User doesn't have to re-explain >90% of the time |
| Search citation trust | <5% complaints about incorrect info |
| Playthrough completion | User marks or finishes a playthrough |

---

## 10. Open Questions / Risks

| # | Question/Risk | Mitigation |
|---|---------------|------------|
| 1 | Memory recall quality – will the system find the right context? | Tune retrieval; use hybrid keyword+semantic search |
| 2 | Web search rate limits / cost at scale | Monitor usage; cache repeated queries |
| 3 | LLM content filtering may block some game content (violence, etc.) | Test with target games; have fallback prompt strategies |
| 4 | Stable context extraction accuracy | Use structured extraction prompts; allow user pin as override |
| 5 | Performance with large conversation history | Benchmark early; consider pruning old data |

---

## 11. Testing Strategy

> **Full test specification:** See [test-spec.md](test-spec.md) for complete test scenarios, acceptance criteria, and traceability matrix.

### 11.1 Approach

- **Test-Driven Development:** Tests written before implementation for all core features
- **Layered testing:** Unit tests for logic, integration tests for service boundaries, end-to-end tests for user scenarios
- **Real API validation:** Key integration points verified against live LLM and search APIs
- **Continuous regression:** Full test suite run after each milestone

### 11.2 Key Test Areas

| Area | What's Verified |
|------|-----------------|
| Persistent memory | Context is stored, retrieved, and correctly recalled in conversation |
| Web search | Queries return relevant, cited results |
| Stable context | Auto-detection, user commands, corrections all update memory accurately |
| Playthrough isolation | No data leaks between playthroughs |
| Error handling | Graceful behavior on API failures, network issues, malformed data |
| User flows | End-to-end scenarios from the User Flows section work as described |

---

## 12. Milestones

Each milestone delivers a complete, testable user experience slice — not a horizontal layer.

| Milestone | User Story | Acceptance Criteria | Spec Coverage | Estimate |
|-----------|-----------|---------------------|---------------|----------|
| **M1: First Conversation** | User can create a playthrough, send a message, and get an AI response | • First-time setup flow works (API key entry → playthrough creation → chat) • User sends a message and receives a coherent response • Chat history persists across browser refreshes | F1.1, F2.1–F2.6, F5.1–F5.2 · §4.1 (create), §4.2 (chat), §4.5 (Gemini) · §6.1 · test-spec §3.1 | 2 weeks |
| **M2: Multi-Playthrough** | User can manage multiple playthroughs and switch between them | • Create, rename, delete playthroughs • List sorted by last played • Switch between playthroughs; chat context stays siloed • Returns to last active playthrough on reopen | F1.2–F1.6 · §4.1 (rename, list, delete, silo, last-active) · §6.3 · test-spec §3.4 | 1 week |
| **M3: Memory Recall** | AI remembers what the user said in previous sessions | • Past conversation context is automatically recalled during chat • User doesn't have to re-explain previously discussed topics • Recalled context is relevant (not random old messages) • LLM response is still plain text (structured output not yet introduced) | F3.1–F3.3 · §4.3 (intro), §4.3.9 (context budget) · §6.2, §6.4 (recall) · test-spec §3.2 | 2 weeks |
| **M4: Web Search & Citations** | AI provides accurate, cited game information from the web | • **Structural transition: LLM response switches from plain text to structured JSON** (`{ response, web_search }`) • LLM decides whether search is needed via `web_search` field in structured output • If search flagged: orchestrator executes search → second LLM call with results • Responses include source URLs as inline citations or footnotes • Non-game queries (greetings, recall requests) return `web_search: null` • Fallback: if JSON parse fails, treat as plain text response | F4.1–F4.5 · F3.4 (partial — structured output infrastructure) · §4.4 · §6.4 (search + cite) · tech-design-session.md §Orchestration · test-spec §3.3 | 2 weeks |
| **M5: Living Memory** | AI automatically tracks game state, entities, and key decisions | • **Extends M4's structured JSON** with `context_deltas` field (`{ response, context_deltas, web_search }`) • Stable context (all 5 types) included in every prompt • AI detects entity info, level-ups, decisions and returns deltas • Orchestrator applies deltas to SQLite stable context store • "📌 Memory updated" indicator shown when deltas applied • User can view memory via natural language ("Show me Keth's character sheet", "What are my house rules?") • User can correct errors ("That's wrong — Keth has 18 DEX") • User can pin facts ("Remember this: Lae'zel is on probation") • Only user messages trigger deltas — AI's own response never does | F3.4–F3.10 · §4.3.1–4.3.9 · §6.5–6.8 · tech-design-session.md §Orchestration · test-spec §3.5–3.10 | 2 weeks |
| **M6: Settings & Polish** | User can manage settings; all user flows complete and polished | • API key management (add, update, validate) • Debug mode toggle with changelog • Error handling for all API failure modes (auth, rate limit, network) • Offline behavior (history visible, clear message when chat unavailable) • Dark mode, typing indicator, responsive layout foundations | F1.7–F1.8, F2.7–F2.8, F6.1–F6.4 · §4.6, §4.2 (errors, offline) · §6.1 (polish) · test-spec §4.1 | 1 week |
| **M7: Release** | v1.0 — all features complete, tested, and stable | • Full test suite passes • Manual QA checklist completed across multiple game types • Export/import playthrough works • Performance targets met (≤5s response, ≤500ms memory recall) | All · §5 Performance Targets · test-spec §5–6 | 1 week |

**Total: ~11 weeks to v1.0**

---

## 13. Approval

| Role | Name | Date | Sign-off |
|------|------|------|----------|
| Product Owner | Jordan | 2026-02-06 | ✅ |
| Tech Lead (Staff Dev) | Morgan | 2026-02-06 | ✅ |
| Junior Developer | Alex | 2026-02-06 | ✅ |
| Spec Author (PM) | Sam | 2026-02-06 | ✅ |
| Tester (QA Lead) | Riley | 2026-02-06 | ✅ |
| UX Consultant | Casey | 2026-02-06 | ✅ |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-03 | Sam | Initial draft |
| 1.1 | 2026-02-03 | Sam | Tech review updates: embedding model, single-call extraction, typing indicator, offline handling, export/import, schema versioning, data versioning, debug changelog, testing strategy |
| 2.0 | 2026-02-05 | Sam | Platform rewrite: updated for web-based UI and browser access |
| 3.0 | 2026-02-06 | Sam | **Product-only rewrite:** Removed all implementation/architecture details. Spec now defines *what* the product does, not *how* it’s built. Technical design is a separate engineering concern. Milestones restructured as vertical user-flow slices. Added Tester and UX Consultant to approval. || 4.1 | 2026-02-05 | Sam | Updated milestones M3/M4/M5 for single-call orchestration layering: M4 is now the structural transition to JSON output, M5 extends it with context deltas. Fixed F4.2 (LLM-decided search, not deterministic). Added F4.5. Fixed stale §4.3.6 reference → §4.3.9. M4 estimate 1wk → 2wk. |
| 4.2 | 2026-02-05 | Sam | Rebalanced context budget: RAG reduced from ~4–6K to ~2K tokens. Stable context is primary memory; RAG is supplementary (past conversation recall only). Total prompt ~9.5–10K, down from ~13–15K. Added explanatory note to §4.3.9 with user study evidence. |