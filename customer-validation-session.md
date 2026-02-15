# Game Companion – Customer Validation Session

**Date:** February 5, 2026  
**Format:** Scenario walkthrough (pre-UX testing)  
**Facilitator:** Jordan (Product Owner)  
**Customer:** Drew – long-time gamer, plays RPGs, strategy, action games, some sports. Currently mid-playthrough of Baldur's Gate 3 (Act 2), Elden Ring (NG+), and Civilization VI marathon. Has used ChatGPT for game questions but stopped because "it forgets everything."  
**Observers (notes only):** Sam (PM), Casey (UX), Riley (QA), Morgan (Tech Lead)

---

## Session Ground Rules (Jordan)

> "Drew, thanks for doing this. I'm going to walk you through some scenarios for a product we're building — an AI game companion. I'm not going to show you screens. I'm going to describe situations and ask you: does this match how you'd actually use it? What's missing? What's weird? There are no wrong answers — if something sounds dumb, say so."

---

## Scenario 1: First-Time Setup

**Jordan:** "You download the app, open it in your browser. It asks you for an API key for the AI service — Gemini, Google's AI — and a separate key for web search. Then it asks you to name your first playthrough. Like 'BG3 – Dark Urge Run.' Then you're in a chat. Does that flow make sense?"

**Drew:** "Uh… API key? Like, I have to go get that myself?"

**Jordan:** "Yeah, you'd sign up for a Gemini API key, paste it in."

**Drew:** "That's going to lose a lot of people. I'd do it because I'm technical, but my friend who also plays BG3 for 200 hours? He'd bail. Can you at least link to where to get it, and explain what it costs? I had no idea if Gemini even has a free tier."

**Jordan:** "Good callout. What about the playthrough name — would you name yours?"

**Drew:** "Yeah, definitely. I'd call mine 'BG3 – Ketheric Run' or whatever. But — do I have to tell it what *game* I'm playing? Because if it just has a name like 'Dark Urge Run,' how does it know I'm playing BG3 and not some other game?"

**Jordan:** "It would figure it out from conversation context."

**Drew:** "Mm. I'd rather just tell it up front. Like, pick a game name or type one in. Then it already has context from message one."

> **📝 Sam:** Strong signal. Add optional "game title" field to playthrough creation. De-risks the cold-start problem. AI can use it for web search context too.  
> **📝 Casey:** API key friction confirmed. Need onboarding UX — inline links, cost explainer, "test your key" button.  
> **📝 Riley:** Test scenario needed: playthrough without game title set — does AI adapt correctly?

---

## Scenario 2: Returning After a Week Away

**Jordan:** "You played BG3 last Tuesday. You open the app a week later. It goes straight to your BG3 playthrough. Your old messages are all there. You type: 'Where did I leave off?' What do you expect?"

**Drew:** "I expect it to tell me where I was — like, 'You were in Act 2, heading to Moonrise Towers, and your party was Keth, Shadowheart, Alfira, and Lae'zel. You had just resolved the Nightsong situation.' That kind of summary."

**Jordan:** "What if it said something more like 'Based on our last conversation, you were discussing whether to side with the goblins'?"

**Drew:** "That's… less useful. I don't care what we *discussed*. I care where I *am* in the game. If I say 'where did I leave off,' I mean in-game state, not chat state."

**Jordan:** "So you want it to track your actual game progress — act, location, quests — not just what you chatted about."

**Drew:** "Yeah, exactly. Like, I told it a week ago that I'd reached Moonrise. It should remember that. If I then say 'I cleared Moonrise and I'm in Act 3 now,' it should update. But it should *know* the difference between game state and random conversation."

> **📝 Sam:** Validates the Playthrough State context type. "Where did I leave off?" is a P1 query that needs to pull from structured state, not RAG chat search.  
> **📝 Casey:** This might be the killer feature for retention. The "welcome back" moment. Consider a startup summary — even unprompted.  
> **📝 Morgan:** Interesting. This suggests we might want a "session start" behavior — when user returns after N hours, system proactively summarizes last known state.

---

## Scenario 3: Character Build Advice (P1 Use Case)

**Jordan:** "Mid-session, you ask: 'Should I multiclass Keth into Paladin or stick with pure Monk?' What do you expect?"

**Drew:** "I expect it to know who Keth is — that he's my protagonist, he's a shadow monk, level 6, DEX build. I don't want to re-explain that. And then I expect it to give me actual build advice — like, 'Paladin 2 gives you smites which scale with your martial arts, but you delay Extra Attack if you dip now.' Specific stuff."

**Jordan:** "What if it gave you generic advice that didn't reference your build?"

**Drew:** "Then it's just ChatGPT and I already have that. The whole point is it *knows* me. If I've told it my stats, my build plan, my playstyle — and it still gives me generic 'Paladin is good for melee builds' — that's useless."

**Jordan:** "What if it also pulled in web search results? Like, 'According to bg3.wiki, the Monk/Paladin multiclass…' with a link?"

**Drew:** "That's great. As long as it blends them. Don't give me a wall of wiki text and then separately my build. Weave it together. 'Given your 18 DEX and the Way of Shadow subclass, here's what bg3.wiki says about the Monk/Paladin dip…'"

> **📝 Sam:** "Weave it together" — the response needs to integrate personal context + web search, not present them as separate blocks. This is a prompt design concern.  
> **📝 Riley:** Scenario needed: ask build question when character sheet is populated vs. when it's not. How does quality degrade?

---

## Scenario 4: Session Journaling (P4 Use Case)

**Jordan:** "After a three-hour session, you type: 'Summarize what happened tonight.' What do you expect?"

**Drew:** *(long pause)* "Hmm. How would it know what happened tonight? I didn't narrate everything to it. I just asked it a few questions during the session."

**Jordan:** "Right — it only knows what you've told it in chat."

**Drew:** "So the summary would be… 'You asked me about multiclassing, then asked how to beat a boss, then asked about Shadowheart's quest.' That's not a session summary. That's a chat log."

**Jordan:** "What would make it a real session summary?"

**Drew:** "I'd need to *tell* it what happened. Like, 'Tonight I cleared the Shadow Cursed Lands, recruited Halsin, Keth hit level 7, and I decided to spare the Nightsong.' Then it goes 'Got it, here's your session summary:' and gives me a nice writeup. But I have to feed it the events."

**Jordan:** "Would you actually do that? At the end of a session, type out what happened?"

**Drew:** "Honestly? Sometimes. After a big session, yeah. After a routine grind session, no. It'd be cool if it prompted me, actually. Like, 'It's been a while since your last message — want to log what happened in your session?'"

> **📝 Sam:** Session journaling (P4) is actually two things: (1) summarize what we discussed (low value, already available), and (2) log what happened in-game (high value, but requires user input). Spec should clarify this distinction.  
> **📝 Casey:** "Prompted journaling" is interesting UX. A gentle nudge after idle time: "Want to log what happened?" Could significantly improve memory quality.  
> **📝 Riley:** Edge case: user never journals — does the AI's memory degrade over time? It only knows what's been chatted about.

---

## Scenario 5: Multi-Game Switching

**Jordan:** "You've got three playthroughs — BG3, Elden Ring, and Civ 6. You switch from BG3 to Elden Ring. You ask: 'What build am I running?'"

**Drew:** "It should know my Elden Ring build. Completely separate from BG3. No bleed."

**Jordan:** "What if you accidentally ask about Shadowheart while in the Elden Ring playthrough?"

**Drew:** "It should say it doesn't know who that is. Or — actually, maybe it should say 'I don't have anyone named Shadowheart in this playthrough. Did you mean to switch to BG3?' That'd be slick."

**Jordan:** "That's interesting. Right now the spec says playthroughs are completely siloed — no cross-referencing at all."

**Drew:** "Silo the *data*, yeah. But if I clearly reference something from another playthrough, a gentle 'Hey, that sounds like it might be from your BG3 playthrough' would be really helpful. I switch games a lot. I *will* ask the wrong playthrough by accident."

> **📝 Sam:** Nuance: "siloed data" ≠ "zero awareness of other playthroughs existing." The AI could know playthrough *names* without accessing their data. Worth a spec refinement — F1.5 is too absolute.  
> **📝 Casey:** This is a common UX pattern — "Did you mean…?" Smart suggestion without violating the data boundary.  
> **📝 Riley:** Test case: reference a character from another playthrough. Verify data isn't leaked but a helpful redirect is offered.

---

## Scenario 6: Civ 6 (Non-RPG, Strategy)

**Jordan:** "Let's try your Civ 6 playthrough. You're playing a marathon game as Rome. You ask: 'What tech should I research next for a domination victory?'"

**Drew:** "Okay so… Civ is really different from an RPG. There's no 'character sheet' in the BG3 sense. My 'character' is a civilization. The stats are like, science output, military strength, what era I'm in. Does the tool even handle that?"

**Jordan:** "The character sheet is designed to be dynamic — the AI would adapt the categories to the game. So instead of STR/DEX, it might track your science per turn, military units, city count."

**Drew:** "Okay, but in Civ, the game state changes *drastically* every few turns. New techs, new units, diplomacy shifts, wars start. In BG3, my character sheet is pretty stable — level, stats, spells. In Civ, it's constantly churning. Would the memory keep up?"

**Jordan:** "The AI updates context whenever you discuss changes."

**Drew:** "That's the problem. In BG3, I naturally talk about my build. In Civ, I don't narrate 'I just researched Gunpowder and built three Musketmen.' I just ask 'what should I do next?' The AI doesn't have my game state unless I tell it, and in a strategy game, the state is *huge*."

**Jordan:** "So for strategy games, the value is more in the advice and less in the memory?"

**Drew:** "Yeah, kind of. The memory that matters in Civ is *strategic* — 'I'm going domination, I'm neighbors with a hostile Alexander, and I'm behind in science.' Not granular game state. If it remembers my strategy and my situation, that's enough. Don't try to be a Civ save file reader."

> **📝 Sam:** Big insight. Memory usefulness varies by genre: RPGs benefit from detailed character/state tracking; strategy games benefit from high-level strategic context. The stable context types need to flex — "character sheets" might be lightweight or even absent for some genres. "Playthrough State" carries the weight.  
> **📝 Casey:** Might need genre-aware system prompts or context templates. An RPG playthrough emphasizes characters. A strategy playthrough emphasizes situation + goals.  
> **📝 Morgan:** Dynamic schema already handles this structurally. But the *prompting* needs to adapt too — the AI should ask different follow-up questions for Civ vs. BG3.

---

## Scenario 7: Web Search Trust

**Jordan:** "You ask: 'What's the best weapon for a DEX build in Elden Ring?' It responds with advice and cites 'fextralife.com' and 'eldenring.wiki.' How do you feel?"

**Drew:** "Fextralife is fine. Standard. I'd trust that. But I'd want to know *which patch* the info is from. Elden Ring got massive balance patches. A weapon that was S-tier in 1.0 might be trash now."

**Jordan:** "We can include the source URL. Patch version awareness is harder."

**Drew:** "Yeah, I get that. The source link is enough — I can click through and check. But if it confidently tells me 'Rivers of Blood is the best DEX weapon' and that was nerfed two years ago, I'll lose trust fast."

**Jordan:** "What would recover that trust?"

**Drew:** "If I can correct it. 'That was nerfed in patch 1.07.' And it goes 'Good to know, I'll note that.' And then next time it doesn't recommend it. That'd be amazing."

> **📝 Sam:** User corrections aren't just for personal data — they're for correcting web search knowledge too. If user says "that info is outdated," the AI should note it in stable context so it doesn't repeat the mistake.  
> **📝 Riley:** Test case: user corrects a web-search-sourced claim. Does it persist? Does the AI avoid repeating it?

---

## Scenario 8: The "📌 Memory Updated" Indicator

**Jordan:** "When the AI detects something to remember — like a character detail or a decision — it shows a small '📌 Memory updated' tag on the message. Thoughts?"

**Drew:** "I like that it's subtle. I don't want a popup every time. But… can I see *what* it remembered? Like, if I click the 📌, does it show me 'Saved: Keth leveled up to 7'?"

**Jordan:** "Currently it's just an indicator, not clickable."

**Drew:** "Make it clickable. Or at least expandable. Because sometimes I'll want to know 'wait, what did it just save? Did it get that right?' If I can't check, I'll be anxious it's saving wrong stuff and I won't know until it hallucinates later."

**Jordan:** "What if it sometimes saves things wrong? Like, you say 'I'm thinking about respeccing to STR' and it saves 'Keth is a STR build.'"

**Drew:** "That'd be annoying but fixable if I can see what it saved and correct it. If it silently saves wrong stuff and I can't see it? That's a trust killer. I'll stop using the memory feature entirely."

> **📝 Casey:** STRONG signal. The 📌 indicator needs to be expandable/clickable to show what was saved. Transparency builds trust. This is probably the single most impactful UX detail for memory feature adoption.  
> **📝 Sam:** Consider: "📌 Saved: Keth reached level 7" — show the summary inline, collapsed by default. Clickable to expand full detail.  
> **📝 Riley:** Test case: verify the indicator shows *accurate* summary of what was saved. Wrong summary = worse than no summary.

---

## Scenario 9: Long Playthrough (60+ Hours)

**Jordan:** "You've been using this for your entire BG3 run. 60 hours. Hundreds of messages. You ask something from early Act 1. Does it remember?"

**Drew:** "It better. That's the whole pitch, right? 'It remembers everything.' If I say 'remember when I killed the goblin leaders in Act 1?' and it goes 'I don't have information about that' — that's a broken promise."

**Jordan:** "What if it remembered the *gist* but not exact details? Like, 'You mentioned dealing with the goblin leaders in Act 1' rather than the specific conversation."

**Drew:** "The gist is fine. I don't need it to quote me verbatim. I need it to have the *context*. If I ask 'why did I side against the goblins?' it should know my reasoning from back then — even if it's a summary. What I don't want is it saying 'I can only recall the last 20 conversations.'"

**Jordan:** "What about speed? If it has to search 60 hours of chat history to find the right context?"

**Drew:** "If it takes an extra second or two, fine. If it takes ten seconds every message because it's searching through everything? That'd get old fast. But honestly, ChatGPT takes forever sometimes and I still use it. If the answers are *better*, I'll wait."

> **📝 Sam:** The "broken promise" framing is critical. If we market "remembers everything," partial recall feels like a bug. Need to set expectations: "remembers context from your entire playthrough" rather than "remembers every word."  
> **📝 Morgan:** Performance budget matters. ≤5s total is fine if results are good. Need to benchmark RAG search at scale early (M3).

---

## Scenario 10: What Would Make You Stop Using It?

**Jordan:** "Last question. What would make you uninstall this?"

**Drew:**
1. "**If it forgets things I told it.** That's the core promise. Break that, I'm out."
2. "**If the web search gives me wrong info confidently.** One bad boss strategy that wastes an hour of my time, and I'll never trust it again."
3. "**If the setup is too complicated.** API keys, config files, running a server — if it feels like a dev tool instead of a game tool, my tolerance is low."
4. "**If it's slower than just Googling it.** For quick questions, Google is instant. This has to be meaningfully better — either through context or memory — to justify the wait."
5. "**If it tries to track too much and gets it wrong.** I'd rather it track less and be accurate than track everything and be 50% wrong."

> **📝 Sam:** #5 is a precision vs. recall tradeoff. Better to save fewer things correctly than everything sloppily. Impacts the structured extraction prompt design.  
> **📝 Casey:** #3 is the onboarding wall again. First-run experience needs to feel like a consumer app, not a dev environment.  
> **📝 Riley:** Each of these is a potential regression test scenario. Especially #1 (memory loss) and #2 (bad web info).

---

## Session Summary – Key Findings

### ✅ Validated (Use Cases That Resonate)

1. **Memory across sessions** — The #1 value prop. "It knows me" is the differentiator.
2. **Character build advice with personal context** — High-value, high-frequency use case.
3. **Web search with citations** — Trusted as long as sources are visible and correctable.
4. **Multi-playthrough isolation** — Essential for multi-game players.
5. **Stable context corrections** — "I can fix it" builds trust; without it, trust collapses.

### ⚠️ Needs Refinement

| # | Finding | Spec Impact |
|---|---------|-------------|
| 1 | **Playthrough needs an optional "game title" field** | Add to F1.1. Helps cold-start, web search context, and system prompts. |
| 2 | **📌 indicator must be expandable/clickable** — show what was saved | Refine F3.5. "Subtle indicator" isn't enough; needs transparency. |
| 3 | **"Where did I leave off?" is a top-priority query** that must pull from structured state, not chat search | Validates Playthrough State. May warrant a dedicated "welcome back" behavior. |
| 4 | **Session journaling ≠ chat summary** — user must narrate game events for meaningful journaling | Clarify P4 use case. Consider "prompted journaling" nudge after idle. |
| 5 | **Siloed playthroughs should still allow "Did you mean…?" redirect** when user references the wrong one | Refine F1.5. Silo data, not awareness of other playthrough names. |
| 6 | **Strategy games use memory differently** — strategic context matters more than granular state | No schema change needed (dynamic schema handles it), but system prompting should be genre-aware. |
| 7 | **User corrections should apply to web-search-sourced info too** — "that was nerfed" should be remembered | Extend F3.9 or add new requirement for "correcting external info." |
| 8 | **API key onboarding is a friction wall** — needs inline help, links, cost explainer, "test your key" button | UX enhancement for first-time setup flow (6.1). |

### 🚫 Not Raised / No Concerns

- Export/import — customer didn't ask about it (low priority confirmed)
- Debug mode — not a customer-facing concern (developer tool)
- Dark mode — "yeah, obviously" (table stakes)
- Model selection — "whatever works" (Gemini fine for v1)

---

## Recommended Spec Changes

| Priority | Change | Section |
|----------|--------|---------|
| **P1** | Add optional `game` field to playthrough creation | F1.1 |
| **P1** | Make 📌 indicator expandable to show what was saved | F3.5 |
| **P1** | Add "welcome back" query handling to user flows | 6.2 |
| **P2** | Refine F1.5 — silo data but allow "did you mean [other playthrough]?" | F1.5 |
| **P2** | Clarify session journaling use case (P4) — user-narrated vs. chat-summarized | Section 3 |
| **P2** | Add requirement: corrections to web-search-sourced info are persisted | F3.9 or new |
| **P3** | Enhance first-time setup flow with API key guidance | 6.1 |
| **P3** | Consider "prompted journaling" nudge after idle time | New UX feature (v1 or v2) |

---

**Jordan:** "Drew, this was incredibly helpful. Thank you."

**Drew:** "Yeah, this sounds cool. When can I use it?"
