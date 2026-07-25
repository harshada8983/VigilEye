from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import mediapipe as mp
import numpy as np
import base64
import threading
processing_lock = threading.Lock()

app = Flask(__name__)
CORS(app)

mp_face_mesh = mp.solutions.face_mesh   # ye line missing thi

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def euclidean_distance(p1, p2):

    return np.linalg.norm(np.array(p1) - np.array(p2))

def calculate_ear(landmarks, eye_points, w, h):

    coords = [(int(landmarks[p].x * w), int(landmarks[p].y * h)) for p in eye_points]
    v1 = euclidean_distance(coords[1], coords[5])
    v2 = euclidean_distance(coords[2], coords[4])
    h1 = euclidean_distance(coords[0], coords[3])

    return (v1 + v2) / (2.0 * h1)

# ---- Mouth landmarks for yawn detection ----

UPPER_LIP = 13
LOWER_LIP = 14
LEFT_MOUTH = 78
RIGHT_MOUTH = 308

def calculate_mar(landmarks, w, h):

    top = (landmarks[UPPER_LIP].x * w, landmarks[UPPER_LIP].y * h)
    bottom = (landmarks[LOWER_LIP].x * w, landmarks[LOWER_LIP].y * h)
    left = (landmarks[LEFT_MOUTH].x * w, landmarks[LEFT_MOUTH].y * h)
    right = (landmarks[RIGHT_MOUTH].x * w, landmarks[RIGHT_MOUTH].y * h)
    vertical = euclidean_distance(top, bottom)
    horizontal = euclidean_distance(left, right)

    return vertical / horizontal

# ---- Head pose landmarks (for head tilt / nodding detection) ----

# indices: nose tip, chin, left eye corner, right eye corner, left mouth corner, right mouth corner

POSE_LANDMARKS = [1, 152, 33, 263, 61, 291]

# generic 3D face model points (approximate, in mm) - standard reference used for solvePnP

MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),          # Nose tip
    (0.0, -330.0, -65.0),     # Chin
    (-225.0, 170.0, -135.0),  # Left eye left corner
    (225.0, 170.0, -135.0),   # Right eye right corner
    (-150.0, -150.0, -125.0), # Left mouth corner
    (150.0, -150.0, -125.0)   # Right mouth corner
], dtype=np.float64)

def get_head_tilt(landmarks, w, h):

    image_points = np.array([
        (landmarks[i].x * w, landmarks[i].y * h) for i in POSE_LANDMARKS
    ], dtype=np.float64)

    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array([

        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]

    ], dtype=np.float64)

    dist_coeffs = np.zeros((4, 1))  # assuming no lens distortion
    success, rotation_vector, _ = cv2.solvePnP(
        MODEL_POINTS, image_points, camera_matrix, dist_coeffs
    )

    if not success:

        return 0.0

    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

    # extract pitch (up/down nod) angle in degrees

    sy = np.sqrt(rotation_matrix[0, 0] ** 2 + rotation_matrix[1, 0] ** 2)
    pitch = np.degrees(np.arctan2(-rotation_matrix[2, 0], sy))

    return round(pitch, 2)

@app.route('/')

def home():

    return jsonify({"status": "Backend is running!"})

@app.route('/analyze', methods=['POST'])

def analyze():

    try:

        data = request.get_json()
        image_data = data['image'].split(',')[1]  # strip "data:image/jpeg;base64,"
        img_bytes = base64.b64decode(image_data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        frame = cv2.resize(frame, (240, 180))
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        with processing_lock:
           results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:

            landmarks = results.multi_face_landmarks[0].landmark
            left_ear = calculate_ear(landmarks, LEFT_EYE, w, h)
            right_ear = calculate_ear(landmarks, RIGHT_EYE, w, h)
            avg_ear = (left_ear + right_ear) / 2.0
            mar = calculate_mar(landmarks, w, h)
            pitch = get_head_tilt(landmarks, w, h)

            return jsonify({

                "face_detected": True,
                "ear": round(avg_ear, 3),
                "mar": round(mar, 3),
                "head_pitch": pitch

            })

        else:

            return jsonify({"face_detected": False, "ear": None, "mar": None, "head_pitch": None})

    except Exception as e:

        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':

    app.run(debug=True, port=5000)
