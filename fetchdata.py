"""
League of Legends Match Data Fetcher
This script fetches match data from the Riot Games API and saves it locally.
It handles both match metadata and timeline data for analysis.
"""

import requests
import json
import os
# Step1: Get API key from https://developer.riotgames.com/
# Note that For development keys, Riot enforces: 20 requests per second, 100 requests every 2 minutes (120s)
api_key = 'RGAPI-45277985-1b24-4a96-906d-502b7882908c'

headers = {'X-Riot-Token': api_key}

# Step 2: Look up PUUID from Riot ID
riot_id_name = "호로록 봄" #Just an example
riot_id_tagline = "pupu"
# API Docs https://developer.riotgames.com/apis#summoner-v4/GET_getBySummonerId
account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{riot_id_name}/{riot_id_tagline}" 

response = requests.get(account_url, headers=headers)
if response.status_code != 200:
    raise Exception(f"❌ Failed to get PUUID: {response.status_code} - {response.text}")

puuid = response.json()["puuid"]
print(f"✅ PUUID for {riot_id_name}#{riot_id_tagline}: {puuid}")

# Step 3: Get list of recent match IDs for that PUUID
match_region = "americas"
count = 50 # Number of matches to fetch
matchlist_url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"

response = requests.get(matchlist_url, headers=headers)
if response.status_code != 200:
    raise Exception(f"❌ Failed to get match IDs: {response.status_code} - {response.text}")

match_ids = response.json()
print(f"✅ Found {len(match_ids)} match IDs")

# Step 4: Download timelines (.json)
os.makedirs("timelines", exist_ok=True)

for match_id in match_ids:
    timeline_path = f'timelines/{match_id}_timeline.json'
    if os.path.exists(timeline_path):
        print(f"⏭️  Timeline for {match_id} already exists, skipping...")
        continue
        
    url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        timeline = response.json()
        with open(timeline_path, 'w') as f:
            json.dump(timeline, f, indent=2)
        print(f"✅ Saved timeline for {match_id}")
    else:
        print(f"❌ Failed to get match {match_id}: {response.status_code} - {response.text}")

# Step 5: Download match metadata (champion names, etc.)
os.makedirs("matches", exist_ok=True)
for match_id in match_ids:
    match_path = f'matches/{match_id}.json'
    if os.path.exists(match_path):
        print(f"⏭️  Match data for {match_id} already exists, skipping...")
        continue
        
    match_url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    response = requests.get(match_url, headers=headers)
    if response.status_code == 200:
        match = response.json()
        with open(match_path, 'w') as f:
            json.dump(match, f, indent=2)
        print(f"✅ Saved match metadata for {match_id}")
    else:
        print(f"❌ Failed to get metadata for {match_id}: {response.status_code} - {response.text}")
