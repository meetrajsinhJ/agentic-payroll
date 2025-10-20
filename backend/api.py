"""
FastAPI Backend for Agentic Payroll System
Provides REST API endpoints for frontend integration
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow import create_workflow
from models import AgentState

app = FastAPI(title="Agentic Payroll API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TIMESHEET_DIR = Path("timesheets/excel")
SALARY_SLIP_DIR = Path("salary_slips")

TIMESHEET_DIR.mkdir(parents=True, exist_ok=True)
SALARY_SLIP_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
async def root():
    return {
        "message": "Agentic AI Payroll System API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "process": "/api/process",
            "salary_slips": "/api/salary-slips",
            "download": "/api/salary-slips/{filename}"
        }
    }


@app.post("/api/upload")
async def upload_timesheet(file: UploadFile = File(...)):
    """Upload a timesheet Excel file"""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx) are allowed")
    
    try:
        file_path = TIMESHEET_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "path": str(file_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/process")
async def process_timesheets():
    """Process all timesheets and generate salary slips"""
    try:
        timesheet_files = list(TIMESHEET_DIR.glob("*.xlsx"))
        
        if not timesheet_files:
            return {
                "message": "No timesheets found to process",
                "total_processed": 0,
                "successful": 0,
                "failed": 0
            }
        
        workflow = create_workflow()
        successful = 0
        failed = 0
        results = []
        
        for timesheet_file in timesheet_files:
            try:
                initial_state = AgentState(
                    timesheet_file_path=str(timesheet_file),
                    timesheet_data=None,
                    extraction_status="pending",
                    calculation_status="pending",
                    pdf_generation_status="pending",
                    error_message=None
                )
                
                final_state = workflow.invoke(initial_state)
                
                if final_state.get("pdf_generation_status") == "success":
                    successful += 1
                    results.append({
                        "file": timesheet_file.name,
                        "status": "success"
                    })
                else:
                    failed += 1
                    results.append({
                        "file": timesheet_file.name,
                        "status": "failed",
                        "error": final_state.get("error_message")
                    })
                    
            except Exception as e:
                failed += 1
                results.append({
                    "file": timesheet_file.name,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "message": f"Processed {len(timesheet_files)} timesheets: {successful} successful, {failed} failed",
            "total_processed": len(timesheet_files),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/api/salary-slips")
async def list_salary_slips():
    """List all generated salary slips"""
    try:
        salary_slips = []
        
        for pdf_file in SALARY_SLIP_DIR.glob("*.pdf"):
            stat = pdf_file.stat()
            parts = pdf_file.stem.split("_")
            
            employee_id = parts[0] if parts else "Unknown"
            employee_name = " ".join(parts[1:-2]) if len(parts) > 2 else "Unknown"
            
            salary_slips.append({
                "filename": pdf_file.name,
                "employee_id": employee_id,
                "employee_name": employee_name,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size": stat.st_size
            })
        
        salary_slips.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "total": len(salary_slips),
            "salary_slips": salary_slips
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list salary slips: {str(e)}")


@app.get("/api/salary-slips/{filename}")
async def download_salary_slip(filename: str):
    """Download a specific salary slip PDF"""
    file_path = SALARY_SLIP_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Salary slip not found")
    
    if not file_path.is_file() or not file_path.suffix == ".pdf":
        raise HTTPException(status_code=400, detail="Invalid file")
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename
    )


@app.delete("/api/salary-slips/{filename}")
async def delete_salary_slip(filename: str):
    """Delete a specific salary slip"""
    file_path = SALARY_SLIP_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Salary slip not found")
    
    try:
        file_path.unlink()
        return {"message": "Salary slip deleted successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
