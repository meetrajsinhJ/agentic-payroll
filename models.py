"""
Data models for the Timesheet to Salary Slip System
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class EmployeeInfo(BaseModel):
    """Employee information model"""
    employee_id: str
    name: str
    department: str
    designation: str
    email: str
    bank_account: str


class WorkingHours(BaseModel):
    """Working hours breakdown"""
    regular_hours: float = Field(description="Total regular working hours")
    overtime_hours: float = Field(description="Total overtime hours")
    leave_days: int = Field(description="Number of leave days taken")
    holiday_work_hours: float = Field(default=0, description="Hours worked on holidays")


class PayPeriod(BaseModel):
    """Pay period information"""
    start_date: str
    end_date: str


class TimesheetData(BaseModel):
    """Complete timesheet data extracted from input"""
    employee: EmployeeInfo
    period: PayPeriod
    hours: WorkingHours
    hourly_rate: Optional[float] = None
    overtime_rate: Optional[float] = None


class GrossSalary(BaseModel):
    """Gross salary breakdown"""
    base_pay: float
    overtime_pay: float
    allowances: float = Field(default=0, description="Additional allowances")
    bonuses: float = Field(default=0, description="Performance bonuses")
    total_gross: float


class Deductions(BaseModel):
    """Salary deductions breakdown"""
    income_tax: float
    social_security: float
    insurance: float = Field(default=0)
    provident_fund: float = Field(default=0)
    other_deductions: float = Field(default=0)
    total_deductions: float


class SalaryCalculation(BaseModel):
    """Complete salary calculation"""
    employee_id: str
    gross_salary: GrossSalary
    deductions: Deductions
    net_salary: float
    calculation_date: str


class SalarySlipData(BaseModel):
    """Complete data for salary slip generation"""
    employee: EmployeeInfo
    period: PayPeriod
    hours: WorkingHours
    salary: SalaryCalculation
    company_name: str = "TechCorp Industries Inc."
    company_address: str = "123 Business Avenue, San Francisco, CA 94102"


class AgentState(BaseModel):
    """State object passed between agents in LangGraph"""
    # Input
    timesheet_file_path: str

    # Agent 1 Output
    timesheet_data: Optional[TimesheetData] = None
    extraction_status: str = "pending"
    extraction_error: Optional[str] = None

    # Agent 2 Output
    salary_calculation: Optional[SalaryCalculation] = None
    calculation_status: str = "pending"
    calculation_error: Optional[str] = None

    # Agent 3 Output
    salary_slip_path: Optional[str] = None
    generation_status: str = "pending"
    generation_error: Optional[str] = None

    # Overall status
    workflow_status: str = "started"

    class Config:
        arbitrary_types_allowed = True
