"use client";

import { useState } from "react";
import TimesheetUpload from "@/components/TimesheetUpload";
import SalarySlipList from "@/components/SalarySlipList";

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-3">
            🤖 Agentic AI Payroll System
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Automated Timesheet Processing & Salary Slip Generation
          </p>
        </header>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-1">
            <TimesheetUpload onUploadSuccess={handleUploadSuccess} />
          </div>

          {/* Salary Slips Section */}
          <div className="lg:col-span-1">
            <SalarySlipList key={refreshKey} />
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-16 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>
            Powered by LangGraph Multi-Agent System | Built with Next.js & FastAPI
          </p>
        </footer>
      </div>
    </div>
  );
}
