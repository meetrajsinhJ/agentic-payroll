"""
LangGraph Workflow for Timesheet to Salary Slip System
Orchestrates the three agents in a sequential workflow
"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from agents.agent1_parser import TimesheetParserAgent
from agents.agent2_calculator import WageCalculatorAgent
from agents.agent3_pdf_generator import SalarySlipGeneratorAgent
from models import TimesheetData, SalaryCalculation


# Define the state that will be passed between agents
class WorkflowState(TypedDict):
    """State object passed between agents"""
    # Input
    timesheet_file_path: str

    # Agent 1 outputs
    timesheet_data: Optional[TimesheetData]
    extraction_status: str
    extraction_error: Optional[str]

    # Agent 2 outputs
    salary_calculation: Optional[SalaryCalculation]
    calculation_status: str
    calculation_error: Optional[str]

    # Agent 3 outputs
    salary_slip_path: Optional[str]
    generation_status: str
    generation_error: Optional[str]

    # Overall status
    workflow_status: str


class TimesheetWorkflow:
    """Main workflow orchestrator using LangGraph"""

    def __init__(self):
        self.parser_agent = TimesheetParserAgent()
        self.calculator_agent = WageCalculatorAgent()
        self.generator_agent = SalarySlipGeneratorAgent()

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def agent1_parse_timesheet(self, state: WorkflowState) -> WorkflowState:
        """Node: Agent 1 - Parse timesheet and extract data"""
        print("\n" + "="*80)
        print("STEP 1: TIMESHEET PARSING")
        print("="*80)

        result = self.parser_agent.process(state["timesheet_file_path"])

        if result["success"]:
            state["timesheet_data"] = result["data"]
            state["extraction_status"] = "success"
            state["extraction_error"] = None
        else:
            state["timesheet_data"] = None
            state["extraction_status"] = "failed"
            state["extraction_error"] = result["error"]
            state["workflow_status"] = "failed_at_parsing"

        return state

    def agent2_calculate_salary(self, state: WorkflowState) -> WorkflowState:
        """Node: Agent 2 - Calculate wages and deductions"""
        print("\n" + "="*80)
        print("STEP 2: SALARY CALCULATION")
        print("="*80)

        # Check if previous step was successful
        if state["extraction_status"] != "success":
            print("[Workflow] Skipping salary calculation due to parsing failure")
            state["calculation_status"] = "skipped"
            return state

        result = self.calculator_agent.process(state["timesheet_data"])

        if result["success"]:
            state["salary_calculation"] = result["data"]
            state["calculation_status"] = "success"
            state["calculation_error"] = None
        else:
            state["salary_calculation"] = None
            state["calculation_status"] = "failed"
            state["calculation_error"] = result["error"]
            state["workflow_status"] = "failed_at_calculation"

        return state

    def agent3_generate_pdf(self, state: WorkflowState) -> WorkflowState:
        """Node: Agent 3 - Generate salary slip PDF"""
        print("\n" + "="*80)
        print("STEP 3: PDF GENERATION")
        print("="*80)

        # Check if previous steps were successful
        if state["calculation_status"] != "success":
            print("[Workflow] Skipping PDF generation due to calculation failure")
            state["generation_status"] = "skipped"
            return state

        result = self.generator_agent.process(
            state["timesheet_data"],
            state["salary_calculation"]
        )

        if result["success"]:
            state["salary_slip_path"] = result["file_path"]
            state["generation_status"] = "success"
            state["generation_error"] = None
            state["workflow_status"] = "completed"
        else:
            state["salary_slip_path"] = None
            state["generation_status"] = "failed"
            state["generation_error"] = result["error"]
            state["workflow_status"] = "failed_at_generation"

        return state

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        # Create the graph
        workflow = StateGraph(WorkflowState)

        # Add nodes (agents)
        workflow.add_node("parse_timesheet", self.agent1_parse_timesheet)
        workflow.add_node("calculate_salary", self.agent2_calculate_salary)
        workflow.add_node("generate_pdf", self.agent3_generate_pdf)

        # Define edges (flow)
        workflow.set_entry_point("parse_timesheet")
        workflow.add_edge("parse_timesheet", "calculate_salary")
        workflow.add_edge("calculate_salary", "generate_pdf")
        workflow.add_edge("generate_pdf", END)

        # Compile the graph
        return workflow.compile()

    def process_timesheet(self, timesheet_file_path: str) -> WorkflowState:
        """Process a single timesheet through the complete workflow"""
        print("\n" + "█"*80)
        print("TIMESHEET TO SALARY SLIP WORKFLOW")
        print(f"Processing: {timesheet_file_path}")
        print("█"*80)

        # Initialize state
        initial_state: WorkflowState = {
            "timesheet_file_path": timesheet_file_path,
            "timesheet_data": None,
            "extraction_status": "pending",
            "extraction_error": None,
            "salary_calculation": None,
            "calculation_status": "pending",
            "calculation_error": None,
            "salary_slip_path": None,
            "generation_status": "pending",
            "generation_error": None,
            "workflow_status": "started"
        }

        # Run the workflow
        final_state = self.workflow.invoke(initial_state)

        # Print summary
        self._print_summary(final_state)

        return final_state

    def _print_summary(self, state: WorkflowState):
        """Print workflow execution summary"""
        print("\n" + "█"*80)
        print("WORKFLOW EXECUTION SUMMARY")
        print("█"*80)

        print(f"\n📄 Input File: {state['timesheet_file_path']}")
        print(f"\n🔄 Workflow Status: {state['workflow_status'].upper()}")

        print("\n" + "-"*80)
        print("Agent Statuses:")
        print("-"*80)

        # Agent 1
        status_icon = "✓" if state["extraction_status"] == "success" else "✗"
        print(f"{status_icon} Agent 1 (Parser): {state['extraction_status'].upper()}")
        if state["extraction_error"]:
            print(f"  Error: {state['extraction_error']}")

        # Agent 2
        status_icon = "✓" if state["calculation_status"] == "success" else "✗" if state["calculation_status"] == "failed" else "⊘"
        print(f"{status_icon} Agent 2 (Calculator): {state['calculation_status'].upper()}")
        if state["calculation_error"]:
            print(f"  Error: {state['calculation_error']}")

        # Agent 3
        status_icon = "✓" if state["generation_status"] == "success" else "✗" if state["generation_status"] == "failed" else "⊘"
        print(f"{status_icon} Agent 3 (PDF Generator): {state['generation_status'].upper()}")
        if state["generation_error"]:
            print(f"  Error: {state['generation_error']}")

        if state["workflow_status"] == "completed":
            print("\n" + "="*80)
            print(f"✓ SUCCESS! Salary slip generated: {state['salary_slip_path']}")
            print("="*80)

            # Print salary details
            if state["salary_calculation"]:
                calc = state["salary_calculation"]
                print(f"\n💰 Salary Summary for {state['timesheet_data'].employee.name}:")
                print(f"   Gross Salary: ${calc.gross_salary.total_gross:,.2f}")
                print(f"   Deductions:   ${calc.deductions.total_deductions:,.2f}")
                print(f"   Net Salary:   ${calc.net_salary:,.2f}")
        else:
            print("\n" + "="*80)
            print(f"✗ WORKFLOW FAILED: {state['workflow_status']}")
            print("="*80)

        print("\n")


# Test the workflow
if __name__ == "__main__":
    import os

    workflow = TimesheetWorkflow()

    # Test with a sample timesheet
    test_file = "timesheets/excel/EMP001_John_Smith_Timesheet_Oct2025.xlsx"

    if os.path.exists(test_file):
        result = workflow.process_timesheet(test_file)
    else:
        print(f"Error: Test file not found: {test_file}")
        print("Please run generate_dummy_timesheets.py first to create test data.")
