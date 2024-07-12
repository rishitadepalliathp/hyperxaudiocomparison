import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QMenu, QAction, QHBoxLayout
from PyQt5.QtCore import Qt, QPoint
from ToggleButton import ToggleStack  # Import the ToggleStack class
from functools import partial

# Reads in file names and establishes necessary lists
path = 'C:\\Users\\TaRi525\\Documents\\Hyper X Intern Project\\Dummy Audio Files'
try:
    names = os.listdir(path)
except Exception as e:
    print(f"Error reading directory: {e}")
    names = []

info = [name.split('_') for name in names]
hyperx_microphones = [thing for thing in info if thing[0] == "HyperX"]
competitor_microphones = [thing for thing in info if thing[0] != "HyperX"]

hyperx_microphones_displayed = []
competitor_microphones_displayed = []

hyperx_microphones.sort()
competitor_microphones.sort()

# Main window class
class ScrollWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HyperX Microphone Comparisons")
        self.setGeometry(100, 100, 2000, 1600)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Left panel for microphone list
        self.left_panel = QFrame()
        self.left_panel.setFrameShape(QFrame.StyledPanel)
        self.left_panel.setStyleSheet("background-color: white;border: none;border-radius: 10px")
        
        # Set the left panel width as a percentage of the screen width or max 600 pixels
        self.set_left_panel_width()  # Call the method to set initial width
        
        main_layout.addWidget(self.left_panel, 1)

        left_layout = QVBoxLayout()
        self.left_panel.setLayout(left_layout)

        # Scroll Area for Microphone List
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
    QScrollBar:vertical {
        border: none;
        background: white;
        width: 12px;
        margin: 0px 0px 0px 0px;
        border-radius: 5px;
    }

    QScrollBar::handle:vertical {
        background: #C0C0C0;
        min-height: 20px;
        border-radius: 5px;
    }

    QScrollBar::add-line:vertical {
        background: none;
        height: 0px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }

    QScrollBar::sub-line:vertical {
        background: none;
        height: 0px;
        subcontrol-position: top;
        subcontrol-origin: margin;
    }
""")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)

        left_layout.addWidget(scroll_area)

        # Horizontal layout for title and toggle switch
        title_layout = QHBoxLayout()

        title = QLabel("Microphones")
        title.setStyleSheet("font-size: 60px; font-family: 'Forma DJR Display';")
        title_layout.addWidget(title)

        # Add ToggleStack to the right of the title
        toggle_stack = ToggleStack()
        title_layout.addWidget(toggle_stack)
        title_layout.setAlignment(toggle_stack, Qt.AlignRight)

        scroll_layout.addLayout(title_layout)

        # Microphone List
        self.microphone_list(scroll_layout)

        self.show()

    def set_left_panel_width(self):
        screen_width = QApplication.primaryScreen().geometry().width()
        desired_width = int(screen_width * 0.27)  # 27% of the screen width
        new_width = min(desired_width, 600)  # Use the smaller of 27% screen width or 600 pixels
        self.left_panel.setFixedWidth(new_width)
        
    def resizeEvent(self, event):
        self.set_left_panel_width()  # Adjust width on resize
        super().resizeEvent(event)

    def microphone_list(self, layout):
        hyperx_title = QLabel("HP/HyperX")
        hyperx_title.setStyleSheet("font-size: 20px; color: #717070;font-family: 'Forma DJR Display';")
        layout.addWidget(hyperx_title)

        for mic in hyperx_microphones:
            if mic[1] not in hyperx_microphones_displayed:
                hyperx_microphones_displayed.append(mic[1])
                button = QPushButton(mic[1])
                button.setMinimumSize(400, 100)
                button.setStyleSheet("font-size: 40px; font-family: 'Forma DJR Micro'; background-color: #DEE0F6; border-radius: 10px;")

                button.clicked.connect(partial(self.show_patterns_menu, button, mic[0], mic[1]))
                
                layout.addWidget(button)

        competitor_title = QLabel("Competitors")
        competitor_title.setStyleSheet("font-size: 20px; color: #717070;font-family: 'Forma DJR Display';")
        layout.addWidget(competitor_title)

        for mic in competitor_microphones:
            if (mic[0] + " " + mic[1]) not in competitor_microphones_displayed:
                competitor_microphones_displayed.append(mic[0] + " " + mic[1])
                button = QPushButton(mic[0] + " " + mic[1])
                button.setMinimumSize(400, 100)
                button.setStyleSheet("font-size: 40px; font-family: 'Forma DJR Micro'; background-color: #F6DEDE; border-radius: 10px;")

                button.clicked.connect(partial(self.show_patterns_menu, button, mic[0], mic[1]))
                
                layout.addWidget(button)

    def show_patterns_menu(self, button, company, model):
        menu = QMenu(button)
        menu.setStyleSheet("QMenu { border-radius: 10px; }")  # Add rounded corners to the menu
        self.create_patterns_menu(menu, company, model)
        # Position the menu at the bottom right corner of the button with a slight offset to the left and up
        offset = button.mapToGlobal(button.rect().bottomRight())
        menu.popup(QPoint(offset.x() - 100, offset.y() - 5))

    def create_patterns_menu(self, menu, company, model):
        if company == "HyperX":
            patterns = list(set(item[2] for item in hyperx_microphones if item[0] == company and item[1] == model))
        else:
            patterns = list(set(item[2] for item in competitor_microphones if item[0] == company and item[1] == model))

        patterns.sort()
        for pattern in patterns:
            positions_menu = QMenu(pattern, self)
            positions_menu.setStyleSheet(menu.styleSheet())

            if company == "HyperX":
                positions = list(set(item[3] for item in hyperx_microphones if item[0] == company and item[1] == model and item[2] == pattern))
            else:
                positions = list(set(item[3] for item in competitor_microphones if item[0] == company and item[1] == model and item[2] == pattern))

            positions.sort()
            for position in positions:
                recordings_menu = QMenu(position, self)
                recordings_menu.setStyleSheet(menu.styleSheet())

                if company == "HyperX":
                    recordings = list(set(item[4][:-4] for item in hyperx_microphones if item[0] == company and item[1] == model and item[2] == pattern and item[3] == position))
                else:
                    recordings = list(set(item[4][:-4] for item in competitor_microphones if item[0] == company and item[1] == model and item[2] == pattern and item[3] == position))

                recordings.sort()
                for recording in recordings:
                    action = QAction(recording, self)
                    recordings_menu.addAction(action)
                    action.triggered.connect(partial(self.display_selection, company, model, pattern, position, recording))
                positions_menu.addMenu(recordings_menu)
            menu.addMenu(positions_menu)

    def display_selection(self, company, model, pattern, position, recording):
        selection_text = f"Selected: {company} {model} {pattern} {position} {recording}"
        print(selection_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ScrollWindow()
    sys.exit(app.exec_())
