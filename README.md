# Agentic AI Timesheet to Salary Slip System

[![CI/CD Pipeline](https://github.com/meetrajsinhJ/agentic-payroll/actions/workflows/ci-cd.yaml/badge.svg)](https://github.com/meetrajsinhJ/agentic-payroll/actions/workflows/ci-cd.yaml)
[![Docker](https://img.shields.io/badge/docker-ghcr.io-blue)](https://github.com/meetrajsinhJ/agentic-payroll/pkgs/container/agentic-payroll)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-brightgreen)](./k8s/)

An intelligent multi-agent system that automates the process of converting employee timesheets into professional salary slips using LangGraph.

## System Architecture

```
Input (Timesheet) → Agent 1 → Agent 2 → Agent 3 → Output (Salary Slip PDF)
                      ↓          ↓          ↓
                   Parse      Calculate   Generate
                    Data       Salary       PDF
```

### Agents

1. **Agent 1: Timesheet Parser**
   - Extracts employee information from Excel/PDF timesheets
   - Parses working hours (regular, overtime, leave days)
   - Validates and structures data

2. **Agent 2: Wage Calculator**
   - Calculates gross salary (base pay, overtime, allowances, bonuses)
   - Processes deductions (tax, social security, insurance, provident fund)
   - Computes net salary

3. **Agent 3: PDF Generator**
   - Creates professional salary slip PDFs
   - Includes company branding and detailed breakdowns
   - Generates timestamped documents

## Features

### Core Functionality
- ✅ Multi-agent workflow orchestration using LangGraph
- ✅ Automatic timesheet parsing (Excel format)
- ✅ Progressive tax calculation
- ✅ Comprehensive deduction processing
- ✅ Professional PDF salary slip generation
- ✅ Batch processing support
- ✅ Error handling and validation
- ✅ Detailed logging and reporting

### DevOps & Deployment
- ✅ Docker containerization
- ✅ Kubernetes deployment (CronJob + Manual Job)
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Automated Docker image builds
- ✅ Security scanning with Trivy
- ✅ GitHub Container Registry integration

## Quick Start

### Option 1: Run Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate test timesheets:
```bash
python generate_dummy_timesheets.py
```

3. Process timesheets:
```bash
python main.py
```

### Option 2: Run with Docker

```bash
# Build image
docker build -t agentic-payroll:latest .

# Run processing
docker run --rm \
  -v $(pwd)/timesheets:/app/timesheets \
  -v $(pwd)/salary_slips:/app/salary_slips \
  agentic-payroll:latest
```

### Option 3: Deploy to Kubernetes

See [DOCKER_DESKTOP_K8S_DEPLOYMENT_GUIDE.md](./DOCKER_DESKTOP_K8S_DEPLOYMENT_GUIDE.md) for complete instructions.

```bash
# Quick deployment
kubectl apply -f k8s/
```

## Usage

### Generate Dummy Timesheets (for testing)

```bash
python generate_dummy_timesheets.py
```

This generates timesheets for 10 hypothetical employees in both Excel and PDF formats.

### Process All Timesheets

```bash
python main.py
```

Processes all Excel timesheets in the `timesheets/excel/` directory and generates salary slips in `salary_slips/`.

### Process Single Timesheet

```bash
python main.py path/to/timesheet.xlsx
```

### Test Individual Agents

```bash
# Test Agent 1
cd agents
python agent1_parser.py

# Test Agent 2
python agent2_calculator.py

# Test Agent 3
python agent3_pdf_generator.py
```

### Test Workflow

```bash
python workflow.py
```

## Project Structure

```
agentic/
├── agents/
│   ├── agent1_parser.py          # Timesheet Parser Agent
│   ├── agent2_calculator.py      # Wage Calculator Agent
│   └── agent3_pdf_generator.py   # PDF Generator Agent
├── timesheets/
│   ├── excel/                    # Input Excel timesheets
│   └── pdf/                      # Input PDF timesheets
├── salary_slips/                 # Generated salary slip PDFs
├── models.py                     # Pydantic data models
├── workflow.py                   # LangGraph workflow orchestration
├── main.py                       # Main execution script
├── generate_dummy_timesheets.py  # Test data generator
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Data Models

### Input (Timesheet)
- Employee ID, Name, Department, Designation
- Email, Bank Account
- Working Hours (Regular, Overtime, Leave Days, Holiday Work)
- Hourly Rates

### Output (Salary Slip)
- Employee Information
- Pay Period
- Working Hours Summary
- Earnings Breakdown
- Deductions Breakdown
- Net Salary

## Tax and Deduction Calculation

### Tax Brackets (Simplified)
- 10% up to $1,000
- 12% from $1,000 to $3,000
- 22% from $3,000 to $5,000
- 24% above $5,000

### Deductions
- **Income Tax**: Progressive based on brackets
- **Social Security & Medicare**: 6.2% + 1.45% = 7.65%
- **Insurance**: $100 flat rate
- **Provident Fund**: 5% of gross salary

## Sample Output

The system generates professional PDF salary slips with:
- Company header and branding
- Employee details
- Pay period information
- Working hours summary
- Detailed earnings breakdown
- Comprehensive deductions
- Highlighted net salary
- Timestamp and footer

## Error Handling

The system includes robust error handling:
- File validation
- Data extraction error recovery
- Calculation error logging
- PDF generation error handling
- Workflow status tracking

## Future Enhancements

- [ ] PDF timesheet parsing using OCR
- [ ] Multiple currency support
- [ ] Configurable tax rules by jurisdiction
- [ ] Email integration for automatic delivery
- [ ] Digital signature support
- [ ] Historical payroll tracking
- [ ] Employee portal integration
- [ ] Multi-language support

## Technologies Used

### Core Technologies
- **LangGraph**: Workflow orchestration
- **Pydantic**: Data validation and modeling
- **Pandas**: Excel data processing
- **ReportLab**: PDF generation
- **Python 3.9+**: Core programming language

### DevOps & Infrastructure
- **Docker**: Containerization
- **Kubernetes**: Orchestration (CronJobs, Jobs, PV/PVC)
- **GitHub Actions**: CI/CD automation
- **GitHub Container Registry**: Docker image storage
- **Trivy**: Security vulnerability scanning

## Documentation

- [Docker Desktop Kubernetes Deployment Guide](./DOCKER_DESKTOP_K8S_DEPLOYMENT_GUIDE.md) - Complete K8s deployment with troubleshooting
- [Minikube Troubleshooting Guide](./MINIKUBE_TROUBLESHOOTING.md) - Volume mounting issues and solutions
- [CI/CD Setup Guide](./CI_CD_SETUP_GUIDE.md) - GitHub Actions pipeline configuration
- [Quick Start Guide](./QUICKSTART.md) - 10-minute deployment guide

## Performance

**Latest Successful Run:**
- Total Employees Processed: 10
- Success Rate: 100% (10/10)
- Processing Time: ~9 seconds
- Total Payroll: $50,876.58
- Container Image Size: 697MB
- Resource Usage: 500m CPU, 512Mi RAM

## License

MIT License

## Author

AIWF Project - Agentic AI System
