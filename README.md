# 🧠 League of Legends AI Jungler Tracker
🔍 1. Match Timeline Fetcher
A script that uses Riot’s API to fetch full timeline and match metadata using match IDs.

Data Sources:

timeline.json: Per-minute snapshots of all players’ stats (level, CS, position, gold, etc.)

metadata.json: Summoner spell IDs, champion, team side

📊 2. Information Parser
From timeline frames:

Extract minute-by-minute (x, y) map positions

Track jungle CS, level, gold

We parse all meaningful events from the timeline:

CHAMPION_KILL → kills and assists

ELITE_MONSTER_KILL → Dragon, Herald, Baron

LEVEL_UP → tracked with interpolated positions

💬 Credits
Built with:

Riot API (match-v5)

Python 3

requests, riotwatcher, and json modules

By: Cheng
