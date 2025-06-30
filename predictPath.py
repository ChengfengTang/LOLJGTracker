import numpy as np
from tensorflow import keras

# Load model and scaler
model = keras.models.load_model('models/Pantheon_model.keras')
scaler = np.load('models/Pantheon_scaler.npy', allow_pickle=True).item()

# Model expects input shape: (1, sequence_length, num_features)
sequence_length = 10  # or whatever you used in training

# Example: starting sequence (replace with real data if available)
# Each entry: [time_in_seconds, x, y, level, cs, gold]
# You need 10 steps to start; here we use dummy values as an example.
initial_sequence = [
    [0, 500, 500, 1, 0, 500],    # 0:00
    [3, 520, 520, 1, 0, 520],    # 0:03
    [6, 540, 540, 1, 0, 540],    # 0:06
    [9, 560, 560, 1, 0, 560],    # 0:09
    [12, 580, 580, 1, 0, 580],   # 0:12
    [15, 600, 600, 1, 0, 600],   # 0:15
    [18, 620, 620, 1, 0, 620],   # 0:18
    [21, 640, 640, 1, 0, 640],   # 0:21
    [24, 660, 660, 1, 0, 660],   # 0:24
    [27, 680, 680, 1, 0, 680],   # 0:27
]
sequence = np.array(initial_sequence)

# Predict every 30 seconds up to 20 minutes (1200 seconds)
for t in range(30, 20*60+1, 30):
    # Prepare input: update the time for the next step
    # Optionally, you can update level/cs/gold if you have a rule or data
    next_input = sequence[-1].copy()
    next_input[0] = t  # update time
    # Optionally, update other features here

    # Prepare input for model
    input_seq = sequence[-sequence_length:]  # last N steps
    input_scaled = scaler.transform(input_seq)
    input_scaled = input_scaled.reshape(1, sequence_length, -1)

    # Predict next position
    pred_xy = model.predict(input_scaled)[0]
    print(f"Time {t//60}:{t%60:02d} - Predicted position: x={pred_xy[0]:.1f}, y={pred_xy[1]:.1f}")

    # Append prediction to sequence for next step
    # For next prediction, you may want to update level/cs/gold as well
    next_row = next_input.copy()
    next_row[1] = pred_xy[0]
    next_row[2] = pred_xy[1]
    sequence = np.vstack([sequence, next_row])