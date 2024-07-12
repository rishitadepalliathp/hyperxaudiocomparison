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
        self.loop_start_line = None
        self.loop_end_line = None
        self.loop_start_handle = None
        self.loop_end_handle = None
        self.loop_start = 0
        self.loop_end = 0
        self.dragging_line = None
        self.loop_line_drag_threshold = 0.01  # Threshold to detect dragging of loop lines
        self.mpl_connect('button_press_event', self.on_click)
        self.mpl_connect('motion_notify_event', self.on_motion)
        self.mpl_connect('button_release_event', self.on_release)
        # Clear the axes to ensure it starts as a white screen
        self.ax.clear()
        self.ax.axis('off')  # Turn off the axes

    def plot_waveform(self, y, sr, title=""):
        self.ax.clear()
        self.ax.plot(np.linspace(0, len(y) / sr, num=len(y)), y, color='#d1b8f2')
        self.ax.set_xlim(0, len(y) / sr)  # Ensure the x-axis starts at 0
        self.ax.set_ylim(-1, 1)  # Set the y-axis limits to -1 to 1
        self.ax.set_xlabel('Time (s)', fontproperties=MATPLOTLIB_FONT)
        self.ax.set_ylabel('Amplitude', fontproperties=MATPLOTLIB_FONT)
        self.ax.set_title(title, fontproperties=MATPLOTLIB_FONT)
        for label in self.ax.get_xticklabels() + self.ax.get_yticklabels():
            label.set_fontproperties(MATPLOTLIB_FONT)
        self.current_line = self.ax.axvline(0, color='b')  # Add a vertical line at the beginning
        self.loop_start_line = self.ax.axvline(self.loop_start, color='g', linestyle='--')
        self.loop_end_line = self.ax.axvline(self.loop_end, color='r', linestyle='--')
        self.loop_start_handle = self.ax.plot(self.loop_start, 1, '>', markersize=20, picker=20, color='#95ed98')[0]
        self.loop_end_handle = self.ax.plot(self.loop_end, 1, '<', markersize=20, picker=20, color='#f07575')[0]
        self.draw()
        self.loop_points_changed.emit(self.loop_start, self.loop_end)






    def update_line(self, current_time):
        if self.current_line:
            self.current_line.set_xdata([current_time])  # Update the x position of the vertical line
            self.draw_idle()  # Use draw_idle to reduce unnecessary redraws

    def on_click(self, event):
        if not self.loop_start_handle or not self.loop_end_handle:
            return  # Exit if no audio has been loaded

        if event.inaxes == self.ax:
            # Check for right-click (button 3)
            if event.button == 3:
                self.reset_loop_points()
                return

            contains_start, _ = self.loop_start_handle.contains(event)
            contains_end, _ = self.loop_end_handle.contains(event)
            if contains_start:
                self.dragging_line = 'start'
            elif contains_end:
                self.dragging_line = 'end'
            else:
                self.update_line(event.xdata)
                self.music_player.set_position_from_click(event.xdata)

    def on_motion(self, event):
        if not self.loop_start_handle or not self.loop_end_handle:
            return  # Exit if no audio has been loaded

        if self.dragging_line and event.inaxes == self.ax:
            if self.dragging_line == 'start':
                self.loop_start = max(0, min(event.xdata, self.loop_end))
                self.loop_start_line.set_xdata([self.loop_start])
                self.loop_start_handle.set_xdata([self.loop_start])
            elif self.dragging_line == 'end':
                self.loop_end = max(self.loop_start, min(event.xdata, self.ax.get_xlim()[1]))
                self.loop_end_line.set_xdata([self.loop_end])
                self.loop_end_handle.set_xdata([self.loop_end])
            self.draw_idle()
            self.loop_points_changed.emit(self.loop_start, self.loop_end)

    def on_release(self, event):
        if not self.loop_start_handle or not self.loop_end_handle:
            return  # Exit if no audio has been loaded

        self.dragging_line = None


    def reset_loop_points(self):
        self.loop_start = 0
        self.loop_end = self.ax.get_xlim()[1]
        self.loop_start_line.set_xdata([self.loop_start])
        self.loop_end_line.set_xdata([self.loop_end])
        self.loop_start_handle.set_xdata([self.loop_start])
        self.loop_end_handle.set_xdata([self.loop_end])
        self.draw_idle()
        self.loop_points_changed.emit(self.loop_start, self.loop_end)


class MusicPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

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

        self.toggleButton = QPushButton("Toggle")
        self.toggleButton.setMinimumHeight(100)
        self.toggleButton.setFont(font)
        self.toggleButton.clicked.connect(self.toggle_waveform)

        self.label = QLabel("00:00/00:00")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(font)
        self.label.setStyleSheet("font-size: 24px;")

        self.fileTreeWidget = QTreeWidget()
        self.fileTreeWidget.setFont(font)
        self.fileTreeWidget.setHeaderHidden(True)
        self.fileTreeWidget.itemClicked.connect(self.display_selected_waveform)

        self.timer = QTimer(self)
        self.timer.setInterval(10)  # Update every 20 milliseconds
        self.timer.timeout.connect(self.update_time)

        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.playButton)
        buttonLayout.addWidget(self.toggleButton)
        buttonLayout.addWidget(self.label)
        buttonLayout.addWidget(self.fileTreeWidget)

        buttonLayout.addStretch()

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
            folder_item = QTreeWidgetItem([folder_name])
            self.fileTreeWidget.addTopLevelItem(folder_item)

            for file_path in file_paths:
                y, sr = librosa.load(file_path, sr=None)
                file_name = os.path.basename(file_path)
                file_label = file_name.split('.')[0].upper()  # Get MALE, FEMALE, PINKNOISE
                waveform_item = QTreeWidgetItem([file_label])
                waveform_item.setFlags(waveform_item.flags() | Qt.ItemIsUserCheckable)  # Add checkbox
                waveform_item.setCheckState(0, Qt.Unchecked)  # Set initial state to unchecked
                folder_item.addChild(waveform_item)
                self.waveform_data.append((y, sr, file_path))

            self.playButton.setEnabled(True)
            # Plot the first waveform and set it as the current media
            if self.waveform_data:
                y, sr, file_path = self.waveform_data[0]
                self.waveformCanvas.plot_waveform(y, sr, title=file_name)  # Corrected call to plot_waveform
            
            # Load the first file in the tree
            self.load_first_file()




    def plot_waveform(self, y, sr, title="", target_sr=2000, smoothing_window=101):
        #Downsample the audio data
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        sr = target_sr

        # Apply a smoothing filter
        y = scipy.signal.savgol_filter(y, smoothing_window, polyorder=3)

        # Find the maximum absolute value to center the plot
        max_abs_y = max(abs(y))

        self.ax.clear()
        self.ax.plot(np.linspace(0, len(y) / sr, num=len(y)), y, color='#d1b8f2')
        self.ax.set_xlim(0, len(y) / sr)  # Ensure the x-axis starts at 0
        self.ax.set_ylim(-max_abs_y, max_abs_y)  # Center the y-axis at zero
        self.ax.set_xlabel('Time (s)', fontproperties=MATPLOTLIB_FONT)
        self.ax.set_ylabel('Amplitude', fontproperties=MATPLOTLIB_FONT)
        self.ax.set_title(title, fontproperties=MATPLOTLIB_FONT)
        for label in self.ax.get_xticklabels() + self.ax.get_yticklabels():
            label.set_fontproperties(MATPLOTLIB_FONT)
        self.current_line = self.ax.axvline(0, color='b')  # Add a vertical line at the beginning
        self.loop_start_line = self.ax.axvline(self.loop_start, color='g', linestyle='--')
        self.loop_end_line = self.ax.axvline(self.loop_end, color='r', linestyle='--')
        self.loop_start_handle = self.ax.plot(self.loop_start, max(y), '>', markersize=20, picker=20, color='#95ed98')[0]
        self.loop_end_handle = self.ax.plot(self.loop_end, max(y), '<', markersize=20, picker=20, color='#f07575')[0]
        self.draw()
        self.loop_points_changed.emit(self.loop_start, self.loop_end)



    def load_and_adjust_waveform(self, y, sr, file_path, folder_name):
        file_name = os.path.basename(file_path)
        duration = librosa.get_duration(y=y, sr=sr)

        self.waveformCanvas.plot_waveform(y, sr, title=f"{folder_name} - {file_name}")

        # Set the new media
        self.set_media(file_path)

        # Maintain the play/pause status
        if not self.is_playing:
            self.mediaPlayer.pause()

        # Reapply loop points
        self.waveformCanvas.loop_start = self.loop_start
        self.waveformCanvas.loop_end = self.loop_end
        self.waveformCanvas.loop_start_line.set_xdata([self.loop_start])
        self.waveformCanvas.loop_end_line.set_xdata([self.loop_end])
        self.waveformCanvas.loop_start_handle.set_xdata([self.loop_start])
        self.waveformCanvas.loop_end_handle.set_xdata([self.loop_end])
        self.waveformCanvas.draw_idle()


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

        # Find the current index in the flat list
        current_index = flat_list.index(current_item)
        next_index = (current_index + 1) % len(flat_list)
        next_item = flat_list[next_index]

        # Get the names of the current and next files
        current_file_label = current_item.text(0)
        next_file_label = next_item.text(0)

        # Load the next file
        self.fileTreeWidget.setCurrentItem(next_item)
        self.display_selected_waveform(next_item)

        # Compare the names and reset loop points if they don't match
        if current_file_label != next_file_label:
            self.waveformCanvas.reset_loop_points()






    def display_selected_waveform(self, item):
        parent = item.parent()
        if parent is None:
            # If a folder is selected, do nothing
            return

        # Save the current position and playback state
        self.playback_position = self.mediaPlayer.position()
        self.is_playing = (self.mediaPlayer.state() == QMediaPlayer.PlayingState)

        folder_name = parent.text(0)
        file_label = item.text(0)
        file_path = next((path for y, sr, path in self.waveform_data if os.path.basename(path).split('.')[0].upper() == file_label and os.path.basename(os.path.dirname(path)) == folder_name), None)

        if file_path:
            for index, (y, sr, path) in enumerate(self.waveform_data):
                if path == file_path:
                    previous_waveform = self.current_waveform
                    self.current_waveform = index
                    old_duration = librosa.get_duration(y=self.waveform_data[previous_waveform][0], sr=self.waveform_data[previous_waveform][1])
                    new_duration = librosa.get_duration(y=y, sr=sr)
                    if old_duration != new_duration:
                        self.waveformCanvas.reset_loop_points()
                    self.load_and_adjust_waveform(y, sr, path, folder_name)
                    break




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
        if (self.mediaPlayer.state() == QMediaPlayer.PlayingState):
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.setPosition(int(self.loop_start * 1000))  # Start playback from loop start
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
