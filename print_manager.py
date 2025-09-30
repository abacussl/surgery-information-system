# print_manager.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QLabel, QListWidgetItem, QMessageBox, QTextBrowser
)
from PyQt5.QtCore import Qt
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtGui import QTextDocument
import database
import os
import subprocess
import sys
import sqlite3
import datetime
import tempfile

class PrintManager(QDialog):
    def __init__(self, patient_id, parent=None, hospital_name="", unit_name=""):
        super().__init__(parent)
        self.patient_id = patient_id
        self.hospital_name = hospital_name
        self.unit_name = unit_name
        self.setWindowTitle("Print Management")
        self.setGeometry(300, 300, 600, 400)
    
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Print History:"))
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)
        self.load_history()

        btn_layout = QHBoxLayout()

        self.print_btn = QPushButton("Print Now")
        self.print_btn.clicked.connect(self.print_directly)
        btn_layout.addWidget(self.print_btn)

        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.show_preview)
        btn_layout.addWidget(self.preview_btn)

        self.open_btn = QPushButton("Open PDF")
        self.open_btn.clicked.connect(self.open_pdf)
        btn_layout.addWidget(self.open_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def load_history(self):
        self.history_list.clear()
        try:
            history = database.get_print_history(self.patient_id)
            for item in history:
                try:
                    printed_at = datetime.datetime.strptime(
                        item['printed_at'], '%Y-%m-%d %H:%M:%S'
                    ).strftime('%d/%m/%Y %H:%M')
                except:
                    printed_at = item['printed_at']
                list_item = QListWidgetItem(f"{printed_at} - {item['report_path']}")
                list_item.setData(Qt.UserRole, item)
                self.history_list.addItem(list_item)
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                QMessageBox.warning(self, "Missing Table", 
                    "Report history table is missing. Please run database repair.")
            else:
                QMessageBox.critical(self, "Database Error", f"Error loading history: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")

    def print_directly(self):
        try:
            from pdf_generator import generate_patient_report
            html, path = generate_patient_report(
                self.patient_id,
                hospital_name=self.hospital_name,
                unit_name=self.unit_name
            )
            self.print_html(html)
            self.load_history()
            QMessageBox.information(self, "Success", "Printed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print: {str(e)}")

    def show_preview(self):
        try:
            selected = self.history_list.selectedItems()
            if selected:
                report_path = selected[0].data(Qt.UserRole)['report_path']
                self._show_preview_dialog(report_path)
            else:
                from pdf_generator import generate_patient_report
                html, path = generate_patient_report(
                    self.patient_id,
                    hospital_name=self.hospital_name,
                    unit_name=self.unit_name
                )
                self._show_preview_dialog(path, html)
                self.load_history()
        except Exception as e:
            QMessageBox.critical(self, "Preview Error", f"Failed to preview: {str(e)}")

    def _show_preview_dialog(self, report_path, html_content=None):
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Report Preview")
        preview_dialog.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout(preview_dialog)

        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView
            from PyQt5.QtCore import QUrl
            web_view = QWebEngineView()
            abs_path = os.path.abspath(report_path).replace('\\', '/')
            web_view.load(QUrl(f"file:///{abs_path}"))
            layout.addWidget(web_view)
        except ImportError:
            if html_content:
                text_browser = QTextBrowser()
                text_browser.setHtml(html_content)
                layout.addWidget(text_browser)
            else:
                try:
                    import pdfminer.high_level
                    from io import StringIO
                    output_string = StringIO()
                    pdfminer.high_level.extract_text_to_fp(
                        open(report_path, 'rb'), output_string
                    )
                    text_browser = QTextBrowser()
                    text_browser.setPlainText(output_string.getvalue())
                    layout.addWidget(text_browser)
                except ImportError:
                    layout.addWidget(QLabel(
                        f"PDF preview requires PyQtWebEngine or pdfminer.six.\nPDF saved at: {report_path}"
                    ))

        open_btn = QPushButton("Open in Default Viewer")
        open_btn.clicked.connect(lambda: self.open_pdf(report_path))
        layout.addWidget(open_btn)

        close_btn = QPushButton("Close Preview")
        close_btn.clicked.connect(preview_dialog.accept)
        layout.addWidget(close_btn)

        preview_dialog.exec_()

    def print_pdf(self, path):
        if os.name == 'nt':
            try:
                os.startfile(path, "print")
            except Exception as e:
                QMessageBox.warning(self, "Print Error", 
                    f"Failed to print: {str(e)}\nPlease open and print manually.")
        else:
            QMessageBox.warning(self, "Print", 
                "Direct printing only supported on Windows. Please open and print manually.")

    def open_pdf(self, path=None):
        if not path:
            selected = self.history_list.selectedItems()
            if not selected:
                return
            path = selected[0].data(Qt.UserRole)['report_path']

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.name == 'nt':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', path])
            else:
                subprocess.call(['xdg-open', path])
        except Exception as e:
            QMessageBox.critical(self, "Open Error", 
                f"Failed to open PDF: {str(e)}\nPath: {path}")

    def print_html(self, html_content):
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)

        if dialog.exec_() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setHtml(html_content)
            doc.print_(printer)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = PrintManager(1)
    dialog.exec_()
    sys.exit(app.exec_())
