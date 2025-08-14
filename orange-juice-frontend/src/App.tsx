import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import CreateAccounts from './components/CreateAccounts';
import CrawlTestCases from './components/CrawlTestCases';

function App() {
  const getLinkClass = ({ isActive }: { isActive: boolean }): string => {
    const baseClasses = "block px-4 py-2 text-gray-300 rounded-md hover:bg-gray-700 hover:text-white";
    return isActive ? `${baseClasses} bg-gray-900 text-white` : baseClasses;
  };

  return (
    <Router>
      <div className="flex h-screen bg-gray-100 font-sans">
        <nav className="w-64 bg-gray-800 text-white p-5">
          <h1 className="text-2xl font-bold mb-10">Orange Juice</h1>
          <ul>
            <li className="mb-2">
              <NavLink to="/create-accounts" className={getLinkClass}>
                Create Accounts
              </NavLink>
            </li>
            <li>
              <NavLink to="/crawl-test-cases" className={getLinkClass}>
                Crawl Test Cases
              </NavLink>
            </li>
          </ul>
        </nav>
        <main className="flex-1 p-10 overflow-auto">
          <Routes>
            <Route path="/create-accounts" element={<CreateAccounts />} />
            <Route path="/crawl-test-cases" element={<CrawlTestCases />} />
            <Route path="/" element={
              <div className="text-center text-gray-500 mt-20">
                <h2 className="text-2xl">Welcome! Select a task from the menu.</h2>
              </div>
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;