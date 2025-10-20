"use client";

import { useState, useCallback } from "react";
import axios from "axios";

interface TimesheetUploadProps {
  onUploadSuccess?: () => void;
}

export default function TimesheetUpload({ onUploadSuccess }: TimesheetUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.name.endsWith(".xlsx")) {
      setFile(droppedFile);
      setMessage(null);
    } else {
      setMessage({ type: "error", text: "Please upload an Excel file (.xlsx)" });
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.name.endsWith(".xlsx")) {
      setFile(selectedFile);
      setMessage(null);
    } else {
      setMessage({ type: "error", text: "Please upload an Excel file (.xlsx)" });
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage({ type: "error", text: "Please select a file first" });
      return;
    }

    setUploading(true);
    setMessage(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post("/api/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setMessage({ type: "success", text: response.data.message });
      setFile(null);
      
      await handleProcess();
      
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Upload failed. Please try again.",
      });
    } finally {
      setUploading(false);
    }
  };

  const handleProcess = async () => {
    setProcessing(true);
    setMessage(null);

    try {
      const response = await axios.post("/api/process");
      setMessage({
        type: "success",
        text: response.data.message,
      });
      
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Processing failed. Please try again.",
      });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
        Upload Timesheet
      </h2>

      <div
        className={"border-2 border-dashed rounded-lg p-8 text-center transition-colors " + (dragActive ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" : "border-gray-300 dark:border-gray-600")}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center justify-center space-y-3">
          <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <div>
            <label htmlFor="file-upload" className="cursor-pointer text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium">
              Click to upload
            </label>
            <span className="text-gray-500 dark:text-gray-400"> or drag and drop</span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">Excel files only (.xlsx)</p>
          <input id="file-upload" type="file" className="hidden" accept=".xlsx" onChange={handleFileChange} />
        </div>
      </div>

      {file && (
        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm text-gray-700 dark:text-gray-300">{file.name}</span>
          </div>
          <button onClick={() => setFile(null)} className="text-red-500 hover:text-red-700 text-sm">
            Remove
          </button>
        </div>
      )}

      {message && (
        <div className={"mt-4 p-3 rounded-lg " + (message.type === "success" ? "bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200" : "bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200")}>
          {message.text}
        </div>
      )}

      <button onClick={handleUpload} disabled={!file || uploading || processing} className="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition-colors">
        {uploading ? "Uploading..." : processing ? "Processing..." : "Upload & Process Timesheet"}
      </button>

      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          <strong>Note:</strong> Upload Excel timesheets (.xlsx). The system will automatically parse data, calculate salaries, and generate PDF salary slips.
        </p>
      </div>
    </div>
  );
}
