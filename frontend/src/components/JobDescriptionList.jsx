import React, { useState } from 'react';

export default function JobDescriptionList({ jobs, onJobAdded, API_URL }) {
  const [isAdding, setIsAdding] = useState(false);
  const [title, setTitle] = useState('');
  const [rawText, setRawText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !rawText.trim()) return;

    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, raw_text: rawText }),
      });

      if (!response.ok) {
        throw new Error('Failed to parse and save job description');
      }

      const data = await response.json();
      alert(`Job role '${data.title}' parsed and saved successfully!`);
      setTitle('');
      setRawText('');
      setIsAdding(false);
      onJobAdded(); // Refresh parent jobs list
    } catch (err) {
      console.error(err);
      alert(`Error saving job description: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-heading)' }}>Job Description Directory</h2>
          <p style={{ margin: 0, fontSize: '0.9rem' }}>Configure targets and requirements for resume compatibility scoring.</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            setIsAdding(!isAdding);
            setSelectedJob(null);
          }}
        >
          {isAdding ? 'View Directory' : '+ Create Job Role'}
        </button>
      </div>

      {isAdding ? (
        <div className="card" style={{ maxWidth: '700px', margin: '0 auto', width: '100%' }}>
          <h3 className="section-title">Add & Parse New Job Description</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Role Title (Fallback)</label>
              <input
                type="text"
                className="input-control"
                placeholder="e.g. Senior Backend Engineer"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Full Job Description Text</label>
              <textarea
                className="input-control"
                placeholder="Paste the job description details here, including responsibilities, mandatory requirements, and tech stack details..."
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                required
                disabled={isLoading}
                style={{ minHeight: '300px' }}
              />
            </div>

            {isLoading ? (
              <div className="spinner-container" style={{ padding: '1rem' }}>
                <div className="spinner"></div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                  Parsing Job Description with AI model...
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => setIsAdding(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Save & Parse
                </button>
              </div>
            )}
          </form>
        </div>
      ) : (
        <div className="detail-grid">
          {/* Sidebar - Jobs List */}
          <div className="sidebar-panel">
            <div className="card" style={{ maxHeight: '600px', overflowY: 'auto', padding: '1rem' }}>
              <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: 'var(--text-highlight)' }}>
                Active Job Roles ({jobs.length})
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {jobs.map((job) => (
                  <div
                    key={job.id}
                    className={`card`}
                    style={{
                      padding: '0.875rem 1rem',
                      cursor: 'pointer',
                      borderRadius: '0.5rem',
                      border: selectedJob?.id === job.id ? '1px solid var(--border-glow)' : '1px solid var(--border-color)',
                      background: selectedJob?.id === job.id ? 'var(--tag-bg)' : 'var(--input-bg)',
                    }}
                    onClick={() => setSelectedJob(job)}
                  >
                    <div style={{ fontWeight: 600, color: 'var(--text-highlight)', fontSize: '0.95rem' }}>
                      {job.title}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      Company: {job.parsed_json?.company || 'N/A'}
                    </div>
                  </div>
                ))}
                {jobs.length === 0 && (
                  <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-muted)' }}>
                    No job roles saved.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Details Pane */}
          <div className="scroll-panel">
            {selectedJob ? (
              <div className="card" style={{ textAlign: 'left' }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    borderBottom: '1px solid var(--border-color)',
                    paddingBottom: '1rem',
                    marginBottom: '1.5rem',
                  }}
                >
                  <div>
                    <h3 style={{ fontSize: '1.5rem', color: 'var(--text-highlight)' }}>{selectedJob.title}</h3>
                    <span style={{ color: 'var(--text-highlight)', fontWeight: 500 }}>
                      {selectedJob.parsed_json?.company || 'N/A'} • {selectedJob.parsed_json?.location || 'Remote/Hybrid'}
                    </span>
                  </div>
                  <span className="badge badge-info">
                    {selectedJob.parsed_json?.employment_type || 'Full Time'}
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  {/* Experience and Education requirements */}
                  <div className="grid-cols-2">
                    <div style={{ background: 'rgba(255,255,255,0.01)', padding: '0.875rem', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>
                        Required Work Experience
                      </span>
                      <strong style={{ fontSize: '1.1rem', color: 'var(--text-highlight)' }}>
                        {selectedJob.parsed_json?.min_experience_years !== null && selectedJob.parsed_json?.min_experience_years !== undefined
                          ? `${selectedJob.parsed_json.min_experience_years}+ Years`
                          : 'Not Specified'}
                      </strong>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.01)', padding: '0.875rem', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>
                        Min Education Level
                      </span>
                      <strong style={{ fontSize: '1.1rem', color: 'var(--text-highlight)', display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {selectedJob.parsed_json?.required_education?.join(', ') || 'Any Degree'}
                      </strong>
                    </div>
                  </div>

                  {/* Skills lists */}
                  <div>
                    <h4 style={{ fontSize: '0.95rem', color: 'var(--text-highlight)', marginBottom: '0.5rem' }}>
                      Required Technical Stack
                    </h4>
                    <div className="skills-grid">
                      {selectedJob.parsed_json?.required_skills?.map((skill, idx) => (
                        <span key={idx} className="tag" style={{ borderLeft: '2px solid var(--border-glow)' }}>
                          {skill}
                        </span>
                      ))}
                      {(!selectedJob.parsed_json?.required_skills || selectedJob.parsed_json.required_skills.length === 0) && (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>None specified.</span>
                      )}
                    </div>
                  </div>

                  {/* Mandatory requirement filters */}
                  {selectedJob.parsed_json?.mandatory_requirements?.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: '0.95rem', color: 'var(--text-highlight)', marginBottom: '0.5rem' }}>
                        Mandatory Filter Criteria
                      </h4>
                      <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        {selectedJob.parsed_json.mandatory_requirements.map((req, idx) => (
                          <li key={idx} style={{ marginBottom: '0.25rem' }}>{req}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Job details text */}
                  <div>
                    <h4 style={{ fontSize: '0.95rem', color: 'var(--text-highlight)', marginBottom: '0.5rem' }}>
                      Responsibilities & Details
                    </h4>
                    <div
                      style={{
                        background: 'rgba(0,0,0,0.2)',
                        padding: '1rem',
                        borderRadius: '0.5rem',
                        fontSize: '0.875rem',
                        lineHeight: '1.6',
                        maxHeight: '300px',
                        overflowY: 'auto',
                        whiteSpace: 'pre-wrap',
                        border: '1px solid var(--border-color)',
                      }}
                    >
                      {selectedJob.raw_text}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div
                className="card"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minHeight: '400px',
                  color: 'var(--text-muted)',
                }}
              >
                Select a Job Description from the list to view parsed requirements.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
