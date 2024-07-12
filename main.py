import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt
from QTFqRes import CSVGrapher
from QTWaveform import WaveWindow
from QGUI import ScrollWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Rishi Project")
        
        # Create central widget and set layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)  # Use QHBoxLayout for the main layout
        main_layout.setSpacing(0)  # Remove spacing between widgets
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Set background color to white for the central widget
        central_widget.setStyleSheet("background-color: white;")

        self.scroll_window = ScrollWindow()
        self.wav = WaveWindow()
        self.csv = CSVGrapher()
        
        # Set size policy for scroll_window to expand vertically
        self.scroll_window.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Create a container widget for the right side
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)  # Use QVBoxLayout for the right container
        right_layout.setSpacing(0)  # Remove spacing between widgets
        right_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Set size policy for right_container to expand both horizontally and vertically
        right_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set background color of right container to gray
        right_container.setStyleSheet("background-color: lightgray;")

        # Add CSVGrapher and WaveWindow to the right layout
        self.csv.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.wav.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.csv)            # Add CSVGrapher to the top
        right_layout.addWidget(self.wav)            # Add WaveWindow to the bottom

        # Add widgets to the main layout with alignment
        main_layout.addWidget(self.scroll_window, alignment=Qt.AlignLeft)   # Add ScrollWindow to the left
        main_layout.addWidget(right_container)      # Add the right container to the right

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
