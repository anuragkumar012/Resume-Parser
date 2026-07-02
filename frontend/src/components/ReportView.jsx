import React from 'react';

export default function ReportView({ reportData, onBack, API_URL }) {
  if (!reportData) return null;

  const candidate = reportData.candidate || {};
  const info = candidate.candidate_info || {};
  const job = reportData.job || {};
  const skillGap = reportData.skill_gap_analysis || {};
  const expAnalysis = reportData.experience_analysis || {};
  const kwAnalysis = reportData.keyword_analysis || {};

  // Score colors
  const scoreColor = 'var(--text-highlight)';

  // Eligibility Status Banner
  let eligClass = 'badge-danger';
  if (reportData.eligibility === 'Eligible') eligClass = 'badge-success';
  else if (reportData.eligibility === 'Partially Eligible') eligClass = 'badge-warning';

  const downloadPdfReport = async () => {
    try {
      const response = await fetch(`${API_URL}/report/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reportData),
      });

      if (!response.ok) throw new Error('PDF Generation Failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `resume_evaluation_${info.name || 'report'}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert('Error downloading PDF scorecard: ' + err.message);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', textAlign: 'left' }}>
      {/* Header Panel */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
        <div>
          <button className="btn btn-secondary" onClick={onBack} style={{ marginBottom: '0.75rem', padding: '0.375rem 0.75rem', fontSize: '0.85rem' }}>
            ← Back to Dashboard
          </button>
          <h2 style={{ fontSize: '1.75rem', color: 'var(--text-highlight)' }}>
            Candidate Scorecard: {info.name || 'Unknown Candidate'}
          </h2>
          <p style={{ margin: 0, fontSize: '0.9rem' }}>
            Target: <strong style={{ color: 'var(--text-highlight)' }}>{job.title}</strong> ({job.company || 'N/A'})
          </p>
        </div>
        <button className="btn btn-primary" onClick={downloadPdfReport}>
          📥 Download PDF Report
        </button>
      </div>

      {/* Main Scorecard Summary */}
      <div className="grid-cols-3">
        {/* ATS Score Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
          <h4 style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>ATS Match Rating</h4>
          <div className="score-circle">
            <span className="score-circle-value" style={{ color: 'var(--text-highlight)' }}>
              {Math.round(reportData.ats_score)}
            </span>
            <span className="score-circle-label">out of 100</span>
          </div>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Score Confidence: {Math.round(reportData.confidence * 100)}%
          </span>
        </div>

        {/* Eligibility Status */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h4 style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>Eligibility Checklist</h4>
          <div>
            <span className={`badge ${eligClass}`} style={{ fontSize: '1rem', padding: '0.4rem 1rem' }}>
              {reportData.eligibility}
            </span>
          </div>
          <div style={{ flex: 1, fontSize: '0.875rem' }}>
            <span style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--text-highlight)' }}>
              Checklist Status Notes:
            </span>
            <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-muted)' }}>
              {reportData.eligibility_reasons?.map((reason, idx) => (
                <li key={idx} style={{ marginBottom: '0.25rem' }}>{reason}</li>
              ))}
              {(!reportData.eligibility_reasons || reportData.eligibility_reasons.length === 0) && (
                <li>Passed structural criteria checks.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Metrics Bar Graph Proxy */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <h4 style={{ fontSize: '1rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Core Categories Matrix</h4>
          
          {/* Item 1 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.125rem' }}>
              <span>Skill Alignment</span>
              <strong style={{ color: 'var(--text-highlight)' }}>{Math.round(reportData.skill_match)}%</strong>
            </div>
            <div className="progress-bar-container">
              <div className="progress-bar-fill" style={{ width: `${reportData.skill_match}%`, backgroundColor: 'var(--text-highlight)' }}></div>
            </div>
          </div>

          {/* Item 2 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.125rem' }}>
              <span>Experience Match</span>
              <strong style={{ color: 'var(--text-highlight)' }}>{Math.round(reportData.experience_match)}%</strong>
            </div>
            <div className="progress-bar-container">
              <div className="progress-bar-fill" style={{ width: `${reportData.experience_match}%`, backgroundColor: 'var(--text-highlight)' }}></div>
            </div>
          </div>

          {/* Item 3 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.125rem' }}>
              <span>Education Alignment</span>
              <strong style={{ color: 'var(--text-highlight)' }}>{Math.round(reportData.education_match)}%</strong>
            </div>
            <div className="progress-bar-container">
              <div className="progress-bar-fill" style={{ width: `${reportData.education_match}%`, backgroundColor: 'var(--text-highlight)' }}></div>
            </div>
          </div>

          {/* Item 4 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.125rem' }}>
              <span>Semantic Cosine Overlap</span>
              <strong style={{ color: 'var(--text-highlight)' }}>{Math.round(reportData.semantic_score)}%</strong>
            </div>
            <div className="progress-bar-container">
              <div className="progress-bar-fill" style={{ width: `${reportData.semantic_score}%`, backgroundColor: 'var(--text-highlight)' }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Details Grid */}
      <div className="detail-grid">
        {/* Sidebar Info */}
        <div className="sidebar-panel">
          {/* Candidate Profile Details */}
          <div className="card">
            <h4 style={{ fontSize: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', marginBottom: '0.75rem', color: 'var(--text-highlight)' }}>
              Candidate Details
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.8rem' }}>Email Address</span>
                <span style={{ wordBreak: 'break-all', color: 'var(--text-highlight)' }}>{info.email || 'Not Provided'}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.8rem' }}>Phone Number</span>
                <span style={{ color: 'var(--text-highlight)' }}>{info.phone || 'Not Provided'}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.8rem' }}>Location</span>
                <span style={{ color: 'var(--text-highlight)' }}>{info.location || 'Not Provided'}</span>
              </div>
              {info.linkedin && (
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.8rem' }}>LinkedIn</span>
                  <a href={info.linkedin} target="_blank" rel="noreferrer" style={{ color: 'var(--text-highlight)', textDecoration: 'underline', wordBreak: 'break-all' }}>
                    Profile Link
                  </a>
                </div>
              )}
              {info.github && (
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.8rem' }}>GitHub</span>
                  <a href={info.github} target="_blank" rel="noreferrer" style={{ color: 'var(--text-highlight)', textDecoration: 'underline', wordBreak: 'break-all' }}>
                    Repository Link
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Resume Strengths & Weaknesses */}
          <div className="card">
            <h4 style={{ fontSize: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', marginBottom: '0.75rem', color: 'var(--text-highlight)' }}>
              Strengths & Weaknesses
            </h4>
            
            {/* Strengths */}
            <div style={{ marginBottom: '1rem' }}>
              <span style={{ color: 'var(--text-highlight)', fontWeight: 600, fontSize: '0.85rem', display: 'block', marginBottom: '0.35rem' }}>
                ✓ Key Strengths
              </span>
              <ul style={{ margin: 0, paddingLeft: '1.1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {reportData.resume_strengths?.map((str, idx) => (
                  <li key={idx} style={{ marginBottom: '0.25rem' }}>{str}</li>
                ))}
                {(!reportData.resume_strengths || reportData.resume_strengths.length === 0) && (
                  <li>No notable strengths flagged automatically.</li>
                )}
              </ul>
            </div>

            {/* Weaknesses */}
            <div>
              <span style={{ color: 'var(--text-highlight)', fontWeight: 600, fontSize: '0.85rem', display: 'block', marginBottom: '0.35rem' }}>
                ⚠ Potential Flags
              </span>
              <ul style={{ margin: 0, paddingLeft: '1.1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {reportData.resume_weaknesses?.map((weak, idx) => (
                  <li key={idx} style={{ marginBottom: '0.25rem' }}>{weak}</li>
                ))}
                {(!reportData.resume_weaknesses || reportData.resume_weaknesses.length === 0) && (
                  <li>No potential warning flags detected.</li>
                )}
              </ul>
            </div>
          </div>
        </div>

        {/* Scroll Details Section */}
        <div className="scroll-panel">
          {/* Skill Gap Matrix */}
          <div className="card">
            <h3 className="section-title">Skill Gap Analysis</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Strong Skills */}
              <div>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-highlight)', marginBottom: '0.5rem' }}>
                  Matching Technical Skills ({skillGap.strong_skills?.length || 0})
                </span>
                <div className="skills-grid">
                  {skillGap.strong_skills?.map((skill, idx) => (
                    <span key={idx} className="tag" style={{ borderLeft: '2px solid var(--text-highlight)', background: 'var(--tag-bg)' }}>
                      {skill}
                    </span>
                  ))}
                  {(!skillGap.strong_skills || skillGap.strong_skills.length === 0) && (
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>None found.</span>
                  )}
                </div>
              </div>

              {/* Missing Skills */}
              <div>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-highlight)', marginBottom: '0.5rem' }}>
                  Missing Required Skills ({skillGap.missing_skills?.length || 0})
                </span>
                <div className="skills-grid">
                  {skillGap.missing_skills?.map((skill, idx) => (
                    <span key={idx} className="tag" style={{ borderLeft: '2px dashed var(--border-color)', background: 'var(--tag-bg)' }}>
                      {skill}
                    </span>
                  ))}
                  {(!skillGap.missing_skills || skillGap.missing_skills.length === 0) && (
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>None missing! Meets all skill list items.</span>
                  )}
                </div>
              </div>

              {/* Weak Skills */}
              {skillGap.weak_skills?.length > 0 && (
                <div>
                  <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                    Weak/Basic Skills ({skillGap.weak_skills.length})
                  </span>
                  <div className="skills-grid">
                    {skillGap.weak_skills.map((skill, idx) => (
                      <span key={idx} className="tag" style={{ borderLeft: '2px solid var(--border-color)' }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Work History & Experience Analysis */}
          <div className="card">
            <h3 className="section-title">Work Experience Breakdown</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="grid-cols-3">
                <div style={{ background: 'rgba(255,255,255,0.01)', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Total Experience</span>
                  <strong style={{ fontSize: '1.1rem', color: 'var(--text-highlight)' }}>
                    {expAnalysis.total_experience_years ? `${expAnalysis.total_experience_years.toFixed(1)} Yrs` : 'N/A'}
                  </strong>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.01)', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Relevant Experience</span>
                  <strong style={{ fontSize: '1.1rem', color: 'var(--text-highlight)' }}>
                    {expAnalysis.relevant_experience_years ? `${expAnalysis.relevant_experience_years.toFixed(1)} Yrs` : 'N/A'}
                  </strong>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.01)', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Average Job Tenure</span>
                  <strong style={{ fontSize: '1.1rem', color: 'var(--text-highlight)' }}>
                    {expAnalysis.average_job_duration_months
                      ? `${(expAnalysis.average_job_duration_months / 12).toFixed(1)} Yrs`
                      : 'N/A'}
                  </strong>
                </div>
              </div>

              {/* Work history timeline */}
              <div style={{ marginTop: '0.5rem' }}>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-highlight)', marginBottom: '1rem' }}>
                  Employment Timeline
                </span>
                <div className="timeline">
                  {candidate.work_experience?.map((exp, idx) => (
                    <div key={idx} className="timeline-item">
                      <div className="timeline-header">
                        <div>
                          <span className="timeline-title">{exp.role}</span>
                          <span className="timeline-subtitle"> at {exp.company}</span>
                        </div>
                        <span className="timeline-date">{exp.duration}</span>
                      </div>
                      <div className="timeline-content">
                        <ul className="bullet-list">
                          {exp.responsibilities?.slice(0, 3).map((resp, rIdx) => (
                            <li key={rIdx}>{resp}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                  {(!candidate.work_experience || candidate.work_experience.length === 0) && (
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No work history parsed.</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Actionable Recommendations */}
          <div className="card">
            <h3 className="section-title">AI Optimization Recommendations</h3>
            <div className="rec-list">
              {reportData.recommendations?.map((item, idx) => (
                <div key={idx} className={`rec-item priority-${item.priority}`}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-highlight)', fontSize: '0.95rem' }}>
                      {item.recommendation}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Section: {item.section}
                    </span>
                  </div>
                  <span className={`badge ${item.priority === 'High' ? 'badge-danger' : item.priority === 'Medium' ? 'badge-warning' : 'badge-info'}`}>
                    {item.priority} Priority
                  </span>
                </div>
              ))}
              {(!reportData.recommendations || reportData.recommendations.length === 0) && (
                <div style={{ textAlign: 'center', padding: '1rem 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  No optimization alerts generated. Excellent resume format and content density!
                </div>
              )}
            </div>
          </div>

          {/* Gemini API Usage & Cost Tracking */}
          {reportData.llm_usage && (
            <div className="card">
              <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-highlight)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="1" x2="12" y2="23"></line>
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>
                Gemini API Token & Cost Tracking
              </h3>
              
              <div className="usage-summary-card">
                <div className="usage-summary-item total-cost">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Total Session Cost
                  </div>
                  <div className="usage-summary-val" style={{ color: 'var(--text-highlight)' }}>
                    ${reportData.llm_usage.total_cost_usd?.toFixed(6)} <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: 'var(--text-muted)' }}>USD</span>
                  </div>
                </div>
                
                <div className="usage-summary-item">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Total Tokens Consumed
                  </div>
                  <div className="usage-summary-val">
                    {reportData.llm_usage.total_tokens?.toLocaleString()} <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: 'var(--text-muted)' }}>tkn</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    Prompt: {reportData.llm_usage.total_prompt_tokens?.toLocaleString()} | Response: {reportData.llm_usage.total_candidate_tokens?.toLocaleString()}
                  </div>
                </div>
              </div>
              
              <h4 style={{ fontSize: '0.9rem', color: 'var(--text-highlight)', marginBottom: '0.75rem' }}>
                Transaction Call Breakdown
              </h4>
              <div className="usage-table-container">
                <table className="usage-table">
                  <thead>
                    <tr>
                      <th>Call / Purpose</th>
                      <th>Model Name</th>
                      <th>Prompt</th>
                      <th>Response</th>
                      <th>Total</th>
                      <th>Estimated Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.llm_usage.calls?.map((call, index) => (
                      <tr key={index}>
                        <td style={{ fontWeight: '500', color: 'var(--text-highlight)' }}>
                          {call.purpose || 'API Call'}
                        </td>
                        <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {call.model_name || 'N/A'}
                        </td>
                        <td>{call.prompt_tokens?.toLocaleString()}</td>
                        <td>{call.candidate_tokens?.toLocaleString()}</td>
                        <td>{call.total_tokens?.toLocaleString()}</td>
                        <td style={{ color: 'var(--text-highlight)', fontWeight: '600' }}>
                          ${call.cost_usd?.toFixed(6)}
                        </td>
                      </tr>
                    ))}
                    {(!reportData.llm_usage.calls || reportData.llm_usage.calls.length === 0) && (
                      <tr>
                        <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1rem' }}>
                          No transaction breakdown available.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
