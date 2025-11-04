import os
import cv2

# --- Core Directories ---
DATA_DIR = "opencv_data"
FACES_DIR = os.path.join(DATA_DIR, "faces")
AGE_MODEL_DIR = os.path.join(DATA_DIR, "age_model")

# --- File Paths ---
LABELS_PATH = os.path.join(DATA_DIR, "labels.pkl")
TRAINER_PATH = os.path.join(DATA_DIR, "trainer.yml")
ID_MAP_PATH = os.path.join(DATA_DIR, "id_map.pkl")
HAAR_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# --- Age Detection Model ---
AGE_PROTO = os.path.join(AGE_MODEL_DIR, "age_deploy.prototxt")
AGE_MODEL = os.path.join(AGE_MODEL_DIR, "age_net.caffemodel")
AGE_BUCKETS = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']

# --- Emotion Detection Configuration ---
EMOTION_MODEL_DIR = os.path.join(DATA_DIR, "emotion_model")
EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

# --- Recognizer Configuration ---
RECOGNITION_CONFIDENCE = 85
TRAINING_IMG_SIZE = (100, 100)

# --- Face Detection Tuning (The Fix) ---
# Lower value (e.g., 1.1) is more sensitive but slower.
HAAR_SCALE_FACTOR = 1.1
# Lower value detects more faces but may include false positives.
HAAR_MIN_NEIGHBORS = 4
HAAR_MIN_SIZE_TRAINING = (80, 80)
HAAR_MIN_SIZE_REALTIME = (40, 40)


# Ensure directories exist
os.makedirs(FACES_DIR, exist_ok=True)
os.makedirs(AGE_MODEL_DIR, exist_ok=True)
os.makedirs(EMOTION_MODEL_DIR, exist_ok=True)

