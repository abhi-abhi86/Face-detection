def get_stylesheet():
    return """
        QWidget {
            background-color: #1c2128; /* Deep Space Blue */
            color: #cdd9e5; /* Light Gray Text */
            font-size: 15px;
            font-family: 'Segoe UI', 'Roboto', 'Helvetica', sans-serif;
        }
        QMainWindow {
            border: 1px solid #333c4a;
        }
        QTabWidget::pane {
            border: 1px solid #333c4a;
            border-radius: 6px;
        }
        QTabBar::tab {
            background: #222831;
            padding: 12px 25px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-weight: bold;
            color: #768390;
        }
        QTabBar::tab:selected {
            background: #2d333b;
            color: #539bf5; /* Bright Blue */
            border-bottom: 2px solid #539bf5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #333c4a;
            border-radius: 6px;
            margin-top: 1ex;
            font-size: 16px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
        }
        QPushButton {
            background-color: #238636; /* GitHub Green */
            color: white;
            border: none;
            padding: 12px;
            border-radius: 6px;
            font-weight: bold;
            transition: background-color 0.2s ease-in-out;
        }
        QPushButton:hover {
            background-color: #2ea043;
        }
        QPushButton:pressed {
            background-color: #2da44e;
        }
        QPushButton:disabled {
            background-color: #555;
            color: #999;
        }
        QPushButton#DeleteButton {
            background-color: #da3633; /* GitHub Red */
        }
        QPushButton#DeleteButton:hover {
            background-color: #f04747;
        }
        QLineEdit, QListWidget {
            background-color: #222831;
            border: 1px solid #333c4a;
            border-radius: 6px;
            padding: 8px;
        }
        QListWidget::item:hover {
            background-color: #2d333b;
        }
        QListWidget::item:selected {
            background-color: #539bf5;
            color: #1c2128;
        }
        QLabel#ImagePreview, QLabel#CameraView {
            background-color: black;
            border: 2px dashed #333c4a;
            border-radius: 6px;
        }
        QStatusBar {
            background-color: #222831;
            font-weight: bold;
        }
        QMessageBox, QProgressDialog {
             background-color: #2d333b;
             border: 1px solid #539bf5;
        }
        QProgressDialog QLabel {
            color: #cdd9e5;
        }
        QProgressDialog QPushButton {
            background-color: #da3633;
        }
        QProgressDialog QPushButton:hover {
            background-color: #f04747;
        }
    """

