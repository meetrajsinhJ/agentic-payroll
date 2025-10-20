"""
Agent 1: Timesheet Parser & Data Extraction Agent
Extracts employee information and working hours from Excel/PDF timesheets
"""
import pandas as pd
import os
from typing import Dict
from models import TimesheetData, EmployeeInfo, WorkingHours, PayPeriod


class TimesheetParserAgent:
    """Agent responsible for parsing timesheets and extracting data"""

    def __init__(self):
        self.name = "Timesheet Parser Agent"

    def parse_excel_timesheet(self, file_path: str) -> Dict:
        """Parse Excel timesheet and extract structured data"""
        print(f"\n[{self.name}] Parsing Excel file: {file_path}")

        try:
            # Read the Excel file
            df = pd.read_excel(file_path, sheet_name='Timesheet')

            # Extract employee information (rows 0-5)
            employee_data = {}
            for idx in range(6):
                field = df.iloc[idx, 0]
                value = df.iloc[idx, 1]
                if pd.notna(field) and pd.notna(value):
                    employee_data[field] = str(value)

            # Extract pay period (rows 8-9)
            period_start = str(df.iloc[8, 1])
            period_end = str(df.iloc[9, 1])

            # Find where daily records start (look for "date" header - lowercase)
            daily_start_row = None
            for idx in range(len(df)):
                if str(df.iloc[idx, 0]).lower() == 'date':
                    daily_start_row = idx
                    break

            if daily_start_row is None:
                raise ValueError("Could not find daily attendance records in timesheet")

            # Extract daily records - read with header
            daily_df = pd.read_excel(
                file_path,
                sheet_name='Timesheet',
                skiprows=daily_start_row,
                nrows=32  # Maximum days in a month + 1 for header
            )

            # The first row should be the header, set it as column names
            daily_df.columns = daily_df.iloc[0]
            daily_df = daily_df[1:]  # Remove the header row from data
            daily_df = daily_df.reset_index(drop=True)

            # Remove any rows with NaN in 'date' column (blank rows)
            if 'date' in daily_df.columns:
                daily_df = daily_df[daily_df['date'].notna()]
            else:
                raise ValueError(f"'date' column not found. Available columns: {daily_df.columns.tolist()}")

            # Calculate working hours summary
            # Filter out weekends and leaves
            work_days = daily_df[daily_df['status'].isin(['Present', 'Half Day'])]
            regular_hours = work_days['hours_worked'].sum()
            overtime_hours = daily_df['overtime_hours'].sum()
            leave_days = len(daily_df[daily_df['status'] == 'Leave'])
            holiday_work_hours = daily_df[daily_df['status'] == 'Holiday Work']['hours_worked'].sum()

            # Find summary section (look for "Total Regular Hours")
            summary_start_row = None
            for idx in range(len(df)):
                if str(df.iloc[idx, 0]).startswith('Total Regular Hours'):
                    summary_start_row = idx
                    break

            # Extract rates from summary
            summary_df = pd.read_excel(
                file_path,
                sheet_name='Timesheet',
                skiprows=summary_start_row,
                nrows=6
            )

            hourly_rate = float(summary_df.iloc[4, 1])
            overtime_rate = float(summary_df.iloc[5, 1])

            print(f"[{self.name}] Successfully extracted data:")
            print(f"  - Employee: {employee_data.get('Name', 'Unknown')}")
            print(f"  - Regular Hours: {regular_hours}")
            print(f"  - Overtime Hours: {overtime_hours}")
            print(f"  - Leave Days: {leave_days}")

            # Structure the data
            timesheet_data = TimesheetData(
                employee=EmployeeInfo(
                    employee_id=employee_data.get('Employee ID', ''),
                    name=employee_data.get('Name', ''),
                    department=employee_data.get('Department', ''),
                    designation=employee_data.get('Designation', ''),
                    email=employee_data.get('Email', ''),
                    bank_account=employee_data.get('Bank Account', '')
                ),
                period=PayPeriod(
                    start_date=period_start,
                    end_date=period_end
                ),
                hours=WorkingHours(
                    regular_hours=float(regular_hours),
                    overtime_hours=float(overtime_hours),
                    leave_days=int(leave_days),
                    holiday_work_hours=float(holiday_work_hours)
                ),
                hourly_rate=hourly_rate,
                overtime_rate=overtime_rate
            )

            return {
                "success": True,
                "data": timesheet_data,
                "error": None
            }

        except Exception as e:
            print(f"[{self.name}] Error parsing timesheet: {str(e)}")
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }

    def parse_pdf_timesheet(self, file_path: str) -> Dict:
        """Parse PDF timesheet - placeholder for future implementation"""
        print(f"[{self.name}] PDF parsing not yet implemented. Please use Excel format.")
        return {
            "success": False,
            "data": None,
            "error": "PDF parsing not implemented yet"
        }

    def process(self, file_path: str) -> Dict:
        """Main processing method - determines file type and parses accordingly"""
        print(f"\n{'='*60}")
        print(f"[{self.name}] Starting timesheet extraction")
        print(f"{'='*60}")

        if not os.path.exists(file_path):
            return {
                "success": False,
                "data": None,
                "error": f"File not found: {file_path}"
            }

        # Determine file type
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in ['.xlsx', '.xls']:
            return self.parse_excel_timesheet(file_path)
        elif file_extension == '.pdf':
            return self.parse_pdf_timesheet(file_path)
        else:
            return {
                "success": False,
                "data": None,
                "error": f"Unsupported file format: {file_extension}"
            }


# Test function
if __name__ == "__main__":
    agent = TimesheetParserAgent()

    # Test with a sample timesheet
    test_file = "../timesheets/excel/EMP001_John_Smith_Timesheet_Oct2025.xlsx"
    if os.path.exists(test_file):
        result = agent.process(test_file)
        if result["success"]:
            print("\n✓ Extraction successful!")
            print(f"Data: {result['data'].model_dump_json(indent=2)}")
        else:
            print(f"\n✗ Extraction failed: {result['error']}")
