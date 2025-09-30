# check_dependencies.py
try:
    import jinja2
    import pdfkit
    from PyQt5 import QtWidgets
    import pandas
    import pysqlite3
    print("✅ All dependencies are installed!")
except ImportError as e:
    print(f"❌ Missing dependency: {e.name}")
    print("Run: pip install jinja2 pdfkit PyQt5 pandas pysqlite3")
