# 🧠 League Insights

A multi-module repository for League of Legends jungler analysis: machine learning model training, web-based match exploration, and live game monitoring with real-time predictions.

## 📁 Project Structure

This repository is organized into three independent modules:

### **`Predict/`** - Machine Learning Training Project
ML pipeline for jungler path prediction and analysis.

**Components:**
- **Data Ingestion**: `topNPlayers.py` - Fetches top ranked players (Challenger, Grandmaster, Master) for training data collection
- **Timeline Parsing**: `AllInfo.py` - Match timeline analysis and data processing
- **Data Fetching**: `fetchdata.py` - Riot API data fetching utilities
- **Champion Categorization**: `TDchampCategory.py` - Categorizes champions by jungler playstyle (aggressive, full_clear, etc.)
- **Model Training**: `TDpredict.py` - ML model training and prediction for enemy jungler location prediction
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

### **`Live/`** - Live Game Monitor & Prediction System
Real-time game monitoring system that visually watches the minimap and provides instant jungler path predictions.

**Components:**
- **Minimap Monitor**: Visually watches the game minimap using screen capture/computer vision
- **Jungler Detection**: Detects when the jungler appears on the minimap and captures coordinates
- **Position Data Collection**: Records captured position information for training data
- **Model Inference Engine**: Loads trained models from `Predict/models/` for live predictions
- **Real-time Prediction API**: Provides live-time jungler path predictions as the game progresses
- **Data Pipeline**: Processes captured minimap data and feeds it into the trained ML model

**Architecture:**
- Visual minimap monitoring (screen capture/computer vision) - no Riot API for live data
- Real-time coordinate capture when jungler appears on minimap
- Captured position data can be used for training (counts as position info)
- Model inference using trained artifacts from Predict module
- Continuous prediction updates as new position data is captured
- Integration with Predict module's trained models

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
- Champion categorization by playstyle (aggressive, full_clear, etc.)
- ML model training for enemy jungler location prediction
- Category-specific model training for improved accuracy

### 🎯 Live Game Monitoring (Live)
- Visual minimap monitoring using screen capture/computer vision
- Automatic jungler detection when they appear on the minimap
- Real-time coordinate capture from minimap positions
- Captured position data used for training (counts as position info)
- Continuous model inference using trained ML models
- Real-time jungler path predictions as the game progresses
- Integration with Predict module's trained models
- Live prediction API for real-time game analysis

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
- **ML Framework**: scikit-learn (Decision Tree, Gradient Boosting)
- **Libraries**: pandas, numpy, scikit-learn

### Live
- **Language**: Python
- **Data Sources**: Visual minimap monitoring (screen capture/computer vision) - no Riot API
- **Computer Vision**: Screen capture and minimap analysis to detect jungler positions
- **Model Integration**: Loads trained models from `Predict/models/`
- **Real-time Processing**: Continuous minimap monitoring and coordinate capture
- **Data Collection**: Captured positions can be used as training data
- **Framework**: (To be determined - likely OpenCV, PIL, or similar for screen capture)

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
5. Train prediction models:
   ```bash
   python TDpredict.py  # Trains models for enemy jungler location prediction
   ```
   - Models will be saved to `models/` directory
   - Supports category-specific models (aggressive, full_clear, etc.)
   - Model artifacts will be used by Live module for real-time predictions

### Live Setup
1. Navigate to the live monitoring directory:
   ```bash
   cd Live
   ```
2. Install dependencies (create `requirements.txt` as needed)
   - Screen capture libraries (e.g., PIL, mss, pyautogui)
   - Computer vision libraries (e.g., OpenCV)
3. Ensure Predict module has trained models in `Predict/models/` directory
4. Configure live game monitoring:
   - Set up minimap screen capture region
   - Configure jungler detection parameters
   - No Riot API needed - purely visual monitoring
5. Run the live monitor:
   ```bash
   python live_monitor.py  # (To be implemented)
   ```
6. The system will:
   - Visually watch the minimap in real-time
   - Detect when jungler appears and capture coordinates
   - Use captured position data for training (as position info)
   - Feed real-time data into trained models from Predict
   - Provide continuous jungler path predictions

## 📝 Notes

- **Replay** is stateless - no database required. Every search fetches fresh data from Riot API.
- **Predict** stores data locally for training purposes. Data is fetched using `topNPlayers.py` and `fetchdata.py`.
- **Live** requires trained models from Predict module. Ensure models are trained and saved in `Predict/models/` before running Live.
- **Live** does not use Riot API - it visually monitors the minimap using screen capture/computer vision.
- When the jungler appears on the minimap, Live captures their coordinates, which counts as position info for training.
- All three modules can run independently, but Live depends on Predict for model artifacts.
- Model inference API in Replay will read model artifacts from Predict (to be implemented).
- Live module provides real-time predictions during active games, while Replay visualizes completed matches.

## 💬 Credits
Built by: Chengfeng Tang
