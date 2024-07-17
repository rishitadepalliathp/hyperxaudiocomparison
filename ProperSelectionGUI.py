import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QListWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QBrush, QColor
from ToggleButton import ToggleStack  # Import the ToggleStack class

# Reads in folder names and establishes necessary lists
path = 'C:\\Users\\TaRi525\\Documents\\Hyper X Intern Project\\GeneratedFolders'
try:
    names = os.listdir(path)
except Exception as e:
    print(f"Error reading directory: {e}")
    names = []

info = [name.split('_') for name in names]
hyperx_microphones = [thing for thing in info if thing[0] == "HyperX"]
competitor_microphones = [thing for thing in info if thing[0] != "HyperX"]

hyperx_microphones.sort()
competitor_microphones.sort()

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
        self.left_panel.setStyleSheet("background-color: white; border: none; border-radius: 10px")
        
        self.set_left_panel_width()  # Call the method to set initial width
        
        main_layout.addWidget(self.left_panel, 1)

        left_layout = QVBoxLayout()
        self.left_panel.setLayout(left_layout)

        # Horizontal layout for title and toggle switch
        title_layout = QHBoxLayout()

        title = QLabel("Microphones")
        title.setStyleSheet("font-size: 60px; font-family: 'Forma DJR Display';")
        title_layout.addWidget(title)

        # Add ToggleStack to the right of the title
        self.toggle_stack = ToggleStack()
        title_layout.addWidget(self.toggle_stack)
        title_layout.setAlignment(self.toggle_stack, Qt.AlignRight)

        left_layout.addLayout(title_layout)

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
        self.scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)

        left_layout.addWidget(scroll_area)

        # Connect the ToggleStack signal to a slot
        for toggle_switch in self.toggle_stack.toggle_switches:
            toggle_switch.toggled.connect(self.handle_toggle)

        # Initialize the tree layout
        self.add_microphone_sections()

        main_layout.addLayout(left_layout, 1)  # Add left_layout to main_layout
        
        # Right panel for displaying checked items
        self.right_panel = QFrame()
        self.right_panel.setFrameShape(QFrame.StyledPanel)
        self.right_panel.setStyleSheet("background-color: white; border: none; border-radius: 10px")
        
        right_layout = QVBoxLayout()
        self.right_panel.setLayout(right_layout)
        
        main_layout.addWidget(self.right_panel, 1)

        # List widget to display checked items
        self.checked_list_widget = QListWidget()
        right_layout.addWidget(self.checked_list_widget)

        self.show()

    def set_left_panel_width(self):
        screen_width = QApplication.primaryScreen().geometry().width()
        desired_width = int(screen_width * 0.27)  # 27% of the screen width
        new_width = min(desired_width, 600)  # Use the smaller of 27% screen width or 600 pixels
        self.left_panel.setFixedWidth(new_width)
        
    def resizeEvent(self, event):
        self.set_left_panel_width()  # Adjust width on resize
        super().resizeEvent(event)

    def add_microphone_sections(self):
        # Clear the existing layout
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.scroll_layout.removeItem(self.scroll_layout.itemAt(i))

        # HyperX section
        self.hyperx_tree = QTreeWidget()
        self.hyperx_tree.setHeaderHidden(True)
        self.hyperx_tree.itemChanged.connect(self.on_item_changed)
        self.hyperx_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #DEE0F6;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            QTreeWidget::item {
                color: black;
            }
            QTreeWidget::item:selected {
                background-color: #BBD2F5;
            }
        """)

        hyperx_font = QFont("Forma DJR Display", 20)
        hyperx_title = QTreeWidgetItem(["Hyper X"])
        hyperx_title.setFont(0, hyperx_font)
        hyperx_title.setFlags(hyperx_title.flags() | Qt.ItemIsUserCheckable)
        hyperx_title.setCheckState(0, Qt.Unchecked)
        self.hyperx_tree.addTopLevelItem(hyperx_title)

        self.add_microphone_items(hyperx_title, hyperx_microphones, hyperx_font, False)

        # Competitor section
        self.competitor_tree = QTreeWidget()
        self.competitor_tree.setHeaderHidden(True)
        self.competitor_tree.itemChanged.connect(self.on_item_changed)
        self.competitor_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #F6DEDE;
                border-radius: 10px;
            }
            QTreeWidget::item {
                color: black;
            }
            QTreeWidget::item:selected {
                background-color: #F4BFBF;
            }
        """)

        competitor_font = QFont("Forma DJR Display", 20)
        competitor_title = QTreeWidgetItem(["Competitors"])
        competitor_title.setFont(0, competitor_font)
        competitor_title.setFlags(competitor_title.flags() | Qt.ItemIsUserCheckable)
        competitor_title.setCheckState(0, Qt.Unchecked)
        self.competitor_tree.addTopLevelItem(competitor_title)

        self.add_microphone_items(competitor_title, competitor_microphones, competitor_font, True)

        self.scroll_layout.addWidget(self.hyperx_tree)
        self.scroll_layout.addWidget(self.competitor_tree)


    def add_microphone_items(self, parent_item, microphones, font, is_competitor):
        if is_competitor:
            companies = {}
            for mic in microphones:
                company = mic[0]
                model = mic[1]
                pattern = mic[2]
                position = mic[3]
                config = mic[4]

                if company not in companies:
                    companies[company] = self.find_or_create_child(parent_item, company, font)
                company_item = companies[company]

                model_item = self.find_or_create_child(company_item, model, font)
                pattern_item = self.find_or_create_child(model_item, pattern, font)
                position_item = self.find_or_create_child(pattern_item, position, font)
                self.find_or_create_child(position_item, config, font)
        else:
            for mic in microphones:
                model = mic[1]
                pattern = mic[2]
                position = mic[3]
                config = mic[4]

                model_item = self.find_or_create_child(parent_item, model, font)
                pattern_item = self.find_or_create_child(model_item, pattern, font)
                position_item = self.find_or_create_child(pattern_item, position, font)
                self.find_or_create_child(position_item, config, font)


    def add_pattern_sections(self):
        # Clear the existing layout
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.scroll_layout.removeItem(self.scroll_layout.itemAt(i))

        # Pattern section
        self.pattern_tree = QTreeWidget()
        self.pattern_tree.setHeaderHidden(True)
        self.pattern_tree.itemChanged.connect(self.on_item_changed_pattern)
        self.pattern_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #DEE0F6;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            QTreeWidget::item {
                color: black;
            }
            QTreeWidget::item:selected {
                background-color: #BBD2F5;
            }
        """)

        pattern_font = QFont("Forma DJR Display", 20)

        # Add items to the pattern section
        self.add_pattern_items(pattern_font)

        self.scroll_layout.addWidget(self.pattern_tree)

    def add_pattern_items(self, font):
        patterns = {}

        # Combine hyperx_microphones and competitor_microphones
        all_microphones = hyperx_microphones + competitor_microphones

        for mic in all_microphones:
            pattern = mic[2]
            company = mic[0]
            model = mic[1]
            position = mic[3]
            config = mic[4]

            if pattern not in patterns:
                patterns[pattern] = QTreeWidgetItem([pattern])
                patterns[pattern].setFont(0, font)
                patterns[pattern].setFlags(patterns[pattern].flags() | Qt.ItemIsUserCheckable)
                patterns[pattern].setCheckState(0, Qt.Unchecked)
                self.pattern_tree.addTopLevelItem(patterns[pattern])

            pattern_item = patterns[pattern]
            company_item = self.find_or_create_child(pattern_item, company, font)
            model_item = self.find_or_create_child(company_item, model, font)
            position_item = self.find_or_create_child(model_item, position, font)
            self.find_or_create_child(position_item, config, font)

    def add_effects_sections(self):
        # Clear the existing layout
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.scroll_layout.removeItem(self.scroll_layout.itemAt(i))

        # Effects section
        self.effects_tree = QTreeWidget()
        self.effects_tree.setHeaderHidden(True)
        self.effects_tree.itemChanged.connect(self.on_item_changed_effects)
        self.effects_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #DEE0F6;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            QTreeWidget::item {
                color: black;
            }
            QTreeWidget::item:selected {
                background-color: #BBD2F5;
            }
        """)

        effects_font = QFont("Forma DJR Display", 20)

        # Add items to the effects section
        self.add_effects_items(effects_font)

        self.scroll_layout.addWidget(self.effects_tree)

    def add_effects_items(self, font):
        effects = {}

        # Combine hyperx_microphones and competitor_microphones
        all_microphones = hyperx_microphones + competitor_microphones

        for mic in all_microphones:
            effect = mic[4]  # Assuming 'config' represents the effect
            company = mic[0]
            model = mic[1]
            pattern = mic[2]
            position = mic[3]

            if effect not in effects:
                effects[effect] = QTreeWidgetItem([effect])
                effects[effect].setFont(0, font)
                effects[effect].setFlags(effects[effect].flags() | Qt.ItemIsUserCheckable)
                effects[effect].setCheckState(0, Qt.Unchecked)
                self.effects_tree.addTopLevelItem(effects[effect])

            effect_item = effects[effect]
            company_item = self.find_or_create_child(effect_item, company, font)
            model_item = self.find_or_create_child(company_item, model, font)
            pattern_item = self.find_or_create_child(model_item, pattern, font)
            self.find_or_create_child(pattern_item, position, font)

    def find_or_create_child(self, parent, text, font):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.text(0) == text:
                return child

        new_child = QTreeWidgetItem([text])
        new_child.setFont(0, font)
        new_child.setForeground(0, QBrush(QColor("black")))  # Ensure the text color is black
        new_child.setFlags(new_child.flags() | Qt.ItemIsUserCheckable)
        new_child.setCheckState(0, Qt.Unchecked)
        parent.addChild(new_child)
        return new_child

    def on_item_changed(self, item, column):
        if column == 0:  # Ensure we are working with the first column where the checkbox is
            state = item.checkState(column)
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, state)
            self.update_checked_list()

    def on_item_changed_pattern(self, item, column):
        if column == 0:  # Ensure we are working with the first column where the checkbox is
            state = item.checkState(column)
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, state)
            self.update_checked_list_pattern()

    def on_item_changed_effects(self, item, column):
        if column == 0:  # Ensure we are working with the first column where the checkbox is
            state = item.checkState(column)
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, state)
            self.update_checked_list_effects()

    def update_checked_list(self):
        self.checked_list_widget.clear()
        self.add_checked_items(self.hyperx_tree)
        self.add_checked_items(self.competitor_tree, is_competitor=True)


    def update_checked_list_pattern(self):
        self.checked_list_widget.clear()
        self.add_checked_items_pattern(self.pattern_tree)

    def update_checked_list_effects(self):
        self.checked_list_widget.clear()
        self.add_checked_items_effects(self.effects_tree)

    def add_checked_items(self, tree_widget, is_competitor=False):
        if tree_widget:
            root = tree_widget.invisibleRootItem()
            stack = [root]
            while stack:
                parent = stack.pop()
                for i in range(parent.childCount()):
                    child = parent.child(i)
                    if child.checkState(0) == Qt.Checked:
                        full_path = self.get_full_path(child, is_competitor)
                        if full_path:
                            self.checked_list_widget.addItem(full_path)
                    stack.append(child)




    def add_checked_items_pattern(self, tree_widget):
        if tree_widget:
            root = tree_widget.invisibleRootItem()
            stack = [root]
            while stack:
                parent = stack.pop()
                for i in range(parent.childCount()):
                    child = parent.child(i)
                    if child.checkState(0) == Qt.Checked:
                        full_path = self.get_full_path_pattern(child)
                        if full_path:
                            self.checked_list_widget.addItem(full_path)
                    stack.append(child)


    def add_checked_items_effects(self, tree_widget):
        if tree_widget:
            root = tree_widget.invisibleRootItem()
            stack = [root]
            while stack:
                parent = stack.pop()
                for i in range(parent.childCount()):
                    child = parent.child(i)
                    if child.checkState(0) == Qt.Checked:
                        full_path = self.get_full_path_effects(child)
                        if full_path:
                            self.checked_list_widget.addItem(full_path)
                    stack.append(child)


    def get_full_path(self, item, is_competitor=False):
        base_path = 'C:\\Users\\TaRi525\\Documents\\Hyper X Intern Project\\GeneratedFolders'
        path = []
        while item:
            path.append(item.text(0))
            item = item.parent()
        if is_competitor:
            path = path[:-1]  # Remove the "Competitors" part
        path.reverse()
        if len(path) == 5:  # Ensure the full path has all five components
            folder_name = "_".join(path)
            return os.path.join(base_path, folder_name)
        return None

    def get_full_path_pattern(self, item):
        base_path = 'C:\\Users\\TaRi525\\Documents\\Hyper X Intern Project\\GeneratedFolders'
        path = []
        while item:
            path.append(item.text(0))
            item = item.parent()
        path.reverse()
        if len(path) == 5:  # Ensure the full path has all five components
            # Reorder the components to Company > Product > Pattern > Position > Effect
            reordered_path = [path[1], path[2], path[0], path[3], path[4]]
            folder_name = "_".join(reordered_path)
            return os.path.join(base_path, folder_name)
        return None

    def get_full_path_effects(self, item):
        base_path = 'C:\\Users\\TaRi525\\Documents\\Hyper X Intern Project\\GeneratedFolders'
        path = []
        while item:
            path.append(item.text(0))
            item = item.parent()
        path.reverse()
        if len(path) == 5:  # Ensure the full path has all five components
            # Reorder the components to Company > Product > Pattern > Position > Effect
            reordered_path = [path[1], path[2], path[3], path[4], path[0]]
            folder_name = "_".join(reordered_path)
            return os.path.join(base_path, folder_name)
        return None



    def handle_toggle(self, label_text):
        self.checked_list_widget.clear()
        if label_text == 'Product':
            self.add_microphone_sections()
            self.update_checked_list()
        elif label_text == 'Pattern':
            self.add_pattern_sections()
            self.update_checked_list_pattern()
        elif label_text == 'Effects':
            self.add_effects_sections()
            self.update_checked_list_effects()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ScrollWindow()
    sys.exit(app.exec_())
