import React, { useState, useEffect } from 'react';
import CVECard from './CVECard';

function News() {
  const [stats, setStats] = useState(null);
  const [cves, setCves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState('today');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedCVE, setSelectedCVE] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    fetchCVEs();
  }, [selectedFilter, selectedSeverity]);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/stats');
      const data = await response.json();
      if (data.success) {
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchCVEs = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5001/api/news', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filter: selectedFilter,
          severity: selectedSeverity === 'all' ? null : selectedSeverity,
          limit: 50
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setCves(data.cves);
      }
    } catch (error) {
      console.error('Error fetching CVEs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCVEClick = (cve) => {
    setSelectedCVE(cve);
  };

  const closeModal = () => {
    setSelectedCVE(null);
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return '#dc2626';
      case 'HIGH': return '#ea580c';
      case 'MEDIUM': return '#f59e0b';
      case 'LOW': return '#84cc16';
      default: return '#64748b';
    }
  };

  return (
    <div style={{
      minHeight: 'calc(100vh - 64px)',
      backgroundColor: '#f8fafc',
      padding: '2rem'
    }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        <h1 style={{ 
          fontSize: '2rem', 
          fontWeight: 'bold',
          color: '#1e293b',
          marginBottom: '2rem'
        }}>
          📰 Latest Vulnerability Updates
        </h1>

        {/* Stats Cards */}
        {stats && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1rem',
            marginBottom: '2rem'
          }}>
            <div style={{
              backgroundColor: '#ffffff',
              padding: '1.5rem',
              borderRadius: '0.75rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem' }}>
                Total CVEs in Database
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
                {stats.total_cves?.toLocaleString()}
              </div>
            </div>

            <div style={{
              backgroundColor: '#ffffff',
              padding: '1.5rem',
              borderRadius: '0.75rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem' }}>
                Last Database Update
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#1e293b' }}>
                {stats.last_update ? new Date(stats.last_update).toLocaleDateString() : 'N/A'}
              </div>
            </div>

            <div style={{
              backgroundColor: '#ffffff',
              padding: '1.5rem',
              borderRadius: '0.75rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem' }}>
                Showing Results
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#1e293b' }}>
                {cves.length} CVEs
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div style={{
          backgroundColor: '#ffffff',
          padding: '1.5rem',
          borderRadius: '0.75rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          marginBottom: '2rem'
        }}>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '1.5rem',
            alignItems: 'center'
          }}>
            {/* Time Filter */}
            <div>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: '600',
                color: '#475569',
                marginBottom: '0.5rem'
              }}>
                Time Period
              </label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {['today', 'week', 'month'].map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setSelectedFilter(filter)}
                    style={{
                      padding: '0.5rem 1rem',
                      borderRadius: '0.5rem',
                      border: selectedFilter === filter ? '2px solid #3b82f6' : '1px solid #e2e8f0',
                      backgroundColor: selectedFilter === filter ? '#eff6ff' : '#ffffff',
                      color: selectedFilter === filter ? '#1e40af' : '#475569',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      textTransform: 'capitalize'
                    }}
                  >
                    {filter}
                  </button>
                ))}
              </div>
            </div>

            {/* Severity Filter */}
            <div>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: '600',
                color: '#475569',
                marginBottom: '0.5rem'
              }}>
                Severity
              </label>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {['all', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((severity) => (
                  <button
                    key={severity}
                    onClick={() => setSelectedSeverity(severity)}
                    style={{
                      padding: '0.5rem 1rem',
                      borderRadius: '0.5rem',
                      border: selectedSeverity === severity ? '2px solid #3b82f6' : '1px solid #e2e8f0',
                      backgroundColor: selectedSeverity === severity ? '#eff6ff' : '#ffffff',
                      color: selectedSeverity === severity ? '#1e40af' : '#475569',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    {severity}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* CVE Grid */}
        {loading ? (
          <div style={{
            textAlign: 'center',
            padding: '4rem',
            color: '#64748b'
          }}>
            <div style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>⏳</div>
            Loading vulnerabilities...
          </div>
        ) : cves.length === 0 ? (
          <div style={{
            backgroundColor: '#ffffff',
            padding: '4rem',
            borderRadius: '0.75rem',
            textAlign: 'center',
            color: '#64748b'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔍</div>
            <div style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              No vulnerabilities found
            </div>
            <div>
              Try adjusting your filters or select a different time period
            </div>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))',
            gap: '1.5rem'
          }}>
            {cves.map((cve, index) => (
              <CVECard 
                key={index} 
                cve={cve} 
                onClick={() => handleCVEClick(cve)}
              />
            ))}
          </div>
        )}

        {/* Modal for CVE Details */}
        {selectedCVE && (
          <div
            onClick={closeModal}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              zIndex: 1000,
              padding: '2rem'
            }}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '1rem',
                maxWidth: '800px',
                width: '100%',
                maxHeight: '90vh',
                overflow: 'auto',
                padding: '2rem',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
              }}
            >
              {/* Modal Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'start',
                marginBottom: '1.5rem'
              }}>
                <h2 style={{
                  fontSize: '1.75rem',
                  fontWeight: 'bold',
                  color: '#1e293b'
                }}>
                  {selectedCVE.cve_id}
                </h2>
                <button
                  onClick={closeModal}
                  style={{
                    fontSize: '1.5rem',
                    color: '#64748b',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '0.25rem'
                  }}
                >
                  ✕
                </button>
              </div>

              {/* Modal Content */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {/* Metadata */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: '1rem'
                }}>
                  <div>
                    <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
                      Severity
                    </div>
                    <div style={{
                      fontSize: '1.125rem',
                      fontWeight: '700',
                      color: getSeverityColor(selectedCVE.severity)
                    }}>
                      {selectedCVE.severity} ({selectedCVE.score})
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
                      Status
                    </div>
                    <div style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1e293b' }}>
                      {selectedCVE.status}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
                      Published
                    </div>
                    <div style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1e293b' }}>
                      {selectedCVE.published}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
                      Last Modified
                    </div>
                    <div style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1e293b' }}>
                      {selectedCVE.lastModified}
                    </div>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <div style={{
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: '#64748b',
                    marginBottom: '0.5rem'
                  }}>
                    Description
                  </div>
                  <div style={{
                    fontSize: '1rem',
                    color: '#475569',
                    lineHeight: '1.7',
                    backgroundColor: '#f8fafc',
                    padding: '1rem',
                    borderRadius: '0.5rem'
                  }}>
                    {selectedCVE.description}
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <a
                    href={`https://nvd.nist.gov/vuln/detail/${selectedCVE.cve_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      padding: '0.75rem 1.5rem',
                      backgroundColor: '#3b82f6',
                      color: '#ffffff',
                      borderRadius: '0.5rem',
                      textDecoration: 'none',
                      fontWeight: '600',
                      fontSize: '0.875rem',
                      textAlign: 'center'
                    }}
                  >
                    View on NVD ↗
                  </a>
                  <button
                    onClick={closeModal}
                    style={{
                      padding: '0.75rem 1.5rem',
                      backgroundColor: '#f1f5f9',
                      color: '#475569',
                      border: 'none',
                      borderRadius: '0.5rem',
                      fontWeight: '600',
                      fontSize: '0.875rem',
                      cursor: 'pointer'
                    }}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default News;