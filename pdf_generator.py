import os
import sys
import pdfkit
import jinja2
import database
from datetime import datetime

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller .exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

def generate_patient_report(patient_id, output_path=None, hospital_name="", unit_name=""):
    patient = database.get_patient(patient_id)
    operation = database.get_patient_operation(patient_id)
    prescriptions = database.get_patient_prescriptions(patient_id)
    investigations = database.get_patient_investigations(patient_id)
    
    # Get operation variables for this patient
    op_variables = database.get_op_variables(patient_id)
    
    # Helper: Date formatting
    def format_date(date_str, format="%d/%m/%Y"):
        if not date_str:
            return ""
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime(format)
        except:
            return date_str

    def format_datetime(dt_str, format="%d/%m/%Y %H:%M"):
        if not dt_str:
            return ""
        try:
            dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
            return dt.strftime(format)
        except:
            return dt_str

    # Context for Jinja2 template
    context = {
        'patient': patient,
        'operation': operation,
        'prescriptions': prescriptions,
        'investigations': investigations,
        'op_variables': op_variables,
        'admission_date': format_date(patient['admission_date']),
        'discharge_date': format_date(patient['discharge_date']),
        'next_appointment': format_datetime(patient['next_appointment']),
        'report_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'hospital_name': hospital_name,
        'unit_name': unit_name
    }

    # Define output path
    if output_path is None:
        output_dir = "reports"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(
            output_dir,
            f"patient_{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

    # Load the report.html template
    template_path = resource_path(os.path.join("templates", "report.html"))
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()

    template_env = jinja2.Environment(loader=jinja2.BaseLoader())
    template = template_env.from_string(template_html)
    html = template.render(context)

    # Use wkhtmltopdf from bundled folder or system PATH
    local_wkhtml = resource_path(os.path.join("wkhtmltopdf", "wkhtmltopdf.exe"))
    if os.path.exists(local_wkhtml):
        wkhtml_path = local_wkhtml
    else:
        import shutil
        wkhtml_path = shutil.which("wkhtmltopdf")
        if not wkhtml_path:
            raise EnvironmentError("wkhtmltopdf not found. Please install or bundle it.")

    # PDF options for A5 landscape with optimized margins
    options = {
        'page-size': 'A5',
        'orientation': 'Landscape',
        'margin-top': '0.3in',
        'margin-right': '0.3in',
        'margin-bottom': '0.3in',
        'margin-left': '0.3in',
        'encoding': "UTF-8",
        'disable-smart-shrinking': None,  # Ensures consistent scaling
        'dpi': 300,  # Higher quality output
        'print-media-type': None,  # Use print styles
        'no-outline': None  # Disable table of contents
    }
    
    config = pdfkit.configuration(wkhtmltopdf=wkhtml_path)
    
    # Generate PDF with landscape A5 settings
    pdfkit.from_string(html, output_path, configuration=config, options=options)

    # Save to history
    with database.db_connection() as cursor:
        cursor.execute(
            "INSERT INTO report_history (patient_id, report_path, printed_at) VALUES (?, ?, ?)",
            (patient_id, output_path, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )

    return html, output_path
