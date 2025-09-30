# repair_db.py
import database

def repair_database():
    print("Repairing database...")
    # This will recreate any missing tables
    database.check_and_create_tables()
    print("Database repair complete!")

if __name__ == "__main__":
    repair_database()
