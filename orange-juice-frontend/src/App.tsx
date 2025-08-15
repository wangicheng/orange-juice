import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import apiClient from './api';
import CreateAccounts from './components/CreateAccounts';
import CrawlTestCases from './components/CrawlTestCases';
import TaskStatus from './components/TaskStatus';
import ProblemList from './components/ProblemList';
import ProblemTestCases from './components/ProblemTestCases';

function App() {
  // 在元件掛載時執行一次，以確保 CSRF cookie 被設定
  useEffect(() => {
    const fetchCsrfToken = async () => {
      try {
        // 只需要發送請求即可，Django 會自動設置 cookie
        await apiClient.get('/api/csrf-cookie/'); 
        console.log('CSRF cookie should be set.');
      } catch (error) {
        console.error('Failed to fetch CSRF token:', error);
      }
    };

    fetchCsrfToken();
  }, []); // 空依賴陣列確保只執行一次

  const getLinkClass = ({ isActive }: { isActive: boolean }): string => {
    const baseClasses = "block px-4 py-2 text-gray-300 rounded-md hover:bg-gray-700 hover:text-white";
    return isActive ? `${baseClasses} bg-gray-900 text-white` : baseClasses;
  };

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <aside className="w-64 bg-gray-800 text-white flex flex-col">
          <div className="p-4 text-2xl font-bold border-b border-gray-700">
            Orange Juice
          </div>
          <nav className="flex-1 p-4 space-y-2">
            <NavLink to="/create-accounts" className={getLinkClass}>Create Accounts</NavLink>
            <NavLink to="/crawl-testcases" className={getLinkClass}>Crawl Test Cases</NavLink>
            <NavLink to="/problems" className={getLinkClass}>Problems</NavLink>
          </nav>
        </aside>
        <main className="flex-1 p-10 overflow-auto">
          <Routes>
            <Route path="/create-accounts" element={<CreateAccounts />} />
            <Route path="/crawl-testcases" element={<CrawlTestCases />} />
            <Route path="/tasks/:taskId" element={<TaskStatus />} />
            <Route path="/problems" element={<ProblemList />} />
            <Route path="/problems/:problemId/testcases" element={<ProblemTestCases />} />
            <Route path="/" element={
              <div className="text-center">
                <h1 className="text-3xl font-bold">Welcome to Orange Juice</h1>
                <p className="mt-2 text-gray-600">Select a task from the sidebar to get started.</p>
              </div>
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;