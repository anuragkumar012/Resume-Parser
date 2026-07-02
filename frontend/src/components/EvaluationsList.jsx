import React, { useState } from 'react';
import CustomDropdown from './CustomDropdown';

export default function EvaluationsList({ jobs, reports, onViewReport, onFilterChange, selectedJobFilter }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEligibilityFilter, setSelectedEligibilityFilter] = useState('');
  const [selectedScoreFilter, setSelectedScoreFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Filter and search logic
  const filteredReports = reports.filter((report) => {
    // Filter by Job description
    const matchesJob = selectedJobFilter === '' || report.job_id === parseInt(selectedJobFilter);

    // Filter by Eligibility
    const matchesEligibility = selectedEligibilityFilter === '' || report.eligibility === selectedEligibilityFilter;

    // Filter by Score
    let matchesScore = true;
    if (selectedScoreFilter === 'high') {
      matchesScore = report.ats_score >= 70;
    } else if (selectedScoreFilter === 'medium') {
      matchesScore = report.ats_score >= 40 && report.ats_score < 70;
    } else if (selectedScoreFilter === 'low') {
      matchesScore = report.ats_score < 40;
    }

    // Search query
    const name = (report.candidate_name || '').toLowerCase();
    const email = (report.candidate_email || '').toLowerCase();
    const title = (report.job_title || '').toLowerCase();
    const query = searchQuery.toLowerCase();
    const matchesSearch = name.includes(query) || email.includes(query) || title.includes(query);

    return matchesJob && matchesEligibility && matchesScore && matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Page Header */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-heading)' }}>Candidate Evaluation Records</h2>
        <p style={{ margin: 0, fontSize: '0.9rem' }}>Real-time ranking of candidate profiles, skill gap analysis, and structural eligibility audits.</p>
      </div>

      {/* Filter and search panel */}
      {!showFilters ? (
        <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setShowFilters(true)}
            style={{
              padding: '0.75rem',
              borderRadius: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '42px',
              height: '42px'
            }}
            title="Show Filters"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="6" x2="21" y2="6" />
              <circle cx="8" cy="6" r="3" fill="var(--bg-card)" stroke="currentColor" strokeWidth="2" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <circle cx="16" cy="12" r="3" fill="var(--bg-card)" stroke="currentColor" strokeWidth="2" />
              <line x1="3" y1="18" x2="21" y2="18" />
              <circle cx="10" cy="18" r="3" fill="var(--bg-card)" stroke="currentColor" strokeWidth="2" />
            </svg>
          </button>
        </div>
      ) : (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--text-highlight)' }}>
                <line x1="3" y1="6" x2="21" y2="6" />
                <circle cx="8" cy="6" r="3" fill="var(--bg-card)" stroke="currentColor" strokeWidth="2" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <circle cx="16" cy="12" r="3" fill="var(--bg-card)" stroke="currentColor" strokeWidth="2" />
                <line x1="3" y1="18" x2="21" y2="18" />
                <circle cx="10" cy="18" r="3" fill="var(--bg-card)" stroke="currentColor" strokeWidth="2" />
              </svg>
              <strong style={{ fontSize: '0.95rem', color: 'var(--text-highlight)' }}>Filter Controls</strong>
            </div>
            
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowFilters(false)}
              style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
            >
              Hide Filters
            </button>
          </div>
 
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', width: '100%' }}>
            <div style={{ flex: '2 1 300px', position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input
                type="search"
                name="search"
                autoComplete="off"
                data-1p-ignore
                data-lpignore="true"
                data-dashlane-ignore="true"
                className="input-control"
                placeholder="Search by name, email or role..."
                style={{ width: '100%', paddingLeft: '1rem', paddingRight: '2.5rem', backgroundImage: 'none' }}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <svg
                style={{
                  position: 'absolute',
                  right: '0.875rem',
                  width: '1.1rem',
                  height: '1.1rem',
                  color: 'var(--text-muted)',
                  pointerEvents: 'none',
                }}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
 
            <div style={{ flex: '1 1 200px' }}>
              <CustomDropdown
                options={[
                  { value: '', label: 'All Job Roles' },
                  ...jobs.map((job) => ({ value: String(job.id), label: job.title })),
                ]}
                style={{ width: '100%' }}
                value={selectedJobFilter}
                onChange={(e) => onFilterChange(e.target.value)}
              />
            </div>
 
            <div style={{ flex: '1 1 200px' }}>
              <CustomDropdown
                options={[
                  { value: '', label: 'All Eligibility' },
                  { value: 'Eligible', label: 'Eligible' },
                  { value: 'Partially Eligible', label: 'Partially Eligible' },
                  { value: 'Not Eligible', label: 'Not Eligible' },
                ]}
                style={{ width: '100%' }}
                value={selectedEligibilityFilter}
                onChange={(e) => setSelectedEligibilityFilter(e.target.value)}
              />
            </div>
 
            <div style={{ flex: '1 1 200px' }}>
              <CustomDropdown
                options={[
                  { value: '', label: 'All ATS Scores' },
                  { value: 'high', label: 'High Score (70%+)' },
                  { value: 'medium', label: 'Medium Score (40%-69%)' },
                  { value: 'low', label: 'Low Score (<40%)' },
                ]}
                style={{ width: '100%' }}
                value={selectedScoreFilter}
                onChange={(e) => setSelectedScoreFilter(e.target.value)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Match Reports Table */}
      <div className="card" style={{ padding: '0' }}>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Candidate Name</th>
                <th>Target Job Role</th>
                <th>ATS Score</th>
                <th>Eligibility</th>
                <th>Match Details</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredReports.map((report) => {
                let eligibilityBadge = 'badge-danger';
                if (report.eligibility === 'Eligible') eligibilityBadge = 'badge-success';
                else if (report.eligibility === 'Partially Eligible') eligibilityBadge = 'badge-warning';

                return (
                  <tr key={report.id}>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-highlight)' }}>
                        {report.candidate_name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {report.candidate_email}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{report.job_title}</div>
                    </td>
                    <td style={{ width: '180px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontWeight: 700, minWidth: '2.5rem', color: 'var(--text-highlight)' }}>
                          {Math.round(report.ats_score)}%
                        </span>
                        <div className="progress-bar-container" style={{ flex: 1 }}>
                          <div
                            className="progress-bar-fill"
                            style={{
                              width: `${report.ats_score}%`,
                            }}
                          ></div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${eligibilityBadge}`}>
                        {report.eligibility}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Skills: {Math.round(report.skill_match)}% • Exp: {Math.round(report.experience_match)}%
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.375rem 0.75rem', fontSize: '0.8rem' }}
                        onClick={() => onViewReport(report.id)}
                      >
                        Scorecard
                      </button>
                    </td>
                  </tr>
                );
              })}
              {filteredReports.length === 0 && (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    No evaluations match your filters. Navigate to 'Upload & Match' to score candidates!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
