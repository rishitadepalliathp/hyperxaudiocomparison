import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from PyQt5.QtGui import QFont
from QTFqRes import CSVGrapher
from QTWaveform import MusicPlayer
from FolderSelectionDialog import FolderSelectionDialog

class MainGUI(QMainWindow):
    def __init__(self, folder_paths):
        super().__init__()

        self.setWindowTitle("Main GUI")
        self.setGeometry(100, 100, 1400, 1000)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)  # Adjust margins (left, top, right, bottom)
        main_layout.setSpacing(5)  # Adjust spacing between components

        # Add Load button
        self.load_button = QPushButton("Load")
        self.load_button.setFont(QFont('Forma DJR Micro', 12))
        self.load_button.clicked.connect(self.open_folders)
        main_layout.addWidget(self.load_button)

        # Create containers for CSVGrapher and MusicPlayer
        self.csv_grapher = CSVGrapher(self)
        self.music_player = MusicPlayer(self)

        # Stack the CSVGrapher and MusicPlayer vertically
        self.stacked_layout = QVBoxLayout()
        self.stacked_layout.setContentsMargins(5, 5, 5, 5)  # Adjust margins
        self.stacked_layout.setSpacing(5)  # Adjust spacing
        self.stacked_layout.addWidget(self.csv_grapher)
        self.stacked_layout.addWidget(self.music_player)
        
        main_layout.addLayout(self.stacked_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # List to store processed folders
        self.processed_folders = set()

        # Process the initial folders
        for folder_path in folder_paths:
            self.process_folder(folder_path)

    def open_folders(self):
        dialog = FolderSelectionDialog(self)
        if dialog.exec_():
            selected_folders = dialog.get_selected_folders()
            for folder_path in selected_folders:
                self.process_folder(folder_path)

    def process_folder(self, folder_path):
        if folder_path in self.processed_folders:
            QMessageBox.warning(self, "Warning", f"The folder {folder_path} has already been added.")
            return

        required_files = ["FRQ.csv"]
        audio_files = ["MALE.wav", "FEMALE.wav", "PINKNOISE.wav"]
        folder_name = os.path.basename(folder_path)

        for file_name in required_files:
            file_path = os.path.join(folder_path, file_name)
            if not os.path.isfile(file_path):
                QMessageBox.critical(self, "Error", f"Missing {file_name} in {folder_name}")
                return

        self.csv_grapher.load_csv(os.path.join(folder_path, "FRQ.csv"), folder_name)

        audio_paths = [os.path.join(folder_path, file_name) for file_name in audio_files]
        missing_files = [file_name for file_name, path in zip(audio_files, audio_paths) if not os.path.isfile(path)]
        
        if missing_files:
            QMessageBox.critical(self, "Error", f"Missing audio files in {folder_name}: {', '.join(missing_files)}")
        else:
            self.music_player.open_files(audio_paths, folder_name)

        # Add the folder to the processed list
        self.processed_folders.add(folder_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Show the folder selection dialog first
    initial_dialog = FolderSelectionDialog(None)
    if initial_dialog.exec_():
        selected_folders = initial_dialog.get_selected_folders()
        if selected_folders:
            main_window = MainGUI(selected_folders)
            main_window.show()
            sys.exit(app.exec_())
