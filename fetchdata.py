"""
League of Legends Match Data Fetcher
This script fetches match data from the Riot Games API and saves it locally.
It handles both match metadata and timeline data for analysis.
"""

import requests
import json
import os
import time
import mysql.connector

# Step1: Get API key from https://developer.riotgames.com/
# Note that For development keys, Riot enforces: 20 requests per second, 100 requests every 2 minutes (120s)
api_key = 'RGAPI-0c152ebe-83a5-4f84-84c6-041d0b79e52c'
headers = {'X-Riot-Token': api_key}

# Read (username, tag) pairs from the summoners table in the test database
players = [
    ("호로록 봄", "pupu"),
    # Add more (username, tag) pairs here
]
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="test"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT username, tag FROM summoners")
    players = [(row[0], row[1]) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    print(f"Loaded {len(players)} players from the database.")
except Exception as e:
    print(f"❌ Failed to load players from database: {e}")
    players = []

match_region = "americas"
count = 100  # Number of matches to fetch per player

# Track all unique match IDs to avoid duplicate downloads
all_match_ids = set()

# Create output directories
os.makedirs("timelines", exist_ok=True)
os.makedirs("matches", exist_ok=True)

for riot_id_name, riot_id_tagline in players:
    # Step 2: Look up PUUID from Riot ID
    account_url = f"https://{match_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{riot_id_name}/{riot_id_tagline}"
    response = requests.get(account_url, headers=headers)
    #time.sleep(1)
    if response.status_code != 200:
        print(f"❌ Failed to get PUUID for {riot_id_name}#{riot_id_tagline}: {response.status_code} - {response.text}")
        continue
    puuid = response.json()["puuid"]
    print(f"✅ PUUID for {riot_id_name}#{riot_id_tagline}: {puuid}")

    # Step 3: Get list of recent match IDs for that PUUID
    matchlist_url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
    response = requests.get(matchlist_url, headers=headers)
    #time.sleep(1)
    if response.status_code != 200:
        print(f"❌ Failed to get match IDs for {riot_id_name}#{riot_id_tagline}: {response.status_code} - {response.text}")
        continue
    match_ids = response.json()
    print(f"✅ Found {len(match_ids)} match IDs for {riot_id_name}#{riot_id_tagline}")

    for match_id in match_ids:
        if match_id in all_match_ids:
            print(f"⏭️  Match {match_id} already processed, skipping...")
            continue
        all_match_ids.add(match_id)

        # Step 4: Download timelines (.json)
        timeline_path = f'timelines/{match_id}_timeline.json'
        if not os.path.exists(timeline_path):
            url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
            response = requests.get(url, headers=headers)
            #time.sleep(1)
            if response.status_code == 200:
                timeline = response.json()
                with open(timeline_path, 'w') as f:
                    json.dump(timeline, f, indent=2)
                print(f"✅ Saved timeline for {match_id}")
            else:
                print(f"❌ Failed to get timeline for {match_id}: {response.status_code} - {response.text}")
        else:
            print(f"⏭️  Timeline for {match_id} already exists, skipping...")

        # Step 5: Download match metadata (champion names, etc.)
        match_path = f'matches/{match_id}.json'
        if not os.path.exists(match_path):
            match_url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
            response = requests.get(match_url, headers=headers)
            #time.sleep(1)
            if response.status_code == 200:
                match = response.json()
                with open(match_path, 'w') as f:
                    json.dump(match, f, indent=2)
                print(f"✅ Saved match metadata for {match_id}")
            else:
                print(f"❌ Failed to get metadata for {match_id}: {response.status_code} - {response.text}")
        else:
            print(f"⏭️  Match data for {match_id} already exists, skipping...")
