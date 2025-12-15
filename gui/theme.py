
"""
Modern Dark Theme for Open-AutoGLM Desktop Client.
"""

PRIMARY_COLOR = "#007AFF"
SUCCESS_COLOR = "#28CD41"
WARNING_COLOR = "#FF9F0A"
DANGER_COLOR = "#FF3B30"
BACKGROUND_COLOR = "#1C1C1E"
SURFACE_COLOR = "#2C2C2E"
TEXT_COLOR = "#FFFFFF"
BORDER_COLOR = "#3A3A3C"

MODERN_DARK_THEME = f"""
/* Global Reset */
QWidget {{
    background-color: {BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
    font-size: 13px;
    selection-background-color: {PRIMARY_COLOR};
    selection-color: white;
}}

/* Main Window */
QMainWindow {{
    background-color: {BACKGROUND_COLOR};
}}

/* Group Box */
QGroupBox {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    margin-top: 24px;
    padding-top: 10px;
    font-weight: bold;
    color: #E5E5E7;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    background-color: {BACKGROUND_COLOR}; /* Matches background to "cut" the border */
}}

/* List Widget */
QListWidget {{
    background-color: {SURFACE_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 5px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {PRIMARY_COLOR};
    color: white;
}}

QListWidget::item:hover:!selected {{
    background-color: #3A3A3C;
}}

/* Line Edit & Text Edit */
QLineEdit, QTextEdit {{
    background-color: {SURFACE_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px;
    color: {TEXT_COLOR};
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {PRIMARY_COLOR};
    background-color: #3A3A3C;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 0 0 8px 8px;
    background-color: {SURFACE_COLOR};
}}

QTabBar::tab {{
    background-color: {BACKGROUND_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    min-width: 80px;
    padding: 8px 16px;
    margin-right: 2px;
    color: #8E8E93;
}}

QTabBar::tab:selected {{
    background-color: {SURFACE_COLOR};
    border-bottom: 2px solid {PRIMARY_COLOR}; /* Accent line */
    color: {TEXT_COLOR};
    font-weight: bold;
}}

QTabBar::tab:hover:!selected {{
    background-color: #2C2C2E;
    color: {TEXT_COLOR};
}}

/* Push Button - Default (Secondary action style) */
QPushButton {{
    background-color: {SURFACE_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 16px;
    color: {TEXT_COLOR};
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #3A3A3C;
    border-color: #636366;
}}

QPushButton:pressed {{
    background-color: #48484A;
}}

QPushButton:disabled {{
    background-color: #1C1C1E;
    color: #48484A;
    border-color: #2C2C2E;
}}

/* Primary Button (Run) - Assign objectName="runBtn" */
QPushButton#runBtn {{
    background-color: {PRIMARY_COLOR};
    border: none;
    color: white;
}}

QPushButton#runBtn:hover {{
    background-color: #0062CC;
}}

QPushButton#runBtn:pressed {{
    background-color: #004999;
}}

/* Danger Button (Stop) - Assign objectName="stopBtn" */
QPushButton#stopBtn {{
    background-color: {DANGER_COLOR};
    border: none;
    color: white;
}}

QPushButton#stopBtn:hover {{
    background-color: #D73328;
}}

/* Warning Button (Resume) - Assign objectName="resumeBtn" */
QPushButton#resumeBtn {{
    background-color: {WARNING_COLOR};
    border: none;
    color: white;
}}

QPushButton#resumeBtn:hover {{
    background-color: #D98908;
}}

/* Scroll Bar */
QScrollBar:vertical {{
    border: none;
    background: {BACKGROUND_COLOR};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: #48484A;
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: #636366;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {BORDER_COLOR};
    width: 1px;
}}
"""
