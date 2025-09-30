# admin_window.py
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QComboBox, QLineEdit, QPushButton,
    QLabel, QMessageBox, QSizePolicy  # Added QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
import database  # ADD THIS IMPORT

class AdminWindow(QMainWindow):
    
    CATEGORIES = [
        "surgeon", "anaesthetist", "anaesthesia_type", "surgery_name",
        "surgery_description", "indication", "management", "drug_name",
        "drug_form", "strength", "dose", "frequency", "route", "duration",
        "investigation", "sex", "hospital_name", "unit_name", "op_variable"
    ]

    data_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Panel - Dropdown Manager")
        self.setGeometry(300, 300, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Category selection
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Select Category:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.CATEGORIES)
        self.category_combo.currentIndexChanged.connect(self.load_category_items)
        category_layout.addWidget(self.category_combo)
        
        main_layout.addLayout(category_layout)
        
        # Items list with move buttons
        list_move_layout = QHBoxLayout()
        main_layout.addLayout(list_move_layout)
        
        # Items list
        self.items_list = QListWidget()
        list_move_layout.addWidget(self.items_list)
        
        # Move buttons (vertical layout)
        move_btn_layout = QVBoxLayout()
        move_btn_layout.setAlignment(Qt.AlignTop)
        
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.setFixedSize(50, 30)
        self.move_up_btn.clicked.connect(self.move_item_up)
        move_btn_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.setFixedSize(50, 30)
        self.move_down_btn.clicked.connect(self.move_item_down)
        move_btn_layout.addWidget(self.move_down_btn)
        
        list_move_layout.addLayout(move_btn_layout)
        
        # Add item section
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("New Item:"))
        
        self.new_item_input = QLineEdit()
        self.new_item_input.setPlaceholderText("Enter new item name")
        add_layout.addWidget(self.new_item_input)
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_new_item)
        add_layout.addWidget(self.add_button)
        
        main_layout.addLayout(add_layout)
        
        # Delete button
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_selected_item)
        main_layout.addWidget(self.delete_button)
        
        # Load initial data
        self.load_category_items()

    def load_category_items(self):
        self.items_list.clear()
        category = self.category_combo.currentText()
        items = database.get_dropdown_options(category)  # FIXED
        
        for item in items:
            list_item = QListWidgetItem(item)
            list_item.setData(Qt.UserRole, item)
            self.items_list.addItem(list_item)

    def add_new_item(self):
        category = self.category_combo.currentText()
        new_item = self.new_item_input.text().strip()
        
        if not new_item:
            QMessageBox.warning(self, "Input Error", "Item name cannot be empty!")
            return
            
        if database.add_dropdown_option(category, new_item):  # FIXED
            self.load_category_items()
            self.new_item_input.clear()
            self.data_updated.emit()
            QMessageBox.information(self, "Success", "Item added successfully!")
        else:
            QMessageBox.warning(self, "Duplicate", "This item already exists in the category!")

    def delete_selected_item(self):
        selected_items = self.items_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select an item to delete!")
            return
            
        category = self.category_combo.currentText()
        item_to_delete = selected_items[0].data(Qt.UserRole)
        
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Delete '{item_to_delete}' from {category}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            if database.delete_dropdown_option(category, item_to_delete):  # FIXED
                self.load_category_items()
                self.data_updated.emit()
                QMessageBox.information(self, "Success", "Item deleted successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete item!")

    # New move item functions
    def move_item_up(self):
        current_row = self.items_list.currentRow()
        if current_row <= 0:
            return  # Already at top or no selection
        
        category = self.category_combo.currentText()
        current_item = self.items_list.takeItem(current_row)
        self.items_list.insertItem(current_row - 1, current_item)
        self.items_list.setCurrentRow(current_row - 1)
        self.save_category_order(category)

    def move_item_down(self):
        current_row = self.items_list.currentRow()
        if current_row < 0 or current_row >= self.items_list.count() - 1:
            return  # Already at bottom or no selection
        
        category = self.category_combo.currentText()
        current_item = self.items_list.takeItem(current_row)
        self.items_list.insertItem(current_row + 1, current_item)
        self.items_list.setCurrentRow(current_row + 1)
        self.save_category_order(category)

    def save_category_order(self, category):
        """Save current order to database"""
        ordered_items = []
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            ordered_items.append(item.text())
        
        # Update database with new order
        if database.update_dropdown_order(category, ordered_items):
            self.data_updated.emit()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = AdminWindow()
    window.show()
    sys.exit(app.exec_())
