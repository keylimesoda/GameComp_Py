# Game Companion – Test Specification

**Version:** 3.0  
**Date:** February 6, 2026  
**Author:** Riley (QA Lead)  
**Status:** Ready for Implementation  

---

## 1. Overview

This document defines the product-level test plan for Game Companion v1. It covers acceptance criteria traceability, end-to-end user scenarios, error handling, performance targets, and manual QA.

> **Note:** Implementation-level test details (unit test names, framework configuration, test file locations) are determined by the engineering team during technical design.

### 1.1 Test Approach

- **Test-Driven Development:** Tests written before implementation for all core features
- **Layered testing:** Unit tests for logic, integration tests for service boundaries, end-to-end tests for user scenarios
- **Real API validation:** Key integration points verified against live LLM and search APIs
- **Continuous regression:** Full test suite run after each milestone

---

## 2. Requirements Traceability Matrix

Maps each functional requirement to test coverage.

### 2.1 Playthrough Management (F1.x)

| Req ID | Requirement | Acceptance Criteria | Status |
|--------|-------------|---------------------|--------|
| F1.1 | Create playthrough with custom name | User can create a playthrough with a name; it appears in the list | 🔴 Not Started |
| F1.2 | Rename playthrough | User can rename an existing playthrough; new name reflected everywhere | 🔴 Not Started |
| F1.3 | List playthroughs sorted by last played | Playthrough list shows most recent first | 🔴 Not Started |
| F1.4 | Open to most recent playthrough | App opens directly to last-used playthrough’s chat | 🔴 Not Started |
| F1.5 | Playthroughs siloed (no cross-reference) | Searching in one playthrough never returns results from another | 🔴 Not Started |
| F1.6 | Delete playthrough with confirmation | Deletion requires confirmation; all associated data removed | 🔴 Not Started |
| F1.7 | Export playthrough to ZIP | User can export; ZIP contains metadata, messages, stable context | 🔴 Not Implemented |
| F1.8 | Import playthrough from ZIP | User can import a ZIP; playthrough appears in list with all data | 🔴 Not Implemented |

### 2.2 Chat Interface (F2.x)

| Req ID | Requirement | Acceptance Criteria | Status |
|--------|-------------|---------------------|--------|
| F2.1 | Minimal chat UI | User can type a message and see AI response in a clean chat view | 🔴 Not Started |
| F2.2 | Natural language only | No slash commands; all interaction is conversational | 🔴 Not Started |
| F2.3 | Dark mode by default | UI renders in dark theme on first load | 🔴 Not Started |
| F2.4 | Mobile-responsive layout | Layout adapts to tablet/phone viewports | ⏸️ Deferred |
| F2.5 | Chat history persists | Messages survive browser close and app restart | 🔴 Not Started |
| F2.6 | Typing indicator | Visual indicator shown while waiting for AI response | 🔴 Not Started |
| F2.7 | Offline error message | Clear message shown when user attempts to chat while offline | 🔴 Not Tested |
| F2.8 | API error handling | Friendly error dialog with expandable technical details | 🔴 Not Tested |

### 2.3 Persistent Memory / RAG (F3.x)

| Req ID | Requirement | Acceptance Criteria | Status |
|--------|-------------|---------------------|--------|
| F3.1 | Conversations stored locally | All messages persist across restarts; visible in chat history | 🔴 Not Started |
| F3.2 | Relevant context retrieved | When user asks a question, relevant past conversations are found and used | 🔴 Not Started |
| F3.3 | Context injected into prompt | AI responses demonstrate awareness of past conversations | 🔴 Not Started |
| F3.4 | Single LLM call with structured output | Response text and context updates extracted from one AI call | 🔴 Not Started |
| F3.4a | Context updates applied silently | User sees only response text; memory updates happen behind the scenes | 🔴 Not Started |
| F3.5 | Memory update indicator | "📌 Memory updated" shown when stable context changes | 🔴 Not Started |
| F3.6 | User can pin message/fact | "Remember this: X" persists X to stable context | 🔴 Not Started |
| F3.7 | Zero manual curation | System is fully automatic; no manual steps required | ✅ By design |
| F3.8 | View stable context via natural language | "Show me Keth’s character sheet" displays formatted data | 🔴 Not Started |
| F3.9 | Update stable context via natural language | "Update Alfira’s spells" modifies the correct record | 🔴 Not Started |

### 2.3a Stable Context Types

| Type | Acceptance Criteria | Status |
|------|---------------------|--------|
| Character Sheets | AI maintains structured character data per party member; viewable/editable via chat | 🔴 Not Started |
| Playthrough State | Current act, location, active quests tracked and updated automatically | 🔴 Not Started |
| Narrative Notes | Key decisions, party dynamics, themes captured as prose and pruned when too long | 🔴 Not Started |

### 2.3b Stable Context Auto-Detection

| Scenario | Acceptance Criteria | Status |
|----------|---------------------|--------|
| Level up discussed | Character sheet level updates automatically | 🔴 Not Started |
| Spell swap | Spell list in character sheet reflects the change | 🔴 Not Started |
| New party member | New character sheet created automatically | 🔴 Not Started |
| Party member removed | Character archived (still searchable, marked as former) | 🔴 Not Started |
| Major decision | Appended to narrative notes and/or playthrough state | 🔴 Not Started |
| Location change | Playthrough state location field updated | 🔴 Not Started |
| Quest complete | Playthrough state quest list updated | 🔴 Not Started |

### 2.4 Web Search (F4.x)

| Req ID | Requirement | Acceptance Criteria | Status |
|--------|-------------|---------------------|--------|
| F4.1 | Web search access | AI can search the web for game-specific information | 🔴 Not Started |
| F4.2 | Deterministic search trigger | Game-specific queries (mechanics, items, NPCs, builds) trigger search; non-game queries (greetings, recall) do not | 🔴 Not Started |
| F4.3 | Citations with source URLs | All external information includes source URLs | 🔴 Not Started |
| F4.4 | Citations inline/footnotes | Citations displayed as inline links or numbered footnotes | 🔴 Not Started |

### 2.5 LLM Backend (F5.x)

| Req ID | Requirement | Acceptance Criteria | Status |
|--------|-------------|---------------------|--------|
| F5.1 | Gemini default model | App uses Gemini for AI responses in v1 | 🔴 Not Started |
| F5.2 | User provides API key | User can enter and validate their own API key | 🔴 Not Started |
| F5.3 | Design supports swapping providers | Adding a new LLM provider doesn’t require rewriting chat logic | ✅ By design |
| F5.4 | Model selection in settings | User can select/change model (v1: Gemini only; extensible for v2) | ⏸️ v2 |

### 2.6 Settings (F6.x)

| Req ID | Requirement | Acceptance Criteria | Status |
|--------|-------------|---------------------|--------|
| F6.1 | API key management | User can add/update API keys for Gemini and web search | 🔴 Not Started |
| F6.2 | Model selection | User can choose between available models | ⏸️ v2 |
| F6.3 | Data storage location | User can see where data is stored | 🔴 Not Started |
| F6.4 | Debug mode changelog | When enabled, all stable context changes logged to a changelog file | 🔴 Not Started |

---

## 3. End-to-End User Scenarios

These scenarios validate complete user journeys. Each can be run as an automated integration test or as a manual QA walkthrough.

### 3.1 First Conversation (M1)

**Scenario:** New user sets up the app and has their first chat

**Steps:**
1. User starts the app and opens the web UI for the first time
2. User enters their Gemini API key on the welcome/settings screen
3. User creates a playthrough named "BG3 – Dark Urge Run"
4. User types: "What class should I pick for a sneaky character?"
5. AI responds with build advice

**Expected:**
- API key accepted and validated
- Playthrough created and visible in list
- AI response is coherent and relevant to the question
- Chat history shows the exchange

**Status:** 🔴 Not Started

### 3.2 Memory Recall Across Sessions (M3)

**Scenario:** AI remembers what the user said in a previous session

**Steps:**
1. User tells the AI: "My character Keth is a level 6 shadow monk"
2. AI acknowledges
3. User closes the browser and reopens the app later
4. User asks: "What class is my character?"

**Expected:**
- Response mentions "shadow monk" (recalled from previous conversation)
- User did not have to re-explain

**Status:** 🔴 Not Started

### 3.3 Web Search with Citations (M4)

**Scenario:** AI searches the web and cites sources

**Steps:**
1. User asks: "How do I beat Margit in Elden Ring?"

**Expected:**
- Response includes specific game advice (not generic)
- At least one source URL cited as an inline link or footnote
- Citations are numbered [1], [2], etc.

**Status:** 🔴 Not Started

### 3.4 Playthrough Isolation (M2)

**Scenario:** Data from one playthrough doesn't leak into another

**Steps:**
1. User creates Playthrough A with messages about "Keth the monk"
2. User creates Playthrough B with messages about "Tav the rogue"
3. In Playthrough A, user asks: "Tell me about my rogue"
4. In Playthrough B, user asks: "Tell me about my monk"

**Expected:**
- Playthrough A has no knowledge of "rogue" (from Playthrough B)
- Playthrough B has no knowledge of "monk" (from Playthrough A)

**Status:** 🔴 Not Started

### 3.5 Stable Context Auto-Update (M5)

**Scenario:** AI automatically extracts and persists game context from conversation

**Steps:**
1. User creates a playthrough for "Baldur's Gate 3"
2. User says: "My character Keth is a level 6 shadow monk with 18 DEX"
3. User asks: "Show me Keth's character sheet"

**Expected:**
- Character sheet exists for "Keth"
- Class shows Monk level 6
- DEX ability shows 18
- "📌 Memory updated" indicator was shown after step 2

**Status:** 🔴 Not Started

### 3.6 Level Up Detection (M5)

**Scenario:** AI detects a level up and updates the character sheet

**Steps:**
1. User has an existing playthrough where Keth is level 6
2. User says: "I just leveled up Keth to level 7!"
3. User asks: "Show me Keth's character sheet"

**Expected:**
- Character sheet shows level 7 (not 6)
- "📌 Memory updated" indicator shown

**Status:** 🔴 Not Started

### 3.7 User Correction (M5)

**Scenario:** User corrects a mistake in AI's memory

**Steps:**
1. AI's memory has Keth with 16 WIS
2. User says: "That's wrong – Keth actually has 18 WIS, not 16"
3. User asks: "Show me Keth's stats"

**Expected:**
- WIS updated to 18
- AI confirms the correction with "📌 Memory updated"

**Status:** 🔴 Not Started

### 3.8 View Stable Context via Natural Language (M5)

**Scenario:** User queries their game memory through chat

**Steps:**
1. User has a playthrough with populated stable context (characters, state, notes)
2. User asks: "Show me Keth's character sheet"
3. User asks: "What do you remember about my party?"
4. User asks: "Where am I in the story?"

**Expected:**
- Character sheet displayed in readable format (not raw data)
- Party summary lists all characters with key stats
- Playthrough state shows act, location, active quests

**Status:** 🔴 Not Started

### 3.9 Pin Fact to Memory (M5)

**Scenario:** User explicitly pins information to memory

**Steps:**
1. User says: "Remember this: Lae'zel is on probation and not fully trusted"
2. User later asks: "What do you remember about Lae'zel?"

**Expected:**
- "📌 Memory updated" indicator shown after step 1
- Response in step 2 includes the probation information

**Status:** 🔴 Not Started

### 3.10 Stable Context in Every Response (M5)

**Scenario:** AI uses stable context to give contextual answers without re-explanation

**Steps:**
1. User has established: Keth is a shadow monk, party uses non-lethal approach
2. User asks: "Should I kill this goblin?"

**Expected:**
- Response references Keth by name
- Response considers the non-lethal philosophy
- User did not have to re-explain character or approach

**Status:** 🔴 Not Started

---

## 4. Error Handling Tests

### 4.1 API Error Scenarios

| Scenario | Expected Behavior | Status |
|----------|-------------------|--------|
| Invalid Gemini API key | "Authentication failed. Check your API key." | 🔴 Not tested |
| Gemini rate limit (429) | "Rate limit reached. Please wait and try again." | 🔴 Not tested |
| Network timeout | "Network error. Check your connection." | 🔴 Not tested |
| Tavily API error | Graceful fallback, chat still responds | 🔴 Not tested |
| Empty RAG results | Chat works without retrieved context | ✅ By design |
| Malformed LLM response | Don't crash, show parse error | 🔴 Not tested |

### 4.2 Edge Cases

| Scenario | Expected Behavior | Status |
|----------|-------------------|--------|
| Very long message (>10K chars) | Chunked properly, no crash | 🔴 Not tested |
| Empty message | Rejected with helpful error | 🔴 Not tested |
| Special characters in playthrough name | Handled correctly | 🔴 Not tested |
| Delete active playthrough | Warning or prevent | 🔴 Not tested |
| Concurrent API requests | No DB corruption | 🔴 Not tested |

---

## 5. Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Chat response latency | ≤5s (network dependent) | 🔴 Not measured |
| RAG search latency | ≤500ms for 1000 chunks | 🔴 Not measured |
| Index 100 messages | ≤30s | 🔴 Not measured |
| App startup time | ≤3s | 🔴 Not measured |
| Memory usage (500 msg history) | ≤200MB | 🔴 Not measured |

---

## 6. Manual QA Checklist (v1 Release)

### 6.1 Happy Path Walkthrough

- [ ] Fresh install → start app → open browser
- [ ] Enter Gemini API key via settings
- [ ] Enter web search API key via settings
- [ ] Create first playthrough
- [ ] Send messages, receive AI responses
- [ ] Close browser and reopen → history persists
- [ ] Switch between playthroughs
- [ ] Delete a playthrough (with confirmation)
- [ ] AI remembers previous session context
- [ ] "📌 Memory updated" indicator appears when context changes
- [ ] View character sheet via natural language
- [ ] Correct an error in AI's memory
- [ ] Pin a fact to memory

### 6.2 Game Scenario Testing

- [ ] RPG (Baldur's Gate 3) - Character builds, party composition
- [ ] Action RPG (Elden Ring) - Boss strategies, weapon locations
- [ ] Strategy (Civ 6) - Tech trees, victory conditions
- [ ] Narrative (Detroit: Become Human) - Story choices, consequences

### 6.3 Stress Testing

- [ ] 500+ messages in single playthrough
- [ ] 10+ playthroughs
- [ ] Rapid message sending
- [ ] Large message content (5000+ chars)

---

## 7. Test Run History

| Date | Automated Tests | Manual QA | Notes |
|------|----------------|-----------|-------|
| *(awaiting first run)* | | | Fresh implementation |

---

## 8. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-04 | Alex | Initial test spec from review meeting |
| 2.0 | 2026-02-05 | Alex | Updated for web-based architecture |
| 3.0 | 2026-02-06 | Riley | **Product-level rewrite:** Removed unit test inventories and API endpoint tables. Replaced with acceptance criteria traceability and user-scenario E2E tests. Implementation test details deferred to engineering. |

