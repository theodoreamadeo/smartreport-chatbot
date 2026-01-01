import openpyxl
from datetime import datetime
import os 
from pathlib import Path
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo

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

            header_font = Font(name="Apos Narrow", size=9, bold=True)
            header_fill = PatternFill(start_color="A9D08E", end_color="A9D08E", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")

            for cell in sheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Create table
            tab = Table(displayName="IssueTrackingTable", ref="A1:E1")
            style = TableStyleInfo(name="None", showFirstColumn=False, showLastColumn=False, showRowStripes=True, showColumnStripes=False)
            tab.tableStyleInfo = style
            sheet.add_table(tab)

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

            # Update table range to include new row
            current_row = sheet.max_row
            for table in sheet.tables.values():
                table.ref = f"A1:E{current_row}"

            # Define color for each type
            color_map = {
                "DATA_PROB": "FFFF00",    # Yellow
                "HARDWARE": "FF0000",     # Red
                "SOFTWARE": "0000FF",     # Blue
                "MISMATCH": "FFA500",     # Orange
                "OTHERS": "808080",       # Gray
                "UNSURE": "FFFFFF"        # White
            }

            # Get color based on type (default to white if type not found)
            fill_color = color_map.get(type.upper(), "FFFFFF")
            fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            
            # Apply color only to the Type cell (column C) in the current row
            sheet[f"C{current_row}"].fill = fill

            main_font = Font(name="Apos Narrow", size=9)
            for cell in sheet[current_row]:
                cell.font = main_font
        
        wb.save(EXCEL_FILE)
        return True
        
    except Exception as e:
        print(f"Error logging to Excel: {e}")
        return False