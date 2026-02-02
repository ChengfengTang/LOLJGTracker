# 🧠 League Insights

A dual-project repository for League of Legends jungler analysis: machine learning model training and web-based match exploration.

## 📁 Project Structure

This repository is organized into two independent subprojects:

### **`Predict/`** - Machine Learning Training Project
ML pipeline for jungler path prediction and analysis.

**Components:**
- **Data Ingestion**: `topNPlayers.py` - Fetches top ranked players (Challenger, Grandmaster, Master) for training data collection
- **Timeline Parsing**: `AllInfo.py` - Match timeline analysis and data processing
- **Data Fetching**: `fetchdata.py` - Riot API data fetching utilities
- **Feature Engineering**: (To be implemented)
- **Model Training**: (To be implemented)
- **Model Artifacts**: (To be stored in `models/` directory)

**Data Storage:**
- Fetches and stores match data locally in `timelines/` and `matches/` directories
- Used for training and testing ML models

### **`Replay/`** - Web Application (OP.GG-style)
OP.GG-style web application for match exploration and visualization.

**Components:**
- **Summoner Lookup**: Search for players by Riot ID (name#tag)
- **Match Browsing**: View recent matches with detailed information
- **Replay Visualization**: Interactive map visualization with real-time champion movement tracking
- **Model Inference API**: Read-only API for ML model predictions (to be implemented)

**Architecture:**
- Flask-based web application
- No database - every search fetches fresh data from Riot API
- Client-side visualization using p5.js

## 🌟 Features

### 🔍 Summoner Lookup
- Search for players by their Riot ID (name#tag)
- Secure API key handling
- Recent matches retrieval

### 📊 Match History
- View recent matches with detailed information
- Game mode display
- Match duration formatting
- Copy match ID functionality
- Team composition visualization

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

### 📈 Data Processing (Predict)
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

### Replay
- **Backend**: Python (Flask)
- **Frontend**: HTML, JavaScript, p5.js
- **APIs**: Riot Games API (match-v5)
- **Storage**: No database - fresh API calls on each request

### Predict
- **Language**: Python
- **APIs**: Riot Games API (match-v5)
- **Storage**: Local file system (`timelines/`, `matches/` directories)
- **ML Framework**: (To be determined)

## 🔧 Setup

### Prerequisites
1. Get a Riot API key from [Riot Developer Portal](https://developer.riotgames.com/)
2. Python 3.7+
3. (Optional) MySQL - only needed if you want to use database features in Predict

### Replay Setup
1. Navigate to the web application directory:
   ```bash
   cd Replay
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python application.py
   ```
4. Open your browser to `http://127.0.0.1:5000`

### Predict Setup
1. Navigate to the ML project directory:
   ```bash
   cd Predict
   ```
2. Install dependencies (create `requirements.txt` as needed)
3. Fetch training data:
   ```bash
   python topNPlayers.py  # Fetches top players
   python fetchdata.py    # Fetches match data for training
   ```
4. Run timeline analysis:
   ```bash
   python AllInfo.py
   ```

## 📝 Notes

- **Replay** is stateless - no database required. Every search fetches fresh data from Riot API.
- **Predict** stores data locally for training purposes. Data is fetched using `topNPlayers.py` and `fetchdata.py`.
- Both projects can run independently.
- Model inference API in Replay will read model artifacts from Predict (to be implemented).

## 💬 Credits
Built by: Chengfeng Tang
