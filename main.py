import cv2
import numpy as np
import pickle
import shutil
import sys
import time
import os

from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QPoint
)
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QListWidget, QTabWidget, QGroupBox, QFileDialog,
    QMessageBox, QStyle, QProgressDialog
)

# --- Import from local modules ---
from stylesheet import get_stylesheet
from utils import Animator
from security import sanitize_filename
import constants as C

# --- Backend Worker for Threading ---
class Worker(QObject):
    finished = Signal(object)
    
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result = self.fn(*self.args, **self.kwargs)
        self.finished.emit(result)

# --- Backend Logic Class ---
class Backend:
    def __init__(self):
        self.age_net = self._load_age_model()
        self.face_cascade = cv2.CascadeClassifier(C.HAAR_PATH)
        self.emotion_net = self._load_emotion_model()

    def _load_age_model(self):
        try:
            return cv2.dnn.readNetFromCaffe(C.AGE_PROTO, C.AGE_MODEL)
        except cv2.error:
            print("Warning: Age detection models not found.")
            return None

    def _load_emotion_model(self):
        """
        Load emotion detection model. 
        
        INSTRUCTIONS FOR EMOTION MODEL:
        For a more accurate emotion detection, you can download a pre-trained emotion model:
        1. Download emotion detection model (e.g., FER2013 trained model)
        2. Place the model files in opencv_data/emotion_model/ directory
        3. Update this method to load your specific model
        
        Current implementation uses a simple OpenCV-based approach for basic emotion detection.
        """
        # For now, we'll use a simple rule-based approach
        # In a production setup, you would load a pre-trained emotion model here
        return None

    def load_labels(self):
        try:
            if not os.path.exists(C.LABELS_PATH): return {}
            with open(C.LABELS_PATH, "rb") as f: return pickle.load(f)
        except (FileNotFoundError, EOFError, pickle.UnpicklingError) as e:
            print(f"Warning: Could not load labels file. It might be corrupted. Error: {e}")
            return {}

    def save_labels(self, labels):
        with open(C.LABELS_PATH, "wb") as f: pickle.dump(labels, f)

    def detect_single_face_for_training(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Using tuned parameters from constants.py for better detection
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=C.HAAR_SCALE_FACTOR,
            minNeighbors=C.HAAR_MIN_NEIGHBORS,
            minSize=C.HAAR_MIN_SIZE_TRAINING
        )
        if len(faces) == 1:
            (x, y, w, h) = faces[0]
            face_roi = gray[y:y+h, x:x+w]
            return cv2.resize(face_roi, C.TRAINING_IMG_SIZE)
        return None

    def train_recognizer(self):
        labels_dict = self.load_labels()
        if not labels_dict: return False, "No faces registered to train."
        
        face_samples, ids = [], []
        label_to_id = {name: i for i, name in enumerate(sorted(labels_dict.keys()))}
        id_to_label = {i: name for name, i in label_to_id.items()}

        for username, face_arrays in labels_dict.items():
            user_id = label_to_id[username]
            for face_array in face_arrays:
                if face_array is not None:
                    face_samples.append(face_array)
                    ids.append(user_id)
        
        if not face_samples: return False, "No valid face data found to train."
        
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(face_samples, np.array(ids))
        recognizer.save(C.TRAINER_PATH)
        with open(C.ID_MAP_PATH, "wb") as f: pickle.dump(id_to_label, f)
        return True, "✅ Model trained successfully."

    def detect_age(self, face_img):
        if self.age_net is None: return ""
        try:
            blob = cv2.dnn.blobFromImage(cv2.resize(face_img, (227, 227)), 1.0, (227, 227),
                                         (78.4263377603, 87.7689143744, 114.895847746), swapRB=False)
            self.age_net.setInput(blob)
            return C.AGE_BUCKETS[self.age_net.forward()[0].argmax()]
        except (cv2.error, IndexError): return "?"

    def detect_emotion(self, face_img):
        """
        Simple emotion detection based on facial features analysis.
        
        For more accurate results, replace this with a pre-trained emotion detection model:
        1. Download FER2013 or similar emotion dataset trained model
        2. Use cv2.dnn.readNetFromTensorflow() or cv2.dnn.readNetFromONNX()
        3. Process the face image through the model
        4. Return the predicted emotion from C.EMOTION_LABELS
        
        Current implementation uses basic image analysis as a demonstration.
        """
        if face_img is None or face_img.size == 0:
            return "Unknown"
        
        try:
            # Convert to grayscale for analysis
            if len(face_img.shape) == 3:
                gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            else:
                gray_face = face_img
            
            # Resize for consistent analysis
            resized_face = cv2.resize(gray_face, (48, 48))
            
            # Simple emotion detection based on basic facial features
            # This is a simplified approach - in production, use a trained model
            
            # Calculate basic statistics
            mean_intensity = np.mean(resized_face)
            std_intensity = np.std(resized_face)
            
            # Detect basic features for emotion estimation
            # This is a very simplified approach for demonstration
            
            # Check for smile-like features (higher intensity in lower face region)
            lower_face = resized_face[32:48, :]
            upper_face = resized_face[0:16, :]
            
            lower_mean = np.mean(lower_face)
            upper_mean = np.mean(upper_face)
            
            # Simple heuristic-based emotion detection
            if lower_mean > upper_mean * 1.1 and std_intensity > 20:
                return "Happy"
            elif std_intensity < 15 and mean_intensity > 120:
                return "Neutral"
            elif mean_intensity < 100:
                return "Sad"
            elif std_intensity > 30:
                return "Surprise"
            else:
                return "Neutral"
                
        except Exception as e:
            print(f"Emotion detection error: {e}")
            return "Unknown"

# --- Manage Faces Tab ---
class ManageTab(QWidget):
    status_updated = Signal(str)
    model_needs_training = Signal()
    user_list_changed = Signal(int)
    
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.img_path = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        left_pane = QWidget(); left_layout = QVBoxLayout(left_pane)
        form_group = QGroupBox("User Details"); form_layout = QVBoxLayout(form_group)
        user_layout = QHBoxLayout(); user_layout.addWidget(QLabel("Username:"))
        self.user_entry = QLineEdit(); user_layout.addWidget(self.user_entry)
        form_layout.addLayout(user_layout)
        self.select_img_btn = QPushButton("Select Image...")
        self.select_img_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        form_layout.addWidget(self.select_img_btn)
        left_layout.addWidget(form_group)
        self.img_preview = QLabel("Image Preview"); self.img_preview.setAlignment(Qt.AlignCenter)
        self.img_preview.setMinimumHeight(200); self.img_preview.setObjectName("ImagePreview")
        left_layout.addWidget(self.img_preview, 1)
        action_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Face"); self.update_btn = QPushButton("Update Face")
        self.delete_btn = QPushButton("Delete User"); self.delete_btn.setObjectName("DeleteButton")
        action_layout.addWidget(self.add_btn); action_layout.addWidget(self.update_btn); action_layout.addWidget(self.delete_btn)
        left_layout.addLayout(action_layout)
        right_group = QGroupBox("Registered Users"); right_layout = QVBoxLayout(right_group)
        self.user_list = QListWidget(); right_layout.addWidget(self.user_list)
        layout.addWidget(left_pane, 2); layout.addWidget(right_group, 3)
        self.select_img_btn.clicked.connect(self.select_image)
        self.add_btn.clicked.connect(self.add_face)
        self.update_btn.clicked.connect(self.update_face)
        self.delete_btn.clicked.connect(self.delete_face)
        self.user_list.currentItemChanged.connect(self.on_user_select)
        Animator.apply_push_animation(self.select_img_btn); Animator.apply_push_animation(self.add_btn)
        Animator.apply_push_animation(self.update_btn); Animator.apply_push_animation(self.delete_btn)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.jpg *.png *.jpeg)")
        if file_path:
            self.img_path = file_path
            pixmap = QPixmap(file_path)
            self.img_preview.setPixmap(pixmap.scaled(self.img_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.status_updated.emit(f"Selected image: {os.path.basename(file_path)}")

    def add_face(self):
        username = sanitize_filename(self.user_entry.text())
        if not username: QMessageBox.critical(self, "Error", "Invalid username."); return
        if not self.img_path: QMessageBox.critical(self, "Error", "An image is required."); return
        img = cv2.imread(self.img_path)
        face = self.backend.detect_single_face_for_training(img)
        if face is None: QMessageBox.critical(self, "Error", "Could not detect a single, clear face."); return
        
        user_dir = os.path.join(C.FACES_DIR, username)
        os.makedirs(user_dir, exist_ok=True)
        count = len(os.listdir(user_dir)) + 1
        save_path = os.path.join(user_dir, f"{count}.png")
        cv2.imwrite(save_path, face)
        
        labels_dict = self.backend.load_labels()
        labels_dict.setdefault(username, []).append(face)
        self.backend.save_labels(labels_dict)
        
        self.status_updated.emit(f"Added face for {username}."); QMessageBox.information(self, "Success", f"Face added for user '{username}'.")
        self.refresh_user_list(); self.model_needs_training.emit()

    def update_face(self):
        if not self.user_list.currentItem(): QMessageBox.critical(self, "Error", "Select a user to update."); return
        if not self.img_path: QMessageBox.critical(self, "Error", "Select a new image to update with."); return
        username = self.user_list.currentItem().text()
        if QMessageBox.question(self, "Confirm Update", f"This will replace all images for '{username}'. Continue?") == QMessageBox.StandardButton.Yes:
            img = cv2.imread(self.img_path); face = self.backend.detect_single_face_for_training(img)
            if face is None: QMessageBox.critical(self, "Error", "No single face detected in new image."); return
            
            user_dir = os.path.join(C.FACES_DIR, username)
            shutil.rmtree(user_dir, ignore_errors=True); os.makedirs(user_dir)
            save_path = os.path.join(user_dir, "1.png"); cv2.imwrite(save_path, face)

            labels_dict = self.backend.load_labels(); labels_dict[username] = [face]
            self.backend.save_labels(labels_dict)

            self.status_updated.emit(f"Updated face for {username}."); QMessageBox.information(self, "Success", f"Face for '{username}' updated.")
            self.model_needs_training.emit()

    def delete_face(self):
        if not self.user_list.currentItem(): QMessageBox.critical(self, "Error", "Select a user to delete."); return
        username = self.user_list.currentItem().text()
        if QMessageBox.question(self, "Confirm Delete", f"Delete all data for '{username}'?") == QMessageBox.StandardButton.Yes:
            labels_dict = self.backend.load_labels()
            if username in labels_dict:
                shutil.rmtree(os.path.join(C.FACES_DIR, username), ignore_errors=True); del labels_dict[username]
                self.backend.save_labels(labels_dict)
                self.status_updated.emit(f"Deleted user: {username}."); QMessageBox.information(self, "Deleted", f"User '{username}' was deleted.")
                self.clear_inputs(); self.refresh_user_list(); self.model_needs_training.emit()

    def on_user_select(self, current_item):
        if not current_item: return
        username = current_item.text()
        self.user_entry.setText(username)
        self.status_updated.emit(f"Selected user: {username}")
        
        # Display the user's first saved image as a preview
        user_dir = os.path.join(C.FACES_DIR, username)
        if os.path.isdir(user_dir) and os.listdir(user_dir):
            first_img_path = os.path.join(user_dir, os.listdir(user_dir)[0])
            pixmap = QPixmap(first_img_path)
            self.img_preview.setPixmap(pixmap.scaled(self.img_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.img_preview.setText("No Preview")


    def refresh_user_list(self):
        self.user_list.clear(); users = sorted(self.backend.load_labels().keys()); self.user_list.addItems(users)
        self.user_list_changed.emit(len(users))

    def clear_inputs(self): self.user_entry.clear(); self.img_preview.clear(); self.img_preview.setText("Image Preview"); self.img_path = None

# --- Recognize Tab ---
class RecognizeTab(QWidget):
    status_updated = Signal(str)
    
    def __init__(self, backend):
        super().__init__(); self.backend = backend; self.camera_active = False
        self.cap = None; self.recognizer = None; self.id_to_label = {}; self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self); self.camera_label = QLabel("Camera is Off")
        self.camera_label.setAlignment(Qt.AlignCenter); self.camera_label.setObjectName("CameraView")
        self.camera_label.setScaledContents(True); layout.addWidget(self.camera_label, 1)
        self.start_stop_btn = QPushButton("Start Recognition"); self.start_stop_btn.clicked.connect(self.toggle_camera)
        self.update_start_stop_button(False); layout.addWidget(self.start_stop_btn)
        self.timer = QTimer(self); self.timer.timeout.connect(self.update_frame)
        Animator.apply_push_animation(self.start_stop_btn)

    def toggle_camera(self):
        if self.camera_active: self.stop_camera()
        else: self.start_camera()

    def start_camera(self):
        if not os.path.exists(C.TRAINER_PATH): QMessageBox.warning(self, "Model Not Found", "Please train the model first."); return
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create(); self.recognizer.read(C.TRAINER_PATH)
            with open(C.ID_MAP_PATH, "rb") as f: self.id_to_label = pickle.load(f)
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to load model files: {e}"); return
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened(): QMessageBox.critical(self, "Camera Error", "Could not access the camera."); return
        self.camera_active = True; self.timer.start(15); self.status_updated.emit("▶️ Recognition started...")
        self.update_start_stop_button(True)

    def stop_camera(self):
        self.camera_active = False; self.timer.stop()
        if self.cap: self.cap.release()
        self.camera_label.setText("Camera is Off"); self.camera_label.setStyleSheet("background-color: black; color: white;")
        self.status_updated.emit("⏹️ Recognition stopped."); self.update_start_stop_button(False)

    def update_frame(self):
        if not self.camera_active or not self.cap: return
        ret, frame = self.cap.read()
        if not ret: return
        frame = cv2.flip(frame, 1); gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Using tuned parameters from constants.py for better real-time detection
        faces = self.backend.face_cascade.detectMultiScale(
            gray,
            scaleFactor=C.HAAR_SCALE_FACTOR,
            minNeighbors=C.HAAR_MIN_NEIGHBORS,
            minSize=C.HAAR_MIN_SIZE_REALTIME
        )
        for (x, y, w, h) in faces:
            face_roi_color = frame[y:y+h, x:x+w]; face_roi_gray = gray[y:y+h, x:x+w]
            
            resized_face = cv2.resize(face_roi_gray, C.TRAINING_IMG_SIZE)
            label_id, confidence = self.recognizer.predict(resized_face)
            
            name = "Unknown"
            if confidence < C.RECOGNITION_CONFIDENCE: name = self.id_to_label.get(label_id, "Unknown")
            
            # Detect age and emotion
            age = self.backend.detect_age(face_roi_color)
            emotion = self.backend.detect_emotion(face_roi_color)
            
            # Build display text with name, age, and emotion
            text_parts = [name]
            if age: text_parts.append(f"Age: {age}")
            if emotion and emotion != "Unknown": text_parts.append(f"Emotion: {emotion}")
            text = " | ".join(text_parts)
            
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape; qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

    def update_start_stop_button(self, is_active):
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop if is_active else QStyle.StandardPixmap.SP_MediaPlay)
        self.start_stop_btn.setText("Stop Recognition" if is_active else "Start Recognition"); self.start_stop_btn.setIcon(icon)

# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("VisionAI - Secure Face Recognition"); self.setGeometry(100, 100, 1000, 750)
        self.setMinimumSize(900, 650); self.backend = Backend(); self.thread = None; self.worker = None
        self.init_ui(); self.setStyleSheet(get_stylesheet()); self.update_model_status()
        self.manage_tab.refresh_user_list(); self.check_camera()

    def check_camera(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened(): QMessageBox.warning(self, "Camera Not Found", "No camera detected. Recognition tab will not function.")
        cap.release()

    def init_ui(self):
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget); tabs = QTabWidget()
        self.manage_tab = ManageTab(self.backend); self.recognize_tab = RecognizeTab(self.backend)
        tabs.addTab(self.manage_tab, self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon), "Manage Faces")
        tabs.addTab(self.recognize_tab, self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), "Recognize")
        train_layout = QHBoxLayout(); self.model_status_label = QLabel("Model Status:")
        train_layout.addWidget(self.model_status_label); train_layout.addStretch()
        self.train_btn = QPushButton("Train Model"); Animator.apply_morph_animation(self.train_btn)
        self.train_btn.clicked.connect(self.train_model); train_layout.addWidget(self.train_btn)
        main_layout.addLayout(train_layout); main_layout.addWidget(tabs); self.statusBar().showMessage("Welcome!")
        self.manage_tab.status_updated.connect(self.update_status_bar)
        self.manage_tab.model_needs_training.connect(lambda: self.update_model_status(True))
        self.manage_tab.user_list_changed.connect(lambda count: self.train_btn.setEnabled(count > 0))
        self.recognize_tab.status_updated.connect(self.update_status_bar)

    def train_model(self): QTimer.singleShot(400, self.start_training_thread)

    def start_training_thread(self):
        self.progress_dialog = QProgressDialog("Training model...", None, 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal); self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()
        self.thread = QThread(); self.worker = Worker(self.backend.train_recognizer)
        self.worker.moveToThread(self.thread); self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_training_finished); self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_training_finished(self, result):
        success, message = result; self.progress_dialog.close()
        if success: self.update_model_status()
        self.statusBar().showMessage(message); QMessageBox.information(self, "Training Complete", message)
        self.thread.quit()

    def update_model_status(self, needs_training=False):
        if needs_training: self.model_status_label.setText("Model Status: 🟡 Needs Training")
        elif os.path.exists(C.TRAINER_PATH): self.model_status_label.setText("Model Status: ✅ Trained")
        else: self.model_status_label.setText("Model Status: ❌ Not Trained")

    def update_status_bar(self, message): self.statusBar().showMessage(message)
    def closeEvent(self, event): self.recognize_tab.stop_camera(); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())

