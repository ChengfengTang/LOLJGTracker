import json, math

with open("timelines/NA1_5286644426_timeline.json") as f:
    timeline = json.load(f)

with open("matches/NA1_5286644426.json") as f:
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
level_dict = {str(i): 1 for i in range(1, 11)}

#print(level_dict)
def ms_to_minsec(ms):
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    return f"{minutes}:{seconds:02d}"

# Where they respawn
def get_base_position(team):
    return {"x": 554, "y": 581} if team == "Blue" else {"x": 14500, "y": 14511}
#https://leagueoflegends.fandom.com/wiki/Death
def calculate_death_timer(level, game_minutes):
    BRW = [-1, 10, 10, 12, 12, 14, 16, 20, 25, 28, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50, 52.5]
    base_timer =BRW[level]

    # Apply Time Impact Factor (TIF)
    if game_minutes < 15:
        tif = 0  # No TIF for 0–14:59, use BRW
    elif game_minutes < 30:
        tif = math.ceil(2 * (game_minutes - 15)) * 0.425 / 100
    elif game_minutes < 45:
        tif = 12.75/60 + math.ceil(2 * (game_minutes - 30)) * 0.30 / 100
    else:
        tif = 21.75/60 + math.ceil(2 * (game_minutes - 45)) * 1.45 / 100

    # Total timer = BRW * (1 + TIF)
    total_timer = base_timer * (1 + tif)
    print("at ", game_minutes, " minutes, level ", level, " respawn in ", total_timer)
    return round(total_timer)

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

        #print(f"{t} - ⚔️  {killer_label} killed {victim_label} at ({x}, {y})")

        # Handle assists
        assists = event.get("assists", [])
        for assist_pid in assists:
            assist_label = get_champ_label(assist_pid)
            #print(f"{t} - 🤝 {assist_label} assisted the kill at ({x}, {y})")

        # Handle death
        # https://leagueoflegends.fandom.com/wiki/Death
        print(f"{t} - 💀 {victim_label} died at ({x}, {y})")
        victim_level = level_dict[str(victim)]
        death_timer = calculate_death_timer(victim_level, int(t.split(":")[0]))
        tempMinSec =  int(t.split(":")[0]) * 60 + int(t.split(":")[1]) + death_timer
        respawn_timer = f"{tempMinSec//60}:{tempMinSec%60:02d}"
        print(f"{respawn_timer} -  {victim_label} respawn")

    elif etype == "ELITE_MONSTER_KILL":
        killer = event.get("actor")
        monster = event.get("monster")
        x, y = event.get("x", "?"), event.get("y", "?")
        killer_label = get_champ_label(killer)
        #print(f"{t} - 👾 {killer_label} killed {monster} at ({x}, {y})")

    elif etype == "LEVEL_UP":
        # Optional: only show key levels (6/11/16)
        level = event.get("level")
        #if level in (6, 11, 16):  # major power spikes
        if True:
            pid = event.get("actor")
            level_dict[str(pid)] = level
            champ_label = get_champ_label(pid)
            #print(f"{t} - 🆙 {champ_label} leveled up to {level}")

# Print participant movement timelines nicely
for p in parsed_data["timelines"]:
    pid = str(p["id"])
    champ = champion_map[pid]["champion"]
    team = champion_map[pid]["team"]
    if team == "Blue":
        team = "🔵" 
    else:
        team = "🔴"

    #print(f"\n{team} {champ}")
   #for entry in p["timeline"]:
        #print(f"  {entry['time']} - Position: ({entry['x']}, {entry['y']}) | Level {entry['level']} | CS {entry['cs']} | Gold {entry['gold']}")