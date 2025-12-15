

import sys
import os
import json
import base64
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, 
                             QListWidget, QSplitter, QGroupBox, QScrollArea, QFrame,
                             QMessageBox, QInputDialog, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QPixmap, QImage, QIcon

from phone_agent.adb import list_devices, quick_connect
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
        # Data
        self.workers = {} # dict: device_id -> AgentWorker
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
        
        self.device_list = QListWidget()
        self.device_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.device_list.setFixedHeight(150)
        
        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        
        self.connect_input = QLineEdit()
        self.connect_input.setPlaceholderText("Remote IP:Port (e.g., 192.168.1.5:5555)")
        self.connect_btn = QPushButton("Connect Remote")
        self.connect_btn.clicked.connect(self.connect_remote_device)
        
        dev_layout.addWidget(QLabel("Select Devices (Check to control):"))
        dev_layout.addWidget(self.device_list)
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
        
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.clicked.connect(self.resume_tasks)
        self.resume_btn.setEnabled(False)
        self.resume_btn.setStyleSheet("background-color: #FF9500; color: white; font-weight: bold; padding: 5px 15px;")

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_tasks)
        self.stop_btn.setEnabled(True)
        self.stop_btn.setStyleSheet("background-color: #FF3B30; color: white;")

        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.run_btn)
        input_layout.addWidget(self.resume_btn)
        input_layout.addWidget(self.stop_btn)
        
        # Split View for Chat and Screenshot
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Chat/Log Area (Tabs)
        self.log_tabs = QTabWidget()
        self.log_tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #333; }")
        
        # System Tab
        self.system_log = QTextEdit()
        self.system_log.setReadOnly(True)
        self.system_log.setStyleSheet(self._get_log_style())
        self.log_tabs.addTab(self.system_log, "System")
        
        # Sync tab selection
        self.log_tabs.currentChanged.connect(self._sync_tabs_from_log)
        
        # Screenshot Preview Area (Tabs for multiple devices)
        self.screenshot_tabs = QTabWidget()
        self.screenshot_tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #333; }")
        self.screenshot_tabs.currentChanged.connect(self._sync_tabs_from_screenshot)
        
        splitter.addWidget(self.log_tabs)
        splitter.addWidget(self.screenshot_tabs)
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
        self.device_list.clear()
        try:
            devices = list_devices()
            if not devices:
                self.device_list.addItem("No devices found")
                return

            for dev in devices:
                # Create checkable item
                from PyQt6.QtWidgets import QListWidgetItem
                # Format: [Manufacturer MarketName/Model] DeviceID (Status) - Product
                
                # Try to use Market Name (e.g. Xiaomi 13), fallback to Model
                name_display = dev.market_name if dev.market_name else dev.model
                
                # Prepend Manufacturer if not already in name
                if dev.manufacturer and name_display and dev.manufacturer.lower() not in name_display.lower():
                    name_display = f"{dev.manufacturer} {name_display}"
                
                name_display = name_display or "Unknown"

                info_parts = [f"[{name_display}]", dev.device_id, f"({dev.status})"]
                if dev.product:
                    info_parts.append(f"- {dev.product}")
                if dev.android_version:
                    info_parts.append(f"[Android {dev.android_version}]")
                
                display_text = " ".join(info_parts)
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, dev.device_id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.device_list.addItem(item)
                
            # Check first device by default if available
            if self.device_list.count() > 0:
                self.device_list.item(0).setCheckState(Qt.CheckState.Checked)

        except Exception as e:
            self.device_list.addItem(f"Error: {e}")

    def connect_remote_device(self):
        """Connect to a remote ADB device."""
        address = self.connect_input.text().strip()
        if not address:
            QMessageBox.warning(self, "Warning", "Please enter an IP address (e.g., 192.168.1.5).")
            return
            
        self.append_log(f"Connecting to {address}...", "#00FFFF")
        self.connect_btn.setEnabled(False)
        
        # Use simple blocking call for now, could be threaded if needed
        success, message = quick_connect(address)
        
        self.connect_btn.setEnabled(True)
        
        if success:
            self.append_log(f"✅ Connection successful: {message}", "#00FF00")
            self.refresh_devices()
            self.connect_input.clear()
        else:
            self.append_log(f"❌ Connection failed: {message}", "#FF3B30")
            QMessageBox.critical(self, "Connection Failed", f"Could not connect to {address}:\n{message}")

    def _get_log_style(self):
        return """
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 10px;
            }
        """

    def append_log(self, text, color="#FFFFFF", style="normal", device_id=None):
        """Append styled text to chat area (System or Device tab)."""
        html = f'<span style="color:{color}; font-weight:{style}">{text}</span><br>'
        
        # Always log to System for overview
        self.system_log.insertHtml(html)
        self.system_log.verticalScrollBar().setValue(self.system_log.verticalScrollBar().maximum())
        
        if device_id:
            # Find or create tab
            tab_index = -1
            for i in range(self.log_tabs.count()):
                if self.log_tabs.tabText(i) == device_id:
                    tab_index = i
                    break
            
            if tab_index == -1:
                new_log = QTextEdit()
                new_log.setReadOnly(True)
                new_log.setStyleSheet(self._get_log_style())
                self.log_tabs.addTab(new_log, device_id)
                tab_index = self.log_tabs.count() - 1
            
            # Append to specific tab
            log_widget = self.log_tabs.widget(tab_index)
            if isinstance(log_widget, QTextEdit):
                log_widget.insertHtml(html)
                log_widget.verticalScrollBar().setValue(log_widget.verticalScrollBar().maximum())

    def _sync_tabs_from_log(self, index):
        """Sync screenshot tab when log tab changes."""
        text = self.log_tabs.tabText(index)
        for i in range(self.screenshot_tabs.count()):
            if self.screenshot_tabs.tabText(i) == text:
                self.screenshot_tabs.setCurrentIndex(i)
                break

    def _sync_tabs_from_screenshot(self, index):
        """Sync log tab when screenshot tab changes."""
        text = self.screenshot_tabs.tabText(index)
        for i in range(self.log_tabs.count()):
            if self.log_tabs.tabText(i) == text:
                self.log_tabs.setCurrentIndex(i)
                break

    def update_screenshot(self, device_id, base64_data):
        try:
            image_data = base64.b64decode(base64_data)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            
            # Find or create tab for this device
            tab_index = -1
            for i in range(self.screenshot_tabs.count()):
                if self.screenshot_tabs.tabText(i) == device_id:
                    tab_index = i
                    break
            
            if tab_index == -1:
                # Create new tab
                label = QLabel()
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("background-color: #000;")
                self.screenshot_tabs.addTab(label, device_id)
                tab_index = self.screenshot_tabs.count() - 1
                # Switch to new tab if it's the only active one
                if self.screenshot_tabs.count() == 1:
                     self.screenshot_tabs.setCurrentIndex(tab_index)

            # Get label from widget
            label = self.screenshot_tabs.widget(tab_index)
            if isinstance(label, QLabel):
                # Scale to fit tab size
                scaled = pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                label.setPixmap(scaled)
                
        except Exception as e:
            print(f"Failed to update screenshot for {device_id}: {e}")

    def get_selected_device_ids(self):
        """Get list of checked device IDs."""
        ids = []
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                device_id = item.data(Qt.ItemDataRole.UserRole)
                if device_id:
                    ids.append(device_id)
        return ids

    def start_task(self):
        task = self.task_input.text().strip()
        if not task:
            QMessageBox.warning(self, "Warning", "Please enter a task description.")
            return
            
        device_ids = self.get_selected_device_ids()
        if not device_ids:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
            
        # Common config
        model_config = {
            "base_url": self.base_url_input.text(),
            "model_name": self.model_name_input.text(),
            "api_key": self.api_key_input.text()
        }
        
        for device_id in device_ids:
            self.append_log(f"Preparing task for {device_id}...", "#AAAAAA")
            if device_id in self.workers and self.workers[device_id].isRunning():
                self.append_log(f"Busy, skipping new task.", "#FFA500", device_id=device_id)
                continue
                
            agent_config = {
                "device_id": device_id,
                "verbose": True
            }
            
            worker = AgentWorker(device_id, model_config, agent_config, task)
            worker.signal_thinking.connect(self.handle_thinking)
            worker.signal_action.connect(self.handle_action)
            worker.signal_error.connect(self.handle_error)
            worker.signal_finished.connect(self.handle_finished)
            worker.signal_log.connect(self.handle_log)
            worker.signal_takeover_request.connect(self.handle_takeover_request)
            
            self.workers[device_id] = worker
            worker.start()
            self.append_log(f"Starting task...", "#00FFFF", device_id=device_id)
            self.append_log(f"ME: {task}", "#007AFF", "bold", device_id=device_id)

    def stop_tasks(self):
        """Stop tasks for checked devices."""
        device_ids = self.get_selected_device_ids()
        for device_id in device_ids:
            if device_id in self.workers:
                self.workers[device_id].stop()
                self.append_log(f"Stopping...", "#FF3B30", device_id=device_id)
        self.resume_btn.setEnabled(False)

    def resume_tasks(self):
        """Resume paused tasks for checked devices."""
        device_ids = self.get_selected_device_ids()
        resumed_count = 0
        for device_id in device_ids:
            if device_id in self.workers:
                if self.workers[device_id].is_paused:
                     self.workers[device_id].resume()
                     self.append_log(f"Resuming...", "#00FF00", device_id=device_id)
                     resumed_count += 1
        
        if resumed_count > 0:
            self.resume_btn.setEnabled(False)
            self.run_btn.setEnabled(False)

    def handle_thinking(self, device_id, content):
        self.append_log(f"🤔 Thinking: {content}", "#AAAAAA", "italic", device_id=device_id)

    def handle_action(self, device_id, action, screenshot_b64):
        self.append_log(f"⚡ Action: {action}", "#00AAFF", device_id=device_id)
        # Update screenshot for specific device tab
        if screenshot_b64:
            self.update_screenshot(device_id, screenshot_b64)

    def handle_error(self, device_id, error):
        self.append_log(f"❌ Error: {error}", "#FF3B30", device_id=device_id)
        self._cleanup_worker(device_id)

    def handle_finished(self, device_id, result):
        self.append_log(f"✅ Finished: {result}", "#00FF00", device_id=device_id)
        self._cleanup_worker(device_id)
        
    def handle_log(self, device_id, message):
         self.append_log(f"ℹ️ {message}", "#DDDDDD", device_id=device_id)

    def handle_takeover_request(self, device_id, message):
        self.append_log(f"⚠️ MANUAL TAKEOVER: {message}", "#FF9500", "bold", device_id=device_id)
        self.resume_btn.setEnabled(True)
        # Optional: could show a pop-up dialog too
        # QMessageBox.information(self, "Manual Intervention Required", f"Device {device_id} needs help:\n{message}")

    def _cleanup_worker(self, device_id):
        if device_id in self.workers:
            del self.workers[device_id]


