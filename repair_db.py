# repair_db.py
import sqlite3
import os

DB_PATH = "urology_data.db"

def create_report_history_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS report_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        report_path TEXT NOT NULL,
        printed_at TEXT NOT NULL,
        FOREIGN KEY(patient_id) REFERENCES patients(id)
    );
    """)
    
    conn.commit()
    conn.close()
    print("report_history table created!")

if __name__ == "__main__":
    create_report_history_table()
