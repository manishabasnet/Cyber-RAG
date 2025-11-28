import React from 'react';

function CVECard({ cve, onClick }) {
  const getSeverityColor = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return '#dc2626';
      case 'HIGH': return '#ea580c';
      case 'MEDIUM': return '#f59e0b';
      case 'LOW': return '#84cc16';
      default: return '#64748b';
    }
  };

  const getSeverityBackground = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return '#fee2e2';
      case 'HIGH': return '#ffedd5';
      case 'MEDIUM': return '#fef3c7';
      case 'LOW': return '#ecfccb';
      default: return '#f1f5f9';
    }
  };

  return (
    <div
      onClick={onClick}
      style={{
        backgroundColor: '#ffffff',
        padding: '1.5rem',
        borderRadius: '0.75rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        border: '1px solid #e2e8f0',
        cursor: 'pointer',
        transition: 'all 0.2s',
        ':hover': {
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          borderColor: '#cbd5e1'
        }
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        e.currentTarget.style.borderColor = '#cbd5e1';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
        e.currentTarget.style.borderColor = '#e2e8f0';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'start',
        marginBottom: '1rem'
      }}>
        <div>
          <div style={{
            fontSize: '1.25rem',
            fontWeight: 'bold',
            color: '#1e293b',
            marginBottom: '0.25rem'
          }}>
            {cve.cve_id}
          </div>
          <div style={{
            fontSize: '0.875rem',
            color: '#64748b',
            display: 'flex',
            gap: '1rem'
          }}>
            <span>📅 Published: {cve.published}</span>
            <span>🔄 Modified: {cve.lastModified}</span>
          </div>
        </div>
        
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          flexDirection: 'column',
          alignItems: 'flex-end'
        }}>
          <span style={{
            padding: '0.375rem 0.75rem',
            borderRadius: '0.5rem',
            fontSize: '0.875rem',
            fontWeight: '700',
            backgroundColor: getSeverityBackground(cve.severity),
            color: getSeverityColor(cve.severity),
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            {cve.severity}
          </span>
          {cve.score !== 'N/A' && (
            <span style={{
              padding: '0.25rem 0.75rem',
              borderRadius: '0.375rem',
              fontSize: '0.875rem',
              fontWeight: '600',
              backgroundColor: '#f1f5f9',
              color: '#475569'
            }}>
              Score: {cve.score}
            </span>
          )}
        </div>
      </div>

      {/* Status Badge */}
      <div style={{ marginBottom: '0.75rem' }}>
        <span style={{
          display: 'inline-block',
          padding: '0.25rem 0.625rem',
          borderRadius: '0.375rem',
          fontSize: '0.75rem',
          fontWeight: '600',
          backgroundColor: cve.status === 'Analyzed' ? '#dbeafe' : '#f3f4f6',
          color: cve.status === 'Analyzed' ? '#1e40af' : '#4b5563'
        }}>
          {cve.status}
        </span>
      </div>

      {/* Description */}
      <div style={{
        fontSize: '0.875rem',
        color: '#475569',
        lineHeight: '1.6',
        display: '-webkit-box',
        WebkitLineClamp: 3,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden'
      }}>
        {cve.description}
      </div>

      {/* Read More Indicator */}
      <div style={{
        marginTop: '1rem',
        fontSize: '0.875rem',
        color: '#3b82f6',
        fontWeight: '500'
      }}>
        Click for details →
      </div>
    </div>
  );
}

export default CVECard;