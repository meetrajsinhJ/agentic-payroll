import pandas as pd
from datetime import datetime, timedelta
import random
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import os

# Create output directories
os.makedirs("timesheets/excel", exist_ok=True)
os.makedirs("timesheets/pdf", exist_ok=True)

# Generate 10 hypothetical employees
employees = [
    {
        "employee_id": "EMP001",
        "name": "John Smith",
        "department": "Engineering",
        "designation": "Senior Software Engineer",
        "email": "john.smith@company.com",
        "bank_account": "1234567890",
        "hourly_rate": 45.00,
        "overtime_rate": 67.50
    },
    {
        "employee_id": "EMP002",
        "name": "Sarah Johnson",
        "department": "Marketing",
        "designation": "Marketing Manager",
        "email": "sarah.johnson@company.com",
        "bank_account": "2345678901",
        "hourly_rate": 42.00,
        "overtime_rate": 63.00
    },
    {
        "employee_id": "EMP003",
        "name": "Michael Chen",
        "department": "Engineering",
        "designation": "DevOps Engineer",
        "email": "michael.chen@company.com",
        "bank_account": "3456789012",
        "hourly_rate": 48.00,
        "overtime_rate": 72.00
    },
    {
        "employee_id": "EMP004",
        "name": "Emily Davis",
        "department": "Human Resources",
        "designation": "HR Specialist",
        "email": "emily.davis@company.com",
        "bank_account": "4567890123",
        "hourly_rate": 35.00,
        "overtime_rate": 52.50
    },
    {
        "employee_id": "EMP005",
        "name": "David Martinez",
        "department": "Sales",
        "designation": "Sales Executive",
        "email": "david.martinez@company.com",
        "bank_account": "5678901234",
        "hourly_rate": 38.00,
        "overtime_rate": 57.00
    },
    {
        "employee_id": "EMP006",
        "name": "Jessica Taylor",
        "department": "Finance",
        "designation": "Financial Analyst",
        "email": "jessica.taylor@company.com",
        "bank_account": "6789012345",
        "hourly_rate": 40.00,
        "overtime_rate": 60.00
    },
    {
        "employee_id": "EMP007",
        "name": "Robert Anderson",
        "department": "Engineering",
        "designation": "Junior Developer",
        "email": "robert.anderson@company.com",
        "bank_account": "7890123456",
        "hourly_rate": 32.00,
        "overtime_rate": 48.00
    },
    {
        "employee_id": "EMP008",
        "name": "Lisa Wong",
        "department": "Operations",
        "designation": "Operations Manager",
        "email": "lisa.wong@company.com",
        "bank_account": "8901234567",
        "hourly_rate": 44.00,
        "overtime_rate": 66.00
    },
    {
        "employee_id": "EMP009",
        "name": "James Brown",
        "department": "Customer Support",
        "designation": "Support Specialist",
        "email": "james.brown@company.com",
        "bank_account": "9012345678",
        "hourly_rate": 30.00,
        "overtime_rate": 45.00
    },
    {
        "employee_id": "EMP010",
        "name": "Maria Garcia",
        "department": "Design",
        "designation": "UI/UX Designer",
        "email": "maria.garcia@company.com",
        "bank_account": "0123456789",
        "hourly_rate": 41.00,
        "overtime_rate": 61.50
    }
]

# Pay period: October 2025
pay_period_start = datetime(2025, 10, 1)
pay_period_end = datetime(2025, 10, 31)

def generate_daily_attendance(employee):
    """Generate daily attendance for an employee for the month"""
    daily_records = []
    current_date = pay_period_start

    while current_date <= pay_period_end:
        day_of_week = current_date.weekday()

        # Skip weekends (Saturday=5, Sunday=6)
        if day_of_week >= 5:
            daily_records.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "day": current_date.strftime("%A"),
                "status": "Weekend",
                "hours_worked": 0,
                "overtime_hours": 0,
                "notes": ""
            })
        else:
            # Random scenarios for realistic data
            scenario = random.choices(
                ["normal", "overtime", "half_day", "leave", "holiday"],
                weights=[70, 15, 5, 8, 2],
                k=1
            )[0]

            if scenario == "normal":
                hours = 8
                overtime = 0
                status = "Present"
                notes = ""
            elif scenario == "overtime":
                hours = 8
                overtime = random.choice([1, 2, 3, 4])
                status = "Present"
                notes = f"Overtime: {overtime}h"
            elif scenario == "half_day":
                hours = 4
                overtime = 0
                status = "Half Day"
                notes = "Personal work"
            elif scenario == "leave":
                hours = 0
                overtime = 0
                status = "Leave"
                notes = random.choice(["Sick Leave", "Casual Leave", "Personal Leave"])
            else:  # holiday
                hours = 8
                overtime = 0
                status = "Holiday Work"
                notes = "Public Holiday - Extra Pay"

            daily_records.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "day": current_date.strftime("%A"),
                "status": status,
                "hours_worked": hours,
                "overtime_hours": overtime,
                "notes": notes
            })

        current_date += timedelta(days=1)

    return daily_records

def create_excel_timesheet(employee, daily_records):
    """Create Excel timesheet for an employee"""

    # Create employee info section
    employee_info = pd.DataFrame({
        "Field": ["Employee ID", "Name", "Department", "Designation", "Email", "Bank Account"],
        "Value": [
            employee["employee_id"],
            employee["name"],
            employee["department"],
            employee["designation"],
            employee["email"],
            employee["bank_account"]
        ]
    })

    # Create period info
    period_info = pd.DataFrame({
        "Field": ["Pay Period Start", "Pay Period End"],
        "Value": [pay_period_start.strftime("%Y-%m-%d"), pay_period_end.strftime("%Y-%m-%d")]
    })

    # Create daily attendance dataframe
    df_daily = pd.DataFrame(daily_records)

    # Calculate summary
    total_regular_hours = df_daily[df_daily['status'].isin(['Present', 'Half Day'])]['hours_worked'].sum()
    total_overtime_hours = df_daily['overtime_hours'].sum()
    total_leave_days = len(df_daily[df_daily['status'] == 'Leave'])
    holiday_work_hours = df_daily[df_daily['status'] == 'Holiday Work']['hours_worked'].sum()

    summary = pd.DataFrame({
        "Metric": [
            "Total Regular Hours",
            "Total Overtime Hours",
            "Total Leave Days",
            "Holiday Work Hours",
            "Hourly Rate ($)",
            "Overtime Rate ($)"
        ],
        "Value": [
            total_regular_hours,
            total_overtime_hours,
            total_leave_days,
            holiday_work_hours,
            employee["hourly_rate"],
            employee["overtime_rate"]
        ]
    })

    # Create Excel file with multiple sheets
    filename = f"timesheets/excel/{employee['employee_id']}_{employee['name'].replace(' ', '_')}_Timesheet_Oct2025.xlsx"

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Write employee info
        employee_info.to_excel(writer, sheet_name='Timesheet', index=False, startrow=0)

        # Write period info
        period_info.to_excel(writer, sheet_name='Timesheet', index=False, startrow=len(employee_info) + 2)

        # Write daily records
        df_daily.to_excel(writer, sheet_name='Timesheet', index=False, startrow=len(employee_info) + len(period_info) + 5)

        # Write summary
        summary.to_excel(writer, sheet_name='Timesheet', index=False, startrow=len(employee_info) + len(period_info) + len(df_daily) + 8)

    print(f"Created Excel: {filename}")
    return filename

def create_pdf_timesheet(employee, daily_records):
    """Create PDF timesheet for an employee"""

    filename = f"timesheets/pdf/{employee['employee_id']}_{employee['name'].replace(' ', '_')}_Timesheet_Oct2025.pdf"

    # Create PDF
    pdf = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph("EMPLOYEE TIMESHEET", title_style))
    story.append(Spacer(1, 0.3*inch))

    # Company info
    company_style = ParagraphStyle(
        'Company',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4a5568'),
        alignment=1
    )
    story.append(Paragraph("TechCorp Industries Inc.", company_style))
    story.append(Paragraph("123 Business Avenue, San Francisco, CA 94102", company_style))
    story.append(Paragraph("Phone: (555) 123-4567 | Email: payroll@techcorp.com", company_style))
    story.append(Spacer(1, 0.3*inch))

    # Employee Information Table
    employee_data = [
        ['EMPLOYEE INFORMATION', ''],
        ['Employee ID:', employee['employee_id']],
        ['Name:', employee['name']],
        ['Department:', employee['department']],
        ['Designation:', employee['designation']],
        ['Email:', employee['email']],
        ['Bank Account:', employee['bank_account']],
    ]

    employee_table = Table(employee_data, colWidths=[2*inch, 4*inch])
    employee_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
        ('SPAN', (0, 0), (-1, 0)),
    ]))
    story.append(employee_table)
    story.append(Spacer(1, 0.2*inch))

    # Pay Period
    period_data = [
        ['PAY PERIOD', ''],
        ['Start Date:', pay_period_start.strftime("%B %d, %Y")],
        ['End Date:', pay_period_end.strftime("%B %d, %Y")],
    ]

    period_table = Table(period_data, colWidths=[2*inch, 4*inch])
    period_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
        ('SPAN', (0, 0), (-1, 0)),
    ]))
    story.append(period_table)
    story.append(Spacer(1, 0.3*inch))

    # Daily Attendance - first 15 days for PDF (to fit on page)
    attendance_data = [['Date', 'Day', 'Status', 'Hours', 'OT', 'Notes']]

    for record in daily_records[:15]:  # Show first 15 days
        attendance_data.append([
            record['date'],
            record['day'][:3],  # Abbreviated day
            record['status'],
            str(record['hours_worked']),
            str(record['overtime_hours']),
            record['notes'][:20]  # Truncate notes
        ])

    attendance_table = Table(attendance_data, colWidths=[1*inch, 0.6*inch, 1*inch, 0.6*inch, 0.5*inch, 2.3*inch])
    attendance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
    ]))
    story.append(Paragraph("DAILY ATTENDANCE RECORD (First 15 Days)", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    story.append(attendance_table)
    story.append(Spacer(1, 0.3*inch))

    # Calculate summary
    df_daily = pd.DataFrame(daily_records)
    total_regular_hours = df_daily[df_daily['status'].isin(['Present', 'Half Day'])]['hours_worked'].sum()
    total_overtime_hours = df_daily['overtime_hours'].sum()
    total_leave_days = len(df_daily[df_daily['status'] == 'Leave'])
    holiday_work_hours = df_daily[df_daily['status'] == 'Holiday Work']['hours_worked'].sum()

    # Summary Table
    summary_data = [
        ['TIMESHEET SUMMARY', ''],
        ['Total Regular Hours:', f"{total_regular_hours} hrs"],
        ['Total Overtime Hours:', f"{total_overtime_hours} hrs"],
        ['Total Leave Days:', f"{total_leave_days} days"],
        ['Holiday Work Hours:', f"{holiday_work_hours} hrs"],
        ['Hourly Rate:', f"${employee['hourly_rate']:.2f}"],
        ['Overtime Rate:', f"${employee['overtime_rate']:.2f}"],
    ]

    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ebf8ff')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#4299e1')),
        ('SPAN', (0, 0), (-1, 0)),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.4*inch))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#718096'),
        alignment=1
    )
    story.append(Paragraph("This is a computer-generated timesheet. For complete daily records, please refer to the Excel version.", footer_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))

    # Build PDF
    pdf.build(story)

    print(f"Created PDF: {filename}")
    return filename

# Generate timesheets for all employees
print("Generating dummy timesheets for 10 employees...\n")

for employee in employees:
    print(f"Processing {employee['name']} ({employee['employee_id']})...")

    # Generate daily attendance
    daily_records = generate_daily_attendance(employee)

    # Create Excel timesheet
    create_excel_timesheet(employee, daily_records)

    # Create PDF timesheet
    create_pdf_timesheet(employee, daily_records)

    print(f"Completed {employee['name']}\n")

print("=" * 60)
print("All timesheets generated successfully!")
print(f"Excel files: timesheets/excel/")
print(f"PDF files: timesheets/pdf/")
print("=" * 60)
