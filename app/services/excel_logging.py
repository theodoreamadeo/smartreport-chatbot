import openpyxl
from datetime import datetime
import os 
from pathlib import Path
from openpyxl.styles import Font

EXCEL_FILE = "logs/ALuL Issue Tracking.xlsx"

def excel_checker ():
    """
    Ensure that the Excel log file and its directory exist.
    Create them if they do not exist.
    """

    Path ("logs").mkdir(exist_ok=True)

    if not os.path.exists(EXCEL_FILE):
        wb = openpyxl.Workbook()
        sheet = wb.active
        if sheet is not None:
            sheet.title = "Production Tracking"
        
        # Add headers
        headers = ["Date", "Reporter", "Type", "Equipment", "Issue Summary"]
        if sheet is not None:
            sheet.append(headers)

        wb.save(EXCEL_FILE)

async def log_report_to_excel(reporter: str, type: str, equipment: str, issue_summary: str):
    """Log the report and AI analysis to Excel"""
    try:
        excel_checker()
        
        wb = openpyxl.load_workbook(EXCEL_FILE)
        sheet = wb.active
        
        row_data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            reporter, 
            type,
            equipment,
            issue_summary
        ]
        print (row_data)

        if sheet is not None:
            sheet.append(row_data)
        
        wb.save(EXCEL_FILE)
        return True
        
    except Exception as e:
        print(f"Error logging to Excel: {e}")
        return False