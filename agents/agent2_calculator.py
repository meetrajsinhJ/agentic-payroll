"""
Agent 2: Wage Calculator & Tax Processor Agent
Calculates gross salary, deductions, and net salary
"""
from datetime import datetime
from typing import Dict
from models import TimesheetData, SalaryCalculation, GrossSalary, Deductions


class WageCalculatorAgent:
    """Agent responsible for calculating wages and processing taxes"""

    def __init__(self):
        self.name = "Wage Calculator Agent"

        # Tax brackets (simplified US federal tax for demonstration)
        self.tax_brackets = [
            {"limit": 1000, "rate": 0.10},   # 10% up to $1000
            {"limit": 3000, "rate": 0.12},   # 12% from $1000 to $3000
            {"limit": 5000, "rate": 0.22},   # 22% from $3000 to $5000
            {"limit": float('inf'), "rate": 0.24}  # 24% above $5000
        ]

        # Standard deduction rates
        self.social_security_rate = 0.062  # 6.2%
        self.medicare_rate = 0.0145       # 1.45%
        self.insurance_flat = 100.0       # $100 flat rate
        self.provident_fund_rate = 0.05   # 5%

    def calculate_progressive_tax(self, gross_salary: float) -> float:
        """Calculate income tax using progressive tax brackets"""
        tax = 0.0
        previous_limit = 0

        for bracket in self.tax_brackets:
            if gross_salary > previous_limit:
                taxable_in_bracket = min(gross_salary - previous_limit, bracket["limit"] - previous_limit)
                tax += taxable_in_bracket * bracket["rate"]
                previous_limit = bracket["limit"]

                if gross_salary <= bracket["limit"]:
                    break

        return round(tax, 2)

    def calculate_gross_salary(self, timesheet_data: TimesheetData) -> GrossSalary:
        """Calculate gross salary from timesheet data"""
        print(f"\n[{self.name}] Calculating gross salary...")

        # Base pay: regular hours × hourly rate
        base_pay = timesheet_data.hours.regular_hours * timesheet_data.hourly_rate
        print(f"  - Base Pay: {timesheet_data.hours.regular_hours} hrs × ${timesheet_data.hourly_rate} = ${base_pay:.2f}")

        # Overtime pay: overtime hours × overtime rate
        overtime_pay = timesheet_data.hours.overtime_hours * timesheet_data.overtime_rate
        print(f"  - Overtime Pay: {timesheet_data.hours.overtime_hours} hrs × ${timesheet_data.overtime_rate} = ${overtime_pay:.2f}")

        # Holiday work: extra pay (1.5x)
        holiday_bonus = timesheet_data.hours.holiday_work_hours * timesheet_data.hourly_rate * 0.5
        print(f"  - Holiday Bonus: {timesheet_data.hours.holiday_work_hours} hrs × ${timesheet_data.hourly_rate} × 0.5 = ${holiday_bonus:.2f}")

        # Allowances (fixed for demonstration)
        allowances = 500.0  # Transportation, housing, etc.
        print(f"  - Allowances: ${allowances:.2f}")

        # Bonuses (performance-based - random for demo)
        bonuses = 0.0
        if timesheet_data.hours.regular_hours >= 160:  # Full month
            bonuses = 200.0
        print(f"  - Bonuses: ${bonuses:.2f}")

        # Total gross
        total_gross = base_pay + overtime_pay + holiday_bonus + allowances + bonuses
        print(f"  - Total Gross Salary: ${total_gross:.2f}")

        return GrossSalary(
            base_pay=round(base_pay, 2),
            overtime_pay=round(overtime_pay, 2),
            allowances=round(allowances + holiday_bonus, 2),
            bonuses=round(bonuses, 2),
            total_gross=round(total_gross, 2)
        )

    def calculate_deductions(self, gross_salary: float) -> Deductions:
        """Calculate all deductions from gross salary"""
        print(f"\n[{self.name}] Calculating deductions...")

        # Income tax (progressive)
        income_tax = self.calculate_progressive_tax(gross_salary)
        print(f"  - Income Tax: ${income_tax:.2f}")

        # Social Security (6.2% of gross, capped at $160,200 annually)
        social_security = gross_salary * self.social_security_rate
        print(f"  - Social Security: ${social_security:.2f}")

        # Medicare (1.45% of gross)
        medicare = gross_salary * self.medicare_rate

        # Total FICA (Social Security + Medicare)
        fica_total = social_security + medicare
        print(f"  - FICA (SS + Medicare): ${fica_total:.2f}")

        # Insurance (flat rate)
        insurance = self.insurance_flat
        print(f"  - Insurance: ${insurance:.2f}")

        # Provident Fund (5% of gross)
        provident_fund = gross_salary * self.provident_fund_rate
        print(f"  - Provident Fund: ${provident_fund:.2f}")

        # Other deductions
        other_deductions = 0.0

        # Total deductions
        total_deductions = income_tax + fica_total + insurance + provident_fund + other_deductions
        print(f"  - Total Deductions: ${total_deductions:.2f}")

        return Deductions(
            income_tax=round(income_tax, 2),
            social_security=round(fica_total, 2),
            insurance=round(insurance, 2),
            provident_fund=round(provident_fund, 2),
            other_deductions=round(other_deductions, 2),
            total_deductions=round(total_deductions, 2)
        )

    def process(self, timesheet_data: TimesheetData) -> Dict:
        """Main processing method - calculates complete salary breakdown"""
        print(f"\n{'='*60}")
        print(f"[{self.name}] Starting wage calculation")
        print(f"{'='*60}")

        try:
            # Calculate gross salary
            gross_salary = self.calculate_gross_salary(timesheet_data)

            # Calculate deductions
            deductions = self.calculate_deductions(gross_salary.total_gross)

            # Calculate net salary
            net_salary = gross_salary.total_gross - deductions.total_deductions
            print(f"\n[{self.name}] Net Salary: ${net_salary:.2f}")

            # Create salary calculation object
            salary_calculation = SalaryCalculation(
                employee_id=timesheet_data.employee.employee_id,
                gross_salary=gross_salary,
                deductions=deductions,
                net_salary=round(net_salary, 2),
                calculation_date=datetime.now().strftime("%Y-%m-%d")
            )

            print(f"\n[{self.name}] ✓ Calculation completed successfully!")

            return {
                "success": True,
                "data": salary_calculation,
                "error": None
            }

        except Exception as e:
            print(f"\n[{self.name}] ✗ Error during calculation: {str(e)}")
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }


# Test function
if __name__ == "__main__":
    from models import EmployeeInfo, WorkingHours, PayPeriod

    # Create sample timesheet data
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

    agent = WageCalculatorAgent()
    result = agent.process(sample_timesheet)

    if result["success"]:
        print("\n" + "="*60)
        print("CALCULATION SUMMARY")
        print("="*60)
        print(result["data"].model_dump_json(indent=2))
