import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter, LogLocator
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit, QSizePolicy, QGridLayout, QListWidget, QListWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.font_manager import FontProperties
import re
import logging
from SmoothnessToggle import SliderStack



logging.basicConfig(level=logging.INFO)

FONT_FAMILY = 'Forma DJR Micro'
FONT_SIZE = 10

def smooth_spectrum(X, f, Noct):
    assert np.isscalar(Noct) and Noct >= 0, 'NOCT must be a non-negative scalar.'
    assert all(f >= 0), 'Frequencies must be non-negative.'
    assert X.shape == f.shape, 'X and F must have the same shape.'

    x_oct = X.copy()  # Initial spectrum
    if Noct > 0:  # Perform smoothing only if Noct is greater than 0
        for i in range(np.argmax(f > 0), len(f)):  # Start from the first positive frequency
            g = gauss_f(f, f[i], Noct)
            x_oct[i] = np.sum(g * X)  # Calculate smoothed spectral coefficient
        if np.all(X >= 0):  # Remove undershoot when X is positive
            x_oct[x_oct < 0] = 0

    return x_oct

def gauss_f(f_x, F, Noct):
    sigma = (F / Noct) / np.pi  # Standard deviation
    g = np.exp(-((f_x - F) ** 2) / (2 * sigma ** 2))  # Gaussian function
    g /= np.sum(g)  # Normalize magnitude
    return g

class CustomNavigationToolbar(NavigationToolbar2QT):
    def __init__(self, canvas, parent=None):
        super().__init__(canvas, parent)
        self.remove_unused_actions()

    def remove_unused_actions(self):
        actions_to_remove = ['Home', 'Back', 'Forward', 'Subplots', 'Customize']
        for action in self.actions():
            if action.text() in actions_to_remove:
                self.removeAction(action)

class NormalizeButton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.button = QPushButton("Normalize to:", self)
        self.input = QLineEdit(self)
        self.input.setMaximumWidth(100)
        self.input.setText('1k')
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.input)
        self.setLayout(self.layout)
        self.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.input.editingFinished.connect(self.format_input)

    def format_input(self):
        try:
            value = float(self.input.text().replace('k', '000').replace('K', '000'))
            if value >= 1000:
                self.input.setText(f'{value / 1000:.1f}k')
            else:
                self.input.setText(f'{value:.0f}')
        except ValueError:
            self.input.clear()

    def update_button_text(self, text):
        self.button.setText(text)


class CustomQListWidget(QListWidget):
    def mousePressEvent(self, event):
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        super().mouseMoveEvent(event)

class CSVGrapher(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dataframes = []
        self.original_dataframes = []
        self.file_names = []
        self.initial_xmin = 20
        self.initial_xmax = 20000
        self.Noct = 12  # Default smoothing factor



        self.setup_ui()
        self.setup_connections()
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.canvas.mpl_connect('button_press_event', self.on_right_click)  # Right-click event
        self.lines = []
        self.original_linewidths = []
        self.highlighted_lines = set()  # To keep track of the currently highlighted lines
        self.update_button_states()
        self.init_plot()


    def resizeEvent(self, event):
        self.update_gui_width()
        super().resizeEvent(event)

    def update_gui_width(self):
        total_width = self.width()
        left_width = int(total_width * 0.73)
        right_width = total_width - left_width

        # Adjust the stretch factors
        self.layout.setStretchFactor(self.left_layout, left_width)
        self.layout.setStretchFactor(self.right_layout, right_width)

    def setup_ui(self):
        self.setWindowTitle("CSV Grapher")
        self.setGeometry(100, 100, 1400, 800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        self.left_layout = QVBoxLayout()
        self.layout.addLayout(self.left_layout, stretch=4)  # Set stretch factor to 4 for the graph area

        self.figure = plt.figure(figsize=(14, 8))
        self.figure.patch.set_facecolor('white')  # Set the figure face color to white
        self.canvas = FigureCanvas(self.figure)
        self.left_layout.addWidget(self.canvas)

        self.toolbar = CustomNavigationToolbar(self.canvas, self)
        self.left_layout.addWidget(self.toolbar)

        # Define a fixed width for the button area
        self.right_layout_widget = QWidget(self)
        self.right_layout_widget.setFixedWidth(400)  # Set the fixed width of the button area
        self.right_layout = QVBoxLayout(self.right_layout_widget)
        self.right_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self.layout.addWidget(self.right_layout_widget, stretch=1)  # Add button area with no stretch


        self.slider_stack = SliderStack(self)
        self.slider_stack.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.slider_stack.valueChanged.connect(self.update_smoothness)  # Connect the signal
        self.right_layout.addWidget(self.slider_stack)

        self.grid_layout = QGridLayout()
        self.right_layout.addLayout(self.grid_layout)

        self.setup_grid_inputs()


        self.scale_button_80_12000 = QPushButton("80 Hz - 12 kHz", self)
        self.scale_button_80_12000.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.scale_button_80_12000.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.right_layout.addWidget(self.scale_button_80_12000)

        self.normalize_button = NormalizeButton(self)
        self.right_layout.addWidget(self.normalize_button)

        # Add the QListWidget for file titles
        self.file_list_widget = CustomQListWidget(self)
        self.file_list_widget.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.right_layout.addWidget(self.file_list_widget)
        self.file_list_widget.itemChanged.connect(self.on_item_changed)


        # Add the "Remove" button
        self.remove_button = QPushButton("Remove", self)
        self.remove_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.remove_button.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.right_layout.addWidget(self.remove_button)



    def setup_grid_inputs(self):
        labels = ["Min X:", "Max X:", "Min Y:", "Max Y:"]
        self.inputs = {}

        for i, label in enumerate(labels):
            row = i // 2
            col = (i % 2) * 2
            input_label = QLabel(label)
            input_label.setFont(QFont(FONT_FAMILY, FONT_SIZE))
            input_field = QLineEdit(self)
            input_field.setMaximumWidth(100)
            input_field.setFont(QFont(FONT_FAMILY, FONT_SIZE))
            input_field.editingFinished.connect(lambda field=input_field: self.format_input(field))
            input_field.returnPressed.connect(self.update_plot)  # Connect the returnPressed signal to update_plot
            self.grid_layout.addWidget(input_label, row, col)
            self.grid_layout.addWidget(input_field, row, col + 1)
            self.inputs[label] = input_field

        # Set initial values for x-axis
        self.inputs["Min X:"].setText("80")
        self.inputs["Max X:"].setText("12k")


    def format_input(self, field):
        try:
            value = float(field.text().replace('k', '000').replace('K', '000'))
            if value >= 1000:
                field.setText(f'{value / 1000:.1f}k')
            else:
                field.setText(f'{value:.0f}')
        except ValueError:
            field.clear()

    def setup_connections(self):
        self.scale_button_80_12000.clicked.connect(self.scale_80_12000)
        self.normalize_button.button.clicked.connect(self.normalize_at_x)
        self.file_list_widget.itemClicked.connect(self.on_file_list_click)
        self.remove_button.clicked.connect(self.remove_selected)


    def update_button_states(self):
        has_files = len(self.file_names) > 0

    def load_csv(self, file_path, folder_name):
        df = pd.read_csv(file_path, skiprows=3)

        if df.shape[1] < 2:
            logging.warning("The CSV file must have at least two columns for x and y axes.")
            return

        df[df.columns[0]] = pd.to_numeric(df[df.columns[0]], errors='coerce')
        df[df.columns[1]] = pd.to_numeric(df[df.columns[1]], errors='coerce')
        df.dropna(subset=[df.columns[0], df.columns[1]], inplace=True)

        # Downsample the data to 2000 points using log scale
        df = self.downsample_data(df, 2000)

        self.dataframes.append(df)
        self.original_dataframes.append(df.copy())
        self.file_names.append(folder_name)  # Use folder name instead of file name

        self.apply_smoothing_and_update_plot()
        self.normalize_at_x()
        self.update_file_list_widget()
        self.autoframe()  # Ensure the plot is framed correctly


    def downsample_data(self, df, num_points=2000):
        if len(df) > num_points:
            min_freq, max_freq = df[df.columns[0]].min(), df[df.columns[0]].max()
            log_indices = np.geomspace(min_freq, max_freq, num_points)
            df = df.set_index(df.columns[0]).reindex(log_indices, method='nearest').reset_index()
        return df

    def plot_csv(self, file_name, overlay=False):
        df = pd.read_csv(file_name, skiprows=3)

        if df.shape[1] < 2:
            logging.warning("The CSV file must have at least two columns for x and y axes.")
            return

        df[df.columns[0]] = pd.to_numeric(df[df.columns[0]], errors='coerce')
        df[df.columns[1]] = pd.to_numeric(df[df.columns[1]], errors='coerce')
        df.dropna(subset=[df.columns[0], df.columns[1]], inplace=True)
        
        # Downsample the data to 2000 points using log scale
        df = self.downsample_data(df, 2000)

        if overlay:
            self.dataframes.append(df)
            self.original_dataframes.append(df.copy())
        else:
            self.dataframes = [df]
            self.original_dataframes = [df.copy()]
            self.file_names = [file_name]

        self.apply_smoothing_and_update_plot()
        self.normalize_at_x()

    def apply_smoothing_and_update_plot(self):
        self.dataframes = [df.copy() for df in self.original_dataframes]  # Reset to original data
        for df in self.dataframes:
            X = df[df.columns[1]].values
            f = df[df.columns[0]].values
            smoothed_X = smooth_spectrum(X, f, self.Noct)  # Use self.Noct
            df[df.columns[1]] = smoothed_X
        self.update_plot()
        self.normalize_at_x()

    def update_file_list_widget(self):
        self.file_list_widget.clear()
        for folder_name in self.file_names:
            item = QListWidgetItem(folder_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # Add checkbox flag
            item.setCheckState(Qt.Unchecked)  # Set default state to unchecked
            self.file_list_widget.addItem(item)
        self.update_button_states()
        
    @pyqtSlot(QListWidgetItem)
    def on_item_changed(self, item):
        checked_items = [item for item in self.file_list_widget.findItems("*", Qt.MatchWildcard) if item.checkState() == Qt.Checked]
        if checked_items:
            self.normalize_button.update_button_text("Normalize Selected to:")
        else:
            self.normalize_button.update_button_text("Normalize to:")




    def parse_input(self, value):
        try:
            if re.match(r'^\d+(\.\d+)?[kK]$', value):
                return round(float(value[:-1]) * 1000, 2)
            elif re.match(r'^\d+(\.\d+)?[mM]$', value):
                return round(float(value[:-1]) * 1_000_000, 2)
            else:
                return round(float(value), 2)
        except ValueError:
            return None

    def update_plot(self, initial=False):
        if not self.dataframes:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self.lines = []  # Clear previous lines
        self.original_linewidths = []  # Clear previous line widths
        for df, file_name in zip(self.dataframes, self.file_names):
            display_name = file_name.split("/")[-1].replace('.csv', '')
            line, = ax.plot(df[df.columns[0]], df[df.columns[1]], label=display_name, picker=True)  # Enable picking
            self.lines.append(line)
            self.original_linewidths.append(line.get_linewidth())

        # Set the axis labels to 'Hz' and 'dB'
        ax.set_xlabel('Hz', fontsize=10, family=FONT_FAMILY)
        ax.set_ylabel('dB', fontsize=10, family=FONT_FAMILY)
        ax.set_xscale('log')
        ax.xaxis.set_major_locator(LogLocator(base=10.0, subs=[1, 2, 4, 8], numticks=15))
        
        # Update the x-axis formatter to use shorthand for large numbers
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: '{:.1f}k'.format(x / 1000) if x >= 1000 else '{:.0f}'.format(x)))
        
        ax.yaxis.set_major_locator(MaxNLocator(nbins=10))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.1f}'.format(y)))

        font_properties = FontProperties(family=FONT_FAMILY, size=8)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font_properties)

        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        if initial:
            ax.set_xlim(left=self.initial_xmin, right=self.initial_xmax)
        else:
            xmin = self.parse_input(self.inputs["Min X:"].text())
            xmax = self.parse_input(self.inputs["Max X:"].text())
            ymin = self.parse_input(self.inputs["Min Y:"].text())
            ymax = self.parse_input(self.inputs["Max Y:"].text())

            # Ensure x-axis limits are within [0, 20000] for log scale
            if xmin is not None and xmax is not None:
                xmin = max(1, xmin)  # Log scale cannot have non-positive values
                xmax = min(20000, xmax)
                if xmin < xmax:
                    ax.set_xlim(left=xmin, right=xmax)
            
            if ymin is not None and ymax is not None and ymin < ymax:
                ax.set_ylim(bottom=ymin, top=ymax)

        ax.set_title("Magnitude Response(s)", family=FONT_FAMILY)
        ax.legend(prop={'family': FONT_FAMILY, 'size': FONT_SIZE})
        self.canvas.draw_idle()

    def on_scroll(self, event):
        if not self.dataframes:
            return  # Exit if no data has been loaded

        ax = self.figure.gca()
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]

        x_factor = 0.1  # Zoom factor for x-axis

        if event.button == 'up':
            y_factor = 0.1
            xlim = [xlim[0] + x_range * x_factor, xlim[1] - x_range * x_factor]
            ylim = [ylim[0] + y_range * y_factor, ylim[1] - y_range * y_factor]
        elif event.button == 'down':
            y_factor = 0.01
            xlim = [xlim[0] - x_range * x_factor, xlim[1] + x_range * x_factor]
            ylim = [ylim[0] - y_range * y_factor, ylim[1] + y_range * y_factor]

        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        self.canvas.draw_idle()


    def on_pick(self, event):
        artist = event.artist
        if artist in self.highlighted_lines:
            self.highlighted_lines.remove(artist)
        else:
            self.highlighted_lines = {artist}
        self.highlight_selected_lines()
        self.update_file_selection()

    def highlight_selected_lines(self):
        if not self.highlighted_lines:
            for line, original_width in zip(self.lines, self.original_linewidths):
                line.set_linewidth(original_width)  # Reset to original width
                line.set_alpha(1.0)  # Reset to full opacity
        else:
            for line in self.lines:
                if line in self.highlighted_lines:
                    line.set_linewidth(2.0)  # Bold the selected line
                    line.set_alpha(1.0)  # Full opacity for selected line
                else:
                    line.set_linewidth(1.0)  # Normal width for non-selected lines
                    line.set_alpha(0.5)  # Reduced opacity for non-selected lines
        self.canvas.draw_idle()
        self.update_file_selection()


    @pyqtSlot(QListWidgetItem)
    def on_file_list_click(self, item):
        index = self.file_list_widget.row(item)
        if index >= 0 and index < len(self.lines):
            line = self.lines[index]
            self.highlighted_lines = {line} if line not in self.highlighted_lines else set()
        self.highlight_selected_lines()
        self.update_file_selection()

    def update_file_selection(self):
        self.file_list_widget.blockSignals(True)  # Prevent signals during selection update
        self.file_list_widget.clearSelection()
        for line in self.highlighted_lines:
            if line in self.lines:  # Ensure the line is in the list before accessing its index
                index = self.lines.index(line)
                item = self.file_list_widget.item(index)
                if item is not None:
                    item.setSelected(True)
        self.file_list_widget.blockSignals(False)

    def enforce_x_limits(self):
        """Ensure the x-axis limits remain within [0, 20000]."""
        ax = self.figure.gca()
        xmin, xmax = ax.get_xlim()
        xmin = max(1, xmin)  # Log scale cannot have non-positive values
        xmax = min(20000, xmax)
        ax.set_xlim(left=xmin, right=xmax)



    def scale_80_12000(self):
        self.inputs["Min X:"].setText("80")
        self.inputs["Max X:"].setText("12k")
        self.update_plot()

    def normalize_at_x(self):
        try:
            x_value = self.parse_input(self.normalize_button.input.text())
            if x_value is not None:
                checked_items = [item for item in self.file_list_widget.findItems("*", Qt.MatchWildcard) if item.checkState() == Qt.Checked]
                if not checked_items:  # No items checked, normalize all loaded files
                    for df in self.dataframes:
                        y_value_at_x = np.interp(x_value, df[df.columns[0]], df[df.columns[1]])
                        df[df.columns[1]] -= y_value_at_x
                else:  # Normalize only the checked files
                    checked_indices = [self.file_list_widget.row(item) for item in checked_items]
                    for index in checked_indices:
                        df = self.dataframes[index]
                        y_value_at_x = np.interp(x_value, df[df.columns[0]], df[df.columns[1]])
                        df[df.columns[1]] -= y_value_at_x
                self.update_plot()
                self.autoframe()  # Autoframe after normalization
            else:
                logging.info("Specified x-value not found in the data.")
        except ValueError:
            logging.error("Invalid input for normalization x-value.")




    def remove_selected(self):
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            return
        indices_to_remove = [self.file_list_widget.row(item) for item in selected_items]
        
        # Remove from the end to avoid index shifting issues
        for index in sorted(indices_to_remove, reverse=True):
            del self.dataframes[index]
            del self.original_dataframes[index]
            del self.file_names[index]
        
        self.update_file_list_widget()
        self.update_plot()
        self.highlighted_lines.clear()
        self.highlight_selected_lines()

    def update_smoothness(self, value):
        self.Noct = value
        self.deselect_all_items()  # Deselect all items in the list before smoothing
        self.smooth_plot()

    def deselect_all_items(self):
        self.file_list_widget.blockSignals(True)  # Prevent signals during deselection
        self.file_list_widget.clearSelection()
        self.highlighted_lines.clear()
        self.file_list_widget.blockSignals(False)
        self.highlight_selected_lines()  # Reset the line styles


    def smooth_plot(self):
        self.apply_smoothing_and_update_plot()

    def autoframe(self):
        if not self.dataframes:
            return

        y_values = np.concatenate([df[df.columns[1]].values for df in self.dataframes])
        mean_y = np.mean(y_values)
        ymin = mean_y - 35
        ymax = mean_y + 35

        self.inputs["Min Y:"].setText(str(round(ymin, 2)))
        self.inputs["Max Y:"].setText(str(round(ymax, 2)))
        self.update_plot()

    def on_right_click(self, event):
        if event.button == 3:  # Right mouse button
            self.autoframe()

    def init_plot(self):
        self.update_plot(initial=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont(FONT_FAMILY, FONT_SIZE))
    window = CSVGrapher()
    window.show()
    sys.exit(app.exec_())

