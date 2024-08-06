import sys
import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QMessageBox, QMainWindow
from PyQt5.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QFont
from matplotlib.font_manager import FontProperties
import scipy.signal
import time
from matplotlib.patches import FancyBboxPatch

# Define font constants
FONT_FAMILY = 'Forma DJR Micro'
FONT_SIZE = 10
MATPLOTLIB_FONT = FontProperties(family=FONT_FAMILY, size=FONT_SIZE)


class WaveformCanvas(FigureCanvas):
    loop_points_changed = pyqtSignal(float, float)

    def __init__(self, music_player, parent=None):
        self.fig, self.ax = plt.subplots()
        self.fig.patch.set_facecolor('white')  # Set the figure face color to white
        super().__init__(self.fig)
        self.setParent(parent)
        self.current_line = None
        self.music_player = music_player
        self.loop_start = 0.0  # Initialize to 0
        self.loop_end = 0.0  # Initialize to 0
        self.dragging = False
        self.selection_patch = None
        self.mpl_connect('button_press_event', self.on_click)
        self.mpl_connect('motion_notify_event', self.on_motion)
        self.mpl_connect('button_release_event', self.on_release)
        # Clear the axes to ensure it starts as a white screen
        self.ax.clear()
        self.ax.axis('off')  # Turn off the axes

    def plot_waveform(self, y, sr, title=""):
        self.ax.clear()
        self.ax.plot(np.linspace(0, len(y) / sr, num=len(y)), y, color='#005fb8')  # Change color to black
        self.ax.set_xlim(0, len(y) / sr)  # Ensure the x-axis starts at 0
        self.ax.set_ylim(-1, 1)  # Set the y-axis limits to -1 to 1
        self.ax.set_xlabel('Time (s)', fontproperties=MATPLOTLIB_FONT)
        self.ax.set_ylabel('Amplitude', fontproperties=MATPLOTLIB_FONT)
        self.ax.set_title(title, fontproperties=MATPLOTLIB_FONT)
        for label in self.ax.get_xticklabels() + self.ax.get_yticklabels():
            label.set_fontproperties(MATPLOTLIB_FONT)
        self.current_line = self.ax.axvline(0, color='k')  # Add a vertical line at the beginning
        self.draw()
        self.update_selection_patch()  # Update the selection patch if loop points are set


    def on_click(self, event):
        if event.inaxes == self.ax:
            if event.button == 3:  # Right-click
                self.reset_loop_points()
            elif event.button == 1:  # Left-click
                modifiers = QApplication.keyboardModifiers()
                if modifiers == Qt.ControlModifier:  # Control-click
                    self.dragging = True
                    self.loop_start = event.xdata if event.xdata is not None else 0.0  # Initialize loop start
                    self.loop_end = event.xdata if event.xdata is not None else 0.0  # Initialize loop end
                    self.update_selection_patch()

                else:  # Regular click
                    self.update_line(event.xdata)
                    self.music_player.set_position_from_click(event.xdata)


    def on_motion(self, event):
        if self.dragging and event.inaxes == self.ax:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:  # Only drag if Control is pressed
                self.loop_end = event.xdata
                self.update_selection_patch()


    def on_release(self, event):
        if self.dragging:
            self.dragging = False
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:  # Only update loop points if Control is pressed
                if event.xdata is not None:  # Ensure event.xdata is not None
                    self.loop_end = event.xdata
                if abs(self.loop_end - self.loop_start) < 0.1:  # Ensure the patch is at least 100 ms wide
                    if self.loop_end > self.loop_start:
                        self.loop_end = self.loop_start + 0.1
                    else:
                        self.loop_start = self.loop_end + 0.1
                self.update_selection_patch()
                self.loop_points_changed.emit(self.loop_start, self.loop_end)

    def update_selection_patch(self):
        if self.selection_patch:
            self.selection_patch.remove()
        
        graph_start, graph_end = self.ax.get_xlim()
        if abs(self.loop_end - self.loop_start) >= abs(graph_end - graph_start):
            # Make the mask transparent if it covers the full graph
            self.selection_patch = self.ax.axvspan(self.loop_start, self.loop_end, color='#d9d9d9', alpha=0.0)
        else:
            # Make the mask colored if it covers a smaller portion
            self.selection_patch = self.ax.axvspan(self.loop_start, self.loop_end, color='#d9d9d9', alpha=0.3)
        
        self.draw_idle()


    def reset_loop_points(self):
        self.loop_start = 0
        self.loop_end = self.ax.get_xlim()[1]
        self.update_selection_patch()
        self.loop_points_changed.emit(self.loop_start, self.loop_end)

    def update_line(self, current_time):
        if self.current_line:
            self.current_line.set_xdata([current_time])  # Update the x position of the vertical line
            self.draw_idle()  # Use draw_idle to reduce unnecessary redraws


class MusicPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
            }
        """)
        self.mediaPlayer = QMediaPlayer()
        self.mediaPlayer.positionChanged.connect(self.update_time)
        self.mediaPlayer.stateChanged.connect(self.update_button_text)
        self.mediaPlayer.stateChanged.connect(self.check_loop)

        self.waveformCanvas = WaveformCanvas(self, self)
        self.waveformCanvas.loop_points_changed.connect(self.set_loop_points)

        font = QFont(FONT_FAMILY, FONT_SIZE)

        self.playButton = QPushButton("Play")
        self.playButton.setMinimumHeight(100)
        self.playButton.setFont(font)
        self.playButton.clicked.connect(self.play_pause)
        self.playButton.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                border-radius: 15px; font-size: 25px;
            }
            QPushButton:pressed {
                background-color: gray;
            }
        """)

        self.toggleButton = QPushButton("Toggle")
        self.toggleButton.setMinimumHeight(100)
        self.toggleButton.setFont(font)
        self.toggleButton.clicked.connect(self.toggle_waveform)
        self.toggleButton.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                border-radius: 15px; font-size: 25px;
            }
            QPushButton:pressed {
                background-color: gray;
            }
        """)
        SCROLL_BAR_STYLE = """
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
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }

            QScrollBar:horizontal {
                border: none;
                background: white;
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #C0C0C0;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                width: 0px;
            }
        """



        self.label = QLabel("00:00/00:00")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(font)
        self.label.setStyleSheet("font-size: 24px;")
        
        self.fileTreeWidget = QTreeWidget()
        self.fileTreeWidget.setFont(font)
        self.fileTreeWidget.setHeaderHidden(True)
        self.fileTreeWidget.itemClicked.connect(self.display_selected_waveform)
        self.fileTreeWidget.setStyleSheet(f"""
            QTreeWidget {{
                background-color: #FFFFFF;
                border: 1px solid black;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            QTreeWidget::item {{
                color: black;
            }}
            QTreeWidget::item:selected {{
                background-color: #BBD2F5;
            }}
            {SCROLL_BAR_STYLE}
        """)


        self.timer = QTimer(self)
        self.timer.setInterval(10)  # Update every 20 milliseconds
        self.timer.timeout.connect(self.update_time)

        buttonLayout = QVBoxLayout()

        # Horizontal layout for Play and Toggle buttons
        play_toggle_hbox_layout = QHBoxLayout()

        # Add the Play and Toggle buttons to the horizontal layout
        play_toggle_hbox_layout.addWidget(self.playButton)
        play_toggle_hbox_layout.addWidget(self.toggleButton)

        # Add the horizontal layout to the main button layout
        buttonLayout.addLayout(play_toggle_hbox_layout)

        buttonLayout.addWidget(self.label)
        buttonLayout.addWidget(self.fileTreeWidget)

        # Horizontal layout for the buttons
        button_hbox_layout = QHBoxLayout()

        # Create the buttons
        male_button = QPushButton("Male")
        female_button = QPushButton("Female")
        pink_noise_button = QPushButton("Pink Noise")
        male_button.setFont(QFont(FONT_FAMILY, 25))
        male_button.setStyleSheet("""
            QPushButton {
                background-color: #4659f5;
                color: white;
                border-radius: 5px;
                font-size: 25px;
            }
            QPushButton:pressed {
                background-color: gray;
            }
        """)
        female_button.setFont(QFont(FONT_FAMILY, 25))
        female_button.setStyleSheet("""
            QPushButton {
                background-color: #aa9ef9;
                color: white;
                border-radius: 5px;
                font-size: 25px;
            }
            QPushButton:pressed {
                background-color: gray;
            }
        """)

        pink_noise_button.setFont(QFont(FONT_FAMILY, 25))
        pink_noise_button.setStyleSheet("""
            QPushButton {
                background-color: #ff83ff;
                color: white;
                border-radius: 5px;
                font-size: 25px;
            }
            QPushButton:pressed {
                background-color: gray;
            }
        """)

        # Add the buttons to the horizontal layout
        button_hbox_layout.addWidget(male_button)
        button_hbox_layout.addWidget(female_button)
        button_hbox_layout.addWidget(pink_noise_button)

        # Add the horizontal layout to the button layout
        buttonLayout.addLayout(button_hbox_layout)
        # Horizontal layout for the Select All and Clear All buttons
        select_clear_hbox_layout = QHBoxLayout()

        # Create the Select All and Clear All buttons
        select_all_button = QPushButton("Select All")
        clear_all_button = QPushButton("Clear All")

        # Add the Select All and Clear All buttons to the horizontal layout
        select_clear_hbox_layout.addWidget(select_all_button)
        select_clear_hbox_layout.addWidget(clear_all_button)

        # Add the horizontal layout to the button layout
        buttonLayout.addLayout(select_clear_hbox_layout)

        buttonContainer = QWidget()
        buttonContainer.setLayout(buttonLayout)
        buttonContainer.setFixedWidth(400)  # Set the fixed width for the button panel

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.waveformCanvas, 4)  # Increase the ratio for the waveform canvas
        mainLayout.addWidget(buttonContainer, 1)

        self.setLayout(mainLayout)

        self.audio_duration = 0
        self.current_waveform = 0
        self.waveform_data = []
        self.playback_position = 0
        self.is_playing = False
        self.loop_start = 0
        self.loop_end = 0
        
        # Add this dictionary to store displayed names and file paths
        self.file_path_dict = {}
        
        pink_noise_button.clicked.connect(self.filter_pink_noise)
        female_button.clicked.connect(self.filter_female)
        male_button.clicked.connect(self.filter_male)
        select_all_button.clicked.connect(self.select_all)
        clear_all_button.clicked.connect(self.clear_all)
        self.current_file_type = None
        for button in [select_all_button, clear_all_button]:
            button.setFont(QFont(FONT_FAMILY, FONT_SIZE))
            button.setStyleSheet("""
                QPushButton {
                    background-color: black;
                    color: white; 
                    border-radius: 5px; font-size: 25px;
                }
                QPushButton:pressed {
                    background-color: gray;
                }
            """)


    def load_first_file(self):
        if self.fileTreeWidget.topLevelItemCount() > 0:
            top_item = self.fileTreeWidget.topLevelItem(0)
            if top_item.childCount() > 0:
                first_child = top_item.child(0)
                self.display_selected_waveform(first_child)
                self.fileTreeWidget.setCurrentItem(first_child)
                self.waveformCanvas.reset_loop_points()  # Reset the start and endpoint lines
    def flatten_tree(self, selected_only=False):
        flat_list = []
        stack = [self.fileTreeWidget.topLevelItem(i) for i in range(self.fileTreeWidget.topLevelItemCount())]

        while stack:
            item = stack.pop(0)
            if not selected_only or item.checkState(0) == Qt.Checked:
                flat_list.append(item)
            for i in range(item.childCount()):
                stack.append(item.child(i))

        return flat_list





    def open_files(self, file_paths, folder_name):
        if file_paths:
            # Create a display name for the folder by replacing underscores with spaces
            display_folder_name = folder_name.replace('_', ' ')

            folder_item = QTreeWidgetItem([display_folder_name])
            self.fileTreeWidget.addTopLevelItem(folder_item)

            for file_path in file_paths:
                y, sr = librosa.load(file_path, sr=None, mono=False)  # Ensure original sample rate and stereo
                file_name = os.path.basename(file_path)

                # Determine the display name with unique identifier
                if 'pinknoise' in file_name.lower():
                    display_name = f"{display_folder_name} - Pink Noise"
                elif 'female' in file_name.lower():
                    display_name = f"{display_folder_name} - Female"
                elif 'male' in file_name.lower() and 'female' not in file_name.lower():
                    display_name = f"{display_folder_name} - Male"
                else:
                    display_name = f"{display_folder_name} - {file_name.split('.')[0].upper()}"

                waveform_item = QTreeWidgetItem([display_name])
                waveform_item.setFlags(waveform_item.flags() | Qt.ItemIsUserCheckable)  # Add checkbox
                waveform_item.setCheckState(0, Qt.Checked)  # Set initial state to checked
                folder_item.addChild(waveform_item)

                # Store the mapping in the dictionary with a unique key
                unique_key = f"{display_folder_name}_{display_name}"
                self.file_path_dict[unique_key] = file_path

                self.waveform_data.append((y, sr, unique_key))

            self.playButton.setEnabled(True)
            # Plot the first waveform and set it as the current media
            if self.waveform_data:
                y, sr, unique_key = self.waveform_data[0]
                display_name = folder_item.child(0).text(0)
                self.waveformCanvas.plot_waveform(y, sr, title=f"{display_folder_name} - {display_name}")  # Use display name for the title

            # Load the first file in the tree
            self.load_first_file()

            # Sort the top-level items (folders) alphabetically
            self.sort_top_level_items()
            # Expand all items
            self.expand_all_items()

    def sort_top_level_items(self):
        top_level_items = []

        while self.fileTreeWidget.topLevelItemCount() > 0:
            item = self.fileTreeWidget.takeTopLevelItem(0)
            if item is not None:
                top_level_items.append(item)

        top_level_items.sort(key=lambda item: item.text(0))

        for item in top_level_items:
            self.fileTreeWidget.addTopLevelItem(item)


    def expand_all_items(self):
        def recursive_expand(item):
            self.fileTreeWidget.expandItem(item)
            for i in range(item.childCount()):
                recursive_expand(item.child(i))

        root = self.fileTreeWidget.invisibleRootItem()
        for i in range(root.childCount()):
            recursive_expand(root.child(i))



    def load_and_adjust_waveform(self, y, sr, file_path, display_name, display_folder_name):
        duration = librosa.get_duration(y=y, sr=sr)

        # Update the title to use the display folder name and display name
        self.waveformCanvas.plot_waveform(y, sr, title=f"{display_folder_name} - {display_name}")

        # Set the new media
        self.set_media(file_path)

        # Maintain the play/pause status
        if not self.is_playing:
            self.mediaPlayer.pause()

        # Reapply loop points (now using selection patch)
        self.waveformCanvas.loop_start = self.loop_start
        self.waveformCanvas.loop_end = self.loop_end
        self.waveformCanvas.update_selection_patch()


    def set_media(self, file_path):
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        self.mediaPlayer.setPosition(self.playback_position)
        self.highlight_current_file()
        # Explicitly set the player to stop
        self.mediaPlayer.stop()





    def toggle_waveform(self):
        if not self.waveform_data:
            return

        # Check for selected items
        selected_items = self.flatten_tree(selected_only=True)

        if selected_items:
            flat_list = [item for item in selected_items if item.childCount() == 0]
        else:
            flat_list = [item for item in self.flatten_tree() if item.childCount() == 0]

        current_item = self.fileTreeWidget.currentItem()

        if current_item not in flat_list:
            # If current_item is not in flat_list, find the first leaf item and use it
            if flat_list:
                next_item = flat_list[0]
            else:
                return
        else:
            # Find the current index in the flat list
            current_index = flat_list.index(current_item)
            next_index = (current_index + 1) % len(flat_list)
            next_item = flat_list[next_index]

        # Load the next file
        self.fileTreeWidget.setCurrentItem(next_item)
        self.display_selected_waveform(next_item, reset_loop_points=False)




    def display_selected_waveform(self, item, reset_loop_points=True):
        parent = item.parent()
        if parent is None:
            # If a folder is selected, do nothing
            return

        # Save the current position and playback state
        self.playback_position = self.mediaPlayer.position()
        self.is_playing = (self.mediaPlayer.state() == QMediaPlayer.PlayingState)

        display_folder_name = parent.text(0)
        display_name = item.text(0)

        # Use the unique key to get the actual file path
        unique_key = f"{display_folder_name}_{display_name}"
        file_path = self.file_path_dict.get(unique_key)

        if file_path:
            for index, (y, sr, key) in enumerate(self.waveform_data):
                if key == unique_key:
                    previous_waveform = self.current_waveform
                    self.current_waveform = index
                    old_duration = librosa.get_duration(y=self.waveform_data[previous_waveform][0], sr=self.waveform_data[previous_waveform][1])
                    new_duration = librosa.get_duration(y=y, sr=sr)
                    if old_duration != new_duration and reset_loop_points:
                        self.waveformCanvas.reset_loop_points()
                    self.load_and_adjust_waveform(y, sr, file_path, display_name, display_folder_name)

                    # Update the current file type
                    self.current_file_type = display_name
                    break

        if reset_loop_points:
            self.waveformCanvas.reset_loop_points()  # Reset loop points every time an item is clicked
    def set_loop_points(self, start, end):
        duration = self.waveformCanvas.ax.get_xlim()[1]
        self.loop_start = max(0, min(start, duration))
        self.loop_end = max(0, min(end, duration))




    def highlight_current_file(self):
        if self.waveform_data:
            current_file = os.path.basename(self.waveform_data[self.current_waveform][2]).split('.')[0].upper()
            current_folder = os.path.basename(os.path.dirname(self.waveform_data[self.current_waveform][2]))
            items = self.fileTreeWidget.findItems(current_file, Qt.MatchRecursive)
            for item in items:
                if item.parent() and item.parent().text(0) == current_folder:
                    self.fileTreeWidget.setCurrentItem(item)
                    self.fileTreeWidget.scrollToItem(item)
                    break


    def play_pause(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.setVolume(100)  # Ensure volume is at 100% before playing
            self.mediaPlayer.play()
            self.timer.start()


    def set_position_from_click(self, time_in_seconds):
        position = int(time_in_seconds * 1000)  # Convert to milliseconds
        self.mediaPlayer.setPosition(position)

    def update_time(self):
        current_position = self.mediaPlayer.position()
        seconds = current_position // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        time_format = f"{minutes:02}:{seconds:02}"

        duration = self.mediaPlayer.duration()
        total_seconds = duration // 1000
        total_minutes = total_seconds // 60
        total_seconds = total_seconds % 60
        total_time_format = f"{total_minutes:02}:{total_seconds:02}"

        self.label.setText(f"{time_format}/{total_time_format}")

        current_time = current_position / 1000.0  # Convert to seconds
        self.waveformCanvas.update_line(current_time)
        
        # Check if we need to loop
        if current_time >= self.loop_end:
            self.mediaPlayer.setPosition(int(self.loop_start * 1000))

    def update_button_text(self, state):
        if (state == QMediaPlayer.PlayingState):
            self.playButton.setText("Pause")
        else:
            self.playButton.setText("Play")

    def check_loop(self, state):
        if (state == QMediaPlayer.StoppedState):
            self.mediaPlayer.setPosition(int(self.loop_start * 1000))
            self.mediaPlayer.play()
    def filter_pink_noise(self):
        root = self.fileTreeWidget.invisibleRootItem()
        stack = [root]
        while stack:
            parent = stack.pop()
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.childCount() == 0:  # Only affect leaf-level items
                    if 'pink noise' in child.text(0).lower():
                        child.setCheckState(0, Qt.Checked)
                    else:
                        child.setCheckState(0, Qt.Unchecked)
                stack.append(child)


    def filter_female(self):
        root = self.fileTreeWidget.invisibleRootItem()
        stack = [root]
        while stack:
            parent = stack.pop()
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.childCount() == 0:  # Only affect leaf-level items
                    if 'female' in child.text(0).lower():
                        child.setCheckState(0, Qt.Checked)
                    else:
                        child.setCheckState(0, Qt.Unchecked)
                stack.append(child)
    def filter_male(self):
        root = self.fileTreeWidget.invisibleRootItem()
        stack = [root]
        while stack:
            parent = stack.pop()
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.childCount() == 0:  # Only affect leaf-level items
                    text = child.text(0).lower()
                    if 'female' not in text and 'pink noise' not in text and 'male' in text:
                        child.setCheckState(0, Qt.Checked)
                    else:
                        child.setCheckState(0, Qt.Unchecked)
                stack.append(child)


    def select_all(self):
        root = self.fileTreeWidget.invisibleRootItem()
        stack = [root]
        while stack:
            parent = stack.pop()
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.childCount() == 0:  # Only affect leaf-level items
                    child.setCheckState(0, Qt.Checked)
                stack.append(child)

    def clear_all(self):
        root = self.fileTreeWidget.invisibleRootItem()
        stack = [root]
        while stack:
            parent = stack.pop()
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.childCount() == 0:  # Only affect leaf-level items
                    child.setCheckState(0, Qt.Unchecked)
                stack.append(child)

    def clear(self):
        try:
            # Clear waveform data
            self.waveform_data.clear()

            # Clear file tree widget
            self.fileTreeWidget.clear()

            # Clear waveform canvas
            self.waveformCanvas.ax.clear()
            self.waveformCanvas.draw_idle()

            # Reset loop points
            self.waveformCanvas.reset_loop_points()

            # Stop and reset media player
            self.mediaPlayer.stop()
            self.mediaPlayer.setMedia(QMediaContent())  # Reset the media content

            # Reset playback state
            self.playback_position = 0
            self.is_playing = False
            self.loop_start = 0
            self.loop_end = 0

            # Reset playback button text
            self.playButton.setText("Play")

            # Reset playback position label
            self.label.setText("00:00/00:00")

            # Disable play button as there are no files to play
            self.playButton.setEnabled(False)

            # Clear the file path dictionary
            self.file_path_dict.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while clearing data: {e}")

    def clear_all_files(self):
        self.waveform_data.clear()
        self.fileTreeWidget.clear()
        self.waveformCanvas.ax.clear()
        self.waveformCanvas.draw()
        self.mediaPlayer.setMedia(QMediaContent())
        self.label.setText("00:00/00:00")
        self.loop_start = 0
        self.loop_end = 0




class WaveWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Single Music Player with Toggle Waveform")
        self.setGeometry(100, 100, 1200, 600)  

        self.player = MusicPlayer(self)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.player)

        widget = QWidget()
        widget.setLayout(mainLayout)

        self.setCentralWidget(widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = WaveWindow()
    main_window.show()
    sys.exit(app.exec_())



