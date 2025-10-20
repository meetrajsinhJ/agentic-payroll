"use client";

import { useState, useEffect } from "react";
import axios from "axios";

interface SalarySlip {
  filename: string;
  employee_id: string;
  employee_name: string;
  created_at: string;
  size: number;
}

export default function SalarySlipList() {
  const [slips, setSlips] = useState<SalarySlip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSalarySlips();
  }, []);

  const fetchSalarySlips = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get("/api/salary-slips");
      setSlips(response.data.salary_slips || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load salary slips");
    } finally {
      setLoading(false);
    }
  };

  const downloadSlip = async (filename: string) => {
    try {
      const response = await axios.get("/api/salary-slips/" + filename, {
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to download salary slip");
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Generated Salary Slips
        </h2>
        <button
          onClick={fetchSalarySlips}
          className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading salary slips...</p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 rounded-lg">
          {error}
        </div>
      )}

      {!loading && !error && slips.length === 0 && (
        <div className="text-center py-8">
          <svg className="w-16 h-16 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="mt-2 text-gray-600 dark:text-gray-400">No salary slips generated yet</p>
          <p className="text-sm text-gray-500 dark:text-gray-500">Upload a timesheet to get started</p>
        </div>
      )}

      {!loading && !error && slips.length > 0 && (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {slips.map((slip) => (
            <div
              key={slip.filename}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
            >
              <div className="flex items-center space-x-3 flex-1">
                <svg className="w-8 h-8 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                </svg>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {slip.employee_name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {slip.employee_id} • {new Date(slip.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <button
                onClick={() => downloadSlip(slip.filename)}
                className="ml-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
              >
                Download
              </button>
            </div>
          ))}
        </div>
      )}

      {!loading && !error && slips.length > 0 && (
        <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <p className="text-sm text-green-800 dark:text-green-200">
            <strong>{slips.length}</strong> salary slip{slips.length !== 1 ? "s" : ""} generated
          </p>
        </div>
      )}
    </div>
  );
}
