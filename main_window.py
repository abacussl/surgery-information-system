# main_window.py
import subprocess
import sys
import os
#from PyQt5.QtCore import QCoreApplication, Qt
#QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)  # Must come before QApplication is created
#QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QLineEdit, QComboBox, QDateEdit, QDateTimeEdit,
    QPushButton, QLabel, QMessageBox, QListWidget, QDialog, QDialogButtonBox,
    QListWidgetItem, QScrollArea, QAbstractItemView, QMenu, QTextEdit
)
from PyQt5.QtCore import QDate, Qt, QDateTime, pyqtSignal
import database
from admin_window import AdminWindow
from print_manager import PrintManager

class PrescriptionWidget(QWidget):
    removed = pyqtSignal(QWidget)  # Signal for safe removal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)        
       
        self.drug_name = QComboBox()
        self.drug_form = QComboBox()
        self.strength = QLineEdit()
        self.dose = QLineEdit()
        self.frequency = QComboBox()
        self.route = QComboBox()
        self.duration = QLineEdit()
        
        self.layout.addWidget(self.drug_name)
        self.layout.addWidget(self.drug_form)
        self.layout.addWidget(QLabel("Strength:"))
        self.layout.addWidget(self.strength)
        self.layout.addWidget(QLabel("Dose:"))
        self.layout.addWidget(self.dose)
        self.layout.addWidget(self.frequency)
        self.layout.addWidget(self.route)
        self.layout.addWidget(QLabel("Duration:"))
        self.layout.addWidget(self.duration)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.delete_self)
        self.layout.addWidget(self.remove_btn)
        
        self.setFixedHeight(40)
  
    def delete_self(self):
        self.removed.emit(self)  # Notify parent before deletion
        self.setParent(None)
        self.deleteLater()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Urology Unit - Patient Management")
        self.setGeometry(100, 100, 1000, 800)  

        # Initialize
        self.prescription_widgets = []         
             
        # Patient form
        self.form_group = QGroupBox("Patient Information")
        self.form_layout = QFormLayout()
        self.form_group.setLayout(self.form_layout)

        # Initialize hospital and unit dropdowns
        self.hospital_combo = QComboBox()
        self.unit_combo = QComboBox()
        
        # Add empty items first
        self.hospital_combo.addItem("")
        self.unit_combo.addItem("")
        
        self.hospital_combo.addItems(database.get_dropdown_options("hospital_name"))
        self.unit_combo.addItems(database.get_dropdown_options("unit_name"))
        
        # Set to first item if available
        if self.hospital_combo.count() > 1:  # Account for empty item
            self.hospital_combo.setCurrentIndex(1)  # Skip empty item
        if self.unit_combo.count() > 1:
            self.unit_combo.setCurrentIndex(1)

        self.form_layout.addRow("Hospital Name:", self.hospital_combo)
        self.form_layout.addRow("Unit Name:", self.unit_combo)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.patient_tab = QWidget()
        self.tabs.addTab(self.patient_tab, "Patient Information")
        self.create_patient_tab()
        
        self.operations_tab = QWidget()
        self.tabs.addTab(self.operations_tab, "Operation Details")
        self.create_operations_tab()
        
        self.investigations_tab = QWidget()
        self.tabs.addTab(self.investigations_tab, "Investigations")
        self.create_investigations_tab()
        
        self.prescriptions_tab = QWidget()
        self.tabs.addTab(self.prescriptions_tab, "Prescriptions")
        self.create_prescriptions_tab()
        
        self.appointment_tab = QWidget()
        self.tabs.addTab(self.appointment_tab, "Appointment")
        self.create_appointment_tab()
        
        # Initialize remaining
        self.current_patient_id = None
        
        # Load dropdowns
        self.load_dropdowns()
        
        # Add first prescription row
        #self.add_prescription_row()
        
        # Clear form
        self.clear_form()
        
        # Clear all dropdowns except hospital/unit
        self.clear_all_dropdowns()
        
        # Add first prescription row
        #self.add_prescription_row()  
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Record")
        self.save_btn.clicked.connect(self.save_record)
        btn_layout.addWidget(self.save_btn)
        
        self.edit_btn = QPushButton("Edit Record")
        self.edit_btn.clicked.connect(self.edit_record)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete Record")
        self.delete_btn.clicked.connect(self.delete_record)
        btn_layout.addWidget(self.delete_btn)
        
        self.clear_btn = QPushButton("Clear Form")
        self.clear_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(self.clear_btn)
        
        self.print_btn = QPushButton("Print Summary")
        self.print_btn.clicked.connect(self.print_summary)
        btn_layout.addWidget(self.print_btn)
        
        self.admin_btn = QPushButton("Admin Panel")
        self.admin_btn.clicked.connect(self.open_admin_panel)
        btn_layout.addWidget(self.admin_btn)
        
        main_layout.addLayout(btn_layout)
        
        # Initialize
        #self.prescription_widgets = []
        #self.add_prescription_row()
        #self.current_patient_id = None
        #self.load_dropdowns()        

    def create_patient_tab(self):
        layout = QFormLayout(self.patient_tab)

        group = QGroupBox("Personal Information")
        group_layout = QFormLayout(group)

        self.name_input = QLineEdit()
        group_layout.addRow("Name:", self.name_input)

        self.age_input = QLineEdit()
        self.age_input.setValidator(QtGui.QIntValidator(0, 120))
        group_layout.addRow("Age:", self.age_input)

        self.sex_combo = QComboBox()
        self.sex_combo.addItem("")  # Add empty item first
        self.sex_combo.addItems(["Male", "Female"])
        group_layout.addRow("Sex:", self.sex_combo)

        self.bht_input = QLineEdit()
        group_layout.addRow("BHT No:", self.bht_input)

        layout.addWidget(group)

        date_group = QGroupBox("Dates")
        date_layout = QFormLayout(date_group)

        self.admission_date = QDateEdit()
        self.admission_date.setCalendarPopup(True)
        self.admission_date.setDate(QDate.currentDate())
        date_layout.addRow("Admission Date:", self.admission_date)

        self.discharge_date = QDateEdit()
        self.discharge_date.setCalendarPopup(True)
        self.discharge_date.setDate(QDate.currentDate())
        date_layout.addRow("Discharge Date:", self.discharge_date)

        layout.addWidget(date_group)

        medical_group = QGroupBox("Medical Information")
        medical_layout = QFormLayout(medical_group)

        self.indication_combo = QComboBox()
        self.indication_combo.addItem("")  # Add empty item
        medical_layout.addRow("Indication:", self.indication_combo)

        self.history_input = QLineEdit()
        medical_layout.addRow("History & Examination:", self.history_input)

        self.management_combo = QComboBox()
        self.management_combo.addItem("")  # Add empty item
        medical_layout.addRow("Management:", self.management_combo)

        layout.addWidget(medical_group)


    def create_operations_tab(self):
        self.op_variable_widgets = [] 
        layout = QFormLayout(self.operations_tab)
        
        self.surgeon_combo = QComboBox()
        self.surgeon_combo.addItem("")  # Add empty item
        layout.addRow("Surgeon:", self.surgeon_combo)
        
        self.anaesthetist_combo = QComboBox()
        self.anaesthetist_combo.addItem("")  # Add empty item
        layout.addRow("Anaesthetist:", self.anaesthetist_combo)
        
        self.anaesthesia_combo = QComboBox()
        self.anaesthesia_combo.addItem("")  # Add empty item
        layout.addRow("Type of Anaesthesia:", self.anaesthesia_combo)
        
        self.surgery_name_combo = QComboBox()
        self.surgery_name_combo.addItem("")  # Add empty item
        layout.addRow("Surgery/Procedure Name:", self.surgery_name_combo)
        
        self.surgery_desc_combo = QComboBox()
        self.surgery_desc_combo.addItem("")  # Add empty item
        layout.addRow("Description:", self.surgery_desc_combo)    
        
        from PyQt5.QtWidgets import QGroupBox, QLineEdit, QPushButton, QHBoxLayout, QListWidget, QListWidgetItem

        # Operation Variables Section
        urology_group = QGroupBox("Operation Variables")
        urology_layout = QVBoxLayout(urology_group)

        # Entry layout
        entry_layout = QHBoxLayout()
        self.op_var_name_combo = QComboBox()
        self.op_var_name_combo.addItems(database.get_dropdown_options("op_variable"))
        entry_layout.addWidget(self.op_var_name_combo)

        self.op_var_value_input = QLineEdit()
        self.op_var_value_input.setPlaceholderText("Enter value (e.g., Left Clipped)")
        entry_layout.addWidget(self.op_var_value_input)

        add_op_var_btn = QPushButton("Add")
        add_op_var_btn.clicked.connect(self.add_op_variable)
        entry_layout.addWidget(add_op_var_btn)

        urology_layout.addLayout(entry_layout)

        # List to show added variables
        self.op_variable_list = QListWidget()
        urology_layout.addWidget(self.op_variable_list)

        # Optional: right-click delete
        self.op_variable_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.op_variable_list.customContextMenuRequested.connect(self.show_op_var_context_menu)

        layout.addWidget(urology_group)

    def add_op_variable(self):
        name = self.op_var_name_combo.currentText()
        value = self.op_var_value_input.text().strip()
        if not value:
            QMessageBox.warning(self, "Missing Value", "Please enter a value for the operation variable.")
            return
        item = QListWidgetItem(f"{name}: {value}")
        item.setData(Qt.UserRole, (name, value))
        self.op_variable_list.addItem(item)
        self.op_var_value_input.clear()

    def show_op_var_context_menu(self, position):
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.op_variable_list.viewport().mapToGlobal(position))
        if action == delete_action:
            selected = self.op_variable_list.currentRow()
            if selected >= 0:
                self.op_variable_list.takeItem(selected)

    def create_investigations_tab(self):
        layout = QVBoxLayout(self.investigations_tab)
        
        self.add_investigation_btn = QPushButton("Add Investigation")
        self.add_investigation_btn.clicked.connect(self.add_investigation)
        layout.addWidget(self.add_investigation_btn)
        
        self.investigations_list = QListWidget()
        self.investigations_list.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.investigations_list)
        
        self.remove_investigation_btn = QPushButton("Remove Selected")
        self.remove_investigation_btn.clicked.connect(self.remove_investigation)
        layout.addWidget(self.remove_investigation_btn)

    def create_prescriptions_tab(self):
        layout = QVBoxLayout(self.prescriptions_tab)
        
        self.prescription_container = QWidget()
        self.prescription_layout = QVBoxLayout(self.prescription_container)
        self.prescription_layout.setAlignment(Qt.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.prescription_container)
        layout.addWidget(scroll)
        
        self.add_prescription_btn = QPushButton("Add Another Prescription")
        self.add_prescription_btn.clicked.connect(self.add_prescription_row)
        layout.addWidget(self.add_prescription_btn)

    def create_appointment_tab(self):
        layout = QFormLayout(self.appointment_tab)
        
        #self.next_appointment = QDateTimeEdit()
        #self.next_appointment.setCalendarPopup(True)
        #self.next_appointment.setDateTime(QDateTime.currentDateTime())
        #layout.addRow("Next Appointment:", self.next_appointment)
        
        self.next_appointment = QDateTimeEdit()
        self.next_appointment.setCalendarPopup(True)
        self.next_appointment.setDateTime(QDateTime.currentDateTime())
        self.next_appointment.setDisplayFormat("yyyy-MM-dd HH:mm")  # ✅ this is important
        layout.addRow("Next Appointment:", self.next_appointment)

    def load_dropdowns(self):
        # Store current selections before updating
        main_dropdown_selections = {}
        dropdown_map = {
            "sex": self.sex_combo,
            "surgeon": self.surgeon_combo,
            "anaesthetist": self.anaesthetist_combo,
            "anaesthesia_type": self.anaesthesia_combo,
            "surgery_name": self.surgery_name_combo,
            "surgery_description": self.surgery_desc_combo,
            "indication": self.indication_combo,
            "management": self.management_combo
        }
        
        # Store current selections for main dropdowns
        for category, combo in dropdown_map.items():
            main_dropdown_selections[category] = combo.currentText()
        
        # Store current selections for prescription widgets
        prescription_selections = []
        for widget in self.prescription_widgets:
            if widget.parent():  # Only consider widgets that are still in the layout
                selections = {
                    'drug_name': widget.drug_name.currentText(),
                    'drug_form': widget.drug_form.currentText(),
                    'frequency': widget.frequency.currentText(),
                    'route': widget.route.currentText()
                }
                prescription_selections.append(selections)
        
        # Update main dropdowns
        for category, combo in dropdown_map.items():
            combo.blockSignals(True)  # Prevent change signals during update
            
            # Preserve the empty first item
            current_index = combo.currentIndex()
            current_text = combo.currentText()
            combo.clear()
            combo.addItem("")  # Add empty item back
            
            # Add options
            options = database.get_dropdown_options(category)
            combo.addItems(options)
            
            # Restore previous selection if it still exists
            if main_dropdown_selections[category] and main_dropdown_selections[category] != "":
                index = combo.findText(main_dropdown_selections[category])
                if index >= 0:
                    combo.setCurrentIndex(index)
                else:
                    combo.setCurrentIndex(0)  # Set to empty if not found
            else:
                combo.setCurrentIndex(0)  # Set to empty
            
            combo.blockSignals(False)
        
        # Update prescription widgets
        for i, widget in enumerate(self.prescription_widgets):
            if widget.parent():  # Only update widgets still in the layout
                for field in ['drug_name', 'drug_form', 'frequency', 'route']:
                    widget_combo = getattr(widget, field)
                    widget_combo.blockSignals(True)
                    
                    # Preserve current selection
                    current_text = widget_combo.currentText()
                    widget_combo.clear()
                    widget_combo.addItem("")  # Add empty item
                    
                    # Add options
                    widget_combo.addItems(database.get_dropdown_options(field))
                    
                    # Restore previous selection if it still exists
                    if i < len(prescription_selections):
                        prev_text = prescription_selections[i][field]
                        if prev_text and prev_text != "":
                            index = widget_combo.findText(prev_text)
                            if index >= 0:
                                widget_combo.setCurrentIndex(index)
                            else:
                                widget_combo.setCurrentIndex(0)  # Set to empty
                        else:
                            widget_combo.setCurrentIndex(0)  # Set to empty
                    else:
                        widget_combo.setCurrentIndex(0)  # Set to empty
                    
                    widget_combo.blockSignals(False)
        
        # Update prescription widgets
        for i, widget in enumerate(self.prescription_widgets):
            if widget.parent():  # Only update widgets still in the layout
                for field in ['drug_name', 'drug_form', 'frequency', 'route']:
                    widget_combo = getattr(widget, field)
                    widget_combo.blockSignals(True)
                    widget_combo.clear()
                    widget_combo.addItems(database.get_dropdown_options(field))
                    
                    # Restore previous selection if it still exists
                    if i < len(prescription_selections):
                        prev_text = prescription_selections[i][field]
                        if prev_text:
                            index = widget_combo.findText(prev_text)
                            if index >= 0:
                                widget_combo.setCurrentIndex(index)
                    widget_combo.blockSignals(False)
        
    def add_prescription_row(self):
        widget = PrescriptionWidget()
        widget.removed.connect(self.remove_prescription_widget)
        self.prescription_layout.addWidget(widget)
        self.prescription_widgets.append(widget)
        
        # Clear existing items and add empty item first
        for field in ['drug_name', 'drug_form', 'frequency', 'route']:
            combo = getattr(widget, field)
            combo.clear()
            combo.addItem("")  # Add empty item
        
        # Load dropdown options
        widget.drug_name.addItems(database.get_dropdown_options("drug_name"))
        widget.drug_form.addItems(database.get_dropdown_options("drug_form"))
        widget.frequency.addItems(database.get_dropdown_options("frequency"))
        widget.route.addItems(database.get_dropdown_options("route"))
        
        # Set to empty selection
        widget.drug_name.setCurrentIndex(0)
        widget.drug_form.setCurrentIndex(0)
        widget.frequency.setCurrentIndex(0)
        widget.route.setCurrentIndex(0)
        
    def remove_prescription_widget(self, widget):
        """Safely remove widget from the list and layout"""
        if widget in self.prescription_widgets:
            self.prescription_widgets.remove(widget)
            widget.setParent(None)
            widget.deleteLater()
        
        # Ensure at least one row remains
        if not self.prescription_widgets:
            self.add_prescription_row()

    def add_investigation(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Investigation")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Select Investigation:"))
        self.investigation_select = QListWidget()
        self.investigation_select.addItems(database.get_dropdown_options("investigation"))
        self.investigation_select.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.investigation_select)
        
        layout.addWidget(QLabel("Value:"))
        self.investigation_value = QLineEdit()
        layout.addWidget(self.investigation_value)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(lambda: self.save_investigations(dialog))
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        dialog.exec_()

    def save_investigations(self, dialog):
        selected = [item.text() for item in self.investigation_select.selectedItems()]
        value = self.investigation_value.text().strip()
        
        if not selected:
            QMessageBox.warning(self, "Selection Error", "Please select at least one investigation!")
            return
            
        if not value:
            QMessageBox.warning(self, "Input Error", "Please enter a value for the investigation!")
            return
            
        for investigation in selected:
            self.investigations_list.addItem(f"{investigation}: {value}")
            
        dialog.accept()

    def remove_investigation(self):
        selected = self.investigations_list.selectedItems()
        if not selected:
            return
            
        for item in selected:
            self.investigations_list.takeItem(self.investigations_list.row(item))
    
    def open_admin_panel(self):
        # Create admin window as modal dialog with parent
        admin_dialog = AdminWindow(self)  # Pass self as parent
        admin_dialog.data_updated.connect(self.load_dropdowns)
        
        # Set window flags to make it a proper dialog
        admin_dialog.setWindowModality(Qt.ApplicationModal)
        admin_dialog.setWindowTitle("Admin Panel")
        admin_dialog.show()

    def save_record(self):
        # Validate required fields
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Patient name is required!")
            return
            
        if not self.bht_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "BHT number is required!")
            return
            
        # Collect patient data
        patient_data = {
            'name': self.name_input.text().strip(),
            'age': int(self.age_input.text()) if self.age_input.text().strip() else None,
            'sex': self.sex_combo.currentText(),
            'admission_date': self.admission_date.date().toString(Qt.ISODate),
            'discharge_date': self.discharge_date.date().toString(Qt.ISODate),
            'bht_no': self.bht_input.text().strip(),
            'indication': self.indication_combo.currentText(),
            'history_exam': self.history_input.text(),
            'management': self.management_combo.currentText(),
            'next_appointment': self.next_appointment.dateTime().toString(Qt.ISODate)
        }
        
        # Collect operation data
        operation_data = {
            'surgeon': self.surgeon_combo.currentText(),
            'anaesthetist': self.anaesthetist_combo.currentText(),
            'anaesthesia_type': self.anaesthesia_combo.currentText(),
            'surgery_name': self.surgery_name_combo.currentText(),
            'surgery_description': self.surgery_desc_combo.currentText(),            
        }
        
        # Collect prescriptions - safer approach
        prescriptions = []
        valid_widgets = []
        
        for widget in self.prescription_widgets:
            try:
                # Check if widget still exists
                if widget.parent() is not None:
                    prescriptions.append({
                        'drug_name': widget.drug_name.currentText(),
                        'drug_form': widget.drug_form.currentText(),
                        'strength': widget.strength.text(),
                        'dose': widget.dose.text(),
                        'frequency': widget.frequency.currentText(),
                        'route': widget.route.currentText(),
                        'duration': widget.duration.text()  # Ensure this exists
                    })
                    valid_widgets.append(widget)
            except RuntimeError:
                # Widget has been deleted, skip it
                continue
        
        # Update the widget list
        self.prescription_widgets = valid_widgets
        
        # Collect investigations
        investigations = []
        for i in range(self.investigations_list.count()):
            item = self.investigations_list.item(i)
            name, value = item.text().split(': ', 1)
            investigations.append({'name': name, 'value': value.strip()})
        
        # Save to database
        try:
            if self.current_patient_id is None:
                # New patient
                patient_id = database.save_patient(patient_data)
                if patient_id is None:
                    QMessageBox.warning(self, "Duplicate BHT", "BHT number already exists!")
                    return
                    
                # Save related records
                database.save_operation(patient_id, operation_data)
                database.save_prescriptions(patient_id, prescriptions)
                database.save_investigations(patient_id, investigations)

                # ✅ Save operation variables
                database.delete_op_variables(patient_id)
                for name, widget in self.op_variable_widgets.items():
                    value = widget.currentText()
                    if value:
                        database.add_op_variable(patient_id, name, value)
                
                self.current_patient_id = patient_id
                QMessageBox.information(self, "Success", "New patient record saved successfully!")
            
            else:
                # Update existing patient
                if not database.update_patient(self.current_patient_id, patient_data):
                    QMessageBox.warning(self, "Duplicate BHT", "BHT number already exists!")
                    return
                    
                # Update related records
                operation = database.get_patient_operation(self.current_patient_id)
                if operation:
                    database.update_operation(operation['id'], operation_data)
                else:
                    database.save_operation(self.current_patient_id, operation_data)
                
                database.save_prescriptions(self.current_patient_id, prescriptions)
                database.save_investigations(self.current_patient_id, investigations)
               
                # ✅ Save operation variables
                database.delete_op_variables(self.current_patient_id)
                for i in range(self.op_variable_list.count()):
                    item = self.op_variable_list.item(i)
                    name, value = item.data(Qt.UserRole)
                    database.add_op_variable(self.current_patient_id, name, value)

                QMessageBox.information(self, "Success", "Patient record updated successfully!")
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save record: {str(e)}")
            print(f"Database error: {e}")

    def edit_record(self):
        # Create search dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Patient")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        # Search input
        layout.addWidget(QLabel("Search by Name or BHT:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.search_patients)
        layout.addWidget(self.search_input)
        
        # Results list
        self.search_results = QListWidget()
        layout.addWidget(self.search_results)
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(lambda: self.load_selected_patient(dialog))
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        dialog.exec_()

    def search_patients(self):
        search_term = self.search_input.text().strip()
        self.search_results.clear()
        
        if search_term:
            results = database.search_patients(search_term)
            for patient in results:
                item = QListWidgetItem(f"{patient['name']} (BHT: {patient['bht_no']})")
                item.setData(Qt.UserRole, patient['id'])
                self.search_results.addItem(item)

    def load_selected_patient(self, dialog):
        selected = self.search_results.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selection Error", "Please select a patient!")
            return
            
        patient_id = selected[0].data(Qt.UserRole)
        self.load_patient_data(patient_id)
        dialog.accept()

    def load_patient_data(self, patient_id):
        # Clear current form
        self.clear_form()
        
        # Load patient data
        patient = database.get_patient(patient_id)
        if patient:
            self.current_patient_id = patient['id']
            self.name_input.setText(patient['name'])
            self.age_input.setText(str(patient['age']) if patient['age'] else "")
            self.sex_combo.setCurrentText(patient['sex'])
            self.admission_date.setDate(QDate.fromString(patient['admission_date'], Qt.ISODate))
            self.discharge_date.setDate(QDate.fromString(patient['discharge_date'], Qt.ISODate))
            self.bht_input.setText(patient['bht_no'])
            self.indication_combo.setCurrentText(patient['indication'])
            self.history_input.setText(patient['history_exam'])
            self.management_combo.setCurrentText(patient['management'])
            self.next_appointment.setDateTime(QDateTime.fromString(patient['next_appointment'], Qt.ISODate))
        
        # Load operation data
        operation = database.get_patient_operation(patient_id)
        if operation:
            self.surgeon_combo.setCurrentText(operation['surgeon'])
            self.anaesthetist_combo.setCurrentText(operation['anaesthetist'])
            self.anaesthesia_combo.setCurrentText(operation['anaesthesia_type'])
            self.surgery_name_combo.setCurrentText(operation['surgery_name'])
            self.surgery_desc_combo.setCurrentText(operation['surgery_description'])

        # ✅ Load op_variables for ureters, bladder, prostate, uoo
        op_vars = database.get_op_variables(patient_id)
        for var in op_vars:
            name = var["name"]
            value = var["value"]
            if name in self.op_variable_widgets:
                index = self.op_variable_widgets[name].findText(value)
                if index >= 0:
                    self.op_variable_widgets[name].setCurrentIndex(index)        
                    
        # ✅ Clear any existing op_variables
        self.op_variable_list.clear()

        # ✅ Load op_variables into the list
        op_vars = database.get_op_variables(patient_id)
        for var in op_vars:
            name = var["name"]
            value = var["value"]
            item = QListWidgetItem(f"{name}: {value}")
            item.setData(Qt.UserRole, (name, value))
            self.op_variable_list.addItem(item)
                    
       # Load prescriptions
        prescriptions = database.get_patient_prescriptions(patient_id)
        self.prescription_widgets = []
        
        # Clear existing widgets
        for i in reversed(range(self.prescription_layout.count())):
            widget = self.prescription_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Add widgets for each prescription
        for drug in prescriptions:
            widget = PrescriptionWidget()
            widget.removed.connect(self.remove_prescription_widget)

            # ✅ Load dropdown options before setting values
            widget.drug_name.addItems(database.get_dropdown_options("drug_name"))
            widget.drug_form.addItems(database.get_dropdown_options("drug_form"))
            widget.frequency.addItems(database.get_dropdown_options("frequency"))
            widget.route.addItems(database.get_dropdown_options("route"))

            # ✅ Now set values safely
            widget.drug_name.setCurrentText(drug['drug_name'])
            widget.drug_form.setCurrentText(drug['drug_form'])
            widget.strength.setText(drug['strength'])
            widget.dose.setText(drug['dose'])
            widget.frequency.setCurrentText(drug['frequency'])
            widget.route.setCurrentText(drug['route'])
            widget.duration.setText(drug['duration'])

            self.prescription_layout.addWidget(widget)
            self.prescription_widgets.append(widget)

        
        # Add one empty row if none exist
        if not self.prescription_widgets:
            self.add_prescription_row()
        
        # Load investigations
        investigations = database.get_patient_investigations(patient_id)
        self.investigations_list.clear()
        for test in investigations:
            self.investigations_list.addItem(f"{test['name']}: {test['value']}")
        
    def delete_record(self):
        if self.current_patient_id is None:
            QMessageBox.warning(self, "No Patient Selected", "Please load a patient record first!")
            return
            
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this patient record? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            if database.delete_patient(self.current_patient_id):
                QMessageBox.information(self, "Success", "Patient record deleted successfully!")
                self.clear_form()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete patient record!")

    # In your MainWindow class:
    def clear_dropdown(self, combo):
        """Clear a dropdown selection reliably"""
        # Save current index and block signals
        current_index = combo.currentIndex()
        combo.blockSignals(True)
        
        # Add a temporary empty item
        combo.insertItem(0, "")
        combo.setCurrentIndex(0)
        
        # Remove the temporary item
        combo.removeItem(0)
        
        # Restore original state
        combo.blockSignals(False)
        combo.setCurrentIndex(-1)

    def clear_all_dropdowns(self):
        """Clear all dropdown selections reliably"""
        # Patient tab
        self.clear_dropdown(self.sex_combo)
        self.clear_dropdown(self.indication_combo)
        self.clear_dropdown(self.management_combo)
        
        # Operations tab
        self.clear_dropdown(self.surgeon_combo)
        self.clear_dropdown(self.anaesthetist_combo)
        self.clear_dropdown(self.anaesthesia_combo)
        self.clear_dropdown(self.surgery_name_combo)
        self.clear_dropdown(self.surgery_desc_combo)
        self.clear_dropdown(self.op_var_name_combo)
        
        # Clear prescription widgets
        for widget in self.prescription_widgets:
            if widget.parent():
                self.clear_dropdown(widget.drug_name)
                self.clear_dropdown(widget.drug_form)
                self.clear_dropdown(widget.frequency)
                self.clear_dropdown(widget.route)

    def clear_form(self):
        """Reset all form fields"""
        self.current_patient_id = None
        self.name_input.clear()
        self.age_input.clear()
        self.admission_date.setDate(QDate.currentDate())
        self.discharge_date.setDate(QDate.currentDate())
        self.bht_input.clear()
        self.history_input.clear()
        self.next_appointment.setDateTime(QDateTime.currentDateTime())
        
        # Set all dropdowns to empty selection
        self.sex_combo.setCurrentIndex(0)
        self.indication_combo.setCurrentIndex(0)
        self.management_combo.setCurrentIndex(0)
        self.surgeon_combo.setCurrentIndex(0)
        self.anaesthetist_combo.setCurrentIndex(0)
        self.anaesthesia_combo.setCurrentIndex(0)
        self.surgery_name_combo.setCurrentIndex(0)
        self.surgery_desc_combo.setCurrentIndex(0)
        self.op_var_name_combo.setCurrentIndex(0)
        self.op_variable_list.clear()
        
        # Clear prescription widgets - only remove existing ones
        for widget in self.prescription_widgets[:]:  # Use a copy of the list
            widget.setParent(None)
            self.prescription_widgets.remove(widget)
        
        # Add exactly one empty row
        self.add_prescription_row()
        
        # Clear investigations
        self.investigations_list.clear()
        
    def print_summary(self):
        if self.current_patient_id is None:
            QMessageBox.warning(self, "No Patient", "Please load or create a patient record first!")
            return
        
        # Show print manager dialog
        self.print_dialog = PrintManager(
            self.current_patient_id,
            self,
            hospital_name=self.hospital_combo.currentText(),
            unit_name=self.unit_combo.currentText()
        )
        self.print_dialog.exec_()

    def showEvent(self, event):
        """Auto-refresh dropdowns when window gains focus"""
        self.load_dropdowns()
        super().showEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
