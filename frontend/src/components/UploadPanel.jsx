import React, { useState } from 'react';
import CustomDropdown from './CustomDropdown';

export default function UploadPanel({ jobs, onAnalysisComplete, API_URL }) {
  const [selectedJobId, setSelectedJobId] = useState('');
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isBatchMode, setIsBatchMode] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  // Handle file drop
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      (file) => file.type === 'application/pdf'
    );
    if (droppedFiles.length > 0) {
      setFiles((prev) => (isBatchMode ? [...prev, ...droppedFiles] : [droppedFiles[0]]));
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files).filter(
      (file) => file.type === 'application/pdf'
    );
    if (selectedFiles.length > 0) {
      setFiles((prev) => (isBatchMode ? [...prev, ...selectedFiles] : [selectedFiles[0]]));
    }
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedJobId) {
      alert('Please select a Job Role.');
      return;
    }
    if (files.length === 0) {
      alert('Please upload at least one PDF resume.');
      return;
    }

    const selectedJob = jobs.find((j) => j.id === parseInt(selectedJobId));
    if (!selectedJob) return;

    setIsLoading(true);
    setStatusMessage('Reading and evaluating resume(s)...');

    try {
      if (isBatchMode || files.length > 1) {
        // Batch mode / Multiple files -> Call /rank
        const formData = new FormData();
        files.forEach((file) => formData.append('files', file));
        formData.append('jd_text', selectedJob.raw_text);

        const response = await fetch(`${API_URL}/rank`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Batch ranking failed.');
        }

        const data = await response.json();
        alert(`Successfully processed ${data.ranked_candidates.length} candidates!`);
        onAnalysisComplete(); // Trigger refresh on dashboard
      } else {
        // Single mode -> Call /analyze
        const formData = new FormData();
        formData.append('file', files[0]);
        formData.append('jd_text', selectedJob.raw_text);

        const response = await fetch(`${API_URL}/analyze`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Resume evaluation failed.');
        }

        const report = await response.json();
        alert(`Analysis complete for ${report.candidate.candidate_info.name || 'Candidate'}!`);
        onAnalysisComplete(report); // Switch to report view directly
      }
      setFiles([]);
    } catch (err) {
      console.error(err);
      alert(`Error during evaluation: ${err.message}`);
    } finally {
      setIsLoading(false);
      setStatusMessage('');
    }
  };

  return (
    <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h3 className="section-title">Evaluate Candidate Resumes</h3>
      
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem' }}>
        <button
          className={`btn ${!isBatchMode ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1 }}
          onClick={() => {
            setIsBatchMode(false);
            setFiles([]);
          }}
          disabled={isLoading}
        >
          Single Resume Mode
        </button>
        <button
          className={`btn ${isBatchMode ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1 }}
          onClick={() => {
            setIsBatchMode(true);
            setFiles([]);
          }}
          disabled={isLoading}
        >
          Batch Rank Mode
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Select Target Job Description</label>
          <CustomDropdown
            options={[
              { value: '', label: '-- Choose Job Role --' },
              ...jobs.map((job) => ({
                value: String(job.id),
                label: `${job.title} (${job.parsed_json?.company || 'Local Database'})`,
              })),
            ]}
            style={{ width: '100%' }}
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            disabled={isLoading}
          />
          {jobs.length === 0 && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              No Job Descriptions found. Please add a Job Role first.
            </span>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">Upload PDF Resume(s)</label>
          <div
            className={`upload-zone ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('resume-file-input').click()}
          >
            <div className="upload-icon">
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <div>
              <p style={{ fontWeight: 500, margin: '0 0 0.25rem 0', color: 'var(--text-highlight)' }}>
                Drag & Drop PDF Resume here
              </p>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                or click to browse local files
              </p>
            </div>
            <input
              id="resume-file-input"
              type="file"
              accept=".pdf"
              multiple={isBatchMode}
              style={{ display: 'none' }}
              onChange={handleFileChange}
              disabled={isLoading}
            />
          </div>
        </div>

        {files.length > 0 && (
          <div style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
            <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-highlight)' }}>
              Selected File(s):
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {files.map((file, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'var(--input-bg)',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <span style={{ fontSize: '0.85rem', wordBreak: 'break-all' }}>{file.name}</span>
                  <button
                    type="button"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                    }}
                    onClick={() => removeFile(idx)}
                    disabled={isLoading}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="spinner-container" style={{ padding: '1rem' }}>
            <div className="spinner"></div>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', margin: 0 }}>{statusMessage}</p>
          </div>
        ) : (
          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '1rem' }}
            disabled={jobs.length === 0 || files.length === 0}
          >
            Start AI Match & Analysis
          </button>
        )}
      </form>
    </div>
  );
}
