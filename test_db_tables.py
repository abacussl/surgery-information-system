# test_db_tables.py
import database

def test_tables_exist():
    with database.db_connection() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        print("Tables in database:", tables)
        
        # Check report_history exists
        if 'report_history' in tables:
            print("report_history table exists!")
        else:
            print("ERROR: report_history table missing!")

if __name__ == "__main__":
    test_tables_exist()
