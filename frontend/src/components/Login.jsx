import React, { useState } from 'react';

export default function Login({ onLogin, API_URL }) {
  const [role, setRole] = useState('candidate'); // 'candidate' or 'company'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Mock users database
  const validCredentials = {
    candidate: { email: 'candidate@resumeintel.com', password: 'candidate123' },
    company: { email: 'hr@company.com', password: 'company123' },
  };

  const handleQuickFill = () => {
    const creds = validCredentials[role];
    setEmail(creds.email);
    setPassword(creds.password);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Basic validation
    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields.');
      return;
    }

    // Email format check
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address.');
      return;
    }

    setIsLoading(true);

    const baseUrl = API_URL || `http://${window.location.hostname}:8000`;
    try {
      const response = await fetch(`${baseUrl}/api/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password: password,
          role: role,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed.');
      }

      onLogin(data.user);
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Server connection error.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card card">
        <div className="login-header">
          <div className="" style={{ overflow: 'hidden', padding: '0.5rem' }}>
            <img src="/favicon.png" alt="Logo" style={{ width: '50%', height: '50%', objectFit: 'contain' }} />
          </div>
          <h2>Resume Intelligence</h2>
          <p className="login-subtitle">Sign in to your dashboard portal</p>
        </div>

        {/* Role Tab Selector */}
        <div className="login-tabs">
          <button
            type="button"
            className={`login-tab ${role === 'candidate' ? 'active' : ''}`}
            onClick={() => {
              setRole('candidate');
              setError('');
              setEmail('');
              setPassword('');
            }}
          >
            Candidate Portal
          </button>
          <button
            type="button"
            className={`login-tab ${role === 'company' ? 'active' : ''}`}
            onClick={() => {
              setRole('company');
              setError('');
              setEmail('');
              setPassword('');
            }}
          >
            Company Portal
          </button>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="login-error">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '0.5rem', flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="email-input">
              {role === 'candidate' ? 'Candidate Email' : 'Company Email'}
            </label>
            <input
              id="email-input"
              type="email"
              className="input-control"
              placeholder={role === 'candidate' ? 'candidate@resumeintel.com' : 'hr@company.com'}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>

          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label className="form-label" htmlFor="password-input">Password</label>
            <input
              id="password-input"
              type="password"
              className="input-control"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary login-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="login-spinner-wrapper">
                <span className="spinner-mini"></span>
                Signing In...
              </span>
            ) : (
              `Sign In as ${role === 'candidate' ? 'Candidate' : 'Company'}`
            )}
          </button>

          {/* Quick-fill helper */}
          <div className="quick-fill-section">
            <div className="quick-fill-divider">
              <span>Or Auto-fill Sandbox Accounts</span>
            </div>
            <button
              type="button"
              className="btn btn-secondary quick-fill-btn"
              onClick={handleQuickFill}
              disabled={isLoading}
            >
              Autofill {role === 'candidate' ? 'Candidate' : 'Company'} Credentials
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
