import React, { useState } from 'react';
import { UserCheck, ShieldAlert, KeyRound, User, ArrowRight } from 'lucide-react';

export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('inspector_01');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please enter both Inspector ID and Password.');
      return;
    }
    // Simulate login
    onLoginSuccess({ username, role: 'Legal Metrology Inspector' });
  };

  return (
    <div style={{ maxWidth: '440px', margin: '3rem auto 0', padding: '0 1rem' }}>
      <div className="panel" style={{ padding: '2.5rem 2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            display: 'inline-flex',
            padding: '1rem',
            borderRadius: '18px',
            background: 'var(--sage-soft)',
            color: 'var(--sage-deep)',
            marginBottom: '1rem',
            boxShadow: '0 6px 16px rgba(93, 143, 111, 0.15)'
          }}>
            <UserCheck size={36} />
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text)' }}>Inspector Portal</h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.88rem', marginTop: '0.3rem' }}>
            Legal Metrology Compliance Enforcement System
          </p>
        </div>

        {error && (
          <div className="alert-box" style={{ marginBottom: '1.5rem', padding: '0.75rem 1rem' }}>
            <div>
              <strong>Authentication Error</strong>
              <span>{error}</span>
            </div>
            <div className="alert-tag">Required</div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Inspector ID
            </label>
            <div style={{ position: 'relative' }}>
              <User size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)' }} />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="search-box"
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem 0.75rem 2.75rem',
                  fontSize: '0.92rem'
                }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1.75rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <KeyRound size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)' }} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="search-box"
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem 0.75rem 2.75rem',
                  fontSize: '0.92rem'
                }}
              />
            </div>
          </div>

          <button type="submit" className="btn primary" style={{ width: '100%', minHeight: '44px' }}>
            <span>Sign In to Enforcement Portal</span>
            <ArrowRight size={18} />
          </button>

          {onContinueAsGuest && (
            <div style={{ marginTop: '1.25rem', textAlign: 'center', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
              <button
                type="button"
                className="btn secondary"
                onClick={onContinueAsGuest}
                style={{ width: '100%', minHeight: '40px', fontSize: '0.85rem' }}
              >
                <span>Continue as Guest</span>
              </button>
              <p style={{ color: 'var(--muted)', fontSize: '0.76rem', marginTop: '0.5rem', lineHeight: '1.4' }}>
                Scan a product without creating an account. Sign in only if you want to save inspections and reports.
              </p>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
