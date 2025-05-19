import requests
import json
import os
# Step1: Get API key from https://developer.riotgames.com/
api_key = 'RGAPI-df2ba4e6-ca77-4cbc-b0f9-9a7153ad2e61'

headers = {'X-Riot-Token': api_key}

# Step 2: Look up PUUID from Riot ID
riot_id_name = "TL Honda CoreJJ" #Just an example
riot_id_tagline = "1123"
# API Docs https://developer.riotgames.com/apis#summoner-v4/GET_getBySummonerId
account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{riot_id_name}/{riot_id_tagline}" 

response = requests.get(account_url, headers=headers)
if response.status_code != 200:
    raise Exception(f"❌ Failed to get PUUID: {response.status_code} - {response.text}")

puuid = response.json()["puuid"]
print(f"✅ PUUID for {riot_id_name}#{riot_id_tagline}: {puuid}")

# Step 3: Get list of recent match IDs for that PUUID
match_region = "americas"
count = 50
matchlist_url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"

response = requests.get(matchlist_url, headers=headers)
if response.status_code != 200:
    raise Exception(f"❌ Failed to get match IDs: {response.status_code} - {response.text}")

match_ids = response.json()
print(f"✅ Found {len(match_ids)} match IDs")

# Step 4: Download timelines (.json)
os.makedirs("timelines", exist_ok=True)

for match_id in match_ids:
    url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        timeline = response.json()
        with open(f'timelines/{match_id}_timeline.json', 'w') as f:
            json.dump(timeline, f, indent=2)
        print(f"✅ Saved timeline for {match_id}")
    else:
        print(f"❌ Failed to get match {match_id}: {response.status_code} - {response.text}")