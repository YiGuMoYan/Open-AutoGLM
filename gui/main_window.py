

import sys
import os
import json
import base64
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, 
                             QListWidget, QSplitter, QGroupBox, QScrollArea, QFrame,
                             QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QPixmap, QImage, QIcon

from phone_agent.adb import list_devices
from gui.workers import AgentWorker

PROFILE_FILE = "profiles.json"
DEFAULT_PROFILES = {
    "Localhost": {
        "base_url": "http://localhost:8000/v1",
        "model_name": "autoglm-phone-9b",
        "api_key": "EMPTY"
    },
    "Zhipu AI": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "model_name": "glm-4-plus",
        "api_key": ""
    },
    "ModelScope": {
        "base_url": "https://api-inference.modelscope.cn/v1/",
        "model_name": "ZhipuAI/chatglm3-6b",
        "api_key": ""
    }
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Open-AutoGLM Desktop Client")
        self.resize(1200, 800)
        
        # Data
        self.worker = None
        self.current_worker = None
        self.device_id = None
        self.profiles = {}
        
        # UI Setup
        self.init_ui()
        self.refresh_devices()
        self.load_profiles()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left Panel: Device & Config
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Device Group
        dev_group = QGroupBox("Device Connection")
        dev_layout = QVBoxLayout(dev_group)
        
        self.device_combo = QComboBox()
        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        
        self.connect_input = QLineEdit()
        self.connect_input.setPlaceholderText("Remote IP:Port (e.g., 192.168.1.5:5555)")
        self.connect_btn = QPushButton("Connect Remote")
        # TODO: Implement remote connect logic
        
        dev_layout.addWidget(QLabel("Select Device:"))
        dev_layout.addWidget(self.device_combo)
        dev_layout.addWidget(self.refresh_btn)
        dev_layout.addWidget(QLabel("Remote Connection:"))
        dev_layout.addWidget(self.connect_input)
        dev_layout.addWidget(self.connect_btn)
        
        # Model Config Group
        model_group = QGroupBox("Model Configuration")
        model_layout = QVBoxLayout(model_group)
        
        # Profile Selection
        profile_layout = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.setEditable(True)
        self.profile_combo.currentIndexChanged.connect(self.apply_profile)
        
        self.save_profile_btn = QPushButton("Save")
        self.save_profile_btn.clicked.connect(self.save_current_profile)
        self.del_profile_btn = QPushButton("Del")
        self.del_profile_btn.clicked.connect(self.delete_current_profile)
        
        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.profile_combo, 1)
        profile_layout.addWidget(self.save_profile_btn)
        profile_layout.addWidget(self.del_profile_btn)
        
        self.base_url_input = QLineEdit("http://localhost:8000/v1")
        self.model_name_input = QLineEdit("autoglm-phone-9b")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("EMPTY")
        
        model_layout.addLayout(profile_layout)
        model_layout.addWidget(QLabel("Base URL:"))
        model_layout.addWidget(self.base_url_input)
        model_layout.addWidget(QLabel("Model Name:"))
        model_layout.addWidget(self.model_name_input)
        model_layout.addWidget(QLabel("API Key:"))
        model_layout.addWidget(self.api_key_input)
        
        left_layout.addWidget(dev_group)
        left_layout.addWidget(model_group)
        left_layout.addStretch()
        
        # Right Panel: Chat & Screen
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Task Input Area
        input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter your task here (e.g., 'Open WhatsApp and send message')...")
        self.task_input.returnPressed.connect(self.start_task)
        
        self.run_btn = QPushButton("Run Task")
        self.run_btn.clicked.connect(self.start_task)
        self.run_btn.setStyleSheet("background-color: #007AFF; color: white; font-weight: bold; padding: 5px 15px;")
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_task)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #FF3B30; color: white;")

        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.run_btn)
        input_layout.addWidget(self.stop_btn)
        
        # Split View for Chat and Screenshot
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Chat/Log Area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        # Screenshot Preview Area
        self.preview_label = QLabel("No Screenshot")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #000; border: 1px solid #333;")
        self.preview_label.setMinimumWidth(300)
        
        splitter.addWidget(self.chat_area)
        splitter.addWidget(self.preview_label)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        right_layout.addWidget(splitter)
        right_layout.addLayout(input_layout)
        
        # Combine
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)

    def load_profiles(self):
        """Load profiles from JSON file."""
        if not os.path.exists(PROFILE_FILE):
             self.profiles = DEFAULT_PROFILES
             self._save_profiles_to_disk()
        else:
            try:
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
            except Exception as e:
                self.append_log(f"Error loading profiles: {e}", "#FF3B30")
                self.profiles = DEFAULT_PROFILES
        
        self.update_profile_combo()

    def update_profile_combo(self):
        self.profile_combo.blockSignals(True)
        current_text = self.profile_combo.currentText()
        self.profile_combo.clear()
        # self.profile_combo.addItem("Custom", None) # No longer needed with editable combo
        
        for name in self.profiles:
            self.profile_combo.addItem(name, name)
            
        # Restore selection if possible, else empty
        index = self.profile_combo.findText(current_text)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)
        else:
            self.profile_combo.setCurrentText(current_text)
            
        self.profile_combo.blockSignals(False)

    def apply_profile(self, index):
        """Apply selected profile to input fields."""
        if index < 0: return
        
        profile_name = self.profile_combo.itemData(index)
        if not profile_name:
            return # Custom, do nothing
            
        profile = self.profiles.get(profile_name)
        if profile:
            self.base_url_input.setText(profile.get("base_url", ""))
            self.model_name_input.setText(profile.get("model_name", ""))
            self.api_key_input.setText(profile.get("api_key", ""))

    def save_current_profile(self):
        """Save current inputs as a profile (update existing or create new)."""
        current_name = self.profile_combo.currentText()
        name, ok = QInputDialog.getText(self, "Save Profile", "Enter profile name:", text=current_name)
        
        if ok and name:
            name = name.strip()
            if not name:
                QMessageBox.warning(self, "Warning", "Profile name cannot be empty.")
                return

            profile = {
                "base_url": self.base_url_input.text(),
                "model_name": self.model_name_input.text(),
                "api_key": self.api_key_input.text()
            }
            
            self.profiles[name] = profile
            self._save_profiles_to_disk()
            
            # Update combo
            self.update_profile_combo()
            self.profile_combo.setCurrentText(name)
            self.append_log(f"Profile '{name}' saved.", "#00FF00")

    def delete_current_profile(self):
        """Delete currently selected profile."""
        profile_name = self.profile_combo.currentText()
        if not profile_name or profile_name not in self.profiles:
            return

        confirm = QMessageBox.question(self, "Confirm Delete", f"Delete profile '{profile_name}'?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            del self.profiles[profile_name]
            self._save_profiles_to_disk()
            self.update_profile_combo()
            self.base_url_input.clear()
            self.model_name_input.clear()
            self.api_key_input.clear()

    def _save_profiles_to_disk(self):
        try:
            with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profiles: {e}")

    def refresh_devices(self):
        self.device_combo.clear()
        try:
            devices = list_devices()
            for dev in devices:
                self.device_combo.addItem(f"{dev.device_id} ({dev.status})", dev.device_id)
            if not devices:
                self.device_combo.addItem("No devices found", None)
        except Exception as e:
            self.device_combo.addItem(f"Error: {e}", None)

    def append_log(self, text, color="#FFFFFF", style="normal"):
        """Append styled text to chat area."""
        html = f'<span style="color:{color}; font-weight:{style}">{text}</span><br>'
        self.chat_area.insertHtml(html)
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    def update_screenshot(self, base64_data):
        try:
            image_data = base64.b64decode(base64_data)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            
            # Scale to fit while keeping aspect ratio
            scaled = pixmap.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(scaled)
        except Exception as e:
            print(f"Failed to update screenshot: {e}")

    def start_task(self):
        task = self.task_input.text().strip()
        if not task:
            return
            
        device_id = self.device_combo.currentData()
        if not device_id:
            self.append_log("Error: No device selected.", "#FF3B30")
            return

        # Prepare Configs
        model_config = {
            "base_url": self.base_url_input.text(),
            "model_name": self.model_name_input.text(),
            "api_key": self.api_key_input.text(),
            "lang": "cn" # Default to Chinese for now
        }
        
        agent_config = {
            "max_steps": 50,
            "device_id": device_id,
            "verbose": True
        }
        
        # UI Updates
        self.task_input.clear()
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.append_log(f"ME: {task}", "#007AFF", "bold")
        
        # Start Worker
        self.worker = AgentWorker(model_config, agent_config, task)
        self.worker.signal_thinking.connect(lambda t: self.append_log(f"THINKING: {t}", "#808080", "italic"))
        self.worker.signal_action.connect(self.handle_action)
        self.worker.signal_error.connect(lambda e: self.append_log(f"ERROR: {e}", "#FF3B30"))
        self.worker.signal_finished.connect(self.handle_finished)
        self.worker.signal_log.connect(lambda t: self.append_log(f"SYS: {t}", "#AAAAAA"))
        
        self.worker.start()

    def handle_action(self, action, screenshot_b64):
        self.append_log(f"ACTION: {action}", "#32CD32")
        if screenshot_b64:
            self.update_screenshot(screenshot_b64)

    def handle_finished(self, result):
        self.append_log(f"FINISHED: {result}", "#FFD700", "bold")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None

    def stop_task(self):
        if self.worker:
            self.worker.stop()
            self.append_log("Task stopped by user.", "#FF3B30")
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.worker = None

