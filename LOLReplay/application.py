#Overview of the Project
#This is a web application that allows users to:

#Look up a League of Legends summoner by their name and tag (e.g., "Player#NA1").
#Retrieve a list of recent matches for that summoner.
#Fetch detailed match data and timelines for visualization.
#Display this information through web pages (SummonerLookup.html, matches.html, replay.html).


from flask import Flask, request, jsonify, send_file, render_template
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Running server on http://127.0.0.1:5000
# Set your Riot API key here
# Get API key from https://developer.riotgames.com/
# One way is to make users enter their own api key so it could never be an issue for public website
#API_KEY = 'RGAPI-b761cebd-10ec-4ea8-9eec-4cc2d45411e0'
#HEADERS = {'X-Riot-Token': API_KEY}

MATCH_REGION = "americas" # May need to add options for EUROPE and ASIA but doesn't seem to matter right now
os.makedirs("timelines", exist_ok=True)
os.makedirs("matches", exist_ok=True)

@app.route("/api/lookup")
def lookup():
    name = request.args.get("name")
    tag = request.args.get("tag")
    api_key = request.args.get("api_key")
    
    if not name or not tag or not api_key:
        return jsonify({"error": "Missing name, tag, or API key"}), 400

    headers = {'X-Riot-Token': api_key}
    url = f"https://{MATCH_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
    r = requests.get(url, headers=headers)
    # If the request fails (status code not 200), returns an error.
    # If successful, returns the API's JSON response (e.g., {"puuid": "abc123", ...}).
    if r.status_code == 429:
        return jsonify({"error": "Rate limit exceeded, try again later"}), 429
    elif r.status_code != 200:
        return jsonify({"error": f"Failed to fetch PUUID: {r.status_code}"}), r.status_code

    return jsonify(r.json())

@app.route("/api/matches/<puuid>")
def get_matches(puuid):
    api_key = request.args.get("api_key")
    if not api_key:
        return jsonify({"error": "Missing API key"}), 400

    start = request.args.get("start", "0")
    count = request.args.get("count", "20")
    
    try:
        start = int(start)
        count = int(count)
    except ValueError:
        return jsonify({"error": "Invalid start or count parameters"}), 400

    headers = {'X-Riot-Token': api_key}
    # Note that For development keys, Riot enforces: 20 requests per second, 100 requests every 2 minutes (120s)
    url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
    r = requests.get(url, headers=headers)
    if r.status_code == 429:
        return jsonify({"error": "Rate limit exceeded, try again later"}), 429
    elif r.status_code != 200:
        return jsonify({"error": f"Failed to fetch matches: {r.status_code}"}), r.status_code
    
    return jsonify(r.json())

@app.route("/api/matches/<puuid>/more")
def get_more_matches(puuid):
    api_key = request.args.get("api_key")
    if not api_key:
        return jsonify({"error": "Missing API key"}), 400

    start = request.args.get("start", "0")
    count = request.args.get("count", "20")
    
    try:
        start = int(start)
        count = int(count)
    except ValueError:
        return jsonify({"error": "Invalid start or count parameters"}), 400

    headers = {'X-Riot-Token': api_key}
    url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
    r = requests.get(url, headers=headers)
    if r.status_code == 429:
        return jsonify({"error": "Rate limit exceeded, try again later"}), 429
    elif r.status_code != 200:
        return jsonify({"error": f"Failed to fetch matches: {r.status_code}"}), r.status_code
    
    return jsonify(r.json())

@app.route("/api/match/<match_id>")
def get_match_data(match_id):
    api_key = request.args.get("api_key")
    if not api_key:
        return jsonify({"error": "Missing API key"}), 400

    headers = {'X-Riot-Token': api_key}
    # Get metadata local or fetch it
    meta = f"matches/{match_id}.json"
    if not os.path.exists(meta): # If
        url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        r = requests.get(url, headers=headers)
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
        r = requests.get(url, headers=headers)
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
    return render_template('SummonerLookup.html')

# Serve matches page
@app.route('/matches.html')
def matches_page():
    return render_template('matches.html')

# Serve replay page
@app.route('/replay.html')
def replay_page():
    return render_template('replay.html') 


if __name__ == "__main__":
    # Local 
    #app.run(debug=True)

    # AWS
    # eb init -p python-3.9 lol-replay --region us-west-3
    # eb create lol-replay-env
    # eb deploy
    # eb open
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)