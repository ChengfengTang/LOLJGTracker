"""
League of Legends Top Players Fetcher
This script fetches the top players from NA's ranked tiers (Challenger, Grandmaster, Master)
and saves their Riot IDs (username and tag) to the database.
"""

import requests
import json
import time
import mysql.connector
from typing import List, Dict

# API key from https://developer.riotgames.com/
api_key = 'RGAPI-45277985-1b24-4a96-906d-502b7882908c'
headers = {'X-Riot-Token': api_key}

def get_db_connection():
    """Establish connection to MySQL database"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="test"
    )

def get_top_players(region: str = "na1", tier: str = "challenger", queue: str = "RANKED_SOLO_5x5") -> List[Dict]:
    """Fetch top players from a specific tier and queue."""
    url = f"https://{region}.api.riotgames.com/lol/league/v4/{tier}leagues/by-queue/{queue}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"❌ Failed to get {tier} players: {response.status_code} - {response.text}")
    
    entries = response.json()["entries"]
    # Sort by league points
    entries.sort(key=lambda x: x["leaguePoints"], reverse=True)
    return entries

def get_riot_id(puuid: str) -> Dict:
    """Get Riot ID (username and tag) from PUUID."""
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"❌ Failed to get Riot ID: {response.status_code} - {response.text}")
    return response.json()

def get_puuid_from_summoner_id(region: str, summoner_id: str) -> str:
    """Get PUUID from summoner ID."""
    url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"❌ Failed to get summoner info: {response.status_code} - {response.text}")
    return response.json()["puuid"]

def check_summoner_exists(cursor, puuid: str) -> bool:
    """Check if a summoner already exists in the database."""
    cursor.execute("SELECT puuid FROM summoners WHERE puuid = %s", (puuid,))
    return cursor.fetchone() is not None

def main():
    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get top players from different tiers
    tiers = ["challenger", "grandmaster", "master"]
    total_players = 0
    new_players = 0
    
    try:
        for tier in tiers:
            print(f"Fetching {tier} players...")
            entries = get_top_players(tier=tier)
            
            for entry in entries:
                try:
                    # Get PUUID
                    puuid = get_puuid_from_summoner_id("na1", entry["summonerId"])
                    time.sleep(1)  # Rate limiting
                    
                    # Skip if player already exists in database
                    if check_summoner_exists(cursor, puuid):
                        print(f"⏭️  Player with PUUID {puuid} already exists, skipping...")
                        total_players += 1
                        continue
                    
                    # Get Riot ID
                    riot_id = get_riot_id(puuid)
                    time.sleep(1)  # Rate limiting
                    
                    # Insert into database
                    cursor.execute(
                        """
                        INSERT INTO summoners (username, tag, puuid) 
                        VALUES (%s, %s, %s)
                        """,
                        (riot_id["gameName"], riot_id["tagLine"], puuid)
                    )
                    conn.commit()
                    
                    print(f"✅ Added {riot_id['gameName']}#{riot_id['tagLine']}")
                    total_players += 1
                    new_players += 1
                    
                except Exception as e:
                    print(f"Error processing player {entry['summonerId']}: {str(e)}")
                    continue
        
        print(f"\n✅ Successfully processed {total_players} players")
        print(f"✅ Added {new_players} new players to the database")
            
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
