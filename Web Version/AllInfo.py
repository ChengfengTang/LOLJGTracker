import json

with open("timelines/NA1_5295473504_timeline.json") as f:
    timeline = json.load(f)

with open("matches/NA1_5295473504.json") as f:
    meta = json.load(f)

frames = timeline["info"]["frames"]
parsed_data = {
    "timelines": [],
    "events": []
}
champion_map = {}
for x in meta["info"]["participants"]:
    pid = str(x["participantId"])
    champion_map[pid] = {
        "champion": x["championName"],
        "team": "Blue" if x["teamId"] == 100 else "Red"
    }

# Extract movement for all 10 players (IDs 1 to 10)
participant_data = {str(i): [] for i in range(1, 11)}

def ms_to_minsec(ms):
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    return f"{minutes}:{seconds:02d}"

for frame in frames:
    ts = ms_to_minsec(frame["timestamp"])
    for pid, pf in frame["participantFrames"].items():
        if "position" not in pf:
            continue
        entry = {
            "time": ts,
            "x": pf["position"]["x"],
            "y": pf["position"]["y"],
            "level": pf.get("level", 1),
            "cs": pf.get("jungleMinionsKilled", 0) + pf.get("minionsKilled", 0),
            "gold": pf.get("currentGold", 0)
        }
        participant_data[pid].append(entry)

for pid, timeline in participant_data.items():
    parsed_data["timelines"].append({
        "id": int(pid),
        "timeline": timeline
    })

# Process events
for frame in frames:
    for event in frame.get("events", []):
        ts = ms_to_minsec(event["timestamp"])
        etype = event["type"]
        event_entry = {"time": ts, "type": etype}

        if etype == "CHAMPION_KILL":
            event_entry.update({
                "actor": event.get("killerId"),
                "victim": event.get("victimId"),
                "x": event.get("position", {}).get("x"),
                "y": event.get("position", {}).get("y"),
                "assists": event.get("assistingParticipantIds", []),
                "note": f"Champion {event.get('killerId')} killed {event.get('victimId')}"
            })
        elif etype == "ELITE_MONSTER_KILL":
            event_entry.update({
                "actor": event.get("killerId"),
                "monster": event.get("monsterType"),
                "x": event.get("position", {}).get("x"),
                "y": event.get("position", {}).get("y"),
                "note": f"Champion {event.get('killerId')} killed {event.get('monsterType')}"
            })
        elif etype == "LEVEL_UP":
            event_entry.update({
                "actor": event.get("participantId"),
                "level": event.get("level"),
                "note": f"Champion {event.get('participantId')} leveled up to {event.get('level')}"
            })
        else:
            continue  # Skip unimportant events

        parsed_data["events"].append(event_entry)

# Helper to get champion label with team
def get_champ_label(pid):
    pid = str(pid)
    champ = champion_map.get(pid, {}).get("champion", f"Champion {pid}")
    team = champion_map.get(pid, {}).get("team", "Unknown")
    if team == "Blue":
        return f"🔵 {champ}" 
    else:
        return f"🔴 {champ}"

# Build announcer lines
for event in parsed_data["events"]:
    t = event["time"]
    etype = event["type"]

    if etype == "CHAMPION_KILL":
        killer = event.get("actor")
        victim = event.get("victim")
        x, y = event.get("x", "?"), event.get("y", "?")
        killer_label = get_champ_label(killer)
        victim_label = get_champ_label(victim)

        print(f"{t} - ⚔️  {killer_label} killed {victim_label} at ({x}, {y})")

        # Handle assists
        assists = event.get("assists", [])
        for assist_pid in assists:
            assist_label = get_champ_label(assist_pid)
            print(f"{t} - 🤝 {assist_label} assisted the kill")

    elif etype == "ELITE_MONSTER_KILL":
        killer = event.get("actor")
        monster = event.get("monster")
        x, y = event.get("x", "?"), event.get("y", "?")
        killer_label = get_champ_label(killer)
        print(f"{t} - 👾 {killer_label} killed {monster} at ({x}, {y})")

    elif etype == "LEVEL_UP":
        # Optional: only show key levels (6/11/16)
        level = event.get("level")
        if level in (6, 11, 16):  # major power spikes
            pid = event.get("actor")
            champ_label = get_champ_label(pid)
            print(f"{t} - 🆙 {champ_label} leveled up to {level}")

# Print participant movement timelines nicely
for p in parsed_data["timelines"]:
    pid = str(p["id"])
    champ = champion_map[pid]["champion"]
    team = champion_map[pid]["team"]
    if team == "Blue":
        team = "🔵" 
    else:
        team = "🔴"

    print(f"\n{team} {champ}")
    for entry in p["timeline"]:
        print(f"  {entry['time']} - Position: ({entry['x']}, {entry['y']}) | Level {entry['level']} | CS {entry['cs']} | Gold {entry['gold']}")
