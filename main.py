"""
Main Execution Script for Timesheet to Salary Slip System
Processes all timesheets and generates salary slips
"""
import os
import glob
from workflow import TimesheetWorkflow
from datetime import datetime


def process_all_timesheets(timesheet_dir: str = None):
    # Auto-detect path: /data/timesheets/excel/ in K8s, ./timesheets/excel locally
    if timesheet_dir is None:
        if os.path.exists("/data/timesheets/excel"):
            timesheet_dir = "/data/timesheets/excel"
        else:
            timesheet_dir = "timesheets/excel"
    """Process all Excel timesheets in the specified directory"""

    print("\n" + "█"*80)
    print("TIMESHEET TO SALARY SLIP PROCESSING SYSTEM")
    print("█"*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Timesheet Directory: {timesheet_dir}")
    print("█"*80 + "\n")

    # Check if directory exists
    if not os.path.exists(timesheet_dir):
        print(f"❌ Error: Directory not found: {timesheet_dir}")
        print("Please run generate_dummy_timesheets.py first to create test data.")
        return

    # Find all Excel files
    timesheet_files = glob.glob(os.path.join(timesheet_dir, "*.xlsx"))

    if not timesheet_files:
        print(f"❌ Error: No Excel files found in {timesheet_dir}")
        return

    print(f"📋 Found {len(timesheet_files)} timesheets to process\n")

    # Initialize workflow
    workflow = TimesheetWorkflow()

    # Process each timesheet
    results = []
    successful = 0
    failed = 0

    for idx, timesheet_file in enumerate(timesheet_files, 1):
        print(f"\n{'='*80}")
        print(f"Processing {idx}/{len(timesheet_files)}")
        print(f"{'='*80}\n")

        # Process the timesheet
        result = workflow.process_timesheet(timesheet_file)
        results.append({
            "file": os.path.basename(timesheet_file),
            "status": result["workflow_status"],
            "salary_slip": result.get("salary_slip_path"),
            "employee_name": result["timesheet_data"].employee.name if result["timesheet_data"] else "N/A",
            "net_salary": result["salary_calculation"].net_salary if result["salary_calculation"] else 0
        })

        if result["workflow_status"] == "completed":
            successful += 1
        else:
            failed += 1

    # Print final summary
    print_final_summary(results, successful, failed)


def print_final_summary(results, successful, failed):
    """Print comprehensive final summary"""
    print("\n\n" + "█"*80)
    print("FINAL PROCESSING SUMMARY")
    print("█"*80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nTotal Timesheets Processed: {len(results)}")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print("\n" + "-"*80)
    print("Detailed Results:")
    print("-"*80)

    for idx, result in enumerate(results, 1):
        status_icon = "✓" if result["status"] == "completed" else "✗"
        print(f"\n{idx}. {status_icon} {result['employee_name']}")
        print(f"   File: {result['file']}")
        print(f"   Status: {result['status']}")

        if result["status"] == "completed":
            print(f"   Net Salary: ${result['net_salary']:,.2f}")
            print(f"   Salary Slip: {os.path.basename(result['salary_slip'])}")

    if successful > 0:
        print("\n" + "="*80)
        print("✓ SALARY SLIPS GENERATED SUCCESSFULLY!")
        print("="*80)
        print(f"Location: salary_slips/")
        print(f"Total Files: {successful}")

        # Calculate total payroll
        total_payroll = sum(r["net_salary"] for r in results if r["status"] == "completed")
        print(f"\n💰 Total Payroll: ${total_payroll:,.2f}")

    print("\n")


def process_single_timesheet(timesheet_path: str):
    """Process a single timesheet file"""
    print("\n" + "█"*80)
    print("TIMESHEET TO SALARY SLIP PROCESSING SYSTEM")
    print("█"*80)
    print(f"Processing single timesheet: {timesheet_path}")
    print("█"*80 + "\n")

    if not os.path.exists(timesheet_path):
        print(f"❌ Error: File not found: {timesheet_path}")
        return

    # Initialize workflow
    workflow = TimesheetWorkflow()

    # Process the timesheet
    result = workflow.process_timesheet(timesheet_path)

    return result


if __name__ == "__main__":
    import sys

    # Check command line arguments
    if len(sys.argv) > 1:
        # Process single file
        timesheet_file = sys.argv[1]
        process_single_timesheet(timesheet_file)
    else:
        # Process all timesheets in default directory
        process_all_timesheets()
