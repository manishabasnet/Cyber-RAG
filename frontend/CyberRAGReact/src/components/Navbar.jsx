import React from 'react';
import { Link, useLocation } from 'react-router-dom';

function Navbar() {
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;
  
  return (
    <nav style={{
      backgroundColor: '#1e293b',
      padding: '1rem 2rem',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <div style={{
        fontSize: '1.5rem',
        fontWeight: 'bold',
        color: '#ffffff',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        🔒 CyberRAG
      </div>
      
      <div style={{ display: 'flex', gap: '1rem' }}>
        <Link 
          to="/" 
          style={{
            color: isActive('/') ? '#60a5fa' : '#e2e8f0',
            textDecoration: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '0.375rem',
            backgroundColor: isActive('/') ? '#334155' : 'transparent',
            transition: 'all 0.2s',
            fontWeight: '500'
          }}
        >
          💬 Chatbot
        </Link>
        
        <Link 
          to="/news" 
          style={{
            color: isActive('/news') ? '#60a5fa' : '#e2e8f0',
            textDecoration: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '0.375rem',
            backgroundColor: isActive('/news') ? '#334155' : 'transparent',
            transition: 'all 0.2s',
            fontWeight: '500'
          }}
        >
          📰 Latest Updates
        </Link>
      </div>
    </nav>
  );
}

export default Navbar;