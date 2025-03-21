from flask import Flask, request, render_template, jsonify, url_for
import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler
from PIL import Image
import os
import cv2
import mediapipe as mp
from datetime import datetime

app = Flask(__name__, template_folder='../web/templates', static_folder='../web/static')


# Load the model and scaler
loaded_model = joblib.load('random_forest_model.pkl')
loaded_scaler = joblib.load('scaler.pkl')

def preprocessing(image):
    mp_hands = mp.solutions.hands

    with mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=2,
        min_detection_confidence=0.5) as hands:
        
        image = cv2.flip(image, 1)
        if image is None:
            print("Error: Unable to read image")
            return None
        # Convert the BGR image to RGB before processing.
        results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if not results.multi_hand_landmarks:
            return None

        for hand_landmarks in results.multi_hand_landmarks:
            f1_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x
            f1_y = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y
            f1_z = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].z

            f2_x = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x
            f2_y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
            f2_z = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].z

            f3_x = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x
            f3_y = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y
            f3_z = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].z

            f4_x = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].x
            f4_y = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y
            f4_z = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].z

            f5_x = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].x
            f5_y = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y
            f5_z = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].z

            w_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x
            w_y = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y
            w_z = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].z

            return scaling(f1_x, f1_y, f1_z, f2_x, f2_y, f2_z, f3_x, f3_y, f3_z, f4_x, f4_y, f4_z, f5_x, f5_y, f5_z, w_x, w_y, w_z)

    return None

def scaling(f1_x, f1_y, f1_z, f2_x, f2_y, f2_z, f3_x, f3_y, f3_z, f4_x, f4_y, f4_z, f5_x, f5_y, f5_z, w_x, w_y, w_z):
    # Example new data provided as a list
    new_data_list = [[f1_x, f1_y, f1_z, f2_x, f2_y, f2_z, f3_x, f3_y, f3_z, f4_x, f4_y, f4_z, f5_x, f5_y, f5_z, w_x, w_y, w_z]]
    # Convert the list to a NumPy array
    new_data_array = np.array(new_data_list)

    # Preprocess the new data using the loaded scaler
    X_new_scaled = loaded_scaler.transform(new_data_array)

    print("New data preprocessed successfully!")
    return X_new_scaled

@app.route('/predict', methods=['POST'])
def predict():
    # Get the image from the request
    file = request.files.get('image')
    if not file:
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'No file provided'}), 400
        return render_template('index.html', error='No file provided')

    # Read the image file directly
    image = Image.open(file.stream)
    image = np.array(image)

    # Preprocess the image data using the loaded scaler
    X_new_scaled = preprocessing(image)
    if X_new_scaled is None:
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'No hand landmarks detected'}), 400
        return render_template('index.html', error='No hand landmarks detected')

    # Make predictions using the loaded model
    predictions = loaded_model.predict(X_new_scaled)
    if request.accept_mimetypes.accept_json:
        return jsonify({'predictions': predictions.tolist()})
    return render_template('index.html', predictions=predictions.tolist())

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)