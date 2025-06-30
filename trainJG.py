"""
Jungle Movement Analysis and Prediction
This script loads jungle movement data from the database and prepares it for training
a model to predict jungler positions at given timestamps.

Model	Best For	Notes
LSTM	Strong sequence modeling	Great starting point with proven results.
GRU	Fast and efficient RNN variant	Often used in production.
Transformer	Long sequences, global patterns	If you have >50k samples, very competitive.
GNN	Complex environments + entity relations	Useful if you model camps, players as graph
Diffusion	Rich, uncertain trajectory sampling	Requires more infra, but high research payoff



Recommendation:
Given the data sparsity, I would recommend:
Reduce the sequence length (e.g., from 10 to 3-5)
Simplify the model architecture
Change the prediction task to be more coarse-grained (e.g., jungle quadrant prediction)
Consider using a rule-based system for short-term predictions (e.g., if jungler is at red buff, they're likely to go to krugs next)
"""

import mysql.connector
import json
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import pandas as pd

def get_db_connection():
    """Establish connection to MySQL database"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="champions"
    )

def load_champion_data(champion_name):
    """
    Load all match data for a specific champion from the database
    Returns a list of matches with their movement data
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT match_id, champion_data FROM {champion_name}")
        matches = cursor.fetchall()
        
        # Process each match's data
        processed_matches = []
        for match_id, champion_data in matches:
            data = json.loads(champion_data)
            if 'timeline' in data and len(data['timeline']) > 0:
                processed_matches.append({
                    'match_id': match_id,
                    'movements': data['timeline']
                })
        
        return processed_matches
    finally:
        cursor.close()
        conn.close()

def time_str_to_seconds(time_str):
    """Convert 'MM:SS' string to total seconds as int."""
    minutes, seconds = map(int, time_str.split(":"))
    return minutes * 60 + seconds

def prepare_sequence_data(matches, sequence_length=10):
    """
    Prepare movement data into sequences for training
    Each sequence contains position data for the last N timestamps
    Uses millisecond precision for timestamps
    """
    X = []  # Input sequences
    y = []  # Target positions
    
    for match in matches:
        movements = match['movements']
        
        # Create sequences using millisecond timestamps
        for i in range(len(movements) - sequence_length):
            sequence = movements[i:i + sequence_length]
            target = movements[i + sequence_length]
            
            # Extract features from sequence
            sequence_features = []
            for move in sequence:
                # Use 'time' converted to seconds instead of 'timestamp_ms'
                features = [
                    time_str_to_seconds(move['time']),
                    move['x'],
                    move['y'],
                    move['level'],
                    move['cs'],
                    move['gold']
                ]
                sequence_features.append(features)
            
            X.append(sequence_features)
            y.append([target['x'], target['y']])
    
    return np.array(X), np.array(y)

def create_model(sequence_length, n_features):
    """
    Create an LSTM model for position prediction
    """
    model = Sequential([
        LSTM(128, input_shape=(sequence_length, n_features), return_sequences=True),
        Dropout(0.2),
        LSTM(64),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dense(2)  # Output: x, y coordinates
    ])
    
    model.compile(
        optimizer='adam',
        loss='mse',
        metrics=['mae']
    )
    
    return model

def train_champion_model(champion_name):
    """
    Train a model for a specific champion
    """
    print(f"\nTraining model for {champion_name}...")
    
    # Load and prepare data
    matches = load_champion_data(champion_name)
    if not matches:
        print(f"No data found for {champion_name}")
        return None
    
    print(f"Loaded {len(matches)} matches")
    
    # Prepare sequences
    X, y = prepare_sequence_data(matches)
    print(f"Prepared {len(X)} training sequences")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale the data
    scaler = StandardScaler()
    X_train_reshaped = X_train.reshape(-1, X_train.shape[-1])
    X_test_reshaped = X_test.reshape(-1, X_test.shape[-1])
    
    X_train_scaled = scaler.fit_transform(X_train_reshaped).reshape(X_train.shape)
    X_test_scaled = scaler.transform(X_test_reshaped).reshape(X_test.shape)
    
    # Create and train model
    model = create_model(X_train.shape[1], X_train.shape[2])
    
    history = model.fit(
        X_train_scaled, y_train,
        validation_data=(X_test_scaled, y_test),
        epochs=50,
        batch_size=32,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            )
        ]
    )
    
    # Evaluate model
    test_loss, test_mae = model.evaluate(X_test_scaled, y_test)
    print(f"\nTest MAE: {test_mae:.2f} units")
    
    # Save model and scaler
    model.save(f'models/{champion_name}_model.keras')
    np.save(f'models/{champion_name}_scaler.npy', scaler)
    
    return model, scaler

def main():
    """Train model for Pantheon only"""
    import os
    if not os.path.exists('models'):
        os.makedirs('models')
    train_champion_model("Pantheon")

if __name__ == "__main__":
    main()