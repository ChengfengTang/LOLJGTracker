"""
League of Legends Enemy Jungler Location Predictor
This module trains and uses ML models to predict enemy jungler location based on:
- Current position (x, y coordinates)
- Time (game time in seconds/minutes)
- Champion category (aggressive, full_clear, etc.)

Future enhancements:
- Lane states
- Objective timers
- Team composition
- Recent events (kills, objectives taken)
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import pickle
from typing import Dict, List, Tuple, Optional

# Import champion categories
try:
    from champCategory import get_champion_category, CHAMPION_CATEGORIES
except ImportError:
    print("Warning: champCategory.py not found. Champion categories will not be used.")
    get_champion_category = None

# Project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
timelines_dir = os.path.join(project_root, "timelines")
matches_dir = os.path.join(project_root, "matches")
models_dir = os.path.join(project_root, "Predict", "models")
os.makedirs(models_dir, exist_ok=True)


class JunglerPredictor:
    """
    Main class for predicting enemy jungler locations.
    Supports both Decision Tree and Gradient Boosting models.
    """
    
    def __init__(self, model_type: str = "gradient_boosting", use_categories: bool = True):
        """
        Initialize the predictor.
        
        Args:
            model_type: "decision_tree" or "gradient_boosting"
            use_categories: Whether to train separate models per champion category
        """
        self.model_type = model_type
        self.use_categories = use_categories
        self.models = {}  # Will store models per category
        self.category_models = {} if use_categories else None
        
    def _create_model(self):
        """Create a model instance based on model_type."""
        if self.model_type == "decision_tree":
            return DecisionTreeRegressor(
                max_depth=20,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42
            )
        elif self.model_type == "gradient_boosting":
            return GradientBoostingRegressor(
                n_estimators=100,
                max_depth=10,
                learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model_type: {self.model_type}")
    
    def extract_features(self, timeline_data: Dict, match_data: Dict, participant_id: int) -> pd.DataFrame:
        """
        Extract features from match data for a specific participant (enemy jungler).
        
        Args:
            timeline_data: Timeline JSON data
            match_data: Match metadata JSON data
            participant_id: Participant ID of the enemy jungler
            
        Returns:
            DataFrame with features: [x, y, time, game_minutes, level, cs, gold, ...]
        """
        features = []
        frames = timeline_data["info"]["frames"]
        
        # Get champion name for category
        champion_name = None
        for p in match_data["info"]["participants"]:
            if p["participantId"] == participant_id:
                champion_name = p["championName"]
                break
        
        champion_category = None
        if self.use_categories and get_champion_category and champion_name:
            champion_category = get_champion_category(champion_name, primary=True)
        
        for frame in frames:
            timestamp_ms = frame["timestamp"]
            timestamp_sec = timestamp_ms / 1000.0
            game_minutes = timestamp_sec / 60.0
            
            participant_frame = frame["participantFrames"].get(str(participant_id))
            if not participant_frame or "position" not in participant_frame:
                continue
            
            pos = participant_frame["position"]
            x = pos["x"]
            y = pos["y"]
            level = participant_frame.get("level", 1)
            cs = participant_frame.get("minionsKilled", 0) + participant_frame.get("jungleMinionsKilled", 0)
            gold = participant_frame.get("currentGold", 0)
            
            # Basic features (will be expanded later)
            feature_row = {
                "x": x,
                "y": y,
                "time": timestamp_sec,
                "game_minutes": game_minutes,
                "level": level,
                "cs": cs,
                "gold": gold,
                "champion_category": champion_category if champion_category else "unknown",
                "participant_id": participant_id
            }
            
            features.append(feature_row)
        
        return pd.DataFrame(features)
    
    def prepare_training_data(self, match_files: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load and prepare training data from match files.
        
        Args:
            match_files: List of match ID strings (without extension)
            
        Returns:
            X (features), y (target: future x, y coordinates)
        """
        all_features = []
        all_targets = []
        
        for match_id in match_files:
            timeline_path = os.path.join(timelines_dir, f"{match_id}_timeline.json")
            match_path = os.path.join(matches_dir, f"{match_id}.json")
            
            if not os.path.exists(timeline_path) or not os.path.exists(match_path):
                print(f"⚠️  Skipping {match_id}: files not found")
                continue
            
            try:
                with open(timeline_path) as f:
                    timeline_data = json.load(f)
                with open(match_path) as f:
                    match_data = json.load(f)
                
                # Find enemy jungler (participantId 6-10 for enemy team, or identify by role)
                # For now, we'll use participant 6 as enemy jungler (simplified)
                # TODO: Properly identify jungler role
                enemy_jungler_id = 6  # Simplified - should identify actual jungler
                
                features_df = self.extract_features(timeline_data, match_data, enemy_jungler_id)
                
                if len(features_df) < 2:
                    continue
                
                # Create targets: predict next position (shift by 1 frame)
                # For now, predict position 30 seconds ahead
                future_seconds = 30
                features_df["future_x"] = None
                features_df["future_y"] = None
                
                for i in range(len(features_df)):
                    current_time = features_df.iloc[i]["time"]
                    future_time = current_time + future_seconds
                    
                    # Find closest future position
                    future_rows = features_df[features_df["time"] >= future_time]
                    if len(future_rows) > 0:
                        future_row = future_rows.iloc[0]
                        features_df.at[i, "future_x"] = future_row["x"]
                        features_df.at[i, "future_y"] = future_row["y"]
                
                # Remove rows without future targets
                features_df = features_df.dropna(subset=["future_x", "future_y"])
                
                if len(features_df) == 0:
                    continue
                
                # Separate features and targets
                feature_cols = ["x", "y", "time", "game_minutes", "level", "cs", "gold"]
                X_batch = features_df[feature_cols]
                y_batch = features_df[["future_x", "future_y"]]
                
                all_features.append(X_batch)
                all_targets.append(y_batch)
                
            except Exception as e:
                print(f"❌ Error processing {match_id}: {e}")
                continue
        
        if len(all_features) == 0:
            raise ValueError("No training data could be loaded!")
        
        X = pd.concat(all_features, ignore_index=True)
        y = pd.concat(all_targets, ignore_index=True)
        
        return X, y
    
    def train(self, match_files: List[str], save_model: bool = True):
        """
        Train the prediction model(s).
        
        Args:
            match_files: List of match ID strings to use for training
            save_model: Whether to save the trained model to disk
        """
        print(f"📊 Loading training data from {len(match_files)} matches...")
        X, y = self.prepare_training_data(match_files)
        
        print(f"✅ Loaded {len(X)} training samples")
        print(f"   Features: {list(X.columns)}")
        print(f"   Targets: {list(y.columns)}")
        
        if self.use_categories and "champion_category" in X.columns:
            # Train separate models per category
            categories = X["champion_category"].unique()
            print(f"\n🎯 Training {len(categories)} category-specific models...")
            
            for category in categories:
                category_mask = X["champion_category"] == category
                X_cat = X[category_mask].drop(columns=["champion_category"])
                y_cat = y[category_mask]
                
                if len(X_cat) < 10:  # Need minimum samples
                    print(f"⚠️  Skipping {category}: insufficient data ({len(X_cat)} samples)")
                    continue
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X_cat, y_cat, test_size=0.2, random_state=42
                )
                
                model = self._create_model()
                model.fit(X_train, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                
                print(f"   {category}: MSE={mse:.2f}, MAE={mae:.2f} ({len(X_cat)} samples)")
                
                self.category_models[category] = model
                
                if save_model:
                    model_path = os.path.join(models_dir, f"{self.model_type}_{category}.pkl")
                    with open(model_path, "wb") as f:
                        pickle.dump(model, f)
                    print(f"   💾 Saved model to {model_path}")
        else:
            # Train single model
            print(f"\n🎯 Training single model...")
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            model = self._create_model()
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            print(f"✅ Model trained: MSE={mse:.2f}, MAE={mae:.2f}")
            
            self.models["default"] = model
            
            if save_model:
                model_path = os.path.join(models_dir, f"{self.model_type}_default.pkl")
                with open(model_path, "wb") as f:
                    pickle.dump(model, f)
                print(f"💾 Saved model to {model_path}")
    
    def predict(self, x: float, y: float, time: float, 
                game_minutes: Optional[float] = None,
                level: int = 1, cs: int = 0, gold: int = 0,
                champion_category: Optional[str] = None) -> Tuple[float, float]:
        """
        Predict enemy jungler location.
        
        Args:
            x: Current x coordinate
            y: Current y coordinate
            time: Current game time in seconds
            game_minutes: Game time in minutes (auto-calculated if None)
            level: Champion level
            cs: Creep score
            gold: Current gold
            champion_category: Champion category (if using category models)
            
        Returns:
            Predicted (x, y) coordinates
        """
        if game_minutes is None:
            game_minutes = time / 60.0
        
        # Prepare feature vector
        features = np.array([[x, y, time, game_minutes, level, cs, gold]])
        
        # Select appropriate model
        if self.use_categories and self.category_models and champion_category:
            if champion_category in self.category_models:
                model = self.category_models[champion_category]
            else:
                # Fallback to default or first available
                model = list(self.category_models.values())[0] if self.category_models else None
        else:
            model = self.models.get("default")
        
        if model is None:
            raise ValueError("No trained model available. Train the model first.")
        
        prediction = model.predict(features)[0]
        return prediction[0], prediction[1]  # future_x, future_y
    
    def load_model(self, category: Optional[str] = None):
        """Load a trained model from disk."""
        if category:
            model_path = os.path.join(models_dir, f"{self.model_type}_{category}.pkl")
        else:
            model_path = os.path.join(models_dir, f"{self.model_type}_default.pkl")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        
        if category:
            self.category_models[category] = model
        else:
            self.models["default"] = model
        
        print(f"✅ Loaded model from {model_path}")


def get_available_matches() -> List[str]:
    """Get list of available match IDs from timelines directory."""
    match_ids = []
    for filename in os.listdir(timelines_dir):
        if filename.endswith("_timeline.json"):
            match_id = filename.replace("_timeline.json", "")
            match_ids.append(match_id)
    return match_ids


if __name__ == "__main__":
    # Example usage
    print("🧠 Enemy Jungler Location Predictor")
    print("=" * 50)
    
    # Initialize predictor
    predictor = JunglerPredictor(
        model_type="gradient_boosting",  # or "decision_tree"
        use_categories=True
    )
    
    # Get available matches
    match_files = get_available_matches()
    print(f"\n📁 Found {len(match_files)} match files")
    
    if len(match_files) == 0:
        print("⚠️  No match files found. Run fetchdata.py first to download matches.")
    else:
        # Use subset for testing (use all for actual training)
        training_matches = match_files[:10]  # Use first 10 for testing
        print(f"🎯 Using {len(training_matches)} matches for training...")
        
        # Train model
        try:
            predictor.train(training_matches, save_model=True)
        except Exception as e:
            print(f"❌ Training failed: {e}")
        
        # Example prediction
        print("\n🔮 Example prediction:")
        try:
            pred_x, pred_y = predictor.predict(
                x=5000, y=5000, time=300, game_minutes=5.0,
                level=6, cs=30, gold=2000,
                champion_category="aggressive"
            )
            print(f"   Predicted location: ({pred_x:.2f}, {pred_y:.2f})")
        except Exception as e:
            print(f"   Prediction failed: {e}")
