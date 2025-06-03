#Overview of the Project
#This is a web application that allows users to:

#Look up a League of Legends summoner by their name and tag (e.g., "Player#NA1").
#Retrieve a list of recent matches for that summoner.
#Fetch detailed match data and timelines for visualization.
#Display this information through web pages (SummonerLookup.html, matches.html, replay.html).


from flask import Flask, request, jsonify, send_file
import requests
import os
import json

app = Flask(__name__)

# Running server on http://127.0.0.1:5000
# Set your Riot API key here
API_KEY = 'RGAPI-d4c07ea9-7ceb-4b95-b24e-fe58067d1a03'
HEADERS = {'X-Riot-Token': API_KEY}
MATCH_REGION = "americas" # May need to add options for EUROPE and ASIA but doesn't seem to matter right now
os.makedirs("timelines", exist_ok=True)
os.makedirs("matches", exist_ok=True)

@app.route("/api/lookup")
def lookup():
    name = request.args.get("name")
    tag = request.args.get("tag")
    if not name or not tag:
        return jsonify({"error": "Missing name or tag"}), 400

    url = f"https://{MATCH_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
    r = requests.get(url, headers=HEADERS)
    # If the request fails (status code not 200), returns an error.
    # If successful, returns the API’s JSON response (e.g., {"puuid": "abc123", ...}).
    if r.status_code == 429:
        return jsonify({"error": "Rate limit exceeded, try again later"}), 429
    elif r.status_code != 200:
        return jsonify({"error": f"Failed to fetch PUUID: {r.status_code}"}), r.status_code

    return jsonify(r.json())

@app.route("/api/matches/<puuid>")
def get_matches(puuid):
    url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count=20" # TODO : add option that gets more instead of 20 at once only
    # Note that For development keys, Riot enforces: 20 requests per second, 100 requests every 2 minutes (120s)
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 429:
        return jsonify({"error": "Rate limit exceeded, try again later"}), 429
    elif r.status_code != 200:
        return jsonify({"error": f"Failed to fetch matches: {r.status_code}"}), r.status_code
    
    return jsonify(r.json())

@app.route("/api/match/<match_id>")
def get_match_data(match_id):
    # Get metadata local or fetch it
    meta = f"matches/{match_id}.json"
    if not os.path.exists(meta): # If
        url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 429:
            return jsonify({"error": "Rate limit exceeded, try again later"}), 429
        elif r.status_code == 200:
            with open(meta, "w") as f:
                json.dump(r.json(), f)
        else:
            return jsonify({"error": f"Failed to fetch match metadata: {r.status_code}"}), r.status_code

    # Get timeline local or fetch it
    timeline = f"timelines/{match_id}_timeline.json"
    if not os.path.exists(timeline):
        url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 429:
            return jsonify({"error": "Rate limit exceeded, try again later"}), 429
        elif r.status_code == 200:
            with open(timeline, "w") as f:
                json.dump(r.json(), f)
        else:
            return jsonify({"error": f"Failed to fetch timeline: {r.status_code}"}), r.status_code

    # Send both files
    try:
        with open(meta) as f:
            meta = json.load(f)
        with open(timeline) as f:
            timeline = json.load(f)
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 500

    return jsonify({"metadata": meta, "timeline": timeline})

# Serve lookup page
@app.route('/')
def home():
    return send_file('SummonerLookup.html')

# Serve matches page
@app.route('/matches.html')
def matches_page():
    return send_file('matches.html')

# Serve replay page
@app.route('/replay.html')
def replay_page():
    return send_file('replay.html') 


if __name__ == "__main__":
    app.run(debug=True)
