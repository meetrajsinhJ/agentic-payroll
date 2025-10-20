"""
Agent 3: Salary Slip PDF Generator Agent
Generates professional PDF salary slips
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from datetime import datetime
import os
from typing import Dict
from models import SalarySlipData, TimesheetData, SalaryCalculation


class SalarySlipGeneratorAgent:
    """Agent responsible for generating PDF salary slips"""

    def __init__(self, output_dir: str = None):
        self.name = "Salary Slip Generator Agent"
        # Auto-detect path: /data/salary_slips/ in K8s, ./salary_slips locally
        if output_dir is None:
            if os.path.exists("/data"):
                output_dir = "/data/salary_slips"
            else:
                output_dir = "salary_slips"
        self.output_dir = output_dir

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_filename(self, employee_id: str, employee_name: str, period_end: str) -> str:
        """Generate filename for the salary slip"""
        clean_name = employee_name.replace(" ", "_")
        period = period_end.replace("-", "")
        filename = f"{employee_id}_{clean_name}_SalarySlip_{period}.pdf"
        return os.path.join(self.output_dir, filename)

    def create_salary_slip_pdf(self, slip_data: SalarySlipData, output_path: str) -> bool:
        """Create the PDF salary slip"""
        print(f"\n[{self.name}] Generating PDF salary slip...")

        try:
            # Create PDF document
            pdf = SimpleDocTemplate(output_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=26,
                textColor=colors.HexColor('#1a365d'),
                spaceAfter=20,
                alignment=1  # Center
            )
            story.append(Paragraph("SALARY SLIP", title_style))
            story.append(Spacer(1, 0.2*inch))

            # Company info
            company_style = ParagraphStyle(
                'Company',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#4a5568'),
                alignment=1
            )
            story.append(Paragraph(slip_data.company_name, company_style))
            story.append(Paragraph(slip_data.company_address, company_style))
            story.append(Spacer(1, 0.3*inch))

            # Pay Period
            period_style = ParagraphStyle(
                'Period',
                parent=styles['Normal'],
                fontSize=11,
                alignment=1,
                spaceAfter=10
            )
            period_text = f"<b>Pay Period:</b> {slip_data.period.start_date} to {slip_data.period.end_date}"
            story.append(Paragraph(period_text, period_style))
            story.append(Spacer(1, 0.2*inch))

            # Employee Information
            emp_data = [
                ['EMPLOYEE INFORMATION', '', '', ''],
                ['Employee ID:', slip_data.employee.employee_id, 'Department:', slip_data.employee.department],
                ['Name:', slip_data.employee.name, 'Designation:', slip_data.employee.designation],
                ['Email:', slip_data.employee.email, 'Bank Account:', slip_data.employee.bank_account],
            ]

            emp_table = Table(emp_data, colWidths=[1.3*inch, 2*inch, 1.3*inch, 2*inch])
            emp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
                ('SPAN', (0, 0), (-1, 0)),
            ]))
            story.append(emp_table)
            story.append(Spacer(1, 0.3*inch))

            # Working Hours Summary
            hours_data = [
                ['WORKING HOURS SUMMARY', ''],
                ['Regular Hours:', f"{slip_data.hours.regular_hours} hrs"],
                ['Overtime Hours:', f"{slip_data.hours.overtime_hours} hrs"],
                ['Leave Days:', f"{slip_data.hours.leave_days} days"],
                ['Holiday Work Hours:', f"{slip_data.hours.holiday_work_hours} hrs"],
            ]

            hours_table = Table(hours_data, colWidths=[3*inch, 2*inch])
            hours_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ebf8ff')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#4299e1')),
                ('SPAN', (0, 0), (-1, 0)),
            ]))
            story.append(hours_table)
            story.append(Spacer(1, 0.3*inch))

            # Earnings Breakdown
            earnings_data = [
                ['EARNINGS', 'AMOUNT'],
                ['Base Pay', f"${slip_data.salary.gross_salary.base_pay:.2f}"],
                ['Overtime Pay', f"${slip_data.salary.gross_salary.overtime_pay:.2f}"],
                ['Allowances', f"${slip_data.salary.gross_salary.allowances:.2f}"],
                ['Bonuses', f"${slip_data.salary.gross_salary.bonuses:.2f}"],
                ['GROSS SALARY', f"${slip_data.salary.gross_salary.total_gross:.2f}"],
            ]

            earnings_table = Table(earnings_data, colWidths=[3*inch, 2*inch])
            earnings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5016')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f0fff4')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#68d391')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#9ae6b4')),
            ]))
            story.append(earnings_table)
            story.append(Spacer(1, 0.2*inch))

            # Deductions Breakdown
            deductions_data = [
                ['DEDUCTIONS', 'AMOUNT'],
                ['Income Tax', f"${slip_data.salary.deductions.income_tax:.2f}"],
                ['Social Security & Medicare', f"${slip_data.salary.deductions.social_security:.2f}"],
                ['Insurance', f"${slip_data.salary.deductions.insurance:.2f}"],
                ['Provident Fund', f"${slip_data.salary.deductions.provident_fund:.2f}"],
                ['Other Deductions', f"${slip_data.salary.deductions.other_deductions:.2f}"],
                ['TOTAL DEDUCTIONS', f"${slip_data.salary.deductions.total_deductions:.2f}"],
            ]

            deductions_table = Table(deductions_data, colWidths=[3*inch, 2*inch])
            deductions_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#742a2a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#fff5f5')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fc8181')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#feb2b2')),
            ]))
            story.append(deductions_table)
            story.append(Spacer(1, 0.3*inch))

            # NET SALARY (Highlighted)
            net_data = [
                ['NET SALARY (TAKE HOME)', f"${slip_data.salary.net_salary:.2f}"],
            ]

            net_table = Table(net_data, colWidths=[3*inch, 2*inch])
            net_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('TOPPADDING', (0, 0), (-1, 0), 15),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
                ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#2c5282')),
            ]))
            story.append(net_table)
            story.append(Spacer(1, 0.4*inch))

            # Footer
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#718096'),
                alignment=1
            )
            story.append(Paragraph("This is a computer-generated salary slip and does not require a signature.", footer_style))
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("For any queries, please contact the HR Department.", footer_style))

            # Build PDF
            pdf.build(story)
            print(f"[{self.name}] ✓ PDF generated successfully: {output_path}")

            return True

        except Exception as e:
            print(f"[{self.name}] ✗ Error generating PDF: {str(e)}")
            return False

    def process(self, timesheet_data: TimesheetData, salary_calculation: SalaryCalculation) -> Dict:
        """Main processing method - generates salary slip PDF"""
        print(f"\n{'='*60}")
        print(f"[{self.name}] Starting PDF generation")
        print(f"{'='*60}")

        try:
            # Create salary slip data object
            slip_data = SalarySlipData(
                employee=timesheet_data.employee,
                period=timesheet_data.period,
                hours=timesheet_data.hours,
                salary=salary_calculation
            )

            # Generate filename
            output_path = self.generate_filename(
                timesheet_data.employee.employee_id,
                timesheet_data.employee.name,
                timesheet_data.period.end_date
            )

            # Create PDF
            success = self.create_salary_slip_pdf(slip_data, output_path)

            if success:
                return {
                    "success": True,
                    "file_path": output_path,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "file_path": None,
                    "error": "Failed to generate PDF"
                }

        except Exception as e:
            print(f"\n[{self.name}] ✗ Error during PDF generation: {str(e)}")
            return {
                "success": False,
                "file_path": None,
                "error": str(e)
            }


# Test function
if __name__ == "__main__":
    from models import EmployeeInfo, WorkingHours, PayPeriod, GrossSalary, Deductions

    # Create sample data
    sample_timesheet = TimesheetData(
        employee=EmployeeInfo(
            employee_id="EMP001",
            name="John Smith",
            department="Engineering",
            designation="Senior Software Engineer",
            email="john.smith@company.com",
            bank_account="1234567890"
        ),
        period=PayPeriod(
            start_date="2025-10-01",
            end_date="2025-10-31"
        ),
        hours=WorkingHours(
            regular_hours=160.0,
            overtime_hours=12.0,
            leave_days=2,
            holiday_work_hours=8.0
        ),
        hourly_rate=45.0,
        overtime_rate=67.50
    )

    sample_calculation = SalaryCalculation(
        employee_id="EMP001",
        gross_salary=GrossSalary(
            base_pay=7200.00,
            overtime_pay=810.00,
            allowances=680.00,
            bonuses=200.00,
            total_gross=8890.00
        ),
        deductions=Deductions(
            income_tax=1912.80,
            social_security=680.51,
            insurance=100.00,
            provident_fund=444.50,
            other_deductions=0.00,
            total_deductions=3137.81
        ),
        net_salary=5752.19,
        calculation_date="2025-10-20"
    )

    agent = SalarySlipGeneratorAgent()
    result = agent.process(sample_timesheet, sample_calculation)

    if result["success"]:
        print(f"\n✓ Salary slip generated: {result['file_path']}")
    else:
        print(f"\n✗ Failed to generate salary slip: {result['error']}")
