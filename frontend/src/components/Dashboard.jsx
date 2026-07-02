import React, { useState, useEffect } from 'react';

export default function Dashboard({ jobs, reports }) {
  const [stats, setStats] = useState({
    totalResumes: 0,
    activeJobs: 0,
    averageAts: 0,
    highlyEligible: 0,
  });

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
    </div>
  );
}
