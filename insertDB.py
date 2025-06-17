"""
League of Legends Match Data Database Manager
This script processes all local match data and stores it in a MySQL database.
It creates separate tables for each champion and stores their match data as JSON.
"""

import json, math
import mysql.connector
from mysql.connector import Error
import os

def get_db_connection():
    """Establish connection to MySQL database"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="champions"
    )

def create_champion_table(champion_name):
    """
    Create a new table for a champion if it doesn't exist
    Each table stores match data with match_id as primary key and champion_data as JSON
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {champion_name} (
                match_id VARCHAR(100) PRIMARY KEY,
                champion_data JSON
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Error creating table for {champion_name}: {e}")
    finally:
        cursor.close()
        conn.close()

def store_champion_data(match_id, champion_name, champion_data):
    """
    Store champion match data in their respective table
    Skips if match already exists in the database
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Create table if it doesn't exist
        create_champion_table(champion_name)
        
        # Check if match already exists
        cursor.execute(f"""
            SELECT match_id FROM {champion_name} WHERE match_id = %s
        """, (match_id,))
        
        if cursor.fetchone():
            print(f"⏭️  Match {match_id} already exists for {champion_name}, skipping...")
            return
        
        # Insert new data
        cursor.execute(f"""
            INSERT INTO {champion_name} (match_id, champion_data)
            VALUES (%s, %s)
        """, (match_id, json.dumps(champion_data)))
        conn.commit()
        print(f"✅ Successfully stored data for {champion_name} in match {match_id}")
    except Error as e:
        print(f"❌ Error storing data for {champion_name}: {e}")
    finally:
        cursor.close()
        conn.close()

def process_match(match_id):
    """
    Process a single match's data
    Extracts jungler movements and events, stores them in champion-specific tables
    """
    print(f"\nProcessing match {match_id}...")
    
    # Load match and timeline data
    timeline_path = f"timelines/{match_id}_timeline.json"
    match_path = f"matches/{match_id}.json"
    
    if not os.path.exists(timeline_path) or not os.path.exists(match_path):
        print(f"Missing files for match {match_id}")
        return
    
    with open(timeline_path) as f:
        timeline = json.load(f)
    
    with open(match_path) as f:
        meta = json.load(f)

    # Only process Summoner's Rift matches (mapId 11)
    if meta["info"]["mapId"] != 11:
        print(f"Skipping match {match_id} - not on Summoner's Rift")
        return

    frames = timeline["info"]["frames"]

    # Create champion mapping for junglers only (participant IDs 2 and 7)
    champion_map = {}
    jungler_ids = ["2", "7"]  # Jungler participant IDs
    for x in meta["info"]["participants"]:
        pid = str(x["participantId"])
        if pid in jungler_ids:  # Only process junglers
            champion_map[pid] = {
                "champion": x["championName"],
                "team": "Blue" if x["teamId"] == 100 else "Red"
            }

    # Initialize data structure for junglers
    champion_data = {pid: {
        "timeline": [],  # Movement data
        "events": []     # Game events (kills, deaths, etc.)
    } for pid in jungler_ids}

    level_dict = {str(i): 1 for i in range(1, 11)}  # Track champion levels

    def ms_to_minsec(ms):
        """Convert milliseconds to MM:SS format"""
        minutes = ms // 60000
        seconds = (ms % 60000) // 1000
        return f"{minutes}:{seconds:02d}"

    def calculate_death_timer(level, game_minutes):
        """
        Calculate respawn timer based on champion level and game time
        Uses Base Respawn Window (BRW) and Time Impact Factor (TIF)
        """
        BRW = [-1, 10, 10, 12, 12, 14, 16, 20, 25, 28, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50, 52.5]
        base_timer = BRW[level]

        # Calculate Time Impact Factor based on game time
        if game_minutes < 15:
            tif = 0
        elif game_minutes < 30: 
            tif = math.ceil(2 * (game_minutes - 15)) * 0.425 / 100
        elif game_minutes < 45:
            tif = 12.75/60 + math.ceil(2 * (game_minutes - 30)) * 0.30 / 100
        else:
            tif = 21.75/60 + math.ceil(2 * (game_minutes - 45)) * 1.45 / 100

        total_timer = base_timer * (1 + tif)
        return round(total_timer)

    # Process movement data for junglers only
    for frame in frames:
        ts = ms_to_minsec(frame["timestamp"])
        for pid, pf in frame["participantFrames"].items():
            if pid not in jungler_ids or "position" not in pf:  # Only process junglers
                continue
            # Store position, level, CS, and gold data
            entry = {
                "time": ts,
                "x": pf["position"]["x"],
                "y": pf["position"]["y"],
                "level": pf.get("level", 1),
                "cs": pf.get("jungleMinionsKilled", 0) + pf.get("minionsKilled", 0),
                "gold": pf.get("currentGold", 0)
            }
            champion_data[pid]["timeline"].append(entry)

    # Process events for junglers only
    for frame in frames:
        for event in frame.get("events", []):
            ts = ms_to_minsec(event["timestamp"])
            etype = event["type"]

            # Handle champion kills
            if etype == "CHAMPION_KILL":
                killer = event.get("killerId")
                victim = event.get("victimId")
                assists = event.get("assistingParticipantIds", [])
                pos = event.get("position", {})
                
                # Record kill event for jungler killer
                if killer and str(killer) in jungler_ids:
                    champion_data[str(killer)]["events"].append({
                        "time": ts,
                        "type": "kill",
                        "data": {
                            "victim": victim,
                            "position": pos,
                            "assists": assists
                        }
                    })
                
                # Record death event for jungler victim
                if str(victim) in jungler_ids:
                    # Calculate respawn timer
                    victim_level = level_dict[str(victim)]
                    game_minutes = int(ts.split(":")[0])
                    death_timer = calculate_death_timer(victim_level, game_minutes)
                    current_seconds = game_minutes * 60 + int(ts.split(":")[1])
                    respawn_seconds = current_seconds + death_timer
                    respawn_timer = f"{respawn_seconds//60}:{respawn_seconds%60:02d}"
                    
                    champion_data[str(victim)]["events"].append({
                        "time": ts,
                        "type": "death",
                        "data": {
                            "killer": killer,
                            "position": pos,
                            "assists": assists,
                            "respawn_time": respawn_timer
                        }
                    })
                
                # Record assist events for jungler assists
                for assist_pid in assists:
                    if str(assist_pid) in jungler_ids:
                        champion_data[str(assist_pid)]["events"].append({
                            "time": ts,
                            "type": "assist",
                            "data": {
                                "victim": victim,
                                "killer": killer,
                                "position": pos
                            }
                        })

            # Handle monster kills
            elif etype == "ELITE_MONSTER_KILL":
                killer = event.get("killerId")
                if str(killer) in jungler_ids:  # Only process if jungler killed the monster
                    monster_type = event.get("monsterType")
                    pos = event.get("position", {})
                    
                    champion_data[str(killer)]["events"].append({
                        "time": ts,
                        "type": "monster_kill",
                        "data": {
                            "monster_type": monster_type,
                            "position": pos
                        }
                    })

            # Handle level ups
            elif etype == "LEVEL_UP":
                pid = event.get("participantId")
                if str(pid) in jungler_ids:  # Only process jungler level ups
                    level = event.get("level")
                    level_dict[str(pid)] = level
                    
                    champion_data[str(pid)]["events"].append({
                        "time": ts,
                        "type": "level_up",
                        "data": {
                            "level": level
                        }
                    })

    # Store data for each jungler in their respective table
    for pid in jungler_ids:
        if pid in champion_map:  # Only store if we have champion data
            champion_name = champion_map[pid]["champion"]
            store_champion_data(match_id, champion_name, champion_data[pid])

    # Print verification data for junglers only
    for pid in jungler_ids:
        if pid in champion_map:
            champion_name = champion_map[pid]["champion"]
            team = champion_map[pid]["team"]
            team_emoji = "🔵" if team == "Blue" else "🔴"
            
            #print(f"\n{team_emoji} {champion_name}")
            #for entry in champion_data[pid]["timeline"]:
                #print(f"  {entry['time']} - Position: ({entry['x']}, {entry['y']}) | Level {entry['level']} | CS {entry['cs']} | Gold {entry['gold']}")
            
            #print("\nEvents:")
            #for event in champion_data[pid]["events"]:
                #print(f"  {event['time']} - {event['type']}: {event['data']}")

def main():
    """Process all matches in the matches directory"""
    # Get all match IDs from the matches directory
    match_files = [f for f in os.listdir("matches") if f.endswith(".json")]
    match_ids = [f.replace(".json", "") for f in match_files]
    
    # Process each match
    for match_id in match_ids:
        process_match(match_id)

if __name__ == "__main__":
    main()
