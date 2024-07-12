import sys
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QColor, QPainter, QBrush, QFont, QPen
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel

class ToggleSwitch(QWidget):
    def __init__(self, parent=None, toggle_stack=None, label_text=""):
        super(ToggleSwitch, self).__init__(parent)
        self.setFixedSize(40, 20)
        self.setCursor(Qt.PointingHandCursor)
        self.checked = False
        self.toggle_stack = toggle_stack
        self.label_text = label_text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the background
        painter.setPen(Qt.NoPen)
        if self.checked:
            painter.setBrush(QBrush(QColor(0, 0, 0)))  # Black color when checked
            painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)
            painter.setBrush(QBrush(QColor(255, 255, 255)))
        else:
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)
            painter.setBrush(QBrush(QColor(255, 255, 255)))

        # Draw the handle with a thin black outline
        pen = QPen(QColor(200, 200, 200), 1)
        painter.setPen(pen)
        if self.checked:
            painter.drawEllipse(self.width() - self.height(), 0, self.height(), self.height())
        else:
            painter.drawEllipse(0, 0, self.height(), self.height())

    def mousePressEvent(self, event):
        if not self.checked:
            self.checked = True
            self.update()
            if self.toggle_stack:
                self.toggle_stack.toggle_changed(self)
        else:
            self.checked = False
            self.update()

class ToggleStack(QWidget):
    def __init__(self, parent=None):
        super(ToggleStack, self).__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # Add "Sort By:" label
        sort_by_label = QLabel("Sort By:")
        sort_by_label.setFont(QFont("Forma DJR Micro", 8))  # Set the font to Forma DJR Micro
        sort_by_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(sort_by_label)

        # Layout for toggle switches
        toggle_layout = QVBoxLayout()
        toggle_layout.setAlignment(Qt.AlignCenter)

        # Labels for the toggle switches
        self.labels = ['Product', 'Pattern', 'Effects']

        # Create and add toggle switches with labels to layout
        self.toggle_switches = []
        for label_text in self.labels:
            h_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setFont(QFont("Forma DJR Micro", 8))  # Set the font to Forma DJR Micro
            label.setAlignment(Qt.AlignLeft)
            toggle_switch = ToggleSwitch(parent=self, toggle_stack=self, label_text=label_text)
            self.toggle_switches.append(toggle_switch)
            h_layout.addWidget(label)
            h_layout.addWidget(toggle_switch)
            h_layout.setAlignment(Qt.AlignCenter)
            toggle_layout.addLayout(h_layout)

        main_layout.addLayout(toggle_layout)

    def toggle_changed(self, active_switch):
        for toggle in self.toggle_switches:
            if toggle != active_switch:
                toggle.checked = False
                toggle.update()
        print(active_switch.label_text)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Toggle Switch Example")

        # Create and set central widget to ToggleStack
        toggle_stack = ToggleStack()
        self.setCentralWidget(toggle_stack)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
