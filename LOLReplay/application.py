"""
League of Legends Replay Tracker Application
===========================================

This Flask web application provides functionality to:
1. Look up League of Legends summoners by their name and tag
2. Retrieve and display recent match history
3. Fetch detailed match data and timelines
4. Visualize match replays and statistics

The application uses:
- Flask for the web framework
- Riot Games API for League of Legends data
- MySQL for data persistence
- Environment variables for configuration
"""

from flask import Flask, request, jsonify, send_file, render_template
import requests
import os
import json
from dotenv import load_dotenv
import mysql.connector

# Load environment variables from .env file for secure configuration
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Running server on http://127.0.0.1:5000
# Set your Riot API key here
# Get API key from https://developer.riotgames.com/
# One way is to make users enter their own api key so it could never be an issue for public website
#API_KEY = 'RGAPI-b761cebd-10ec-4ea8-9eec-4cc2d45411e0'
#HEADERS = {'X-Riot-Token': API_KEY}

MATCH_REGION = "americas" # May need to add options for EUROPE and ASIA but doesn't seem to matter right now

# MySQL connection
def get_db_connection():
    """
    Establishes and returns a connection to the MySQL database.
    Returns:
        mysql.connector.connection: Database connection object
    """
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="test"
    )

@app.route("/api/lookup")
def lookup():
    """
    API endpoint to look up a League of Legends summoner by name and tag.
    
    Query Parameters:
        name (str): Summoner's name
        tag (str): Summoner's tag (e.g., NA1)
        api_key (str): Riot Games API key
    
    Returns:
        JSON response containing the summoner's PUUID and other account information
    """
    name = request.args.get("name")
    tag = request.args.get("tag")
    api_key = request.args.get("api_key")
    
    # Validate required parameters
    if not name or not tag or not api_key:
        return jsonify({"error": "Missing name, tag, or API key"}), 400

    # Set up API request headers
    headers = {'X-Riot-Token': api_key}
    url = f"https://{MATCH_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
    r = requests.get(url, headers=headers)
    # If the request fails (status code not 200), returns an error.
    # If successful, returns the API's JSON response (e.g., {"puuid": "abc123", ...}).
    if r.status_code == 429:
        return jsonify({"error": "Rate limit exceeded, try again later"}), 429
    elif r.status_code != 200:
        return jsonify({"error": f"Failed to fetch PUUID: {r.status_code}"}), r.status_code

    # Store summoner data in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO summoners (username, tag, puuid) 
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        username = VALUES(username),
        tag = VALUES(tag),
        updated_at = CURRENT_TIMESTAMP
        """,
        (name, tag, r.json().get('puuid'))
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(r.json())

@app.route("/api/matches/<puuid>")
def get_matches(puuid):
    """
    API endpoint to retrieve recent matches for a summoner.
    
    Parameters:
        puuid (str): Player's unique identifier
    
    Query Parameters:
        api_key (str): Riot Games API key
        start (int): Starting index for pagination (default: 0)
        count (int): Number of matches to retrieve (default: 20)
    
    Returns:
        JSON array of match IDs
    """
    api_key = request.args.get("api_key")
    if not api_key:
        return jsonify({"error": "Missing API key"}), 400

    # Parse and validate pagination parameters
    start = request.args.get("start", "0")
    count = request.args.get("count", "20")
    
    try:
        start = int(start)
        count = int(count)
    except ValueError:
        return jsonify({"error": "Invalid start or count parameters"}), 400

    # Fetch matches from Riot API
    headers = {'X-Riot-Token': api_key}
    # Note that For development keys, Riot enforces: 20 requests per second, 100 requests every 2 minutes (120s)
    url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
    r = requests.get(url, headers=headers)
    
    # Handle API response
    if r.status_code == 429:
        return jsonify({"error": "Rate limit exceeded, try again later"}), 429
    elif r.status_code != 200:
        return jsonify({"error": f"Failed to fetch matches: {r.status_code}"}), r.status_code
    
    return jsonify(r.json())

@app.route("/api/matches/<puuid>/more")
def get_more_matches(puuid):
    """
    API endpoint to load additional matches for pagination.
    Similar to get_matches but specifically for loading more matches.
    
    Parameters and functionality are identical to get_matches.
    """
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
    """
    API endpoint to retrieve detailed match data and timeline.
    
    Parameters:
        match_id (str): Unique identifier for the match
    
    Query Parameters:
        api_key (str): Riot Games API key
    
    Returns:
        JSON object containing match metadata and timeline data
    """
    api_key = request.args.get("api_key")
    if not api_key:
        return jsonify({"error": "Missing API key"}), 400

    # Try to get data from MySQL first
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if match exists in database
    cursor.execute("SELECT match_data FROM matches WHERE match_id = %s", (match_id,))
    match_result = cursor.fetchone()
    
    cursor.execute("SELECT timeline_data FROM timelines WHERE match_id = %s", (match_id,))
    timeline_result = cursor.fetchone()

    # If not in database, fetch from Riot API and store
    if not match_result or not timeline_result:
        headers = {'X-Riot-Token': api_key}
        
        # Get match data
        url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return jsonify({"error": f"Failed to fetch match metadata: {r.status_code}"}), r.status_code
        match_data = r.json()
        
        # Get timeline data
        url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return jsonify({"error": f"Failed to fetch timeline: {r.status_code}"}), r.status_code
        timeline_data = r.json()
        
        # Store in MySQL
        cursor.execute(
            "INSERT INTO matches (match_id, match_data) VALUES (%s, %s)",
            (match_id, json.dumps(match_data))
        )
        cursor.execute(
            "INSERT INTO timelines (match_id, timeline_data) VALUES (%s, %s)",
            (match_id, json.dumps(timeline_data))
        )
        conn.commit()
    else:
        # Use data from database
        match_data = json.loads(match_result['match_data'])
        timeline_data = json.loads(timeline_result['timeline_data'])

    cursor.close()
    conn.close()
    
    return jsonify({"metadata": match_data, "timeline": timeline_data})

# Route handlers for serving HTML pages
@app.route('/')
def home():
    """Serve the main summoner lookup page"""
    return render_template('SummonerLookup.html')

# Serve matches page
@app.route('/matches.html')
def matches_page():
    """Serve the matches history page"""
    return render_template('matches.html')

# Serve replay page
@app.route('/replay.html')
def replay_page():
    """Serve the match replay visualization page"""
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