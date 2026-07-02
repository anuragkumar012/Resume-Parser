import React from 'react';

export default function ConfirmationModal({ isOpen, title, message, type = 'confirm', onConfirm, onCancel }) {
  if (!isOpen) return null;

  // Icon and button configurations based on modal type
  let iconMarkup = null;
  let buttonsMarkup = null;

  if (type === 'success') {
    iconMarkup = (
      <div
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          backgroundColor: 'rgba(40, 167, 69, 0.1)',
          border: '1px solid rgba(40, 167, 69, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#28a745',
          flexShrink: 0
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      </div>
    );
    
    buttonsMarkup = (
      <button
        type="button"
        className="btn btn-primary"
        style={{ minWidth: '100px' }}
        onClick={onCancel}
      >
        OK
      </button>
    );
  } else if (type === 'error') {
    iconMarkup = (
      <div
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          backgroundColor: 'rgba(220, 53, 69, 0.1)',
          border: '1px solid rgba(220, 53, 69, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#dc3545',
          flexShrink: 0
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </div>
    );
    
    buttonsMarkup = (
      <button
        type="button"
        className="btn btn-secondary"
        style={{ minWidth: '100px' }}
        onClick={onCancel}
      >
        Close
      </button>
    );
  } else {
    // Default to 'confirm'
    iconMarkup = (
      <div
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          backgroundColor: 'rgba(220, 53, 69, 0.1)',
          border: '1px solid rgba(220, 53, 69, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ff4d4d',
          flexShrink: 0
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
      </div>
    );
    
    buttonsMarkup = (
      <>
        <button
          type="button"
          className="btn btn-secondary"
          style={{ minWidth: '100px' }}
          onClick={onCancel}
        >
          Cancel
        </button>
        <button
          type="button"
          className="btn btn-danger"
          style={{
            minWidth: '100px',
            backgroundColor: '#dc3545',
            borderColor: '#dc3545',
            color: '#ffffff'
          }}
          onClick={onConfirm}
        >
          Delete
        </button>
      </>
    );
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        animation: 'fadeIn 0.2s ease-out'
      }}
      onClick={onCancel}
    >
      <div
        className="card"
        style={{
          maxWidth: '480px',
          width: '90%',
          padding: '2rem',
          border: '1px solid var(--border-color)',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.5)',
          background: 'var(--bg-card)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem',
          transform: 'scale(1)',
          animation: 'scaleIn 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {iconMarkup}
          <h3 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-heading)', color: 'var(--text-highlight)', margin: 0 }}>
            {title}
          </h3>
        </div>

        <p style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
          {message}
        </p>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '0.5rem' }}>
          {buttonsMarkup}
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scaleIn {
          from { transform: scale(0.95); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
