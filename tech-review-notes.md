# ⚠️ SUPERSEDED – Historical Reference Only

> **This document has been superseded as of February 6, 2026.**  
> The spec was restructured to a pure product document (v3.0), and all technical decisions are being made fresh in [tech-design-session.md](tech-design-session.md).  
> This file is retained as historical context only. Do not use these decisions as a starting point for implementation.

---

# Game Companion – Technical Spec Review

**Date:** February 3, 2026  
**Status:** ❌ Superseded by spec v3.0 product-only rewrite  
**Participants:**
- **Alex** – Junior Developer
- **Morgan** – Staff Developer
- **Jordan** – Product Owner
- **Sam** – Spec Author (Product Manager)

**Document Reviewed:** spec.md v1.0 Draft

---

## Meeting Transcript

### Opening

**Sam (PM):** Alright, we've got product sign-off. Let's do the tech review. Morgan, Alex – tear it apart.

**Morgan (Staff):** I've read through it. Overall, it's well-structured. I have questions in three areas: the RAG implementation, the stable context extraction, and the LLM abstraction layer. Let's start with RAG.

---

### 1. RAG Implementation

**Morgan (Staff):** Section 4.3 says we're using "local SQLite + vector store (e.g., LiteDB or local FAISS/Chroma)". That's three very different things. We need to pick one.

**Alex (Junior):** What's the difference?

**Morgan (Staff):** 
- **FAISS** is Facebook's vector similarity library. Fast, but it's Python-native. We'd need to wrap it or use a port.
- **Chroma** is a full vector DB, also Python-first, though there's a .NET client.
- **LiteDB** is a .NET embedded document DB – but it doesn't do vector search natively.

For a .NET MAUI app, I'd recommend **Milvus Lite** or **Qdrant** (both have .NET clients), or we roll our own with **SQLite + a vector extension** like `sqlite-vss`.

**Sam (PM):** What's your recommendation?

**Morgan (Staff):** For v1, **SQLite with sqlite-vss extension**. Single dependency, works offline, .NET friendly. We can swap later if needed.

**Jordan (PO):** Does that affect timeline?

**Morgan (Staff):** No, might even simplify it. One database instead of two.

**Alex (Junior):** How do we generate the embeddings? The spec mentions a vector store but not the embedding model.

**Morgan (Staff):** Good catch. We need to call an embedding API. Options:
1. **Gemini's embedding API** – keeps us in one ecosystem
2. **OpenAI's ada-002** – industry standard, but adds another API key
3. **Local model** – e.g., run a small model via ONNX

**Sam (PM):** For v1, let's use Gemini's embedding API since we're already requiring that key. Add it to the spec?

**Morgan (Staff):** Yes. I'll note that as a spec update.

> **📋 ACTION: Add embedding model choice to spec (Gemini embedding API for v1)**

---

### 2. Stable Context Extraction

**Morgan (Staff):** Section 4.3.4 says "AI analyzes its own response and extracts key facts." How exactly?

**Sam (PM):** The idea is after each response, we run a secondary prompt asking the LLM to extract structured updates.

**Morgan (Staff):** So every user message triggers *two* LLM calls? One for the response, one for extraction?

**Sam (PM):** That was my assumption, yes.

**Morgan (Staff):** That doubles API costs and latency. On a 60-hour playthrough with hundreds of messages, that adds up.

**Alex (Junior):** Could we do it in one call? Like, ask the LLM to respond AND output structured context updates?

**Morgan (Staff):** Yes – we can use **structured output** or **function calling**. Gemini supports both. The response would include:
```json
{
  "response": "Here's my advice on your build...",
  "context_updates": [
    { "type": "character_sheet", "target": "Keth", "field": "level", "value": 7 }
  ]
}
```

**Sam (PM):** That's cleaner. Let's do that.

**Jordan (PO):** Does that change the user experience?

**Morgan (Staff):** No, it's invisible. Just more efficient.

> **📋 ACTION: Spec should note single-call extraction using structured output / function calling**

---

### 3. LLM Abstraction Layer

**Alex (Junior):** Section 4.5 says "architecture supports swapping LLM providers." How do we actually do that?

**Morgan (Staff):** We need an abstraction interface. Something like:

```csharp
public interface ILlmClient
{
    Task<ChatResponse> ChatAsync(ChatRequest request);
    Task<float[]> EmbedAsync(string text);
}
```

Then we have `GeminiClient`, `OpenAiClient`, `OllamaClient` implementations. The orchestrator only talks to the interface.

**Alex (Junior):** And the user picks which one in settings?

**Morgan (Staff):** Exactly. Dependency injection swaps the implementation at runtime.

**Sam (PM):** For v1, we only ship `GeminiClient`, but the interface exists?

**Morgan (Staff):** Correct. The abstraction is cheap to build now and expensive to retrofit later.

> **📋 ACTION: Add ILlmClient interface to architecture section**

---

### 4. Web Search Behavior

**Morgan (Staff):** Section 4.4 says "AI proactively searches when confidence is low." How does the AI decide?

**Sam (PM):** We'd prompt it to self-assess. "If you're unsure about game-specific facts, search first."

**Morgan (Staff):** That's fuzzy. In practice, LLMs either search too much (cost) or too little (bad answers). 

**Jordan (PO):** The requirement was "search often to ensure correct info" and "all info should be well-cited."

**Morgan (Staff):** Then let's make it deterministic for v1: **always search for game-specific queries**. The orchestrator detects query type and triggers search before the LLM call.

**Alex (Junior):** How do we detect "game-specific"?

**Morgan (Staff):** Heuristics first: if the message mentions game mechanics, items, NPCs, locations, builds – search. We can use a lightweight classifier or even keyword matching. Refinement comes later.

**Sam (PM):** I like deterministic. Easier to debug, easier to trust.

> **📋 ACTION: Change search behavior from "AI decides" to "orchestrator triggers on game-specific queries"**

---

### 5. API Key Security

**Morgan (Staff):** Section NF6 says "API keys stored encrypted locally." How?

**Alex (Junior):** Windows has DPAPI, right?

**Morgan (Staff):** Yes. On Windows, we use `ProtectedData` class. On Mac/iOS, Keychain. On Android, EncryptedSharedPreferences. MAUI has `SecureStorage` that abstracts this.

**Sam (PM):** So we just use `SecureStorage`?

**Morgan (Staff):** For v1, yes. It's cross-platform and good enough. We're not storing credit cards, just API keys.

> **📋 ACTION: Specify MAUI SecureStorage for API key storage**

---

### 6. Performance Concerns

**Morgan (Staff):** Section NF4 says "response latency ≤ 5s." Let's break that down:

| Step | Estimated Time |
|------|----------------|
| Embed user query | 200ms |
| Vector search (local) | 50ms |
| Web search (Tavily) | 500-1000ms |
| LLM call (Gemini) | 2000-4000ms |
| Context extraction (if separate) | 1500-3000ms |
| **Total** | **4-8 seconds** |

If we do single-call extraction, we save 1.5-3s. That puts us in the 4-5s range.

**Jordan (PO):** Is 5s acceptable?

**Sam (PM):** For a "tab over" companion, yes. You're not expecting instant response while actively gaming.

**Morgan (Staff):** Agreed. But we should show a typing indicator so it doesn't feel broken.

> **📋 ACTION: Add typing/thinking indicator to UI requirements**

---

### 7. Offline Behavior

**Alex (Junior):** NF5 says "app launches and shows history offline; chat requires connectivity." What happens if someone tries to chat offline?

**Morgan (Staff):** Clear error state. "You're offline. Connect to continue chatting." We should queue the message so it sends when reconnected.

**Sam (PM):** Queuing feels over-engineered for v1. Just show the error.

**Morgan (Staff):** Fair. Queue is v2 if users complain.

> **📋 ACTION: Add offline error handling to UI requirements (no message queuing in v1)**

---

### 8. Data Backup / Export

**Morgan (Staff):** The spec doesn't mention backup or export. If someone's 60-hour playthrough data is lost, that's devastating.

**Jordan (PO):** Cloud sync is v2, but what about manual export?

**Sam (PM):** Good point. We should have "Export Playthrough" that dumps everything to a JSON/ZIP file. And "Import Playthrough" to restore.

**Alex (Junior):** That also helps with the future cloud sync – same format.

**Morgan (Staff):** Yes. Let's add that to v1 scope. It's low effort and high value.

> **📋 ACTION: Add F1.7 and F1.8 – Export/Import playthrough data**

---

### 9. Character Sheet Schema Versioning

**Morgan (Staff):** Section 4.3.2 shows a character sheet schema. What happens when we add fields later? Old playthroughs won't have them.

**Alex (Junior):** Schema migration?

**Morgan (Staff):** Exactly. We need a `schema_version` field and migration logic. For v1, version is 1. When we add fields in v2, we write a migrator.

**Sam (PM):** Add it to the schema?

**Morgan (Staff):** Yes. Also applies to Playthrough State and Narrative Notes structures.

> **📋 ACTION: Add schema_version to all stable context types**

---

### 10. Testing Strategy

**Alex (Junior):** How do we test the RAG quality? Like, how do we know it's retrieving the right context?

**Morgan (Staff):** Good question. We need:
1. **Unit tests** for embedding/retrieval mechanics
2. **Integration tests** with sample playthroughs (like those BG3 docs Sam showed)
3. **Manual QA** with real gameplay scenarios

**Sam (PM):** I can provide my BG3 conversation exports as test fixtures.

**Morgan (Staff):** Perfect. We'll create a test suite that:
- Loads a sample playthrough
- Asks questions that should retrieve specific context
- Validates the retrieved chunks contain expected content

> **📋 ACTION: Add testing strategy section to spec; use real playthrough data as fixtures**

---

### 11. Mobile Architecture Check

**Morgan (Staff):** NF1 says "Windows v1, architecture supports Android/iOS v2." MAUI gets us there, but a few gotchas:

1. **SQLite + sqlite-vss**: Need to verify the vector extension works on mobile
2. **SecureStorage**: Works cross-platform ✓
3. **UI layout**: Spec says "mobile-responsive" – we need to actually test this during v1

**Alex (Junior):** Should we test on Android emulator during v1?

**Morgan (Staff):** Yes, but not for release. Just to catch layout issues early. Better than a full rewrite later.

> **📋 ACTION: Add "verify mobile layout in emulator" to M7 (polish phase)**

---

## Summary of Spec Updates Required

| # | Section | Change |
|---|---------|--------|
| 1 | 4.3 | Specify embedding model: Gemini embedding API |
| 2 | 4.3 | Clarify single-call extraction using structured output |
| 3 | 5 | Specify SQLite + sqlite-vss as vector store |
| 4 | 6 | Add ILlmClient abstraction to architecture |
| 5 | 4.4 | Change search trigger from "AI decides" to "orchestrator detects game-specific queries" |
| 6 | 5 | Specify MAUI SecureStorage for API keys |
| 7 | 4.2 | Add typing/thinking indicator requirement |
| 8 | 4.2 | Add offline error handling requirement |
| 9 | 4.1 | Add F1.7 Export and F1.8 Import playthrough |
| 10 | 4.3.2 | Add schema_version to stable context types |
| 11 | New | Add testing strategy section |
| 12 | 12 | Add mobile layout verification to M7 |

---

## Sign-Off

| Role | Name | Approved | Notes |
|------|------|----------|-------|
| Staff Developer | Morgan | ✅ | Pending spec updates |
| Junior Developer | Alex | ✅ | Ready to start on M1 |
| Product Owner | Jordan | ✅ | Export/import is good addition |
| Spec Author | Sam | ✅ | Will update spec with actions |

---

## Follow-Up Discussion (Post-Review)

**Jordan (PO):** Wait, I have a few follow-up questions before we close this out.

### On #2 – Single-Call Extraction

**Jordan (PO):** If we're moving to single-call extraction with structured output, how do we make sure the user only sees the "response" part and not the context update JSON?

**Morgan (Staff):** Good catch. Two approaches:

1. **Function calling mode**: Gemini's function calling returns the response text separately from the function call payload. The orchestrator only displays `response.text` to the user; the `function_call` data goes to the context updater.

2. **Structured output with parsing**: If we use a JSON schema response, we parse it server-side and only render `response.message` to the chat UI.

Either way, the orchestrator acts as a filter – raw LLM output never hits the UI directly.

**Alex (Junior):** So the flow is:
```
User message → Orchestrator → LLM (returns response + updates)
                    ↓
         Parse structured output
                    ↓
    ┌───────────────┴───────────────┐
    ↓                               ↓
Display response              Apply context updates
to user                       to stable context
```

**Morgan (Staff):** Exactly. The user never sees the plumbing.

> **📋 ACTION: Document response/context separation in orchestrator design**

---

### On #9 – Export Feature

**Jordan (PO):** Love the export add. Just want to confirm – this exports everything? Chat history, stable context, the works?

**Sam (PM):** Yes, full playthrough state. Single ZIP file with:
- `playthrough.json` (metadata)
- `messages.json` (full chat history)
- `stable-context/` folder (state, character sheets, narrative notes)
- `embeddings.bin` (optional – could regenerate on import)

**Morgan (Staff):** I'd skip exporting embeddings. They're large and can be regenerated from messages on import. Keeps the export file reasonable.

**Jordan (PO):** Makes sense. User backs up the "meaning," we regenerate the "index."

> **📋 ACTION: Export excludes embeddings; import regenerates them**

---

### On #10 – Stable Context Versioning (Expanded)

**Jordan (PO):** On schema versioning – I think we need two levels:
1. **Schema version** – what fields exist (for migrations)
2. **Data version** – how many times this specific context has been touched

The second one helps with debugging. "Why does Keth show level 5 when I said level 6?" – you can trace the update history.

**Morgan (Staff):** So each stable context gets a `version` counter that increments on every update?

**Jordan (PO):** Yes. And ideally a changelog showing what changed and when.

**Alex (Junior):** That could get bloated fast. Every spell swap, every level up...

**Morgan (Staff):** Agreed. Two options:

**Option A – Inline changelog (compact)**
```json
{
  "name": "Keth",
  "schema_version": 1,
  "data_version": 14,
  "last_updated": "2026-02-03T18:30:00Z",
  "changelog": [
    { "v": 14, "ts": "2026-02-03T18:30:00Z", "field": "level", "old": 5, "new": 6 },
    { "v": 13, "ts": "2026-02-02T21:15:00Z", "field": "spells.level2", "change": "added Hold Person" }
  ]
}
```
Changelog capped at last N entries (e.g., 20).

**Option B – Separate changelog file (debug mode)**
- Stable context stays lean
- `changelog.jsonl` file per playthrough, append-only
- Only written when debug mode is enabled in settings
- Full history for power users, zero bloat for normal users

**Jordan (PO):** I like Option B. Keep the core clean, make the changelog opt-in for debugging.

**Sam (PM):** Agreed. Add a "Debug Mode" toggle in settings that enables changelog logging.

**Morgan (Staff):** Done. We'll add:
- `data_version` (integer, increments on update) to all stable context
- `last_updated` timestamp
- Optional `changelog.jsonl` when debug mode is on

> **📋 ACTION: Add data_version + last_updated to stable context; changelog.jsonl as debug-mode feature**

---

## Updated Summary of Spec Changes

| # | Section | Change |
|---|---------|--------|
| 1 | 4.3 | Specify embedding model: Gemini embedding API |
| 2 | 4.3 | Clarify single-call extraction using structured output |
| **2a** | **6** | **Document response/context separation in orchestrator (user never sees raw structured output)** |
| 3 | 5 | Specify SQLite + sqlite-vss as vector store |
| 4 | 6 | Add ILlmClient abstraction to architecture |
| 5 | 4.4 | Change search trigger from "AI decides" to "orchestrator detects game-specific queries" |
| 6 | 5 | Specify MAUI SecureStorage for API keys |
| 7 | 4.2 | Add typing/thinking indicator requirement |
| 8 | 4.2 | Add offline error handling requirement |
| 9 | 4.1 | Add F1.7 Export and F1.8 Import playthrough |
| **9a** | **4.1** | **Export excludes embeddings; import regenerates them** |
| 10 | 4.3.2 | Add schema_version to stable context types |
| **10a** | **4.3.2** | **Add data_version + last_updated to stable context** |
| **10b** | **4.6** | **Add Debug Mode setting; enables changelog.jsonl logging** |
| 11 | New | Add testing strategy section |
| 12 | 12 | Add mobile layout verification to M7 |

---

## Revised Sign-Off (Final)

| Role | Name | Approved | Notes |
|------|------|----------|-------|
| Staff Developer | Morgan | ✅ | All concerns addressed |
| Junior Developer | Alex | ✅ | Clear on orchestrator flow |
| Product Owner | Jordan | ✅ | Versioning approach approved |
| Spec Author | Sam | ✅ | Will apply all updates |

---

## Next Steps

1. **Sam** updates spec.md with all action items (now 15 total)
2. **Morgan** creates technical architecture diagram (detailed)
3. **Alex** sets up project scaffolding (M1)
4. **Team** reconvenes for sprint planning

---

*Meeting adjourned.*
