from flask import Flask, request, jsonify, send_file, render_template_string
import requests
import os
import json

app = Flask(__name__)

# Running server on http://127.0.0.1:5000
# Set your Riot API key here
API_KEY = 'RGAPI-f240c49a-b5d4-4bd1-8641-c1c69fb7f937'
HEADERS = {'X-Riot-Token': API_KEY}
MATCH_REGION = "americas" # May need to add options for EUROPE and ASIA but doesn't seem to matter right now

# Ensure directories exist
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
    if r.status_code != 200:
        return jsonify({"error": f"Failed to fetch PUUID: {r.status_code}"}), r.status_code

    return jsonify(r.json())

@app.route("/api/matches/<puuid>")
def get_matches(puuid):
    url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count=20"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return jsonify({"error": f"Failed to fetch matches: {r.status_code}"}), r.status_code

    return jsonify(r.json())

@app.route("/api/match/<match_id>")
def get_match_data(match_id):
    # Get metadata
    meta_file = f"matches/{match_id}.json"
    if not os.path.exists(meta_file):
        url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            with open(meta_file, "w") as f:
                json.dump(r.json(), f)
        else:
            return jsonify({"error": f"Failed to fetch match metadata: {r.status_code}"}), r.status_code

    # Get timeline
    timeline_file = f"timelines/{match_id}_timeline.json"
    if not os.path.exists(timeline_file):
        url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            with open(timeline_file, "w") as f:
                json.dump(r.json(), f)
        else:
            return jsonify({"error": f"Failed to fetch timeline: {r.status_code}"}), r.status_code

    # Send both files
    with open(meta_file) as f:
        meta = json.load(f)
    with open(timeline_file) as f:
        timeline = json.load(f)

    return jsonify({"metadata": meta, "timeline": timeline})

# Serve static visualization files (optional if using frontend separately)
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
    return send_file('replay.html')  # Not created yet


if __name__ == "__main__":
    app.run(debug=True)
