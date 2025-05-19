import json

# Load timeline file
with open("timelines/NA1_5281492721_timeline.json", "r") as f:
    timeline = json.load(f)

# Junglers are participantId 2 and 7 
jungler_ids = ["2", "7"]
jungler_announcements = []

# Helper to convert ms to mm:ss format
def ms_to_minsec(ms):
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    return f"{minutes}:{seconds:02d}"

# Go through each frame (per minute)
for frame in timeline["info"]["frames"]:
    timestamp = frame["timestamp"]
    minsec = ms_to_minsec(timestamp)

    for pid in jungler_ids:
        pf = frame["participantFrames"].get(pid)
        if pf and "position" in pf:
            x, y = pf["position"]["x"], pf["position"]["y"]
            cs = pf.get("jungleMinionsKilled", 0)
            level = pf.get("level", 1)
            gold = pf.get("currentGold", 0)
            jungler_announcements.append(f"{minsec} - Jungler {pid} is at ({x}, {y}) | Level {level} | CS {cs} | Gold {gold}")

# Go through events and add relevant ones
for frame in timeline["info"]["frames"]:
    for event in frame.get("events", []):
        ts = event["timestamp"]
        minsec = ms_to_minsec(ts)
        etype = event["type"]

        # Only include relevant jungler events
        if etype == "CHAMPION_KILL":
            killer = event.get("killerId")
            assists = event.get("assistingParticipantIds", [])
            victim = event.get("victimId")
            pos = event.get("position", {})
            if str(killer) in jungler_ids:
                jungler_announcements.append(f"{minsec} - ⚔️ Jungler {killer} killed champion {victim} at ({pos.get('x', '?')}, {pos.get('y', '?')})")
            elif str(victim) in jungler_ids:
                jungler_announcements.append(f"{minsec} - 💀 Jungler {victim} got killed by champion {killer} at ({pos.get('x', '?')}, {pos.get('y', '?')})")
            for assist_pid in assists:
                if str(assist_pid) in jungler_ids:
                    jungler_announcements.append(f"{minsec} - 🤝 Jungler {assist_pid} assisted a kill on champion {victim} at ({pos.get('x')}, {pos.get('y')})")
        elif etype == "ELITE_MONSTER_KILL":
            killer = event.get("killerId")
            if str(killer) in jungler_ids:
                monster_type = event.get("monsterType")
                pos = event.get("position", {})
                jungler_announcements.append(f"{minsec} - 👾 Jungler {killer} killed {monster_type} at ({pos.get('x', '?')}, {pos.get('y', '?')})")
        elif etype == "LEVEL_UP":
            pid = event.get("participantId")
            level = event.get("level")
            if str(pid) in jungler_ids:
                jungler_announcements.append(f"{minsec} - 🆙 Jungler {pid} leveled up to {level}")

for x in jungler_announcements:
    print(x)