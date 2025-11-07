# VisionAI - Secure Face Recognition

This repository contains a desktop application for real-time face recognition, age estimation, and emotion detection, built with PySide6 and OpenCV.

## Features

- **Real-time Recognition**: Detects and recognizes faces from a live webcam feed.
- **User Management**: A graphical user interface to add, update, and delete users for face recognition.
- **Model Training**: Train the face recognition model with the collected user faces.
- **Age and Emotion Detection**: Estimates the age and detects the emotion of the person in front of the camera.

## Project Structure

```
opencv_data/      # Datasets, models, and trained data
├── age_model/
├── emotion_model/
└── faces/
main.py           # Main application script
requirements.txt  # Python dependencies
README.md         # Project documentation
...
```

## Getting Started

### Prerequisites

- Python 3.x
- OpenCV
- PySide6

### Installation

1.  Clone the repo:
    ```bash
   [ git clone https://github.com/Darshan-CodeCrafter/disease-detection.git
    cd disease-detection](https://github.com/Darshan-CodeCrafter/Face-detection.git)
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  Run the main script:
    ```bash
    python main.py
    ```
2.  **Manage Faces Tab**:
    *   Add new users by entering a username and selecting an image with a clear face.
    *   Train the model using the "Train Model" button. The model status will indicate if it's trained or needs training.
3.  **Recognize Tab**:
    *   Click "Start Recognition" to begin detecting and identifying faces from your webcam.

## Models Used

-   **Face Detection**: Haar Cascade Classifier.
-   **Face Recognition**: Local Binary Patterns Histograms (LBPH).
-   **Age Detection**: A pre-trained Caffe model.
-   **Emotion Detection**: A pre-trained ONNX model.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE.txt)
