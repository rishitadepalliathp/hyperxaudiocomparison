import sys
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QFileDialog, QListWidget, QHBoxLayout, QMessageBox, QApplication, QListWidgetItem
from PyQt5.QtCore import Qt

class FolderSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Folders")
        self.setGeometry(100, 100, 600, 400)

        self.layout = QVBoxLayout(self)

        self.folder_list = QListWidget(self)
        self.layout.addWidget(self.folder_list)

        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("+")
        self.add_button.clicked.connect(self.add_folder)
        button_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("—")
        self.remove_button.clicked.connect(self.remove_selected)
        button_layout.addWidget(self.remove_button)
        
        self.ok_button = QPushButton("Compare")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
#         self.cancel_button = QPushButton("Cancel")
#         self.cancel_button.clicked.connect(self.reject)
#         button_layout.addWidget(self.cancel_button)

        self.layout.addLayout(button_layout)

    def add_folder(self):
        initial_directory = "C:/Users/TaRi525/Documents/Hyper X Intern Project/Practice Folders"
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", initial_directory)
        if folder_path:
            # Check if folder is already in the list
            folder_name = os.path.basename(folder_path)
            for i in range(self.folder_list.count()):
                if self.folder_list.item(i).data(Qt.UserRole) == folder_path:
                    return  # Folder already exists, do nothing

            # Add folder to the list
            item = QListWidgetItem(folder_name)
            item.setData(Qt.UserRole, folder_path)
            self.folder_list.addItem(item)

    def remove_selected(self):
        for item in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(item))

    def get_selected_folders(self):
        return [self.folder_list.item(i).data(Qt.UserRole) for i in range(self.folder_list.count())]

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = FolderSelectionDialog()
    if dialog.exec_():
        print(dialog.get_selected_folders())
    sys.exit(app.exec_())
