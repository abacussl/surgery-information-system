
# d# database.py
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = "urology_data.db"

@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()

# database.py (update the initialization at the end)

# Always check and create missing tables
def check_and_create_tables():
    with db_connection() as cursor:
        # Get existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        # Table creation commands
        table_creations = [
            """CREATE TABLE IF NOT EXISTS dropdown_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                value TEXT NOT NULL,
                UNIQUE(category, value)
            );""",
            """CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                sex TEXT,
                admission_date TEXT,
                discharge_date TEXT,
                bht_no TEXT UNIQUE,
                indication TEXT,
                history_exam TEXT,
                management TEXT,
                next_appointment TEXT
            );""",
            """CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                surgeon TEXT,
                anaesthetist TEXT,
                anaesthesia_type TEXT,
                surgery_name TEXT,
                surgery_description TEXT,
                FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
            );""",
            """CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                drug_name TEXT,
                drug_form TEXT,
                strength TEXT,
                dose TEXT,
                frequency TEXT,
                route TEXT,
                duration TEXT,
                FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
            );""",
            """CREATE TABLE IF NOT EXISTS investigations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
            );""",
            """CREATE TABLE IF NOT EXISTS op_variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
            );""",
            """CREATE TABLE IF NOT EXISTS report_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                report_path TEXT NOT NULL,
                printed_at TEXT NOT NULL,
                FOREIGN KEY(patient_id) REFERENCES patients(id)
            );"""
        ]

        # Execute each creation command
        for create_cmd in table_creations:
            cursor.execute(create_cmd)

# Initialize database on start
if not os.path.exists(DB_PATH):
    # Create new database
    check_and_create_tables()
else:
    # Ensure all tables exist in existing database
    check_and_create_tables()

# CRUD Operations
def add_dropdown_option(category, value):
    with db_connection() as cursor:
        try:
            cursor.execute(
                "INSERT INTO dropdown_options (category, value) VALUES (?, ?)",
                (category, value)
            )
            return True
        except sqlite3.IntegrityError:
            return False  # Duplicate entry

def get_dropdown_options(category):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT value FROM dropdown_options WHERE category = ? ORDER BY value",
            (category,)
        )
        return [row[0] for row in cursor.fetchall()]

def delete_dropdown_option(category, value):
    with db_connection() as cursor:
        cursor.execute(
            "DELETE FROM dropdown_options WHERE category = ? AND value = ?",
            (category, value)
        )
        return cursor.rowcount > 0

def remove_obsolete_operation_categories():
    obsolete = ["ureters", "bladder", "prostate", "uoo"]
    with db_connection() as cursor:
        for item in obsolete:
            cursor.execute(
                "DELETE FROM dropdown_options WHERE category = ?",
                (item,)
            )

def add_op_variable(patient_id, name, value):
    with db_connection() as cursor:
        cursor.execute(
            "INSERT INTO op_variables (patient_id, name, value) VALUES (?, ?, ?)",
            (patient_id, name, value)
        )

def get_op_variables(patient_id):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT name, value FROM op_variables WHERE patient_id = ?",
            (patient_id,)
        )
        rows = cursor.fetchall()
        return [{'name': row[0], 'value': row[1]} for row in rows]

def delete_op_variables(patient_id):
    with db_connection() as cursor:
        cursor.execute(
            "DELETE FROM op_variables WHERE patient_id = ?",
            (patient_id,)
        )

def save_patient(patient_data):
    with db_connection() as cursor:
        try:
            cursor.execute("""
                INSERT INTO patients (
                    name, age, sex, admission_date, discharge_date,
                    bht_no, indication, history_exam, management, next_appointment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_data['name'],
                patient_data['age'],
                patient_data['sex'],
                patient_data['admission_date'],
                patient_data['discharge_date'],
                patient_data['bht_no'],
                patient_data['indication'],
                patient_data['history_exam'],
                patient_data['management'],
                patient_data['next_appointment']
            ))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Duplicate BHT

def update_patient(patient_id, patient_data):
    with db_connection() as cursor:
        try:
            cursor.execute("""
                UPDATE patients SET
                    name = ?,
                    age = ?,
                    sex = ?,
                    admission_date = ?,
                    discharge_date = ?,
                    bht_no = ?,
                    indication = ?,
                    history_exam = ?,
                    management = ?,
                    next_appointment = ?
                WHERE id = ?
            """, (
                patient_data['name'],
                patient_data['age'],
                patient_data['sex'],
                patient_data['admission_date'],
                patient_data['discharge_date'],
                patient_data['bht_no'],
                patient_data['indication'],
                patient_data['history_exam'],
                patient_data['management'],
                patient_data['next_appointment'],
                patient_id
            ))
            return True
        except sqlite3.IntegrityError:
            return False  # Duplicate BHT

def delete_patient(patient_id):
    with db_connection() as cursor:
        cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        return cursor.rowcount > 0

def search_patients(search_term):
    with db_connection() as cursor:
        cursor.execute("""
            SELECT id, name, bht_no FROM patients
            WHERE name LIKE ? OR bht_no LIKE ?
            ORDER BY name
        """, (f'%{search_term}%', f'%{search_term}%'))
        return cursor.fetchall()

def get_patient(patient_id):
    with db_connection() as cursor:
        cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        return cursor.fetchone()

def save_operation(patient_id, operation_data):
    with db_connection() as cursor:
        cursor.execute("""
            INSERT INTO operations (
                patient_id, surgeon, anaesthetist, anaesthesia_type,
                surgery_name, surgery_description
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            operation_data['surgeon'],
            operation_data['anaesthetist'],
            operation_data['anaesthesia_type'],
            operation_data['surgery_name'],
            operation_data['surgery_description']
        ))
        return cursor.lastrowid


def update_operation(operation_id, operation_data):
    with db_connection() as cursor:
        cursor.execute("""
            UPDATE operations SET
                surgeon = ?,
                anaesthetist = ?,
                anaesthesia_type = ?,
                surgery_name = ?,
                surgery_description = ?
            WHERE id = ?
        """, (
            operation_data['surgeon'],
            operation_data['anaesthetist'],
            operation_data['anaesthesia_type'],
            operation_data['surgery_name'],
            operation_data['surgery_description'],
            operation_id
        ))

def get_patient_operation(patient_id):
    with db_connection() as cursor:
        cursor.execute("SELECT * FROM operations WHERE patient_id = ?", (patient_id,))
        return cursor.fetchone()

def save_prescriptions(patient_id, prescriptions):
    with db_connection() as cursor:
        cursor.execute("DELETE FROM prescriptions WHERE patient_id = ?", (patient_id,))
        for drug in prescriptions:
            cursor.execute("""
                INSERT INTO prescriptions (
                    patient_id, drug_name, drug_form, strength, 
                    dose, frequency, route, duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                drug['drug_name'],
                drug['drug_form'],
                drug['strength'],
                drug['dose'],
                drug['frequency'],
                drug['route'],
                drug['duration']
            ))

#def get_patient_prescriptions(patient_id):
#    with db_connection() as cursor:
#        cursor.execute("SELECT * FROM prescriptions WHERE patient_id = ?", (patient_id,))
#       return cursor.fetchall()
# database.py
def get_patient_prescriptions(patient_id):
    with db_connection() as cursor:
        cursor.execute("""
            SELECT 
                drug_name, drug_form, strength, dose, 
                frequency, route, duration 
            FROM prescriptions 
            WHERE patient_id = ?
        """, (patient_id,))
        return cursor.fetchall()

def save_investigations(patient_id, investigations):
    with db_connection() as cursor:
        cursor.execute("DELETE FROM investigations WHERE patient_id = ?", (patient_id,))
        for test in investigations:
            cursor.execute("""
                INSERT INTO investigations (patient_id, name, value)
                VALUES (?, ?, ?)
            """, (patient_id, test['name'], test['value']))

def get_patient_investigations(patient_id):
    with db_connection() as cursor:
        cursor.execute("SELECT * FROM investigations WHERE patient_id = ?", (patient_id,))
        return cursor.fetchall()

def get_print_history(patient_id):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT * FROM report_history WHERE patient_id = ? ORDER BY printed_at DESC",
            (patient_id,)
        )
        return cursor.fetchall()

# Initialize the database
if not os.path.exists(DB_PATH):
    initialize_database()# database.py
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = "urology_data.db"

@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()

def initialize_database():
    with db_connection() as cursor:
        # Dropdown options table - FIXED MISSING PARENTHESIS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dropdown_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            value TEXT NOT NULL,
            UNIQUE(category, value)
        );
        """)
        
        # Patients table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            sex TEXT,
            admission_date TEXT,
            discharge_date TEXT,
            bht_no TEXT UNIQUE,
            indication TEXT,
            history_exam TEXT,
            management TEXT,
            next_appointment TEXT
        );
        """)
        
        # Operations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            surgeon TEXT,
            anaesthetist TEXT,
            anaesthesia_type TEXT,
            surgery_name TEXT,
            surgery_description TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
        """)
        
        # Prescriptions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            drug_name TEXT,
            drug_form TEXT,
            strength TEXT,
            dose TEXT,
            frequency TEXT,
            route TEXT,
            duration TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
        """)
        
        # Investigations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS investigations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            value TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
        """)
        
        # Report history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            report_path TEXT NOT NULL,
            printed_at TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        );
        """)

# CRUD Operations
def add_dropdown_option(category, value):
    with db_connection() as cursor:
        try:
            cursor.execute(
                "INSERT INTO dropdown_options (category, value) VALUES (?, ?)",
                (category, value)
            )
            return True
        except sqlite3.IntegrityError:
            return False  # Duplicate entry

def get_dropdown_options(category):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT value FROM dropdown_options WHERE category = ? ORDER BY value",
            (category,)
        )
        return [row[0] for row in cursor.fetchall()]

def delete_dropdown_option(category, value):
    with db_connection() as cursor:
        cursor.execute(
            "DELETE FROM dropdown_options WHERE category = ? AND value = ?",
            (category, value)
        )
        return cursor.rowcount > 0

def save_patient(patient_data):
    with db_connection() as cursor:
        try:
            cursor.execute("""
                INSERT INTO patients (
                    name, age, sex, admission_date, discharge_date,
                    bht_no, indication, history_exam, management, next_appointment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_data['name'],
                patient_data['age'],
                patient_data['sex'],
                patient_data['admission_date'],
                patient_data['discharge_date'],
                patient_data['bht_no'],
                patient_data['indication'],
                patient_data['history_exam'],
                patient_data['management'],
                patient_data['next_appointment']
            ))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Duplicate BHT

def update_patient(patient_id, patient_data):
    with db_connection() as cursor:
        try:
            cursor.execute("""
                UPDATE patients SET
                    name = ?,
                    age = ?,
                    sex = ?,
                    admission_date = ?,
                    discharge_date = ?,
                    bht_no = ?,
                    indication = ?,
                    history_exam = ?,
                    management = ?,
                    next_appointment = ?
                WHERE id = ?
            """, (
                patient_data['name'],
                patient_data['age'],
                patient_data['sex'],
                patient_data['admission_date'],
                patient_data['discharge_date'],
                patient_data['bht_no'],
                patient_data['indication'],
                patient_data['history_exam'],
                patient_data['management'],
                patient_data['next_appointment'],
                patient_id
            ))
            return True
        except sqlite3.IntegrityError:
            return False  # Duplicate BHT

def delete_patient(patient_id):
    with db_connection() as cursor:
        cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        return cursor.rowcount > 0

def search_patients(search_term):
    with db_connection() as cursor:
        cursor.execute("""
            SELECT id, name, bht_no FROM patients
            WHERE name LIKE ? OR bht_no LIKE ?
            ORDER BY name
        """, (f'%{search_term}%', f'%{search_term}%'))
        return cursor.fetchall()

def get_patient(patient_id):
    with db_connection() as cursor:
        cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        return cursor.fetchone()

def save_operation(patient_id, operation_data):
    with db_connection() as cursor:
        cursor.execute("""
            INSERT INTO operations (
                patient_id, surgeon, anaesthetist, anaesthesia_type,
                surgery_name, surgery_description
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            operation_data['surgeon'],
            operation_data['anaesthetist'],
            operation_data['anaesthesia_type'],
            operation_data['surgery_name'],
            operation_data['surgery_description']            
        ))
        return cursor.lastrowid

def update_operation(operation_id, operation_data):
    with db_connection() as cursor:
        cursor.execute("""
            UPDATE operations SET
                surgeon = ?,
                anaesthetist = ?,
                anaesthesia_type = ?,
                surgery_name = ?,
                surgery_description = ?
            WHERE id = ?
        """, (
            operation_data['surgeon'],
            operation_data['anaesthetist'],
            operation_data['anaesthesia_type'],
            operation_data['surgery_name'],
            operation_data['surgery_description'],           
            operation_id
        ))

def get_patient_operation(patient_id):
    with db_connection() as cursor:
        cursor.execute("SELECT * FROM operations WHERE patient_id = ?", (patient_id,))
        return cursor.fetchone()

def save_prescriptions(patient_id, prescriptions):
    with db_connection() as cursor:
        cursor.execute("DELETE FROM prescriptions WHERE patient_id = ?", (patient_id,))
        for drug in prescriptions:
            cursor.execute("""
                INSERT INTO prescriptions (
                    patient_id, drug_name, drug_form, strength, 
                    dose, frequency, route, duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                drug['drug_name'],
                drug['drug_form'],
                drug['strength'],
                drug['dose'],
                drug['frequency'],
                drug['route'],
                drug['duration']
            ))

def get_patient_prescriptions(patient_id):
    with db_connection() as cursor:
        cursor.execute("SELECT * FROM prescriptions WHERE patient_id = ?", (patient_id,))
        return cursor.fetchall()

def save_investigations(patient_id, investigations):
    with db_connection() as cursor:
        cursor.execute("DELETE FROM investigations WHERE patient_id = ?", (patient_id,))
        for test in investigations:
            cursor.execute("""
                INSERT INTO investigations (patient_id, name, value)
                VALUES (?, ?, ?)
            """, (patient_id, test['name'], test['value']))

def get_patient_investigations(patient_id):
    with db_connection() as cursor:
        cursor.execute("SELECT * FROM investigations WHERE patient_id = ?", (patient_id,))
        return cursor.fetchall()

def get_print_history(patient_id):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT * FROM report_history WHERE patient_id = ? ORDER BY printed_at DESC",
            (patient_id,)
        )
        return cursor.fetchall()

# Initialize the database
if not os.path.exists(DB_PATH):
    initialize_database()
    
# database.py (new function)
def update_dropdown_order(category, ordered_items):
    """Update the display order of dropdown options"""
    try:
        # Clear existing order
        cursor.execute("DELETE FROM dropdown_options WHERE category=?", (category,))
        
        # Reinsert items in new order
        for order_index, item in enumerate(ordered_items):
            cursor.execute(
                "INSERT INTO dropdown_options (category, option, display_order) VALUES (?, ?, ?)",
                (category, item, order_index)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Order update failed: {e}")
        return False
