# test_db.py
import database

def test_dropdown_operations():
    print("Testing dropdown operations...")
    
    # Add options
    database.add_dropdown_option("surgeon", "Dr. Smith")
    database.add_dropdown_option("surgeon", "Dr. Johnson")
    database.add_dropdown_option("anaesthesia", "General")
    
    # Retrieve options
    surgeons = database.get_dropdown_options("surgeon")
    print("Surgeons:", surgeons)
    
    # Try duplicate
    result = database.add_dropdown_option("surgeon", "Dr. Smith")
    print("Add duplicate:", "Failed" if not result else "Success (should fail)")
    
    # Delete option
    database.delete_dropdown_option("surgeon", "Dr. Johnson")
    print("Surgeons after deletion:", database.get_dropdown_options("surgeon"))

if __name__ == "__main__":
    test_dropdown_operations()
    print("Check database file created: urology_data.db")
