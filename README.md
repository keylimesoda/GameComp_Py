# LoreKeeper 🎮

**Your AI game companion that actually remembers.**

Ever lose track of NPCs, quests, or that one conversation from 30 hours ago? LoreKeeper is an AI companion that builds a living memory of your game — characters, relationships, quests, world state — all from natural conversation. No spreadsheets. No wikis. Just talk about your game and it remembers everything.

Perfect for **Baldur's Gate 3**, **D&D campaigns**, and any story-heavy RPG.

## What It Does

- 🧠 **Remembers everything** — Characters, relationships, quest progress, world events
- 🗣️ **Natural conversation** — Just talk about your game like you would with a friend
- 📊 **Visual knowledge graph** — See how characters and factions connect
- 💾 **Persistent memory** — Pick up right where you left off, even weeks later
- 🔒 **Runs locally** — Your data stays on your machine, not in the cloud

## Getting Started

1. **Download** the latest release for your platform (Windows or macOS) from [Releases](https://github.com/keylimesoda/LoreKeeper/releases)
2. **Run** LoreKeeper — it opens in your web browser
3. **Sign in** with your GitHub account (free — this powers the AI)
4. **Start a campaign** and tell it about your game!

### For Developers

```bash
pip install -e ".[dev]"
gamecompanion
# Open http://localhost:8000
```

## How It Works

You chat naturally about your game session. LoreKeeper listens, extracts the important stuff, and builds structured memory behind the scenes. Next time you ask "wait, who was that merchant in Rivington?" — it knows.

The AI runs through your GitHub account (free tier works fine). Everything else runs on your machine.

## Example

> **You:** "We just finished the Goblin Camp. Killed the three leaders but spared Halsin. Shadowheart used her artifact on the portal. Gale is getting suspicious about the tadpole."
>
> **LoreKeeper:** *Automatically updates character sheets for Shadowheart, Gale, and Halsin. Logs the Goblin Camp as cleared. Notes the artifact usage and Gale's growing suspicion. Adds relationship tension between party members.*

Next session, ask "What's Gale's deal with the tadpole?" and get a full recap.

## Supported Games

LoreKeeper works with any narrative game, but it's especially great for:
- **Baldur's Gate 3** — Track companion relationships, quest flags, world state
- **D&D / Tabletop RPGs** — Never lose session notes again
- **RPGs with branching stories** — Remember which choices you made and why

## Feedback & Issues

Found a bug? Have an idea? [Open an issue](https://github.com/keylimesoda/LoreKeeper/issues) or just tell us what game you're using it with!

---

*Built by gamers who got tired of forgetting what happened in Act 1.* 🎲
