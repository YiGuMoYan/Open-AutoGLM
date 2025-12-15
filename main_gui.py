
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.theme import MODERN_DARK_THEME

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_DARK_THEME)
    
    # Set global style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
