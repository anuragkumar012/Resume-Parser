import React, { useState, useEffect } from 'react';

export default function Dashboard({ jobs, reports, onViewReport, onFilterChange, selectedJobFilter }) {
  const [stats, setStats] = useState({
    totalResumes: 0,
    activeJobs: 0,
    averageAts: 0,
    highlyEligible: 0,
  });

  const [searchQuery, setSearchQuery] = useState('');

  // Calculate statistics whenever jobs or reports update
  useEffect(() => {
    const totalResumes = reports.length;
    const activeJobs = jobs.length;
    
    // Average ATS
    const validScores = reports.map((r) => r.ats_score).filter((s) => s >= 0);
    const averageAts = validScores.length
      ? Math.round(validScores.reduce((acc, score) => acc + score, 0) / validScores.length)
      : 0;

    // Eligible candidates status count
    const highlyEligible = reports.filter((r) => r.eligibility === 'Eligible' && r.ats_score >= 70).length;

    setStats({
      totalResumes,
      activeJobs,
      averageAts,
      highlyEligible,
    });
  }, [jobs, reports]);

  // Filter and search logic
  const filteredReports = reports.filter((report) => {
    // Filter by Job description
    const matchesJob = selectedJobFilter === '' || report.job_id === parseInt(selectedJobFilter);
    
    // Search query
    const name = (report.candidate_name || '').toLowerCase();
    const email = (report.candidate_email || '').toLowerCase();
    const title = (report.job_title || '').toLowerCase();
    const query = searchQuery.toLowerCase();
    const matchesSearch = name.includes(query) || email.includes(query) || title.includes(query);
    
    return matchesJob && matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Page Header */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-heading)' }}>Recruiter Analytics Dashboard</h2>
        <p style={{ margin: 0, fontSize: '0.9rem' }}>Real-time ranking of candidate profiles, skill gap analysis, and structural eligibility audits.</p>
      </div>

      {/* Analytics Summary Cards */}
      <div className="grid-cols-4">
        {/* Stat 1 */}
        <div className="card stat-card">
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Evaluations</span>
            <div className="stat-val">{stats.totalResumes}</div>
          </div>
          <span className="stat-icon" style={{ color: 'var(--text-highlight)' }}>📄</span>
        </div>
        
        {/* Stat 2 */}
        <div className="card stat-card">
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Job Roles Configured</span>
            <div className="stat-val">{stats.activeJobs}</div>
          </div>
          <span className="stat-icon" style={{ color: 'var(--text-highlight)' }}>💼</span>
        </div>

        {/* Stat 3 */}
        <div className="card stat-card">
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Average ATS Score</span>
            <div className="stat-val" style={{ color: 'var(--text-highlight)' }}>
              {stats.averageAts}%
            </div>
          </div>
          <span className="stat-icon" style={{ color: 'var(--text-highlight)' }}>📈</span>
        </div>

        {/* Stat 4 */}
        <div className="card stat-card">
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Highly Eligible (70+)</span>
            <div className="stat-val" style={{ color: 'var(--text-highlight)' }}>{stats.highlyEligible}</div>
          </div>
          <span className="stat-icon" style={{ color: 'var(--text-highlight)' }}>🏆</span>
        </div>
      </div>

      {/* Filter and search panel */}
      <div className="card" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flex: 1, minWidth: '300px' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <input
              type="text"
              className="input-control"
              placeholder="Search candidate by name, email, or role..."
              style={{ width: '100%', paddingLeft: '1rem' }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          <select
            className="input-control"
            style={{ minWidth: '220px' }}
            value={selectedJobFilter}
            onChange={(e) => onFilterChange(e.target.value)}
          >
            <option value="">All Job Roles</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>
        </div>
      </div>

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
                // Score color indicator
                let scoreColor = 'var(--text-highlight)';

                // Eligibility Badge
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
                        <span style={{ fontWeight: 700, minWidth: '2.5rem', color: scoreColor }}>
                          {Math.round(report.ats_score)}%
                        </span>
                        <div className="progress-bar-container" style={{ flex: 1 }}>
                          <div
                            className="progress-bar-fill"
                            style={{
                              width: `${report.ats_score}%`,
                              backgroundColor: scoreColor,
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
