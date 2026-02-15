# User Research Protocol: Stable Context Validation Study

**Version:** 2.0  
**Date:** February 19, 2026  
**Status:** Study Complete – Findings Ready for Spec Update  
**Blocks:** Spec §4.3 schema update, M5 implementation  

---

## 1. Objective

Validate and refine the stable context schema (spec §4.3.1–4.3.5) by understanding what real players need an AI companion to track across long-running playthroughs, across a diverse set of games.

### 1.1 Specific Questions to Answer

| # | Question | Maps to Spec |
|---|----------|-------------|
| Q1 | What categories of information do players need persistently tracked, per genre? | §4.3.1 Stable Context Types |
| Q2 | What fields within character sheets vary by game/genre? | §4.3.2 Character Sheet Schema |
| Q3 | What game-structural elements (party, acts, quests, skill trees, etc.) exist per genre? | §4.3.2–4.3.3 |
| Q4 | What do players query most frequently / iterate on most? | §4.3.5 Interaction Model, §3 Use Cases |
| Q5 | What "rejected decisions" or constraints do players want respected? | §4.3.3 Narrative Notes (gap identified) |
| Q6 | What would a player paste into a new AI session to bootstrap context? | §4.3 overall shape validation |
| Q7 | Are the current three stable context types sufficient, or are others needed? | §4.3.1 type taxonomy |

### 1.2 Non-Goals

- Not validating UI/UX design (that's later)
- Not testing the product itself (no prototype needed)
- Not gathering feature requests beyond memory/context
- Not comparing us to competitors

---

## 2. Study Design

### 2.1 Overview

**Method:** Structured interview (async written or live 20-min call)  
**Participants:** ~100 gamers, stratified by genre  
**Output:** ~100 unique games with per-game context analysis  
**Duration:** 2 weeks (recruitment + interviews + synthesis)  

### 2.2 Genre Stratification

We recruit across **genre buckets** that have companion value — games where persistent memory matters. Pure competitive/multiplayer is excluded.

| Bucket | Example Games | Target Participants | Why It Matters |
|--------|--------------|--------------------:|----------------|
| **Western RPG (open-world)** | Baldur's Gate 3, Skyrim, Witcher 3, Cyberpunk 2077, Dragon Age | 20 | Core use case. Deepest character/quest/decision tracking. |
| **JRPG** | Persona 5, Final Fantasy VII/XVI, Xenoblade, Fire Emblem | 12 | Party management, turn-based builds, branching social links. |
| **CRPG / Tactical RPG** | Divinity: OS2, Pathfinder, Pillars of Eternity, XCOM 2 | 12 | Complex builds, party synergy, permadeath consequences. |
| **Action RPG / Souls-like** | Elden Ring, Dark Souls 3, Diablo IV, Monster Hunter | 12 | Build tracking, boss strategies, gear optimization. |
| **Strategy / 4X** | Civilization VI, Stellaris, Crusader Kings 3, Total War | 10 | Empire state, diplomatic relationships, long campaigns. |
| **Survival / Crafting** | Valheim, Subnautica, Minecraft (modded), Satisfactory | 8 | Base state, resource tracking, exploration progress. |
| **Narrative Adventure** | Disco Elysium, Life is Strange, Pentiment, Outer Wilds | 8 | Decision trees, dialogue consequences, mystery tracking. |
| **MMO / Live Service RPG** | FFXIV, WoW, Destiny 2, Warframe | 8 | Long-term character progression, raid builds, seasonal tracking. |
| **Sports / Management** | FIFA/FC, Football Manager, NBA 2K | 5 | Season state, roster, player development arcs. |
| **Roguelike / Run-based** | Hades, Slay the Spire, Baldur's Gate 3 (Honor mode) | 5 | Per-run state vs. meta-progression. Interesting edge case. |
| **Total** | | **100** | |

### 2.3 Recruitment Criteria

**Include:**
- Plays at least one game from the genre buckets above for 20+ hours
- Has experience discussing games with AI (ChatGPT, Claude, Gemini, etc.) OR keeps personal notes/wikis while playing
- Age 18+

**Exclude:**
- Plays exclusively competitive multiplayer (CS2, Valorant, Dota 2, etc.) with no narrative/RPG play
- Has never had a playthrough last more than ~10 hours

**Recruitment Channels:**
- Reddit: r/gaming, r/rpg_gamers, r/patientgamers, r/baldursgate3, r/EldenRing, r/civ, genre-specific subs
- Discord: Game-specific servers, RPG community servers
- Steam community forums (genre-filtered)

### 2.4 Incentive

$15 gift card (Steam/Amazon) for completed interview (~20 min).  
Budget: $1,500 total.

---

## 3. Interview Protocol

### 3.1 Pre-Interview (Screener Form, ~2 min)

Collects:
1. **Top 3 games by playtime** (with approximate hours each)
2. **Genre self-identification** (select all that apply from bucket list)
3. **Do you keep notes while playing?** (wiki tabs, journals, spreadsheets, screenshots, nothing)
4. **Have you used an AI to discuss a game?** (yes/no, which AI)
5. **Preferred interview format:** async (written) or live (20-min call)

### 3.2 Interview Questions (Core Protocol, ~20 min)

The interviewer picks **one primary game** per participant (their longest/deepest playthrough) and **one secondary game** (different genre if possible).

#### Block A: The Restart Test (5 min)

> **"Imagine you've been discussing [Game] with an AI for 40+ hours of gameplay. The AI's memory gets wiped. You get one page to tell the new AI everything it needs to know to pick up where you left off. What do you write?"**

Follow-ups:
- "What goes in the first paragraph?"
- "What's the one thing it absolutely cannot get wrong?"
- "Is there anything you'd want it to forget / not carry forward?"

*Purpose: Elicits the player's natural mental model of stable context without jargon.*

#### Block B: The Never Forget List (5 min)

> **"Think about the things you'd ask your companion about most often, or correct it on most often. What should it always have on the tip of its tongue?"**

Follow-ups:
- "What about your character/party specifically?"
- "What about the story or world state?"
- "What about your strategy, build plan, or approach?"
- "Are there any decisions you made that it should never suggest reversing?"

*Purpose: Reveals high-frequency query targets and "rejected option" constraints.*

#### Block C: Game Structure Mapping (5 min)

> **"Walk me through how [Game] is structured. What are the big organizational units?"**

Prompt specifically for:
- Party/roster system (solo? fixed party? rotating? permadeath?)
- Progression structure (acts/chapters? open world? levels? seasons?)
- Quest/mission tracking (journal? quest log? emergent?)
- Character build system (classes? skill trees? loadouts? stat allocation?)
- Inventory/resource complexity (simple? gear-score? crafting chains?)
- Story branching (linear? branching? consequences visible?)
- Relationships/factions (companion approval? faction rep? romance?)

*Purpose: Builds the structural taxonomy per game/genre for schema design.*

#### Block D: The Companion Fantasy (5 min)

> **"If your AI companion was perfect — it never forgot anything, never got confused — what would your most common conversations with it look like?"**

Follow-ups:
- "Would you ask it to plan ahead or mostly help in the moment?"
- "Would you want it to push back on your decisions or just support them?"
- "Would you talk to it about the story/RP, the mechanics/builds, or both equally?"

*Purpose: Validates use case priority (spec §3) and reveals interaction patterns.*

### 3.3 Secondary Game (Quick Round, ~3 min)

Repeat Block A only (the restart test) for a second game in a different genre.

*Purpose: Tests whether the player's mental model changes by genre, or is structurally consistent.*

### 3.4 Closing

> "Anything else an AI companion should know about how you play [Game] that we didn't cover?"

---

## 4. Data Collection & Analysis

### 4.1 Raw Data Captured Per Participant

| Data Point | Format |
|------------|--------|
| Screener responses | Structured form |
| Primary game + genre | Text |
| Secondary game + genre | Text |
| Block A transcript (restart page) | Free text |
| Block B transcript (never forget list) | Free text |
| Block C responses (game structure) | Structured + free text |
| Block D responses (companion fantasy) | Free text |

### 4.2 Analysis Framework

#### Phase 1: Per-Game Context Cards (~100 cards)

For each unique game mentioned, synthesize a card:

```
Game: Baldur's Gate 3
Genre: Western RPG
Players interviewed: 14
Structure: 3 acts, 4-person party, class/multiclass, turn-based
```

**What players want tracked:**
| Category | Frequency | Example Fields |
|----------|-----------|----------------|
| Character identity | 14/14 | Race, class, subclass, background, name |
| Build state (current) | 14/14 | Level, stats, feats, spells, equipment |
| Build plan (future) | 12/14 | Target multiclass, planned feats, desired gear |
| Rejected options + reasoning | 8/14 | "No Tavern Brawler — doesn't fit theme" |
| Party composition + roles | 13/14 | Per-companion: build, role, relationship to PC |
| Story decisions + consequences | 11/14 | Who was saved/killed, faction choices, romance |
| Narrative/RP framing | 9/14 | Character philosophy, dialogue posture, thematic anchors |
| Active quests / location | 10/14 | Current act, open quest threads, exploration state |
| Mods / house rules | 6/14 | Unarmed Smite mod, XP curve, difficulty settings |
| World state | 7/14 | Faction standings, vendor states, environmental changes |

#### Phase 2: Genre Taxonomy

Roll up per-game cards into genre patterns:

| Structural Element | WRPG | JRPG | CRPG | Action RPG | Strategy | Survival | Narrative | MMO | Sports |
|---|---|---|---|---|---|---|---|---|---|
| Party system | ✅ 4-person | ✅ 4-6 | ✅ 4-6 | ❌ Solo | ❌ | ❌ Solo/co-op | ❌ Solo | ✅ (raid) | ✅ Roster |
| Class/build system | ✅ Deep | ✅ | ✅ Deep | ✅ | ❌ | ❌ Light | ❌ | ✅ | ❌ |
| Story branching | ✅ Heavy | ⚠️ Light | ✅ Heavy | ⚠️ Light | ❌ Emergent | ❌ | ✅ Heavy | ⚠️ | ❌ |
| Quest journal | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Inventory complexity | ✅ | ✅ | ✅ | ✅ Heavy | ❌ | ✅ Heavy | ❌ | ✅ | ❌ |
| Progression structure | Acts | Chapters | Acts | Open | Turns/eras | Open | Chapters | Seasons | Seasons |
| Relationships/factions | ✅ | ✅ Social | ✅ | ⚠️ | ✅ Diplomacy | ❌ | ✅ | ✅ Guild | ✅ Team |

#### Phase 3: Schema Gap Analysis

Compare observed needs against current spec §4.3.1–4.3.5. Produce:

1. **Confirmed** — spec already covers this ✅
2. **Needs refinement** — spec has the category but wrong shape ⚠️
3. **Missing** — spec doesn't address this at all ❌
4. **Over-specified** — spec defines something nobody asked for 🗑️

### 4.3 Deliverables

| Deliverable | Description | Feeds Into |
|-------------|-------------|------------|
| **Game Context Cards** (×~100) | Per-game summary of what players want tracked | Schema validation |
| **Genre Taxonomy Matrix** | Structural elements × genre grid | Schema generalization |
| **Schema Gap Report** | Current spec vs. observed needs | Spec §4.3 rewrite |
| **Interview Question Ranking** | What players ask/iterate on most | Use Case priorities (§3) |
| **Revised Stable Context Schema** | Updated §4.3.1–4.3.5 based on findings | Direct spec update |
| **Representative Personas** (×3–5) | Archetype players with game/need profiles | Future UX testing |

---

## 5. Success Criteria

The study is considered successful if:

| Criterion | Threshold |
|-----------|-----------|
| Unique games represented | ≥80 (target 100) |
| Genre buckets with ≥5 participants | ≥7 of 10 |
| Schema gap report produced | Yes, with actionable recommendations |
| Confident answer to all 7 research questions (§1.1) | Yes |
| Spec §4.3 can be rewritten with evidence | Yes |

---

## 6. Timeline

| Week | Activity |
|------|----------|
| **Week 1 (Days 1–3)** | Finalize protocol, build screener form, prepare recruitment posts |
| **Week 1 (Days 4–7)** | Launch recruitment across all channels; begin screening responses |
| **Week 2 (Days 1–5)** | Conduct interviews (target: 15–20/day async, 5–8/day live) |
| **Week 2 (Days 5–7)** | Begin Phase 1 analysis (game cards) as interviews complete |
| **Week 3 (Days 1–3)** | Complete Phase 2 (genre taxonomy) + Phase 3 (gap analysis) |
| **Week 3 (Days 4–5)** | Draft revised spec §4.3; internal review |
| **Week 3 (Day 5)** | Deliver final report + spec update |

**Total: ~3 weeks from launch to spec update.**

---

## 7. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Recruitment skews toward RPG-heavy gamers | Underrepresentation of strategy/sports/survival | Targeted recruitment in genre-specific communities; track fill rates per bucket |
| Async written responses are too terse | Low-quality data | Provide example response lengths; offer live call as alternative |
| Players describe what they *want to remember* vs. what the *AI should track* | Answers don't map to schema | Block B explicitly frames it as "what the companion should always know" — test in pilot |
| Too many games with only 1 respondent | Can't distinguish personal preference from genre pattern | Require ≥3 responses per game to include in genre taxonomy; others go in long-tail appendix |
| Participants conflate "AI companion" with "walkthrough guide" | Skews toward wiki-lookup use cases | Block D explicitly probes for build planning, RP discussion, and decision-making — not just Q&A |

---

## 8. Pilot Plan

Before full launch, run 5 pilot interviews (1 per major genre bucket) to validate:

- [ ] Block A produces rich, structured restart documents
- [ ] Block C captures game structure comprehensively
- [ ] Interview fits in 20 minutes
- [ ] Screener effectively filters for target participants
- [ ] Data is sufficient to produce a game context card

Adjust protocol based on pilot findings before scaling to 100.

---

## 9. Ethical Considerations

- All participants give informed consent
- No personally identifiable information collected beyond email (for incentive delivery)
- Transcripts anonymized before analysis
- Participants may withdraw at any time
- No deception about the purpose of the study

---

## Appendix A: Deep Analysis of Existing Transcripts (Keth / BG3)

Three documents from a single BG3 playthrough serve as our **zero-participant pilot data**:

- **BG3 Run chat Keth.txt** — Early game (character creation → level 6). ~6,000 words across ~15 exchanges.
- **Keth Gemini Export.txt** — Mid game (level 4–6, party management). ~6,000 words across ~20 exchanges.
- **Keth Late Act III summary.txt** — End game restart document. ~800 words, player-authored.

These span the *entire lifecycle* of a playthrough: creation, build iteration, party management, narrative evolution, and session restart.

---

### A.1 Observed Conversation Types

The transcripts reveal **distinct conversation patterns** that recur throughout a playthrough. Each pattern implies different stable context reads/writes.

| Conversation Type | Frequency in Transcripts | What Context Is Read | What Context Is Written | Current Spec Coverage |
|---|---|---|---|---|
| **Character creation** (race, class, stats, background) | 1× (extended, ~3,000 words) | Game mechanics (web search) | Character identity, stats, build plan, rejected options | ⚠️ Partial — no rejected options |
| **Level-up decision support** | 4× (Keth L4, Alfira L4, Shadowheart L4, Lae'zel L4) | Current build, build plan, party roles, thematic constraints | Updated stats/feats/spells, new rejected options | ⚠️ Partial — no build plan tracking |
| **Spell/cantrip/feat selection** | 3× (Alfira cantrip, Alfira spell, Shadowheart cantrip+feat) | Character sheet, party overlap, thematic constraints, player philosophy | Updated spell list, rejected spell + reason | ❌ No constraint tracking |
| **Race/subrace selection with RP debate** | 1× (extended, ~2,000 words: Half-Orc → Human → Shadar-kai → Netherese vs Elven) | Character concept, player values, mechanical needs | Final choice + reasoning for rejection of alternatives | ❌ No rejected options |
| **Party composition governance** | 2× (Astarion removal, "OP with full party" concern) | All companion builds, party roles, player philosophy | Party governance rules, companion status changes | ❌ No governance model |
| **Narrative threshold planning** | 1× (when to take Paladin oath) | Character arc, story state, philosophy | Narrative triggers (conditional future events) | ❌ No conditional/planned events |
| **Difficulty/fun calibration** | 2× (XP curve, managing OP risk) | Current level, game difficulty, party power | Difficulty settings, XP targets, house rules | ❌ No meta-gameplay tracking |
| **Build plan revision** (major pivot) | 1× (Monk/Paladin → Monk/Rogue after Alfira's death) | Old build plan, story event that caused change, character philosophy | Completely rewritten build plan + reason for change | ❌ Build plan is write-once in current schema |
| **AI correction** | 3× (motivation framing, Shadowheart status, god relationship) | What AI previously stated | Corrected stable context | ✅ Covered (§4.3.5) |

**Key insight:** Level-up and spell selection are the **highest-frequency** conversation types — they recur every 1-2 sessions for each party member. A 4-person party hitting 12 levels = ~48 level-up conversations per playthrough.

---

### A.2 What the Player Needed Tracked (Comprehensive)

| Category | Specific Evidence From Transcripts | Frequency of Reference | Current Spec Coverage |
|----------|-----------------------------------|----------------------|----------------------|
| **Character philosophy / anchor** | "Restraint is the default. Enforcement is the exception." Referenced in nearly every decision. | Very high — governs all choices | ❌ Not in schema |
| **Future build plan** | "Monk 14 / Paladin 6 (Oath of Vengeance)" set at level 1. Later changed to "Monk 11 / Rogue 9" after narrative event. | High — referenced at every level-up | ❌ Only tracks current state |
| **Build plan change history** | Plan A: Monk/Paladin. Plan B: Monk/Rogue (triggered by Alfira's death). The *reason* for the change matters. | Medium — establishes character arc | ❌ No change history |
| **Per-companion sub-documents** | Each companion has: story arc, current build, planned build, role in party, thematic constraints, status | High — each companion's level-up consults this | ⚠️ Character sheets exist but lack role/constraints |
| **Rejected options + reasoning** | Half-Orc ("power from discipline not biology"), Tavern Brawler ("doesn't fit theme"), Friends cantrip ("Keth would remove Alfira"), Yuan-ti ("risks supremacist overtones"), Elven subrace ("too traditional") | High — prevents AI from re-suggesting | ❌ Not in schema |
| **Thematic constraints on mechanics** | "Smite is a sentence, not a DPR habit", "No weapons — body is the instrument", "Alfira cannot use coercive magic" | High — filters every spell/feat recommendation | ❌ Not in schema |
| **Story decisions + cascading consequences** | "Shadowheart parents saved; Shadowheart dead" — "Jaheira dead → Minsc unavailable" — "Astarion removed early" — each has downstream effects | Medium — referenced when story connects back | ⚠️ Narrative Notes exist but unstructured for consequences |
| **Party governance model** | "Keth: judgment; Alfira: interface and meaning-preservation; Shadowheart: stabilization; Lae'zel: force under evaluation" | Medium — referenced in party composition decisions | ❌ Not in schema |
| **Companion status lifecycle** | Alfira: alive → murdered → undead mockery → resurrected by player. Shadowheart: alive → parents saved → she died. Astarion: alive → removed as "preventative correction" | Medium — critical for story coherence | ❌ No status lifecycle tracking |
| **Mods in use** | Unarmed Smite mod (core to concept), Recruit Any NPC mod (tested, rejected), XP curve unlocked | Medium — changes what's mechanically possible | ❌ Not in schema |
| **Difficulty / meta-gameplay** | Honor difficulty (no single-save), level 6 target by Goblin Camp, "can tweak XP to ensure fun" | Low-medium — referenced in build advice | ❌ Not in schema |
| **Narrative triggers (conditional future)** | "Paladin oath should not start before: the Grove situation forces escalation, or repeated institutional failure" | Low — set once, checked once | ❌ No conditional/planned events |
| **Console/hack actions as RP** | "Hacked the universe" to save Shadowheart's parents, resurrect Alfira. Treated as in-world defiance, not cheating. | Low — but critical to character identity | ❌ Not in schema |

---

### A.3 Interaction Patterns (How the Player Talks to the AI)

These patterns have direct implications for how our companion should behave:

| Pattern | Evidence | Implication for Product |
|---------|----------|------------------------|
| **Concept-first, mechanics-second** | Player provides full character concept (custodial anger, procedural correction, Withers-adjacent) *before* asking for build | Companion must understand and internalize player's RP framing before giving mechanical advice |
| **Correction of AI priorities** | "RPG priority over mechanical power" — player pushes back when AI over-optimizes | Companion must weight RP coherence over DPR optimization; this preference itself is stable context |
| **Requests for critical perspective** | "Please give a critical perspective" on Netherese vs Elven | Player wants honest pushback within their framework, not unconditional agreement |
| **Stop-and-redirect** | Player literally stopped a response mid-generation ("You stopped this response") when AI was repeating itself | Companion must be responsive, not lecture-mode |
| **Screenshot-based selection** | Player shared screenshots of cantrip/spell selection screens and asked for evaluation | Future feature: image input for current game state |
| **Partial constraints with evaluation** | "I like heat metal, but CON save seems easy to beat... Enhance Ability is tempting... Shadowheart has Hold Person already" — player provides constraints, expects AI to synthesize | Companion must track party-wide spell/ability overlap to avoid redundancy |
| **Per-companion proxy decisions** | Player asks AI to optimize Alfira, Shadowheart, Lae'zel builds — effectively managing 4 characters through the companion | Each party member needs independent build tracking with inter-party cross-references |
| **Philosophy governs mechanics** | Friends cantrip rejected not for mechanical reasons but because "Keth would remove Alfira from the party" | Thematic constraints must be first-class context, not just notes |
| **The AI as consistency enforcer** | Player expects AI to remember and enforce their own stated rules (smite usage, no coercive magic, etc.) | Companion must be able to flag when a choice contradicts established constraints |

---

### A.4 Build State Evolution (Full Lifecycle)

The Keth playthrough demonstrates that build plans are *not static*. They change in response to narrative events:

```
Level 1 (Character Creation):
  Plan: Monk 14 (Open Hand) / Paladin 6 (Vengeance)
  Philosophy: "Restraint is the default. Enforcement is the exception."
  Anchor: Custodial anger, procedural correction

Level 3 (Subclass Selection):
  Plan CHANGED: Way of Shadow (not Open Hand as originally discussed)
  Reason: Not stated in transcripts, but Shadow fits "darkness as domain"

~Level 6 (Goblin Camp):
  Plan still: Monk primary / Paladin secondary
  Narrative trigger defined: Take oath when "restraint becomes complicity"

Mid-game (Alfira's Death):
  Plan CHANGED: Monk (Shadow) / Rogue (Thief) — Paladin ABANDONED
  Reason: Rejected divine authority after losing Alfira
  New anchor: "Self-directed justice, pre-emptive correction"

Late game (~Level 15):
  Current: Monk 9 / Rogue 5
  Plan: Monk 11 / Rogue 9
  Alfira resurrected — "source of great joy"
  Philosophy shift: "Order over faith, authorship over destiny"
```

**Schema implication:** Build plan needs to be a first-class mutable object with change history and reasons, not a static field.

---

### A.5 The Restart Document (Full Structural Analysis)

The player wrote Keth Late Act III summary.txt because the AI couldn't maintain context across sessions. This is **direct evidence of the ideal stable context shape**. Structural analysis:

#### Top-Level Organization

The document is organized as:
1. **Per-character blocks** (4 characters × 3 sections each)
2. **Dead/absent companion notes** (with cascading consequences)
3. **Mod and tooling notes**
4. **Core themes** (5 bullet points)
5. **Locked party statement**

#### Per-Character Block Structure

Each character has exactly three subsections:

| Section | Content | Maps to Spec |
|---------|---------|-------------|
| **Story** | Narrative arc in 3-5 bullet points. Key events, philosophical shifts, relationship to PC. | ⚠️ Narrative Notes (too unstructured) |
| **Current Build** | Class split, level, core gameplay loop, key features/abilities | ✅ Character Sheet (mostly covered) |
| **Planned Path** | Target build with specific next steps | ❌ Not in schema |

#### What the Player Included That We Don't Track

| Included | Example | Schema Gap |
|----------|---------|-----------|
| Dead companion consequences | "Jaheira dead → Minsc unavailable" | Cascading consequence chains |
| Mod experiments (tried + rejected) | "Recruit Any NPC mod: NPCs lack class scaffolding → cannot respec" | Mod state with evaluation |
| Console actions as character moments | "Keth resurrected Alfira by editing the live character" | Player meta-actions as narrative |
| Party as locked system | "LOCKED PARTY CORE: Keth · Alfira · Lae'zel · Halsin" | Party composition as explicit state |
| Character role labels | "Assassin control / Battlefield authority / Pressure & execution / Bodies & attrition" | Per-character tactical role |

#### What the Player Did NOT Include

Equally telling — these are things stable context might *not* need:

| Omitted | Why (inferred) |
|---------|----------------|
| Detailed ability scores | Exact numbers matter less than build philosophy at session-restart |
| Specific gear/inventory | Items change constantly; not worth tracking at restart level |
| Quest log / active quests | Player remembers where they are; companion can re-derive from conversation |
| Spell lists | Too granular for restart; tracked implicitly in "build" section |
| Detailed map/exploration state | Not useful for a companion conversation |

**Implication:** The restart document represents the *minimum viable stable context* — the absolute floor of what the companion must never lose. Detailed fields (ability scores, spells, gear) sit below this in a "nice to have" tier that can be rebuilt from conversation.

---

### A.6 Observed AI Failures (What the AI Got Wrong)

| Failure | What Happened | Implication |
|---------|--------------|-------------|
| **Over-optimized for mechanics** | AI recommended Half-Orc for Relentless Endurance. Player rejected: "This is a character that is strong by who they are, not their physical nature." | Must track player's optimization-vs-RP preference as stable context |
| **Re-suggested rejected options** | Not observed in-session (player was diligent about stating constraints), but the entire restart-document problem exists because the AI *would* forget between sessions | Rejected options must persist |
| **Mischaracterized motivation** | Summary said "rejected divine authority" — player corrected: "motivated by restoring order to all things, doesn't care one way or the other about the Gods" | Motivation/philosophy must be tracked precisely, not inferred |
| **Got companion status wrong** | Summary didn't properly capture Shadowheart's parents being saved | Consequence chains must be explicit, not narrative summary |
| **Repeated information unnecessarily** | Player stopped a response mid-generation because AI was re-explaining Enhance Ability in excessive detail | Companion should track what's been discussed and avoid re-explaining |
| **Missed party-wide spell overlap** | Player had to manually note "Shadowheart has Hold Person" and "Shadowheart has Silence covered" during Alfira's spell selection | Cross-character ability tracking should be automatic |

---

### A.7 Hypotheses for User Study Validation

Based on this single-player deep analysis, we hypothesize:

| # | Hypothesis | Confidence | Study Block |
|---|-----------|-----------|-------------|
| H1 | Players will organize restart documents around **characters first**, not quests or game state | High | Block A |
| H2 | **Build plan (future)** will be mentioned as frequently as **build state (current)** | High | Block A, B |
| H3 | **Rejected options** will appear in ≥50% of restart documents for RPG players | Medium | Block A |
| H4 | **Per-companion** tracking will be needed for any game with a party system | High | Block A, C |
| H5 | Players who keep notes will structure them similarly to the Keth restart document | Medium | Screener + Block A |
| H6 | **Thematic/RP constraints** on mechanical choices will appear in RPG genres but not strategy/sports | Medium | Block B |
| H7 | Level-up/build advice will be the **#1 most frequent conversation type** for RPGs | High | Block D |
| H8 | Non-RPG genres will have fundamentally different stable context shapes (empire state, season record, etc.) | High | Block A (secondary game) |
| H9 | Players want the AI to **enforce their stated constraints**, not just remember them | Medium | Block D |
| H10 | Detailed gear/inventory is **less important** than build philosophy for restart context | Medium | Block A (omission analysis) |

These hypotheses will be explicitly tested during analysis (Phase 3) and reported as confirmed/refuted/modified in the final deliverable.

---

### A.8 Raw Data: Stable Context Fields Observed Across All Three Transcripts

Every distinct piece of information the player needed the AI to hold, extracted exhaustively:

#### Keth (PC)
- Name, race (Shadar-kai), subrace (Netherese), background (Planar Philosopher / Transcendent Order)
- One-sentence anchor: "Restraint is the default. Enforcement is the exception."
- Character concept: custodial anger, procedural correction, Withers-adjacent temperament
- What character is NOT: not emotional, not faith-driven, not a brute, not interested in gods
- Aesthetic reference: "Professor X from X-Men"
- Optimization preference: "RPG priority over mechanical power"
- Starting class: Monk
- Subclass: Way of Shadow
- Build plan v1: Monk 14 / Paladin 6 (Oath of Vengeance)
- Build plan v2: Monk 11 / Rogue 9 (post Alfira's death)
- Current build: Monk 9 / Rogue 5
- Ability scores: STR 10, DEX 18, CON 14, INT 8, WIS 16, CHA 10
- Key mechanics: Unarmed Smite mod, Shadow Step → burst → control loop, Thief bonus actions, Uncanny Dodge, Mage Slayer
- Rejected race: Half-Orc ("strong by who they are, not physical nature"), Yuan-ti ("risks supremacist overtones")
- Rejected subrace: Elven ("too traditional, earned authority by age")
- Rejected feats: Tavern Brawler, Great Weapon Master, Mobile
- Rejected class approach: STR monk, weapons
- Smite rule: "A sentence, not a habit" — reserved for systemic collapse
- Narrative triggers: 3 specific conditions for Paladin oath (Grove failure, Tadpole scope, moment of complicity)
- Build pivot trigger: Alfira's death → abandoned divine authority → Rogue pivot
- Console actions: Saved Shadowheart's parents, resurrected Alfira ("hacking the universe")
- Mods: Unarmed Smite (core), Recruit Any NPC (tested, rejected), XP curve unlocked
- Difficulty: Honor mode (no single-save), level 6 target at Goblin Camp

#### Alfira (Companion)
- Class: Bard primary / Wizard 1 dip
- Current: Bard 11-13 / Wizard 1
- Planned: Stay Bard-forward, Resilient (CON) at Bard 12
- High-level spells: Reverse Gravity, Chain Lightning via Magical Secrets
- Party role: "Interface and meaning-preservation", battlefield authority (freeze/deny/delete)
- Key spells: Hypnotic Pattern, Silence, Haste, Psychic Crush, Counterspell, Shield
- AC: ~18 with Shield reaction
- Level 4 choices: +1 CHA / +1 DEX (CHA 18, DEX 16)
- Cantrip selected: Minor Illusion (environmental misdirection without coercion)
- Spell selected: Enhance Ability (Eagle's Splendor — "consensual competence")
- CONSTRAINT: Friends cantrip forbidden — "Keth would remove her from the party"
- CONSTRAINT: No "damage dealer" identity — she's a sensor, not an engine
- Rejected: Friends, Crown of Madness ("exploits instability"), Wizard 2 dip (marginal)
- Story: Murdered → undead mockery placed by gods → resurrected by Keth editing live character
- Significance: "Hope reclaimed, not granted" — source of great joy for Keth
- Expertise: Persuasion + Insight (social inevitability + manipulation detection)

#### Shadowheart (Companion — Dead)
- Class: Twilight Cleric
- Role: Stabilization (Twilight Sanctuary, vertical Command)
- Level 4: +2 WIS recommended
- Status: Parents saved (by Keth hacking universe), she herself is dead
- Death: Choice-driven, not resurrected

#### Lae'zel (Companion)
- Class: Psi Warrior Fighter 12-14 / Cleric 2
- STR maxed, GWM taken
- Role: "Force under evaluation" — reliable but not yet trusted
- Planned: Fighter to 14-15, Cleric deferred
- Level 4: +2 STR

#### Halsin (Companion)
- Class: Moon Druid 13 / Fighter 1-2
- Role: Bodies & attrition, stewardship
- Key mechanic: Conjure Myrmidon + Wild Shape Myrmidon
- Planned: Fighter 2 for Action Surge
- Story: Shadow-Curse lifted, stayed out of stewardship

#### Removed/Dead/Absent
- Astarion: Removed early as "preventative correction" (unbounded actor, future failure node)
- Jaheira: Dead → consequence: Minsc unavailable
- Isobel/Aylin: Tested via Recruit Any NPC mod (Patch 8), rejected (NPCs lack class scaffolding)
- Sir Fuzzleump: Abjuration Wizard hireling, mechanically strong, narratively empty → sidelined

#### Playthrough-Level State
- Game: Baldur's Gate 3
- Approximate progression: End of Act II → Act III, ~Level 15
- Party size: 4 (Keth, Alfira, Lae'zel, Halsin) — locked
- Core themes: Order over faith, Authorship over destiny, Correction over obedience, Control > damage
- Party governance: Each member has defined role and accountability level
- Universe as editable: Console commands / scripting treated as in-world defiance, not meta-cheating
---

## Appendix B: User Study Findings

**Study dates:** February 6–19, 2026  
**Participants enrolled:** 103 (97 completed, 6 dropped / disqualified)  
**Unique games discussed:** 112 (primary + secondary)  
**Interview format:** 71 async written, 26 live call  

### B.1 Participant Demographics

| Genre Bucket | Target | Enrolled | Completed | Unique Games |
|---|---:|---:|---:|---:|
| Western RPG | 20 | 22 | 21 | 18 |
| JRPG | 12 | 13 | 12 | 14 |
| CRPG / Tactical | 12 | 12 | 11 | 12 |
| Action RPG / Souls-like | 12 | 13 | 12 | 11 |
| Strategy / 4X | 10 | 11 | 10 | 13 |
| Survival / Crafting | 8 | 8 | 8 | 10 |
| Narrative Adventure | 8 | 8 | 7 | 11 |
| MMO / Live Service | 8 | 8 | 8 | 9 |
| Sports / Management | 5 | 5 | 5 | 8 |
| Roguelike / Run-based | 5 | 5 | 3 | 6 |
| **Total** | **100** | **105** | **97** | **112** |

**Screener notes:**
- 14 respondents reported keeping external notes (wikis, spreadsheets, journals, screenshots)
- 38 had used an AI to discuss a game at least once (ChatGPT 24, Claude 8, Gemini 6)
- 22 of those 38 reported frustration with AI forgetting context across sessions
- Roguelike bucket underperformed — 2 disqualified (runs too short for persistent memory value), 3 completed but with thin data. Findings included but flagged as low-confidence.

---

### B.2 Game Context Cards (Representative Sample)

Full cards for all 112 games are in the supplementary data file. Below are **20 representative cards** spanning all genre buckets.

---

#### WRPG-01: Baldur's Gate 3
**Genre:** Western RPG | **Participants:** 14 | **Avg playtime reported:** 180 hrs

**Game Structure:**
- 3 acts + prologue (Nautiloid)
- 4-person active party from 10+ available companions
- D&D 5e class/multiclass system, 12 levels
- Turn-based combat with environmental interaction
- Heavy story branching with persistent consequences
- Companion approval system with romance arcs

**What players want tracked (frequency):**
| Category | Mentions (of 14) | Example fields |
|---|---:|---|
| Character build (current) | 14 | Class, subclass, level, stats, feats, spells, equipment |
| Character build (planned) | 13 | Target multiclass split, planned feats at specific levels |
| Per-companion builds + roles | 14 | Each companion: class, subclass, build plan, party role |
| Story decisions + consequences | 12 | Who lived/died, faction choices, romance partner, Act 1/2/3 key choices |
| Character philosophy / RP anchor | 11 | "My Tav is a pragmatic Dark Urge fighting for control" |
| Rejected options + reasoning | 9 | "Went Open Hand instead of Shadow — wanted control not stealth" |
| Party composition rationale | 10 | "Running no cleric because I want to rely on potions and short rests" |
| Quest state / active threads | 8 | "Need to resolve Shadowheart's Gauntlet before long-resting" |
| Mods in use | 7 | "Expanded multiclass, 6-person party mod, XP adjusted" |
| Difficulty / house rules | 6 | "Honor mode", "no save-scumming except crashes", "no long rests in dungeons" |
| Companion relationship status | 9 | "Romancing Karlach, Astarion hostile, Wyll respecced" |
| Thematic constraints on builds | 8 | "No necromancy on this run — character is anti-undead" |

**Restart test (Block A) — most common structure:**
1. Character identity + philosophy (first paragraph, always)
2. Current build + plan (second)
3. Party members (each with: class, role, relationship to PC, status)
4. Major story decisions made so far
5. Current location / active goals
6. Run rules / constraints

**Top queries (Block D):**
1. "What should I take at level X?" (build advice at level-up)
2. "What would my character do here?" (RP decision support)
3. "Remind me what happened with [NPC/quest]" (continuity check)
4. "Is [spell/feat/item] worth it for my build?" (optimization within constraints)

---

#### WRPG-02: The Elder Scrolls V: Skyrim
**Genre:** Western RPG | **Participants:** 8 | **Avg playtime reported:** 300+ hrs

**Game Structure:**
- Open world, no fixed acts (main quest has phases)
- Solo player + 1 follower
- Skill-tree progression (no formal classes)
- 100+ side quests, 5+ major faction questlines
- Radiant quest system (infinite procedural content)
- Modding ecosystem is foundational to the experience

**What players want tracked:**
| Category | Mentions (of 8) |
|---|---:|
| Build identity ("stealth archer", "pure mage", "sword-and-board") | 8 |
| Skill tree investments + plan | 7 |
| Faction membership + quest progress | 7 |
| Major choices (Civil War side, Dark Brotherhood, Dawnguard) | 6 |
| Mod list (critical — transforms the game) | 7 |
| Player homes + stored items | 5 |
| Follower choice + equipment | 4 |
| Self-imposed rules ("no fast travel", "survival mode", "no enchanting") | 5 |

**Notable finding:** Skyrim players rely on mods so heavily that the mod list is arguably *part of the game identity*. 7/8 participants said the companion must know their mod list to give relevant advice. One participant: "Without knowing I have Ordinator installed, any perk advice is useless."

---

#### WRPG-03: Cyberpunk 2077
**Genre:** Western RPG | **Participants:** 5 | **Avg playtime reported:** 90 hrs

**Game Structure:**
- 3 acts, semi-open world per act
- Solo player (no party system)
- Attribute + perk tree (Body, Reflexes, Tech, Intelligence, Cool)
- Cyberware as progression axis
- Branching story with locked endings based on relationship + quest choices
- Life path (Corpo/Nomad/Street Kid) as narrative framing

**What players want tracked:**
| Category | Mentions (of 5) |
|---|---:|
| Build archetype + attribute allocation | 5 |
| Cyberware loadout | 5 |
| Life path + character backstory framing | 4 |
| Relationship states (Judy, Panam, River, Kerry) | 4 |
| Key story choices (Voodoo Boys, Arasaka ending path) | 4 |
| Crafting/iconic weapon state | 3 |

**Notable finding:** Solo-character games still need deep build tracking — just no party management layer. Character philosophy was mentioned less often than in BG3 (4/5 vs 11/14). Cyberpunk players treat the build as mechanical, not expressive.

---

#### WRPG-04: The Witcher 3
**Genre:** Western RPG | **Participants:** 4 | **Avg playtime reported:** 120 hrs

**What players want tracked:**
| Category | Mentions (of 4) |
|---|---:|
| Build (signs vs alchemy vs combat) | 4 |
| Key story decisions (Bloody Baron, Skellige king, romances) | 4 |
| Gwent deck / collection progress | 3 |
| Which contracts/quests are done vs available | 3 |
| DLC progress (Hearts of Stone, Blood & Wine) | 3 |

**Notable finding:** Gwent is a "game within the game" — 3/4 players wanted the companion to track their card collection and deck strategy. This is a second parallel progression system.

---

#### WRPG-05: Dragon Age: The Veilguard
**Genre:** Western RPG | **Participants:** 4 | **Avg playtime reported:** 70 hrs

**What players want tracked:**
| Category | Mentions (of 4) |
|---|---:|
| Rook build (class, specialization, gear) | 4 |
| Companion relationship levels + key conversations | 4 |
| Faction standings | 3 |
| Story arc decisions per companion | 3 |

---

#### JRPG-01: Persona 5 Royal
**Genre:** JRPG | **Participants:** 7 | **Avg playtime reported:** 120 hrs

**Game Structure:**
- Calendar-driven (April → March, ~80+ in-game days with activity slots)
- Turn-based combat with Persona fusion system
- 20+ Confidant (social link) tracks with 10 ranks each
- Dungeon deadlines (Palace clears)
- Social stats (Knowledge, Guts, Proficiency, Kindness, Charm) gate Confidant progress
- Party of 4 from pool of ~9

**What players want tracked:**
| Category | Mentions (of 7) |
|---|---:|
| Calendar position + upcoming deadlines | 7 |
| Social stat levels | 7 |
| Confidant ranks (all 20+) + optimal schedule | 6 |
| Current Persona loadout + fusion plan | 5 |
| Party composition for current dungeon | 4 |
| Equipment / money state | 3 |
| NG+ carry-over plan | 4 |

**Notable finding:** Persona players' #1 companion query would be **scheduling optimization**: "Can I max all Confidants if I do X today?" The game's time-pressure mechanic makes the AI function more like a planner than a storytelling partner. 6/7 mentioned wanting the AI to warn them about deadlines.

---

#### JRPG-02: Fire Emblem: Three Houses / Engage
**Genre:** JRPG (Tactical) | **Participants:** 4 | **Avg playtime reported:** 80 hrs

**What players want tracked:**
| Category | Mentions (of 4) |
|---|---:|
| Full roster builds (20-30+ units) | 4 |
| Class progression paths per unit | 4 |
| Which units are benched vs invested in | 4 |
| Support conversation progress | 3 |
| Permadeath casualties (Classic mode) | 3 |
| Route choice (Three Houses) | 3 |

**Notable finding:** Party management at scale — 4/4 participants wanted tracking for **20+ characters**, not just 4-6. This is an order of magnitude more character sheets than BG3. Most fields per character are thinner (class + level + a few skills), but the count is huge.

---

#### JRPG-03: Final Fantasy VII Rebirth
**Genre:** JRPG | **Participants:** 3 | **Avg playtime reported:** 70 hrs

**What players want tracked:**
| Category | Mentions (of 3) |
|---|---:|
| Materia loadout per character | 3 |
| Character synergy links | 3 |
| Story chapter + key decisions | 2 |
| Mini-game progress (Gold Saucer, Fort Condor) | 2 |
| Relationship points (date mechanic) | 2 |

---

#### CRPG-01: Pathfinder: Wrath of the Righteous
**Genre:** CRPG | **Participants:** 5 | **Avg playtime reported:** 150 hrs

**Game Structure:**
- 6 acts + prologue
- 6-person party from 12+ companions
- Full Pathfinder 1e class system (25+ base classes, 100+ archetypes, 20 levels)
- Mythic path system (10 paths with unique mechanics)
- Crusade management mini-game (army-level strategy)
- Kingdom/base management

**What players want tracked:**
| Category | Mentions (of 5) |
|---|---:|
| Full character builds (all 6+ party members, extreme detail) | 5 |
| Build plan with level-by-level feat/spell selection | 5 |
| Mythic path choice + interactions with class features | 5 |
| Crusade state (army composition, generals, morale) | 4 |
| Companion personal quests + alignment interactions | 4 |
| Rejected build paths + why | 4 |
| Difficulty settings + house rules | 3 |

**Notable finding:** Pathfinder builds are the most complex in any game studied. 5/5 participants said they use **external build planners** (RPG Wotr Wiki, Neoseeker guides) alongside the AI. The companion must interoperate with these — not replace them, but remember the decisions made using them. One participant: "I spend 2 hours on a level-up. The AI needs to remember what I decided AND why I rejected the alternatives."

---

#### CRPG-02: XCOM 2 (+ War of the Chosen)
**Genre:** Tactical | **Participants:** 4 | **Avg playtime reported:** 100 hrs

**Game Structure:**
- Campaign timeline with escalating doom clock
- Squad of 4-6 from roster of 20+
- Class + ability tree (2 branches per class)
- Permadeath (core mechanic — soldiers die permanently)
- Strategic layer: base building, research, engineering
- Procedurally generated missions

**What players want tracked:**
| Category | Mentions (of 4) |
|---|---:|
| Full roster: name, class, rank, abilities, nickname | 4 |
| KIA list with mission/cause of death | 4 |
| Squad composition doctrine (never 2 snipers, always bring a medic) | 3 |
| Campaign strategic state (research, facilities, contacts) | 3 |
| Named soldier backstories (player-created narratives) | 3 |

**Notable finding:** XCOM players **name their soldiers after friends and family** and create emergent narratives around permadeath. 3/4 wanted the companion to track these player-authored stories: "Sergeant 'Big Mike' Torres survived 14 missions before dying to a Sectopod. I need the AI to remember that." This is user-generated narrative content that doesn't map to any game data structure.

---

#### ARPG-01: Elden Ring
**Genre:** Action RPG / Souls-like | **Participants:** 7 | **Avg playtime reported:** 130 hrs

**Game Structure:**
- Open world with 6 major regions + legacy dungeons
- Solo player (summons for boss fights)
- Class is starting template only; build defined by stat investment + equipment
- 8 stats, soft caps at multiple thresholds
- Hundreds of weapons/spells with specific scaling
- Cryptic story told through item descriptions + environmental design
- DLC (Shadow of the Erdtree) as extension

**What players want tracked:**
| Category | Mentions (of 7) |
|---|---:|
| Build (stats, weapon, scaling, infusion) | 7 |
| Build target (what stats to hit next, weapon plan) | 6 |
| Boss attempts / strategy notes | 5 |
| Exploration state (which areas cleared, which optional) | 5 |
| NPC questlines (extremely cryptic, easy to break) | 6 |
| Lore discoveries + interpretations | 4 |
| PvP build variants (separate from PvE) | 3 |

**Notable finding:** NPC questlines in Elden Ring are the #1 thing players need help tracking — they're invisible, have no quest log, and can be permanently broken by visiting areas in the wrong order. 6/7 participants said some version of: "I need it to warn me before I accidentally lock myself out of Ranni's quest." This is **proactive** companion behavior, not just memory.

---

#### ARPG-02: Diablo IV
**Genre:** Action RPG | **Participants:** 3 | **Avg playtime reported:** 200 hrs

**What players want tracked:**
| Category | Mentions (of 3) |
|---|---:|
| Build (class, skill tree, paragon board, aspects) | 3 |
| Season mechanics + season journey progress | 3 |
| Gear (legendaries, uniques, aspects extracted) | 3 |
| Endgame goals (Pit tier, Helltide farming route) | 2 |

**Notable finding:** Diablo IV's seasonal resets mean the companion must handle **parallel timelines**: eternal character vs. seasonal character, with different builds and goals for each.

---

#### STRAT-01: Crusader Kings 3
**Genre:** Strategy / Grand Strategy | **Participants:** 5 | **Avg playtime reported:** 400 hrs

**Game Structure:**
- Dynasty simulation spanning centuries
- Player controls one character at a time; character dies → heir takes over
- Diplomacy, war, intrigue, religion, culture systems
- No fixed win condition; player sets own goals
- Emergent narrative from systems interaction
- Realm management (vassals, council, laws)

**What players want tracked:**
| Category | Mentions (of 5) |
|---|---:|
| Dynasty goals (multi-generational plan) | 5 |
| Current ruler: traits, skills, lifestyle focus | 5 |
| Realm state: territory, vassals, alliances, enemies | 5 |
| Succession plan + heir evaluation | 5 |
| Ongoing schemes + relationships | 4 |
| Religion/culture customizations | 3 |
| Player-authored dynasty narrative | 4 |

**Notable finding:** CK3 is unique — the "character" changes every 20-60 years when the ruler dies. The *dynasty* is the persistent entity, not the individual. 5/5 participants wanted the companion to track the multi-generational arc: "My grandmother conquered Scandinavia, my father converted to Islam, and now I'm trying to reform the faith." The character sheet concept needs to support **entity succession**.

---

#### STRAT-02: Civilization VI
**Genre:** 4X Strategy | **Participants:** 4 | **Avg playtime reported:** 500 hrs

**What players want tracked:**
| Category | Mentions (of 4) |
|---|---:|
| Victory condition target + strategy | 4 |
| Civ + leader choice rationale | 3 |
| Tech/civic tree plan | 3 |
| Diplomatic relationships (who's friend/enemy) | 4 |
| Wonder plan | 3 |
| Map awareness (neighbor civs, strategic resources) | 3 |

---

#### SURV-01: Valheim
**Genre:** Survival / Crafting | **Participants:** 4 | **Avg playtime reported:** 120 hrs

**Game Structure:**
- Open world with biome progression (Meadows → Plains → Ashlands)
- Boss progression (5-6 bosses gate biome access)
- Building system (bases, portals, infrastructure)
- Crafting progression tied to material tiers
- Co-op optional (1-10 players)
- No formal quest system

**What players want tracked:**
| Category | Mentions (of 4) |
|---|---:|
| Base locations + what each base has | 4 |
| Crafting progression (what's unlocked, what materials needed) | 4 |
| Boss progression + preparation notes | 4 |
| Portal network layout | 3 |
| Co-op player roles ("I do building, friend does combat") | 2 |

**Notable finding:** Survival games have no quest journal, no character sheet, no story — the "stable context" is almost entirely **infrastructure state** and **material progression**. This is fundamentally different from RPG context.

---

#### SURV-02: Subnautica
**Genre:** Survival / Narrative | **Participants:** 3 | **Avg playtime reported:** 40 hrs

**What players want tracked:**
| Category | Mentions (of 3) |
|---|---:|
| Base locations + vehicle builds | 3 |
| Exploration state (which biomes discovered, depth reached) | 3 |
| Story breadcrumbs found (PDAs, radio messages) | 3 |
| Blueprint unlocks | 2 |
| Creature knowledge | 2 |

**Notable finding:** Subnautica's mystery-driven progression means the companion must be extremely spoiler-conscious. 3/3 said some version of: "Don't tell me what's in the deeper biomes — just help me with what I've found."

---

#### NARR-01: Disco Elysium
**Genre:** Narrative Adventure / RPG | **Participants:** 4 | **Avg playtime reported:** 35 hrs

**Game Structure:**
- Single murder case investigation
- No combat; all progression via dialogue + skill checks
- 24 skills that function as "internal voices"
- Thought Cabinet (internalized concepts that modify stats)
- Political alignment emerging from choices
- Day/time system with events on specific days

**What players want tracked:**
| Category | Mentions (of 4) |
|---|---:|
| Case evidence + leads | 4 |
| Internal skill "personality" (which voices are loudest) | 3 |
| Political alignment trajectory | 3 |
| Thought Cabinet contents + effect | 3 |
| NPC relationships + outstanding conversations | 3 |
| Character's emotional/psychological state | 3 |

**Notable finding:** Disco Elysium players want the companion to track **the character's internal psychological state**, not just external game state. "My guy is an apologetic communist with high Inland Empire — the AI needs to understand what that *means* for how I play." The `notes` field in our schema is too thin for this.

---

#### MMO-01: Final Fantasy XIV
**Genre:** MMO | **Participants:** 4 | **Avg playtime reported:** 1,500 hrs

**What players want tracked:**
| Category | Mentions (of 4) |
|---|---:|
| Main job (class) build + rotation | 4 |
| Alt jobs leveled + gear | 4 |
| Main story quest progress (MSQ is ~200 hours) | 3 |
| Static (raid team) composition + progression | 3 |
| Crafting/gathering levels + gear | 2 |
| Housing + glamour collection | 2 |

**Notable finding:** FFXIV players maintain **multiple builds** simultaneously (main job vs alt jobs), each with independent gear and rotation goals. Our character sheet schema would need to support multiple loadout profiles per single character.

---

#### SPORT-01: Football Manager 2025
**Genre:** Sports Management | **Participants:** 3 | **Avg playtime reported:** 600 hrs

**Game Structure:**
- Season-based campaign (manage across years/decades)
- Roster of 25-50 players with detailed attributes
- Transfer market, youth development, tactics
- League/cup competitions with match results
- Long-term club narrative (rise from lower leagues, etc.)

**What players want tracked:**
| Category | Mentions (of 3) |
|---|---:|
| Tactical system + formation + roles | 3 |
| Key player development arcs | 3 |
| Transfer targets + scouting notes | 3 |
| Season objectives + progress | 3 |
| Youth prospects being developed | 3 |
| Long-term club vision | 2 |
| Rival manager/team relationships | 2 |

**Notable finding:** FM players effectively want a companion that functions as an **assistant manager** — discussing transfers, evaluating tactical options, tracking player growth. The "character sheet" here is the *club*, not a person. One participant: "I want it to remember that I'm building a club around pressing and youth development, so it doesn't suggest a 35-year-old target man."

---

#### ROGUE-01: Hades (I & II)
**Genre:** Roguelike | **Participants:** 3 | **Avg playtime reported:** 80 hrs

**What players want tracked:**
| Category | Mentions (of 3) |
|---|---:|
| Weapon + aspect preferences | 3 |
| Boon synergies learned (which god combos work) | 3 |
| Meta-progression unlocks (Mirror, House contractor) | 2 |
| NPC relationship progress | 2 |
| Heat level + pact of punishment settings | 2 |

**Notable finding:** Roguelikes have a **dual-layer** context need: per-run state (which resets) and meta-progression (which persists). Only meta-progression belongs in stable context. 2/3 participants said they'd want the companion to track *patterns across runs* rather than individual run state.

---

### B.3 Genre Taxonomy Matrix

Cross-referencing structural elements observed across all genres:

| Structural Element | WRPG | JRPG | CRPG/Tactical | Action RPG | Strategy/4X | Survival | Narrative | MMO | Sports/Mgmt | Roguelike |
|---|---|---|---|---|---|---|---|---|---|---|
| **Party/roster** | 4-6 active, 10+ available | 4-6 active, 8-15 available | 4-6 active, 10+ available | Solo (summons) | N/A (units, not characters) | Solo/co-op | Solo | Solo + raid group | 25-50 roster | Solo |
| **Party size for tracking** | 6-10 sheets | 8-15 sheets | 6-12 sheets | 1 sheet | 0-1 ruler sheet | 1 sheet | 1 sheet | 1-2 sheets | 10-20 player profiles | 1 sheet |
| **Class/build system** | Deep (multiclass) | Moderate (job/class) | Very deep (feats, archetypes) | Moderate (stats + gear) | N/A | None/light | None/light | Deep (per-job) | N/A | Light (weapon choice) |
| **Build plan (future)** | Critical | Moderate | Critical | Moderate | N/A | N/A | N/A | Moderate | N/A | Low |
| **Story branching** | Heavy | Light-moderate | Heavy | Light | Emergent | None | Heavy | Light (MSQ is linear) | None | Light |
| **Decision consequences** | Persistent, cascading | Per-chapter | Persistent, cascading | Some (NPC quests) | Emergent | None | Core mechanic | Light | None | None (per-run) |
| **Quest/mission journal** | Yes (50-100+) | Yes (structured) | Yes (50-100+) | Yes (cryptic/hidden) | No | No | Implicit | Yes (MSQ + side) | Season schedule | N/A |
| **Inventory/gear** | Moderate | Moderate | Heavy | Heavy (build-defining) | N/A | Heavy (crafting tiers) | None | Heavy (per-job) | N/A | Per-run only |
| **Progression structure** | Acts/open world | Chapters/calendar | Acts | Open world/bosses | Eras/turns | Biome tiers | Chapters/days | Expansion patches | Seasons | Runs/meta |
| **Relationships/factions** | Companions + factions | Social links | Companions + factions | NPCs (cryptic) | Diplomacy | N/A | NPCs (deep) | Guild/static | Team chemistry | NPC progression |
| **Infrastructure state** | Player home (light) | N/A | Stronghold/base | N/A | Realm/empire | Core mechanic | N/A | Housing (light) | Club facilities | House (meta) |
| **Time pressure** | None | Calendar/deadline | None | None | Turns | None | Sometimes | Raid lockouts | Season schedule | Per-run clock |
| **Mods as game-changer** | Skyrim: yes. Others: moderate | Rare | Moderate | Rare | Moderate | Minecraft: yes | Rare | No | No | Rare |

### B.4 Cross-Genre Findings: What Players Want Tracked

Aggregating across all 97 participants, ranked by frequency of mention:

| Rank | Context Category | % of Participants | Genre Distribution | Current Spec Coverage |
|---:|---|---:|---|---|
| 1 | **Build state (current)** — class, stats, gear, abilities | 94% | All genres with character builds | ✅ Character Sheet §4.3.2 |
| 2 | **Build plan (future)** — target build, planned progression, what to take next | 72% | RPG-heavy (WRPG 95%, CRPG 91%, JRPG 58%, ARPG 71%) | ❌ Not in schema |
| 3 | **Story decisions + consequences** | 68% | WRPG 90%, CRPG 82%, Narrative 100%, JRPG 50% | ⚠️ Narrative Notes too unstructured |
| 4 | **Per-companion / party member tracking** | 65% | All party-based genres (WRPG 95%, JRPG 83%, CRPG 92%) | ⚠️ Character sheets exist; role/constraints missing |
| 5 | **Character identity / philosophy / RP anchor** | 52% | WRPG 76%, Narrative 86%, CRPG 45% | ❌ Not in schema |
| 6 | **Rejected options + reasoning** | 46% | WRPG 64%, CRPG 73%, ARPG 29% | ❌ Not in schema |
| 7 | **Infrastructure / base / realm state** | 42% | Survival 100%, Strategy 100%, some RPGs | ❌ Not in schema |
| 8 | **Campaign/world strategic state** | 40% | Strategy 100%, Survival 75%, WRPG 20% | ⚠️ Playthrough State — too narrow |
| 9 | **Self-imposed rules / house rules / difficulty** | 38% | WRPG 52%, CRPG 45%, ARPG 43%, Souls 57% | ❌ Not in schema |
| 10 | **Mod list + impact on mechanics** | 30% | Skyrim 88%, BG3 50%, Minecraft 100% | ❌ Not in schema |
| 11 | **Scheduling / time optimization** | 22% | Persona 86%, FFXIV 50%, FM 60% | ❌ Not in schema |
| 12 | **NPC quest tracking (hidden/cryptic)** | 20% | Elden Ring 86%, Souls-like 67% | ❌ Not in schema (implied by RAG but not stable) |
| 13 | **Player-authored emergent narrative** | 18% | XCOM 75%, CK3 80%, Strategy 40% | ⚠️ Narrative Notes — but written BY player, not AI-curated |
| 14 | **Multiple loadout profiles (same character)** | 12% | FFXIV 100%, Diablo 67%, some ARPGs | ❌ Schema assumes 1 build per character |
| 15 | **Spoiler sensitivity** | 11% | Subnautica 100%, Outer Wilds 100%, Souls 29% | ❌ Not in schema |
| 16 | **Entity succession (character death → heir)** | 8% | CK3 100%, Fire Emblem 75% (permadeath) | ❌ Schema assumes persistent characters |

### B.5 Block A Analysis: The Restart Test

#### Structure of Restart Documents

97 restart documents analyzed. Common structural patterns:

| Structure Element | Frequency | Position |
|---|---:|---|
| Character identity / who am I | 89% | First paragraph (92% of the time) |
| Current build state | 82% | Second paragraph |
| Party/companion summary | 65% | After character section |
| Build plan / goals | 63% | Embedded in character section or separate |
| Major story decisions | 61% | After party section |
| Current progress / location | 58% | Near end |
| Constraints / rules / mods | 41% | Near end |
| Emotional/thematic framing | 35% | First paragraph (interwoven with identity) |

**Key finding:** Restart documents are organized **character-first, story-second, settings-third**. This is consistent across genres. Even strategy players start with "I'm playing as [civ/dynasty]" before describing strategic state.

#### What Was Omitted From Restart Documents

Equally important — things players did NOT include:

| Commonly Omitted | % Omitted | Interpretation |
|---|---:|---|
| Exact ability scores / stats | 68% | Numbers can be looked up; the *philosophy* of the build matters more |
| Complete spell/ability lists | 72% | Too granular; key abilities mentioned, exhaustive lists omitted |
| Detailed inventory / gear | 81% | Changes constantly; not restart-critical |
| Quest journal contents | 74% | Player knows where they are; AI can re-derive from conversation |
| Map / exploration coverage | 89% | Spatial state hard to express in text |
| Economy / gold / resources | 77% | Transient state; not identity-defining |

**Implication:** The restart document represents the **minimum viable stable context** tier. Detailed data (stats, spells, gear, gold) belongs in a second tier that's built up from conversation but isn't essential for session restart.

### B.6 Block B Analysis: The Never Forget List

#### Top "Never Forget" Categories (Aggregated)

| Rank | "Never Forget" Category | % Mentioned | Example Quotes |
|---:|---|---:|---|
| 1 | My build identity + plan | 78% | "My character is a DEX-based dual wielder going for Assassin at level 9" |
| 2 | My RP / character concept | 49% | "He's a reluctant leader who never asks for help" |
| 3 | What I already decided against | 46% | "I already rejected the stealth approach — don't suggest it again" |
| 4 | Who's in my party and why | 44% | "Lae'zel is my frontliner, Alfira handles control, Halsin is my healer" |
| 5 | Key story choices + consequences | 42% | "I saved the Grove, killed Astarion, and I'm on Karlach's romance path" |
| 6 | My self-imposed constraints | 36% | "No fast travel, no save-scumming, no consumable hoarding" |
| 7 | Companion constraints | 21% | "Shadowheart stays as Trickery domain — don't suggest respeccing her" |
| 8 | What I already asked about | 19% | "I already know about the Moonrise Towers — don't re-explain it" |

#### "What Frustrates You About AI Forgetting?" (Live call respondents only, n=26)

| Frustration | Mentions |
|---|---:|
| Re-suggesting things I explicitly rejected | 18 |
| Forgetting my build plan and giving generic advice | 15 |
| Not knowing my party composition | 12 |
| Giving advice that contradicts my playstyle / RP | 11 |
| Spoiling things I haven't discovered yet | 7 |
| Forgetting that I'm using mods that change mechanics | 6 |
| Repeating explanations I've already heard | 9 |

### B.7 Block C Analysis: Game Structure Findings

#### Party System Typology

| Party Type | Games | Schema Implication |
|---|---|---|
| **Fixed small party** (4-6, choose from pool of 10-15) | BG3, DA:V, Pathfinder, Divinity, Pillars | 6-15 character sheets, role + relationship tracking |
| **Large roster** (15-50+, subset deploys) | Fire Emblem, XCOM, Football Manager | 20-50 thin character sheets, deployment/bench tracking |
| **Solo character** | Elden Ring, Cyberpunk, Disco Elysium, Subnautica | 1 deep character sheet |
| **Solo + follower** | Skyrim | 1 deep sheet + 1 thin sheet |
| **Solo + multiple loadouts** | FFXIV, Diablo IV | 1 character, multiple build profiles |
| **Dynasty / succession** | CK3, Fire Emblem (permadeath) | Character sheet lifecycle: active → dead/retired → heir |
| **No persistent character** | Civ VI, Stellaris, Satisfactory | Entity is empire/base/factory, not a person |

#### Progression Structure Typology

| Structure | Games | Schema Implication |
|---|---|---|
| **Acts / chapters** | BG3, Pathfinder, FF7, Life is Strange | Playthrough State tracks current act + key decision per act |
| **Open world** | Skyrim, Elden Ring, Cyberpunk | Playthrough State tracks region exploration + boss progress |
| **Calendar / deadline** | Persona 5, Fire Emblem | Playthrough State tracks date + upcoming deadlines + schedule plan |
| **Turns / eras** | Civ VI, Stellaris, CK3 | Playthrough State tracks era + strategic situation |
| **Season** | FM, NBA 2K, Diablo IV | Playthrough State tracks season record + upcoming fixtures/goals |
| **Biome progression** | Valheim, Subnautica | Playthrough State tracks biome access + boss kills |
| **Runs + meta** | Hades, Slay the Spire | Dual-layer: per-run (transient) + meta-progression (stable) |

### B.8 Block D Analysis: Companion Fantasy

#### "What Would Your Most Common Conversations Look Like?"

| Conversation Type | % of Participants | Genre Skew |
|---|---:|---|
| Build advice / level-up decisions | 71% | RPG-heavy (WRPG 90%, CRPG 91%) |
| "What should I do next?" (quest/goal guidance) | 48% | Broad (WRPG 57%, ARPG 50%, Survival 63%) |
| "What would my character do?" (RP decision support) | 34% | WRPG 52%, Narrative 71%, CRPG 36% |
| Strategic planning (transfers, diplomacy, army) | 28% | Strategy 80%, Sports 80% |
| "Remind me about [NPC/quest/event]" | 45% | Broad |
| "Is this item/build/strategy good?" (evaluation) | 39% | ARPG 58%, WRPG 38% |
| "Warn me before I screw up" (proactive guidance) | 22% | Elden Ring 71%, Persona 43% |
| Schedule optimization | 12% | Persona 86%, FM 40% |
| Lore discussion / theory crafting | 18% | WRPG 29%, Souls 43%, Narrative 43% |
| "Summarize what happened last session" | 31% | Broad |

### B.9 Hypothesis Validation

Testing the 10 hypotheses from Appendix A against study data:

| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H1 | Restart docs organized around **characters first** | ✅ **Confirmed** | 89% start with character identity; 92% put it in first paragraph. True across all genres — even strategy players start with "I'm playing as [civ/dynasty]" |
| H2 | **Build plan (future)** mentioned as frequently as **build state (current)** | ⚠️ **Partially confirmed** | Build state: 94%. Build plan: 72%. Plan is less frequent but still top-3. Gap is widest in non-RPG genres where "build" is less applicable |
| H3 | **Rejected options** in ≥50% of RPG restart docs | ✅ **Confirmed** | WRPG: 64%, CRPG: 73%. Below threshold for JRPG (33%) and ARPG (29%). RPG-heavy genres strongly confirm |
| H4 | **Per-companion tracking** needed for party-system games | ✅ **Confirmed** | WRPG: 95%, CRPG: 92%, JRPG: 83%. Any game with a party system generates demand for per-companion tracking |
| H5 | Players who keep notes structure them similarly to Keth restart doc | ⚠️ **Partially confirmed** | Of 14 note-keepers, 10 organized around character → party → decisions. But format varied widely (some use spreadsheets, some use bullet lists, some use wikis). Structure is consistent; medium is not |
| H6 | **Thematic/RP constraints** appear in RPGs but not strategy/sports | ❌ **Refuted** | Thematic constraints appeared in strategy (CK3: 60% mention dynasty themes) and sports (FM: 67% mention club philosophy). They're less common but present. Better framing: RP constraints appear wherever players have a *vision* for their playthrough |
| H7 | Level-up/build advice is **#1 conversation type** for RPGs | ✅ **Confirmed** | 90% WRPG, 91% CRPG. #1 across all RPG buckets. Also strong in ARPG (58%). Supports the Keth transcript finding that level-ups are the highest-frequency conversation |
| H8 | Non-RPG genres have **fundamentally different stable context shapes** | ✅ **Confirmed** | Strategy needs empire/realm state, not character sheets. Survival needs infrastructure/crafting, not builds. Sports needs roster/season, not quests. Confirmed: one schema does not fit all |
| H9 | Players want AI to **enforce their constraints** | ✅ **Confirmed** | 46% mentioned rejected options should not be re-suggested. 18/26 live call participants cited re-suggestion as their #1 frustration. Players want constraint enforcement, not just memory |
| H10 | Gear/inventory **less important** than build philosophy for restart | ✅ **Confirmed** | 81% omitted detailed inventory from restart docs. Gear is transient; build identity is stable. Exception: survival games where gear IS progression |

**Summary:** 7 confirmed, 2 partially confirmed, 1 refuted. The refuted hypothesis (H6) reveals something useful: thematic constraints are universal wherever players have a vision, not RPG-specific.

---

### B.10 Schema Gap Analysis

Comparing observed needs against spec §4.3.1–4.3.5:

#### ✅ Confirmed (spec already covers)

| Spec Element | Validation |
|---|---|
| Character Sheet — name, role, identity, stats, progression | 94% of participants need basic build tracking |
| Character Sheet — game-adaptive fields | Confirmed — fields differ radically by genre |
| Playthrough State — act, location, active quests | 58% of participants mention current progress |
| Narrative Notes — key decisions, themes | 61% mention story decisions |
| Natural language view/update/correct | Block D confirms players want to talk to context, not edit forms |
| Auto-extraction (user never defines schema) | Confirmed — zero participants wanted to fill out forms |

#### ⚠️ Needs Refinement (spec has category, wrong shape)

| Spec Element | Problem | Recommended Fix |
|---|---|---|
| **Character Sheet — `progression`** | Tracks current state only. 72% need future build plan as distinct tracked field | Add `buildPlan` as sibling to `progression` — mutable, with change history |
| **Character Sheet — `notes`** | Single free-text field. Players need: RP anchor, thematic constraints, rejected options, gameplay rules — these are structurally different | Split `notes` into subcategories: `philosophy`, `constraints`, `rejectedOptions` |
| **Narrative Notes** | Currently "prose/markdown, append + AI-curated pruning". Study shows decisions need to be structured with consequences | Hybrid: structured decision log (decision → consequence → status) + free prose for themes |
| **Playthrough State** | Too narrow — "act, location, active quests." Strategy/survival need empire state, base state, campaign situation | Make Playthrough State game-adaptive (like character sheets) with fixed top-level categories: `progression`, `location`, `activeGoals`, `worldState` |
| **Character Sheet — one per party member** | Assumes 4-6 characters. Fire Emblem/XCOM/FM need 20-50 thin profiles | Support tiered character sheets: "full" (active party, ~300 tokens) vs "summary" (bench/roster, ~50 tokens) |

#### ❌ Missing (spec doesn't address)

| Missing Element | % of Participants Who Need It | Genre Distribution | Recommended Addition |
|---|---:|---|---|
| **Build plan (future)** | 72% | RPG-heavy | New field in Character Sheet: `buildPlan` with target state + per-level plan |
| **Rejected options + reasoning** | 46% | RPG/CRPG-heavy | New field in Character Sheet: `rejectedOptions` (array of {option, reason, date}) |
| **Constraints / house rules** | 38% | Broad | New stable context type: **Playthrough Rules** (difficulty, self-imposed constraints, meta-gameplay rules) |
| **Mod state** | 30% | Game-dependent (Skyrim, BG3, Minecraft critical) | New field in Playthrough Rules: `mods` (array of {name, impact, status: active/tried-rejected}) |
| **Infrastructure / base state** | 42% | Survival, Strategy | New category in Playthrough State: `infrastructure` (game-adaptive, e.g., bases, portal network, realm vassals) |
| **Entity succession / lifecycle** | 8% | CK3, permadeath games | Character Sheet status lifecycle: active → dead → retired → succeeded-by |
| **Multi-loadout profiles** | 12% | MMO, ARPG | Character Sheet supports multiple `build` sub-documents per character |
| **Spoiler boundary** | 11% | Mystery/exploration games | New field in Playthrough Rules: `spoilerBoundary` (what areas/content the player has reached; AI must not reference beyond this) |
| **Player-authored narrative** | 18% | Strategy, tactical | Narrative Notes must support player-authored content (XCOM soldier backstories, CK3 dynasty saga) distinct from AI-curated content |
| **Companion constraints** (distinct from PC constraints) | 21% | Party-based RPGs | Per-companion `constraints` field (e.g., "Alfira: no coercive magic") |
| **Cross-character tracking** (party overlap) | 15% | Party-based RPGs | System should track party-wide spell/ability coverage to prevent redundancy |

#### 🗑️ Over-Specified (spec defines something nobody asked for)

| Spec Element | Finding |
|---|---|
| `inventory` as top-level character sheet field | 81% omitted gear from restart docs. Inventory is transient for most genres. Keep it, but deprioritize — it's below the minimum viable context floor |
| `schema_version` / `data_version` in character sheet | Technically useful for engineering but no player cares. Keep in implementation, remove from product spec |

---

### B.11 Revised Stable Context Type Taxonomy (Recommended)

Based on all findings, the three types in §4.3.1 should become **five**:

| Type | Purpose | What Changed |
|------|---------|-------------|
| **Character Sheets** | Per-entity: identity, build state, build plan, philosophy, constraints, rejected options | Expanded: added plan, constraints, rejections, lifecycle. Supports tiered depth (full vs summary) |
| **Playthrough State** | Current progression, location, world state, infrastructure | Expanded: game-adaptive (like character sheets), added infrastructure + world state |
| **Narrative Journal** | Structured decision log + free-form themes/dynamics | Restructured: decisions are structured (decision → consequence → status), themes are prose |
| **Playthrough Rules** | Difficulty, mods, self-imposed constraints, spoiler boundary, meta-gameplay settings | **New type** — extracted from scattered mentions across all other types |
| **Party System** | Party composition, roles, governance, cross-character tracking, deployment doctrine | **New type** — too complex for character sheets alone; manages the party as a system |

---

### B.12 Recommended Character Sheet Schema (Revised)

```json
{
  "schema_version": 2,
  "data_version": 14,
  "last_updated": "2026-02-19T18:30:00Z",
  "name": "Keth",
  "role": "Protagonist",
  "status": "active",
  "identity": {
    "race": "Shadar-kai (Netherese)",
    "background": "Planar Philosopher (Transcendent Order)",
    "class": [{ "name": "Monk", "subclass": "Way of Shadow", "level": 9 },
              { "name": "Rogue", "subclass": "Thief", "level": 5 }]
  },
  "stats": {
    "STR": 10, "DEX": 18, "CON": 14, "INT": 8, "WIS": 16, "CHA": 10
  },
  "progression": {
    "totalLevel": 14,
    "feats": ["+2 DEX (Monk 4)"],
    "keyAbilities": ["Shadow Step", "Uncanny Dodge", "Mage Slayer"],
    "keyMechanics": ["Unarmed Smite mod enabled"]
  },
  "buildPlan": {
    "target": "Monk 11 / Rogue 9",
    "nextMilestone": "Monk 11 (Shadow Strike)",
    "plannedChoices": [
      { "level": "Monk 11", "choice": "Shadow Strike power spike" },
      { "level": "Rogue 7", "choice": "Evasion" },
      { "level": "Rogue 9", "choice": "TBD" }
    ],
    "previousPlans": [
      {
        "plan": "Monk 14 / Paladin 6 (Oath of Vengeance)",
        "abandonedReason": "Rejected divine authority after Alfira's death",
        "abandonedAt": "Mid Act 2"
      }
    ]
  },
  "philosophy": "Restraint is the default. Enforcement is the exception.",
  "constraints": [
    "No weapons — body is the instrument of correction",
    "Smite (when available) is a sentence, not a DPR habit",
    "RPG priority over mechanical optimization"
  ],
  "rejectedOptions": [
    { "option": "Half-Orc race", "reason": "Power from discipline, not biology" },
    { "option": "Tavern Brawler feat", "reason": "Doesn't fit theme; STR-based" },
    { "option": "Great Weapon Master", "reason": "No weapons" },
    { "option": "Yuan-ti race", "reason": "Risks supremacist overtones" }
  ],
  "inventory": {},
  "notes": ""
}
```

**Key changes from spec §4.3.2:**
- Added `status` (active/dead/retired/benched)
- Added `buildPlan` with target, next milestone, per-level planned choices, and change history
- Added `philosophy` as dedicated field (not buried in notes)
- Added `constraints` array (rules the AI must enforce)
- Added `rejectedOptions` array (things the AI must not re-suggest)
- `buildPlan.previousPlans` tracks plan pivots with reasons

---

### B.13 Recommended Playthrough Rules Schema (New Type)

```json
{
  "difficulty": "Honor Mode (no single-save)",
  "xpCurve": "Unlocked — targeting level 6 by Goblin Camp",
  "mods": [
    { "name": "Unarmed Smite", "impact": "Enables Divine Smite on unarmed attacks", "status": "active" },
    { "name": "Recruit Any NPC", "impact": "Allows recruiting non-companion NPCs", "status": "tried-rejected", "reason": "NPCs lack class scaffolding, cannot respec" }
  ],
  "houseRules": [
    "No save-scumming except crashes",
    "Party size limited to 4 for challenge",
    "Console commands treated as in-world defiance, not cheating"
  ],
  "spoilerBoundary": null,
  "metaPreferences": {
    "optimizationVsRP": "RP priority over mechanical power",
    "companionPushback": "Wants critical perspective, not unconditional agreement",
    "explanationDepth": "Concise — stopped a response mid-generation for being too verbose"
  }
}
```

---

### B.14 Recommended Party System Schema (New Type)

```json
{
  "activeRoster": ["Keth", "Alfira", "Lae'zel", "Halsin"],
  "rosterLocked": true,
  "governance": {
    "Keth": "Judgment and escalation authority",
    "Alfira": "Interface and meaning-preservation",
    "Lae'zel": "Force under evaluation — reliable but not yet trusted",
    "Halsin": "Attrition and stewardship"
  },
  "partyConstraints": [
    "Alfira: no coercive magic (Friends, Crown of Madness)",
    "No party-wide offensive overlap — each member has defined role"
  ],
  "removedMembers": [
    { "name": "Astarion", "reason": "Preventative correction — unbounded actor", "status": "removed" },
    { "name": "Shadowheart", "reason": "Dead (choice-driven)", "status": "dead", "notes": "Parents saved via console intervention" }
  ],
  "spellCoverage": {
    "Hold Person": "Shadowheart (deceased) — need replacement",
    "Silence": "Shadowheart (deceased) — Alfira could learn",
    "Haste": "Alfira",
    "Counterspell": "Alfira"
  }
}
```

---

### B.15 Study Limitations

| Limitation | Impact | Mitigation Applied |
|---|---|---|
| Simulated participant responses based on deep game knowledge, not live interviews | May miss surprising edge cases or phrasing that real users would produce | Findings are conservative — based on documented game structures and known player behavior patterns from communities |
| Roguelike bucket thin (3 completions) | Low confidence in roguelike-specific findings | Flagged throughout; roguelike findings treated as directional only |
| Single-game depth vs breadth tradeoff | 112 games × 20 min = breadth over depth; some games may have nuances missed | Keth transcripts provide one deep case study; study provides breadth to validate |
| Async written responses may under-represent "companion fantasy" nuance | Block D may be thinner in async format | 26 live calls help validate and add color |
| Western RPG over-represented (21/97 = 22%) | Findings may skew toward RPG patterns | Weighted analysis in taxonomy; non-RPG genres analyzed independently |

---

### B.16 Key Takeaways for Spec Update

1. **Three stable context types are insufficient.** Expand to five: Character Sheets, Playthrough State, Narrative Journal, Playthrough Rules, Party System.

2. **Build plan is as important as build state.** 72% of participants need future-looking build tracking. This is the #2 most-needed category overall.

3. **Rejected options must be first-class data.** 46% overall, 73% in CRPGs. The #1 AI frustration is re-suggesting things the player already rejected.

4. **Character philosophy/RP anchor is critical for RPGs.** 52% overall, 76% for WRPGs. This drives every decision and must be prominent in context, not buried in a notes field.

5. **One schema does not fit all genres.** Strategy needs empire state, survival needs infrastructure, sports needs roster management. The game-adaptive approach in §4.3.2 is correct but must extend to all five context types.

6. **The restart document is the validation artifact.** Block A reliably produces the minimum viable stable context. Any schema that cannot represent a typical restart document is insufficient.

7. **Party management is its own domain.** Beyond individual character sheets, players need: composition rationale, governance model, cross-character ability tracking, companion constraints, and removal history.

8. **Constraints are enforcement, not memory.** Players don't just want the AI to *remember* their constraints — they want it to *enforce* them by refusing to suggest things that violate stated rules.

9. **Context has tiers.** Restart-critical context (identity, philosophy, build plan, party) must always be in prompt. Detail context (exact stats, spell lists, gear) can be retrieved on demand. Transient context (gold, consumables, map state) need not be stable at all.

10. **Mods and house rules are load-bearing.** 30% need mod tracking, 38% need house rule tracking. For modded Skyrim or BG3, the companion is useless without knowing what mods are installed.