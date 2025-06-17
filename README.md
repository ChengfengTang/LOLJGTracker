# 🧠 League of Legends AI Jungler Tracker

A web application that allows users to track and visualize League of Legends matches with a focus on jungler movement and game events.

## 🌟 Features

### 🔍 Summoner Lookup
- Search for players by their Riot ID (name#tag)
- Secure API key handling
- Recent matches retrieval
- Persistent summoner data storage

### 📊 Match History
- View recent matches with detailed information
- Game mode display
- Match duration formatting
- Copy match ID functionality
- Team composition visualization
- Cached match data for faster retrieval

### 🎮 Replay System
- Interactive map visualization
- Real-time champion movement tracking
- Event-based interpolation for:
  - Kills and assists
  - Deaths and respawns
  - Monster kills
  - Level ups
- Accurate death timer calculation based on:
  - Champion level
  - Game time
  - Base Respawn Window (BRW)
  - Time Impact Factor (TIF)

### 📈 Data Processing
- Per-minute snapshots of player stats:
  - Position (x, y)
  - Level
  - CS (minions + jungle)
  - Gold
- Event tracking:
  - Champion kills and assists
  - Elite monster kills (Dragon, Herald, Baron)
  - Level ups
  - Deaths and respawns

## 🛠️ Technical Stack
- **Backend**: Python (Flask)
- **Frontend**: HTML, JavaScript, p5.js
- **APIs**: Riot Games API (match-v5)
- **Database**: MySQL
- **Data Processing**: Python (requests, json)

## 🔧 Setup
1. Get a Riot API key from [Riot Developer Portal](https://developer.riotgames.com/)
2. Clone the repository
3. Install MySQL and create a database named 'test'
4. Create required tables:
   ```sql
   CREATE TABLE summoners (
       summoner_id INT AUTO_INCREMENT PRIMARY KEY,
       username VARCHAR(100) NOT NULL,
       tag VARCHAR(50) NOT NULL,
       puuid VARCHAR(100) NOT NULL,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
   );

   CREATE TABLE matches (
       match_id VARCHAR(100) PRIMARY KEY,
       match_data JSON
   );

   CREATE TABLE timelines (
       match_id VARCHAR(100) PRIMARY KEY,
       timeline_data JSON,
       FOREIGN KEY (match_id) REFERENCES matches(match_id)
   );
   ```
5. Install dependencies: `pip install -r requirements.txt`
6. Run the application: `python application.py`

## 💬 Credits
Built by: Cheng

## 📝 License
This project is not endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing League of Legends.
