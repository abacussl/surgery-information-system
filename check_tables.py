# check_tables.py
import sqlite3

def check_table_exists(table_name):
    conn = sqlite3.connect('urology_data.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    result = cursor.fetchone()
    conn.close()
    return bool(result)

if __name__ == "__main__":
    required_tables = [
        "dropdown_options", "patients", "operations", 
        "prescriptions", "investigations", "report_history"
    ]
    
    print("Database Status:")
    all_exist = True
    for table in required_tables:
        exists = check_table_exists(table)
        print(f"{table}: {'✅' if exists else '❌'}")
        if not exists:
            all_exist = False
            
    if all_exist:
        print("\nAll tables are present!")
    else:
        print("\nSome tables are missing. Run repair_db.py to fix.")
