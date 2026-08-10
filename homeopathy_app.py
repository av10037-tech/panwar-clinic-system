import sys
import os
import sqlite3
import urllib.parse
import webbrowser
import time
import pandas as pd
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, 
    QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QTabWidget, QMessageBox, QFormLayout, QComboBox, QTextEdit, QFileDialog, QCompleter, QScrollArea, QDateEdit
)
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon

try:
    import pyautogui
    AUTO_SEND_AVAILABLE = True
except ImportError:
    AUTO_SEND_AVAILABLE = False

MEDICAL_STYLE = """
QMainWindow {
    background-color: #f0fdf4;
}
QTabWidget::pane {
    border: 1px solid #bbf7d0;
    background: #ffffff;
    border-radius: 6px;
}
QTabBar::tab {
    background: #dcfce7;
    color: #166534;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
    font-size: 13px;
}
QTabBar::tab:selected {
    background: #15803d;
    color: #ffffff;
}
QLabel {
    color: #14532d;
    font-size: 13px;
    font-weight: 500;
}
QLineEdit, QComboBox, QTextEdit, QDateEdit {
    background-color: #ffffff;
    border: 1px solid #bbf7d0;
    border-radius: 4px;
    padding: 6px;
    font-size: 13px;
    color: #0f172a;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {
    border: 1px solid #15803d;
}
QPushButton {
    background-color: #15803d;
    color: white;
    font-weight: bold;
    font-size: 13px;
    padding: 8px 16px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #166534;
}
QTableWidget {
    background-color: #ffffff;
    gridline-color: #e2e8f0;
    border: 1px solid #bbf7d0;
    selection-background-color: #dcfce7;
    selection-color: #166534;
}
QHeaderView::section {
    background-color: #f0fdf4;
    color: #166534;
    padding: 6px;
    font-weight: bold;
    border: 1px solid #bbf7d0;
}
"""

class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        self.filter_model = QSortFilterProxyModel(self)
        self.filter_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filter_model.setFilterKeyColumn(0)
        
        self.source_model = QStandardItemModel(self)
        self.filter_model.setSourceModel(self.source_model)
        
        self.setModel(self.filter_model)
        self.lineEdit().textEdited.connect(self.on_text_edited)

    def set_items(self, items):
        self.source_model.clear()
        for item in items:
            self.source_model.appendRow(QStandardItem(item))
            
    def on_text_edited(self, text):
        self.filter_model.setFilterFixedString(text)
        if not self.view().isVisible() and text:
            self.showPopup()


class WhatsAppThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, phone, message):
        super().__init__()
        self.phone = phone
        self.message = message

    def run(self):
        try:
            encoded_message = urllib.parse.quote(self.message)
            whatsapp_url = f"whatsapp://send?phone={self.phone}&text={encoded_message}"
            webbrowser.open(whatsapp_url)
            
            if AUTO_SEND_AVAILABLE:
                time.sleep(2.5)
                pyautogui.press('enter')
            self.finished.emit("Success")
        except Exception as e:
            self.finished.emit(str(e))


class HomeopathyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panwar Homoeopathic Clinic & Pharmacy Management System")
        self.setGeometry(100, 100, 1250, 950)
        self.setStyleSheet(MEDICAL_STYLE)
        
        if os.path.exists("logo.ico"):
            self.setWindowIcon(QIcon("logo.ico"))
        elif os.path.exists("Logo.png"):
            self.setWindowIcon(QIcon("Logo.png"))
        
        self.init_db()
        
        main_layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        title_label = QLabel("🌿 Panwar Homoeopathic Clinic\n(Dr. Rishipal Singh & Hemant Singh Panwar)")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #15803d; padding: 5px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        self.patient_tab = QWidget()
        self.inventory_tab = QWidget()
        self.billing_tab = QWidget()
        
        self.tabs.addTab(self.patient_tab, "📋 Patient Records & History Checker")
        self.tabs.addTab(self.inventory_tab, "💊 Inventory & Stock Update")
        self.tabs.addTab(self.billing_tab, "🖩 Billing & Dispensing")
        
        self.setup_patient_ui()
        self.setup_inventory_ui()
        self.setup_billing_ui()
        
        self.check_followup_reminders()

    def init_db(self):
        db_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "PanwarClinic", "clinic_data.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, age TEXT, phone TEXT, address TEXT, 
            visit_type TEXT, visit_date TEXT, symptoms TEXT)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            med_name TEXT, potency TEXT, stock_ml REAL, price_per_ml REAL)''')
            
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS external_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            med_name TEXT, stock_qty REAL, price REAL)''')
            
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT, phone TEXT, medicine TEXT, 
            total_ml REAL, amount REAL, payment_mode TEXT, days_given INTEGER, bill_date TEXT)''')
            
        self.conn.commit()
        
        self.safe_add_column('patients', 'address', 'TEXT')
        self.safe_add_column('patients', 'visit_date', 'TEXT')
        self.safe_add_column('bills', 'days_given', 'INTEGER')

    def safe_add_column(self, table_name, column_name, column_type):
        try:
            self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def setup_patient_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.p_id = QLineEdit()
        self.p_id.setPlaceholderText("Leave blank for new, enter ID to Update existing")
        
        self.p_name = QLineEdit()
        self.p_age = QLineEdit()
        self.p_phone = QLineEdit()
        self.p_address = QLineEdit()
        
        self.p_visit_type = QComboBox()
        self.p_visit_type.addItems(["First Visit", "Second Visit (Follow-up)", "Third Visit (Follow-up)", "Regular Patient"])
        
        self.p_date = QLineEdit()
        self.p_date.setText(datetime.now().strftime("%Y-%m-%d"))
        
        self.p_symptoms = QTextEdit()
        self.p_symptoms.setMaximumHeight(40)
        
        form_layout.addRow("Patient ID (Only for Update):", self.p_id)
        form_layout.addRow("Patient Name:", self.p_name)
        form_layout.addRow("Age:", self.p_age)
        form_layout.addRow("Phone Number:", self.p_phone)
        form_layout.addRow("Address:", self.p_address)
        form_layout.addRow("Visit Type:", self.p_visit_type)
        form_layout.addRow("Date of Visit (YYYY-MM-DD):", self.p_date)
        form_layout.addRow("Symptoms / Problem:", self.p_symptoms)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Save New Patient")
        btn_save.clicked.connect(self.save_patient)
        
        btn_update = QPushButton("🔄 Update Existing Patient Record")
        btn_update.clicked.connect(self.update_patient)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_update)
        
        checker_layout = QHBoxLayout()
        self.search_patient_input = QLineEdit()
        self.search_patient_input.setPlaceholderText("Type patient name to check past medical & medicine history...")
        
        btn_search_history = QPushButton("🔍 Check Patient History")
        btn_search_history.clicked.connect(self.search_patient_history)
        
        checker_layout.addWidget(self.search_patient_input)
        checker_layout.addWidget(btn_search_history)

        self.patient_history_table = QTableWidget()
        self.patient_history_table.setColumnCount(6)
        self.patient_history_table.setHorizontalHeaderLabels(["Bill ID", "Patient Name", "Phone", "Medicines Given", "Days / Amount", "Visit Date"])
        self.patient_history_table.setMaximumHeight(150)

        self.patient_table = QTableWidget()
        self.patient_table.setColumnCount(8)
        self.patient_table.setHorizontalHeaderLabels(["ID", "Name", "Age", "Phone", "Address", "Visit Type", "Visit Date", "Symptoms"])
        
        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("<hr><b>🔍 Patient Visit & Medicine History Checker:</b>"))
        layout.addLayout(checker_layout)
        layout.addWidget(self.patient_history_table)
        layout.addWidget(QLabel("<hr><b>Recent Patients Registration List:</b>"))
        layout.addWidget(self.patient_table)
        
        self.patient_tab.setLayout(layout)
        self.load_patients()
        self.update_patient_completer()

    def update_patient_completer(self):
        self.cursor.execute("SELECT name, phone FROM patients")
        patients = self.cursor.fetchall()
        
        self.patient_dict = {p[0]: p[1] for p in patients}
        patient_names = list(self.patient_dict.keys())
        
        if patient_names:
            completer = QCompleter(patient_names, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            self.p_name.setCompleter(completer)
            
            search_completer = QCompleter(patient_names, self)
            search_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            search_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            self.search_patient_input.setCompleter(search_completer)
            
            if hasattr(self, 'b_patient'):
                self.b_patient.set_items(patient_names)
        
        self.p_name.textChanged.connect(self.auto_fill_phone)

    def auto_fill_phone(self, text):
        if text in self.patient_dict:
            self.p_phone.setText(str(self.patient_dict[text]))

    def search_patient_history(self):
        search_name = self.search_patient_input.text().strip()
        if not search_name:
            QMessageBox.warning(self, "Error", "Please enter a patient name to search history!")
            return
            
        self.cursor.execute("""
            SELECT id, patient_name, phone, medicine, amount, days_given, bill_date 
            FROM bills WHERE patient_name LIKE ? ORDER BY id DESC
        """, (f"%{search_name}%",))
        rows = self.cursor.fetchall()
        
        self.patient_history_table.setRowCount(len(rows))
        if not rows:
            QMessageBox.information(self, "Not Found", f"No past medication history found for '{search_name}'.")
            return
            
        for row_idx, row_data in enumerate(rows):
            b_id, p_name, phone, medicine, amount, days, b_date = row_data
            
            self.patient_history_table.setItem(row_idx, 0, QTableWidgetItem(str(b_id)))
            self.patient_history_table.setItem(row_idx, 1, QTableWidgetItem(str(p_name)))
            self.patient_history_table.setItem(row_idx, 2, QTableWidgetItem(str(phone)))
            self.patient_history_table.setItem(row_idx, 3, QTableWidgetItem(str(medicine)))
            self.patient_history_table.setItem(row_idx, 4, QTableWidgetItem(f"{days} Days (₹{amount})"))
            self.patient_history_table.setItem(row_idx, 5, QTableWidgetItem(str(b_date)))

    def save_patient(self):
        name = self.p_name.text()
        age = self.p_age.text()
        phone = self.p_phone.text()
        address = self.p_address.text()
        visit_type = self.p_visit_type.currentText()
        visit_date = self.p_date.text()
        symptoms = self.p_symptoms.toPlainText()
        
        if not name:
            QMessageBox.warning(self, "Error", "Patient name is required!")
            return
            
        self.cursor.execute("""
            INSERT INTO patients (name, age, phone, address, visit_type, visit_date, symptoms) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, age, phone, address, visit_type, visit_date, symptoms))
        self.conn.commit()
        QMessageBox.information(self, "Success", "Patient record saved successfully!")
        
        self.clear_patient_form()
        self.load_patients()
        self.update_patient_completer()

    def update_patient(self):
        try:
            p_id = int(self.p_id.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid Patient ID to update!")
            return
            
        name = self.p_name.text()
        age = self.p_age.text()
        phone = self.p_phone.text()
        address = self.p_address.text()
        visit_type = self.p_visit_type.currentText()
        visit_date = self.p_date.text()
        symptoms = self.p_symptoms.toPlainText()
        
        if not name:
            QMessageBox.warning(self, "Error", "Patient name is required!")
            return
            
        self.cursor.execute("SELECT id FROM patients WHERE id=?", (p_id,))
        if not self.cursor.fetchone():
            QMessageBox.warning(self, "Error", f"Patient ID {p_id} not found!")
            return
            
        self.cursor.execute("""
            UPDATE patients SET name=?, age=?, phone=?, address=?, visit_type=?, visit_date=?, symptoms=?
            WHERE id=?
        """, (name, age, phone, address, visit_type, visit_date, symptoms, p_id))
        self.conn.commit()
        QMessageBox.information(self, "Success", f"Patient ID {p_id} updated successfully!")
        
        self.clear_patient_form()
        self.load_patients()
        self.update_patient_completer()

    def clear_patient_form(self):
        self.p_id.clear()
        self.p_name.clear()
        self.p_age.clear()
        self.p_phone.clear()
        self.p_address.clear()
        self.p_symptoms.clear()
        self.p_date.setText(datetime.now().strftime("%Y-%m-%d"))

    def load_patients(self):
        self.cursor.execute("SELECT * FROM patients")
        rows = self.cursor.fetchall()
        self.patient_table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            for col_idx, data in enumerate(row_data):
                self.patient_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def setup_inventory_ui(self):
        layout = QVBoxLayout()
        
        import_layout = QHBoxLayout()
        lbl_import = QLabel("<b>📂 Import Inventory from Excel / CSV file:</b>")
        btn_import_excel = QPushButton("📁 Attach Excel & Import Stock")
        btn_import_excel.setStyleSheet("background-color: #0284c7;")
        btn_import_excel.clicked.connect(self.import_inventory_from_excel)
        import_layout.addWidget(lbl_import)
        import_layout.addWidget(btn_import_excel)
        layout.addLayout(import_layout)
        layout.addWidget(QLabel("<hr>"))

        form_layout = QFormLayout()
        self.m_name = QLineEdit()
        self.m_potency = QLineEdit()
        self.m_stock = QLineEdit()
        self.m_price = QLineEdit()
        
        form_layout.addRow("<b>Add Homeopathic Stock Medicine (Manual):</b>", QLabel(""))
        form_layout.addRow("Medicine Name:", self.m_name)
        form_layout.addRow("Potency (e.g. 30, 200, Q):", self.m_potency)
        form_layout.addRow("Stock Quantity (ml):", self.m_stock)
        form_layout.addRow("Price per ml:", self.m_price)
        
        btn_add_med = QPushButton("➕ Add Homeopathic Medicine")
        btn_add_med.clicked.connect(self.save_medicine)

        ext_form_layout = QFormLayout()
        self.e_name = QLineEdit()
        self.e_stock = QLineEdit()
        self.e_price = QLineEdit()
        
        ext_form_layout.addRow("<b>Add External / Patent Medicine Inventory:</b>", QLabel(""))
        ext_form_layout.addRow("External Medicine Name:", self.e_name)
        ext_form_layout.addRow("Stock Quantity (Units):", self.e_stock)
        ext_form_layout.addRow("Price per Unit (₹):", self.e_price)
        
        btn_add_ext = QPushButton("➕ Add External Medicine to Inventory")
        btn_add_ext.setStyleSheet("background-color: #0284c7;")
        btn_add_ext.clicked.connect(self.save_external_medicine)

        inv_header_layout = QHBoxLayout()
        inv_header_layout.addWidget(QLabel("<b>Homeopathic Stock Inventory:</b>"))
        
        btn_refresh_inv = QPushButton("🔄 Refresh Inventories")
        btn_refresh_inv.clicked.connect(self.load_inventory)
        inv_header_layout.addWidget(btn_refresh_inv)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(["ID", "Medicine Name", "Potency", "Stock (ml)", "Price/ml"])
        self.inventory_table.setMaximumHeight(150)

        self.ext_inventory_table = QTableWidget()
        self.ext_inventory_table.setColumnCount(4)
        self.ext_inventory_table.setHorizontalHeaderLabels(["ID", "External Medicine Name", "Stock (Units)", "Price (₹)"])
        self.ext_inventory_table.setMaximumHeight(150)

        layout.addLayout(form_layout)
        layout.addWidget(btn_add_med)
        layout.addWidget(QLabel("<hr>"))
        layout.addLayout(ext_form_layout)
        layout.addWidget(btn_add_ext)
        layout.addWidget(QLabel("<hr>"))
        layout.addLayout(inv_header_layout)
        layout.addWidget(self.inventory_table)
        layout.addWidget(QLabel("<b>External Medicines Inventory:</b>"))
        layout.addWidget(self.ext_inventory_table)
        
        self.inventory_tab.setLayout(layout)
        self.load_inventory()

    def import_inventory_from_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx *.xls *.csv)")
        if not file_path:
            return
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    med_name = str(row.iloc[0]).strip()
                    if not med_name or med_name.lower() in ['nan', 'medicine name', 'med_name', 'stock quantity (ml/g)']:
                        continue
                        
                    potency = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else "Q"
                    stock = float(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else 100.0
                    price = float(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else 1.0
                    
                    self.cursor.execute("INSERT INTO inventory (med_name, potency, stock_ml, price_per_ml) VALUES (?, ?, ?, ?)", 
                                        (med_name, potency, stock, price))
                    imported_count += 1
                except Exception:
                    continue
                    
            self.conn.commit()
            self.load_inventory()
            self.load_billing_inventory()
            QMessageBox.information(self, "Success", f"Successfully imported {imported_count} medicines from Excel file!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to import Excel file!\nError details: {str(e)}")

    def save_medicine(self):
        name = self.m_name.text()
        potency = self.m_potency.text()
        try:
            stock = float(self.m_stock.text())
            price = float(self.m_price.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Stock and Price must be numbers!")
            return
            
        self.cursor.execute("INSERT INTO inventory (med_name, potency, stock_ml, price_per_ml) VALUES (?, ?, ?, ?)", (name, potency, stock, price))
        self.conn.commit()
        self.load_inventory()
        self.load_billing_inventory()
        QMessageBox.information(self, "Success", "Homeopathic medicine added successfully!")
        self.m_name.clear(); self.m_potency.clear(); self.m_stock.clear(); self.m_price.clear()

    def save_external_medicine(self):
        name = self.e_name.text()
        try:
            stock = float(self.e_stock.text())
            price = float(self.e_price.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Stock and Price must be numbers!")
            return
            
        self.cursor.execute("INSERT INTO external_inventory (med_name, stock_qty, price) VALUES (?, ?, ?)", (name, stock, price))
        self.conn.commit()
        self.load_inventory()
        self.load_billing_inventory()
        QMessageBox.information(self, "Success", "External medicine added to inventory successfully!")
        self.e_name.clear(); self.e_stock.clear(); self.e_price.clear()

    def load_inventory(self):
        self.cursor.execute("SELECT * FROM inventory")
        rows = self.cursor.fetchall()
        self.inventory_table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            for col_idx, data in enumerate(row_data):
                self.inventory_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

        self.cursor.execute("SELECT * FROM external_inventory")
        ext_rows = self.cursor.fetchall()
        self.ext_inventory_table.setRowCount(len(ext_rows))
        for row_idx, row_data in enumerate(ext_rows):
            for col_idx, data in enumerate(row_data):
                self.ext_inventory_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def setup_billing_ui(self):
        layout = QVBoxLayout()
        
        billing_top_layout = QHBoxLayout()
        billing_top_layout.addWidget(QLabel("<b>Available Inventories Stock Reference:</b>"))
        
        btn_refresh_stock = QPushButton("🔄 Refresh Stock List")
        btn_refresh_stock.clicked.connect(self.load_billing_inventory)
        billing_top_layout.addWidget(btn_refresh_stock)
        
        layout.addLayout(billing_top_layout)

        tables_layout = QHBoxLayout()
        self.billing_inventory_table = QTableWidget()
        self.billing_inventory_table.setColumnCount(5)
        self.billing_inventory_table.setHorizontalHeaderLabels(["ID", "Name", "Potency", "Stock", "Price/ml"])
        self.billing_inventory_table.setMaximumHeight(110)

        self.billing_ext_table = QTableWidget()
        self.billing_ext_table.setColumnCount(4)
        self.billing_ext_table.setHorizontalHeaderLabels(["ID", "Ext. Name", "Stock", "Price"])
        self.billing_ext_table.setMaximumHeight(110)

        tables_layout.addWidget(self.billing_inventory_table)
        tables_layout.addWidget(self.billing_ext_table)
        layout.addLayout(tables_layout)

        form_layout = QFormLayout()
        
        self.b_patient = SearchableComboBox()
        self.b_patient.setPlaceholderText("Type patient name to auto-suggest...")
        self.b_patient.currentTextChanged.connect(self.billing_auto_fill_phone)

        self.b_phone = QLineEdit()
        
        self.b_days = QLineEdit()
        self.b_days.setText("7")
        
        self.b_ml_per_day = QLineEdit()
        self.b_ml_per_day.setText("1.0")
        
        self.b_payment_mode = QComboBox()
        self.b_payment_mode.addItems(["Cash", "UPI (Paytm, Google Pay, PhonePe)"])
        
        form_layout.addRow("Patient Name (Auto-Suggest):", self.b_patient)
        form_layout.addRow("Patient Mobile Number:", self.b_phone)
        form_layout.addRow("Number of Days (e.g., 7 or 14 days):", self.b_days)
        form_layout.addRow("Dose per day (ml):", self.b_ml_per_day)
        form_layout.addRow("Payment Mode:", self.b_payment_mode)

        prescription_container_layout = QVBoxLayout()
        prescription_header = QHBoxLayout()
        prescription_header.addWidget(QLabel("<b>Prescription Medicines List:</b>"))
        
        btn_add_row = QPushButton("➕ Add Stock Medicine")
        btn_add_row.clicked.connect(lambda: self.add_prescription_row(is_external=False))
        prescription_header.addWidget(btn_add_row)

        btn_add_external = QPushButton("➕ Add External Medicine")
        btn_add_external.clicked.connect(lambda: self.add_prescription_row(is_external=True))
        btn_add_external.setStyleSheet("background-color: #0284c7;")
        prescription_header.addWidget(btn_add_external)
        
        prescription_container_layout.addLayout(prescription_header)

        self.med_rows_layout = QVBoxLayout()
        self.med_rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.med_rows_layout)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setMinimumHeight(140)
        scroll_area.setMaximumHeight(180)
        
        prescription_container_layout.addWidget(scroll_area)
        
        self.med_widgets = []
        self.add_prescription_row(is_external=False)
        self.add_prescription_row(is_external=False)

        btn_generate = QPushButton("🖨️ Calculate, Save & Send WhatsApp")
        btn_generate.clicked.connect(self.generate_and_send_bill)
        
        self.bill_output = QLabel("Bill Details will appear here...")
        self.bill_output.setStyleSheet("font-size: 14px; background-color: #ffffff; border: 1px solid #bbf7d0; padding: 10px; border-radius: 4px;")
        
        collection_layout = QHBoxLayout()
        self.lbl_collection = QLabel("<b>Total Collection: ₹0.00</b>")
        self.lbl_collection.setStyleSheet("font-size: 14px; color: #166534; font-weight: bold; padding: 4px;")
        
        lbl_date_pick = QLabel("Select Date for Collection:")
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.dateChanged.connect(self.update_collection_for_selected_date)
        
        btn_today_col = QPushButton("Today")
        btn_today_col.clicked.connect(lambda: self.date_picker.setDate(QDate.currentDate()))
        
        collection_layout.addWidget(self.lbl_collection)
        collection_layout.addStretch()
        collection_layout.addWidget(lbl_date_pick)
        collection_layout.addWidget(self.date_picker)
        collection_layout.addWidget(btn_today_col)

        self.bills_table = QTableWidget()
        self.bills_table.setColumnCount(7)
        self.bills_table.setHorizontalHeaderLabels(["ID", "Patient Name", "Phone", "Medicines", "Total Qty", "Amount", "Mode & Date"])
        self.bills_table.setMaximumHeight(140)

        layout.addLayout(form_layout)
        layout.addLayout(prescription_container_layout)
        layout.addWidget(btn_generate)
        layout.addWidget(self.bill_output)
        layout.addLayout(collection_layout)
        layout.addWidget(QLabel("<b>Generated Bills History:</b>"))
        layout.addWidget(self.bills_table)
        
        self.billing_tab.setLayout(layout)
        self.load_billing_inventory()
        self.load_bills_history()
        self.update_patient_completer()

    def billing_auto_fill_phone(self, text):
        if text in self.patient_dict:
            self.b_phone.setText(str(self.patient_dict[text]))

    def add_prescription_row(self, is_external=False):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 2)
        
        input_widget = SearchableComboBox()
        input_widget.setMinimumHeight(30)
        
        if is_external:
            input_widget.setPlaceholderText("Type 1-2 letters to search External Medicine...")
            if hasattr(self, 'ext_medicine_list_items'):
                input_widget.set_items(self.ext_medicine_list_items)
        else:
            input_widget.setPlaceholderText("Type 1-2 letters to search Stock Medicine...")
            if hasattr(self, 'medicine_list_items'):
                input_widget.set_items(self.medicine_list_items)
            
        btn_remove = QPushButton("❌ Remove")
        btn_remove.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 4px 10px;")
        btn_remove.setFixedSize(90, 30)
        
        def remove_row():
            row_widget.setParent(None)
            row_widget.deleteLater()
            item_tuple = (is_external, input_widget, row_widget)
            if item_tuple in self.med_widgets:
                self.med_widgets.remove(item_tuple)
                
        btn_remove.clicked.connect(remove_row)
        
        row_layout.addWidget(input_widget)
        row_layout.addWidget(btn_remove)
        
        self.med_rows_layout.addWidget(row_widget)
        self.med_widgets.append((is_external, input_widget, row_widget))

    def load_billing_inventory(self):
        self.cursor.execute("SELECT id, med_name, potency, stock_ml, price_per_ml FROM inventory")
        rows = self.cursor.fetchall()
        self.billing_inventory_table.setRowCount(len(rows))
        
        self.medicine_map = {}
        self.medicine_list_items = []

        for row_idx, row_data in enumerate(rows):
            med_id, med_name, potency, stock, price = row_data
            for col_idx, data in enumerate(row_data):
                self.billing_inventory_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
            
            display_text = f"ID: {med_id} - {med_name} ({potency}) [Stock: {stock}ml]"
            self.medicine_list_items.append(display_text)
            self.medicine_map[display_text] = med_id

        self.cursor.execute("SELECT id, med_name, stock_qty, price FROM external_inventory")
        ext_rows = self.cursor.fetchall()
        self.billing_ext_table.setRowCount(len(ext_rows))
        
        self.ext_medicine_map = {}
        self.ext_medicine_list_items = []

        for row_idx, row_data in enumerate(ext_rows):
            ext_id, ext_name, stock, price = row_data
            for col_idx, data in enumerate(row_data):
                self.billing_ext_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
            
            display_text = f"ExtID: {ext_id} - {ext_name} [Stock: {stock}] (₹{price})"
            self.ext_medicine_list_items.append(display_text)
            self.ext_medicine_map[display_text] = (ext_id, price)

        for is_ext, widget, _ in self.med_widgets:
            current_val = widget.currentText()
            if is_ext:
                widget.set_items(self.ext_medicine_list_items)
            else:
                widget.set_items(self.medicine_list_items)
            widget.setCurrentText(current_val)

    def load_bills_history(self):
        self.cursor.execute("SELECT * FROM bills ORDER BY id DESC")
        rows = self.cursor.fetchall()
        self.bills_table.setRowCount(len(rows))
        
        for row_idx, row_data in enumerate(rows):
            for col_idx, data in enumerate(row_data):
                self.bills_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

        self.update_collection_for_selected_date()

    def update_collection_for_selected_date(self):
        selected_date_str = self.date_picker.date().toString("yyyy-MM-dd")
        self.cursor.execute("SELECT amount, bill_date FROM bills")
        rows = self.cursor.fetchall()
        
        total_collection = 0.0
        for amount, bill_date_str in rows:
            if selected_date_str in str(bill_date_str):
                total_collection += float(amount)
                
        is_today = (selected_date_str == datetime.now().strftime("%Y-%m-%d"))
        label_title = "Today's Total Collection" if is_today else f"Collection ({selected_date_str})"
        self.lbl_collection.setText(f"<b>{label_title}: ₹{total_collection:.2f}</b>")

    def generate_and_send_bill(self):
        patient = self.b_patient.currentText().strip()
        phone = self.b_phone.text().strip()
        payment_mode = self.b_payment_mode.currentText()
        
        if not patient:
            QMessageBox.warning(self, "Error", "Please enter or select a patient name!")
            return
            
        if not self.med_widgets:
            QMessageBox.warning(self, "Error", "Please add at least one medicine to the prescription!")
            return
            
        try:
            days = int(self.b_days.text())
            ml_per_day = float(self.b_ml_per_day.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numeric values for Days and Dose!")
            return
            
        total_amount = 0.0
        med_descriptions = []
        total_ml_all = 0.0
        
        for is_ext, widget, _ in self.med_widgets:
            med_text = widget.currentText().strip()
            if is_ext:
                if med_text and med_text in self.ext_medicine_map:
                    ext_id, ext_price = self.ext_medicine_map[med_text]
                    self.cursor.execute("SELECT med_name, stock_qty FROM external_inventory WHERE id=?", (ext_id,))
                    ext_med = self.cursor.fetchone()
                    if ext_med:
                        ext_name, current_ext_stock = ext_med
                        if current_ext_stock < 1:
                            QMessageBox.warning(self, "Stock Alert", f"Out of stock for external medicine: {ext_name}!")
                            return
                        total_amount += ext_price
                        med_descriptions.append(f"{ext_name} [External]")
                        self.cursor.execute("UPDATE external_inventory SET stock_qty=? WHERE id=?", (current_ext_stock - 1, ext_id))
            else:
                if med_text and med_text in self.medicine_map:
                    med_id = self.medicine_map[med_text]
                    self.cursor.execute("SELECT med_name, potency, stock_ml, price_per_ml FROM inventory WHERE id=?", (med_id,))
                    med = self.cursor.fetchone()
                    
                    if med:
                        med_name, potency, current_stock, price_per_ml = med
                        total_ml_needed = days * ml_per_day
                        
                        if current_stock < total_ml_needed:
                            QMessageBox.warning(self, "Stock Alert", f"Not enough stock for {med_name} ({potency})! Available: {current_stock} ml")
                            return
                            
                        total_amount += (total_ml_needed * price_per_ml)
                        total_ml_all += total_ml_needed
                        med_descriptions.append(f"{med_name} ({potency})")
                        
                        new_stock = current_stock - total_ml_needed
                        self.cursor.execute("UPDATE inventory SET stock_ml=? WHERE id=?", (new_stock, med_id))

        if not med_descriptions:
            QMessageBox.warning(self, "Error", "Please select valid medicines from suggestions!")
            return

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
        combined_med_desc = ", ".join(med_descriptions)
        
        self.cursor.execute("""
            INSERT INTO bills (patient_name, phone, medicine, total_ml, amount, payment_mode, days_given, bill_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (patient, phone, combined_med_desc, total_ml_all, total_amount, payment_mode, days, current_datetime))
        
        self.conn.commit()
        
        self.load_inventory()
        self.load_billing_inventory()
        self.load_bills_history()
        
        bill_display_text = f"""=== PANWAR HOMOEOPATHIC CLINIC ===
Patient Name: {patient}
Prescribed Medicines: {combined_med_desc}
Duration: {days} Days
Payment Mode: {payment_mode}
---------------------------------
Total Amount to Pay: ₹{total_amount:.2f}
================================="""
        
        self.bill_output.setText(bill_display_text)

        customer_whatsapp_message = f"Thanks for visiting Panwar Homoeopathic Clinic. Please revisit after {days} days."

        if phone:
            self.whatsapp_thread = WhatsAppThread(phone, customer_whatsapp_message)
            self.whatsapp_thread.start()

        QMessageBox.information(self, "Success", "Prescription bill generated successfully!")
        self.clear_billing_form()

    def clear_billing_form(self):
        self.b_patient.setEditText("")
        self.b_phone.clear()
        self.b_days.setText("7")
        self.b_ml_per_day.setText("1.0")
        self.b_payment_mode.setCurrentIndex(0)
        
        for _, _, row_widget in self.med_widgets:
            row_widget.setParent(None)
            row_widget.deleteLater()
        self.med_widgets.clear()
        
        self.add_prescription_row(is_external=False)
        self.add_prescription_row(is_external=False)

    def check_followup_reminders(self):
        try:
            self.cursor.execute("SELECT patient_name, phone, days_given, bill_date FROM bills")
            rows = self.cursor.fetchall()
            today = datetime.now().date()
            
            for row in rows:
                p_name, p_phone, days_given, b_date_str = row[0], row[1], row[2], row[3]
                if not p_phone or not days_given:
                    continue
                bill_date = datetime.strptime(b_date_str.split()[0], "%Y-%m-%d").date()
                days_passed = (today - bill_date).days
                
                trigger_day = days_given - 3
                if days_passed == trigger_day:
                    reminder_msg = f"Hello {p_name}, gentle reminder from Panwar Homoeopathic Clinic. Your medicine course is completing in 3 days. Please visit for follow-up."
        except Exception:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HomeopathyApp()
    window.show()
    sys.exit(app.exec())