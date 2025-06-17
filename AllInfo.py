"""
League of Legends Match Analysis Script
This script analyzes specific match timeline data to track champion movements, events, and death timers.
It processes both timeline and match metadata to provide detailed game analysis.
"""

import json, math

# Load match timeline and metadata
with open("timelines/NA1_5286644426_timeline.json") as f:
    timeline = json.load(f)

with open("matches/NA1_5286644426.json") as f:
    meta = json.load(f)

# Initialize data structures
frames = timeline["info"]["frames"]
parsed_data = {
    "timelines": [],  # Stores movement data for all champions
    "events": []      # Stores game events (kills, objectives, etc.)
}

# Create mapping of participant IDs to champion names and teams
champion_map = {}
for x in meta["info"]["participants"]:
    pid = str(x["participantId"])
    champion_map[pid] = {
        "champion": x["championName"],
        "team": "Blue" if x["teamId"] == 100 else "Red"
    }

# Initialize data structures for all 10 players
participant_data = {str(i): [] for i in range(1, 11)}  # Movement data for each player
level_dict = {str(i): 1 for i in range(1, 11)}         # Track champion levels

def ms_to_minsec(ms):
    """Convert milliseconds to MM:SS format"""
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    return f"{minutes}:{seconds:02d}"

def get_base_position(team):
    """Get spawn position coordinates based on team"""
    return {"x": 554, "y": 581} if team == "Blue" else {"x": 14500, "y": 14511}
#https://leagueoflegends.fandom.com/wiki/Death
def calculate_death_timer(level, game_minutes):
    """
    Calculate respawn timer based on champion level and game time
    Uses Base Respawn Window (BRW) and Time Impact Factor (TIF)
    Reference: https://leagueoflegends.fandom.com/wiki/Death
    """
    # Base Respawn Window values for each level
    BRW = [-1, 10, 10, 12, 12, 14, 16, 20, 25, 28, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50, 52.5]
    base_timer = BRW[level]

    # Calculate Time Impact Factor based on game time
    if game_minutes < 15:
        tif = 0  # No TIF for 0–14:59
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

# Process movement data for all champions
for frame in frames:
    ts = ms_to_minsec(frame["timestamp"])
    for pid, pf in frame["participantFrames"].items():
        if "position" not in pf:
            continue
        # Store position, level, CS, and gold data for each champion
        entry = {
            "time": ts,
            "x": pf["position"]["x"],
            "y": pf["position"]["y"],
            "level": pf.get("level", 1),
            "cs": pf.get("jungleMinionsKilled", 0) + pf.get("minionsKilled", 0),
            "gold": pf.get("currentGold", 0)
        }
        participant_data[pid].append(entry)

# Store movement data in parsed_data
for pid, timeline in participant_data.items():
    parsed_data["timelines"].append({
        "id": int(pid),
        "timeline": timeline
    })

# Process game events
for frame in frames:
    for event in frame.get("events", []):
        ts = ms_to_minsec(event["timestamp"])
        etype = event["type"]
        event_entry = {"time": ts, "type": etype}

        # Handle different event types
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
    """Format champion label with team color emoji"""
    pid = str(pid)
    champ = champion_map.get(pid, {}).get("champion", f"Champion {pid}")
    team = champion_map.get(pid, {}).get("team", "Unknown")
    if team == "Blue":
        return f"🔵 {champ}" 
    else:
        return f"🔴 {champ}"

# Process and print events with formatted output
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
        tempMinSec = int(t.split(":")[0]) * 60 + int(t.split(":")[1]) + death_timer
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

# Print movement data for each champion
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