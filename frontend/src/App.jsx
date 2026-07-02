import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import JobDescriptionList from './components/JobDescriptionList';
import UploadPanel from './components/UploadPanel';
import ReportView from './components/ReportView';
import logoSvg from './assets/logo.svg';

const API_URL = `http://${window.location.hostname}:8000`;

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [jobs, setJobs] = useState([]);
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [selectedJobFilter, setSelectedJobFilter] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleTheme = () => {
    setTheme((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', next);
      return next;
    });
  };

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'light') {
      root.classList.add('light-theme');
    } else {
      root.classList.remove('light-theme');
    }
  }, [theme]);

  // Fetch initial data
  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_URL}/jobs`);
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (err) {
      console.error('Error fetching jobs:', err);
    }
  };

  const fetchReports = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/reports`);
      if (res.ok) {
        const data = await res.json();
        setReports(data);
      }
    } catch (err) {
      console.error('Error fetching reports:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    fetchReports();
  }, []);

  // Event handlers
  const handleViewReport = async (reportId) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/reports/${reportId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedReport(data);
        setActiveTab('report');
      } else {
        alert('Could not retrieve report scorecard.');
      }
    } catch (err) {
      console.error(err);
      alert('Error fetching report detail: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalysisComplete = (newReport) => {
    fetchReports();
    fetchJobs();
    if (newReport) {
      setSelectedReport(newReport);
      setActiveTab('report');
    } else {
      setActiveTab('dashboard');
    }
  };

  return (
    <div className="app-container">
      {/* Header and navigation bar */}
      <header className="app-header">
        <div className="header-brand-bar">
          <div className="brand">
            <div className="brand-logo">
              <img src={logoSvg} alt="Logo" />
            </div>
            <div className="brand-text">Resume Intelligence Platform</div>
          </div>
          <button
            className="menu-toggle"
            onClick={() => setIsMenuOpen((prev) => !prev)}
            aria-label="Toggle Navigation Menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {isMenuOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </>
              ) : (
                <>
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </>
              )}
            </svg>
          </button>
        </div>

        <nav className={`nav-tabs ${isMenuOpen ? 'open' : ''}`}>
          <button
            className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('dashboard');
              fetchReports();
              setIsMenuOpen(false);
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="9" />
              <rect x="14" y="3" width="7" height="5" />
              <rect x="14" y="12" width="7" height="9" />
              <rect x="3" y="16" width="7" height="5" />
            </svg>
            Dashboard
          </button>

          <button
            className={`tab-btn ${activeTab === 'jobs' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('jobs');
              fetchJobs();
              setIsMenuOpen(false);
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
            </svg>
            Job Specs
          </button>

          <button
            className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('upload');
              setIsMenuOpen(false);
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            Upload & Match
          </button>

          <button
            className="tab-btn"
            style={{
              marginLeft: '1rem',
              background: 'var(--theme-btn-bg)',
              color: 'var(--theme-btn-text)',
              border: '1px solid var(--border-color)',
            }}
            onClick={() => {
              toggleTheme();
              setIsMenuOpen(false);
            }}
          >
            {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
          </button>
        </nav>
      </header>

      {/* Main workspace container */}
      <main className="main-content">
        {isLoading && activeTab !== 'report' && (
          <div className="spinner-container">
            <div className="spinner"></div>
            <p style={{ color: 'var(--text-muted)' }}>Updating metrics database...</p>
          </div>
        )}

        {!isLoading && activeTab === 'dashboard' && (
          <Dashboard
            jobs={jobs}
            reports={reports}
            onViewReport={handleViewReport}
            onFilterChange={setSelectedJobFilter}
            selectedJobFilter={selectedJobFilter}
          />
        )}

        {activeTab === 'jobs' && (
          <JobDescriptionList
            jobs={jobs}
            onJobAdded={fetchJobs}
            API_URL={API_URL}
          />
        )}

        {activeTab === 'upload' && (
          <UploadPanel
            jobs={jobs}
            onAnalysisComplete={handleAnalysisComplete}
            API_URL={API_URL}
          />
        )}

        {activeTab === 'report' && (
          <ReportView
            reportData={selectedReport}
            onBack={() => {
              setActiveTab('dashboard');
              fetchReports();
            }}
            API_URL={API_URL}
          />
        )}
      </main>
    </div>
  );
}

export default App;
