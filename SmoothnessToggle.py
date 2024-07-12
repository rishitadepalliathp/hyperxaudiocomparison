import sys
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QBrush, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QSizePolicy

class CustomSlider(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, labels, parent=None):
        super(CustomSlider, self).__init__(parent)
        self.labels = labels
        self.num_positions = len(labels)
        self.current_position = self.num_positions - 1  # Auto-start at the last position (12)
        self.setFixedHeight(50)  # Increased the height to allow space for the labels
        self.setCursor(Qt.PointingHandCursor)
        self.font = QFont("Forma DJR Micro", 8)
        self.is_dragging = False

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Allow horizontal expansion

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        track_rect = QRect(20, self.height() // 2 - 10, self.width() - 40, 10)
        handle_center_x = self.current_position * (self.width() - 40) // (self.num_positions - 1) + 20
        handle_radius = 10

        # Draw plain track
        painter.setBrush(QBrush(QColor(200, 200, 200)))  # Grey color for the track
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, 5, 5)

        # Draw handle
        painter.setBrush(QBrush(QColor(255, 255, 255)))  # White handle
        handle_y = track_rect.center().y()  # Center the handle on the track
        painter.drawEllipse(QRect(handle_center_x - handle_radius, handle_y - handle_radius, 2 * handle_radius, 2 * handle_radius))

        # Draw labels
        painter.setFont(self.font)
        painter.setPen(QColor(0, 0, 0))
        for i, label in enumerate(self.labels):
            text_x = 20 + i * (self.width() - 40) // (self.num_positions - 1)
            text_rect = QRect(text_x - 20, self.height() // 2 + 10, 40, 20)  # Lifted the vertical position by 5 pixels
            painter.drawText(text_rect, Qt.AlignCenter, label)

    def mousePressEvent(self, event):
        self.is_dragging = True
        self.update_position(event.x())

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.update_position(event.x())

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.update_position(event.x())
        self.valueChanged.emit(self.current_position)

    def update_position(self, x):
        position = max(0, min(self.num_positions - 1, round((x - 20) / (self.width() - 40) * (self.num_positions - 1))))
        if position != self.current_position:
            self.current_position = position
            self.update()

class SliderStack(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super(SliderStack, self).__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(5)  # Adjust vertical spacing as needed
        main_layout.setContentsMargins(0, 0, 0, 0)  # Set the margins to zero or a smaller value

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Allow horizontal expansion

        # Add "Smoothness" label
        sort_by_label = QLabel("Smoothing Octave:")
        sort_by_label.setFont(QFont("Forma DJR Micro", 8))  # Set the font to Forma DJR Micro
        sort_by_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(sort_by_label)

        # Labels for the slider
        self.labels = ['1/3', '1/6', '1/9', '1/12']

        # Create and add custom slider to layout
        self.slider = CustomSlider(self.labels, parent=self)
        self.slider.valueChanged.connect(self.on_value_changed)
        main_layout.addWidget(self.slider)

    def on_value_changed(self, position):
        value = int(self.labels[position][2:])
        self.valueChanged.emit(value)  # Emit the label value
        print(value)



# Main function to start the application
def main():
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("Custom Slider Example")
    main_window.setGeometry(100, 100, 400, 200)

    central_widget = QWidget()
    main_window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    slider_stack = SliderStack()
    layout.addWidget(slider_stack)

    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
