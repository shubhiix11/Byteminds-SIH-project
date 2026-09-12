import React from 'react';
import { ShieldCheck, LayoutDashboard, Camera, Database, FileText, LogIn, LogOut, Activity, Bell } from 'lucide-react';

export default function Navbar({
  activeTab,
  setActiveTab,
  isConnected,
  healthData,
  scanResult,
  user,
  onLogout,
  searchQuery = '',
  onSearchChange = () => {}
}) {
  const ocrDetections = scanResult?.ocr_detections?.length ?? scanResult?.debug?.["LOCAL OCR"]?.detections_count ?? null;
  const ocrExecuted = Boolean(scanResult);

  return (
    <>
      {/* Sidebar Navigation matching frontend-design/index.html */}
      <aside className="sidebar">
        <div className="logo" onClick={() => setActiveTab('dashboard')} title="LabelSure Platform">
          <span className="logo-badge">
            <ShieldCheck size={18} strokeWidth={2.6} />
          </span>
          <span>LabelSure</span>
        </div>

        <nav className="nav" aria-label="Sidebar navigation">
          <button
            className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
            type="button"
          >
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </button>

          <button
            className={`nav-link ${activeTab === 'scan' ? 'active' : ''}`}
            onClick={() => setActiveTab('scan')}
            type="button"
          >
            <Camera size={18} />
            <span>Scan Product</span>
          </button>

          <button
            className={`nav-link ${activeTab === 'results' ? 'active' : ''}`}
            onClick={() => setActiveTab('results')}
            type="button"
          >
            <FileText size={18} />
            <span>Scan Report</span>
            {scanResult && (
              <span className="chip" style={{ marginLeft: 'auto', fontSize: '0.62rem', minHeight: '20px', padding: '0 6px' }}>
                Active
              </span>
            )}
          </button>

          <button
            className={`nav-link ${activeTab === 'repository' ? 'active' : ''}`}
            onClick={() => setActiveTab('repository')}
            type="button"
          >
            <Database size={18} />
            <span>Repository</span>
          </button>
        </nav>

        {/* Backend & Engine Health Badges */}
        <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div className={`status-pill ${isConnected ? 'online' : 'offline'}`} style={{ width: '100%', justifyContent: 'flex-start', fontSize: '0.72rem' }} title="Flask Backend API">
            <span className="pulse-dot"></span>
            <span>{isConnected ? 'Backend: CONNECTED' : 'Backend: OFFLINE'}</span>
          </div>

          <div
            className="status-pill online"
            style={{
              width: '100%',
              justifyContent: 'flex-start',
              fontSize: '0.7rem',
              background: (!ocrExecuted || ocrDetections > 0) ? 'var(--sage-soft)' : 'var(--terracotta-soft)',
              color: (!ocrExecuted || ocrDetections > 0) ? 'var(--sage-deep)' : '#b55246'
            }}
            title="Local Tesseract OCR Engine"
          >
            <span>
              {ocrExecuted ? (ocrDetections > 0 ? `OCR: ${ocrDetections} Detections` : 'OCR: No text found') : 'OCR: Tesseract (Local)'}
            </span>
          </div>

          <div
            className="status-pill online"
            style={{ width: '100%', justifyContent: 'flex-start', fontSize: '0.7rem', background: 'var(--sage-soft)', color: 'var(--sage-deep)' }}
            title="Open Food Facts API v3"
          >
            <span>OFF: API v3 Active</span>
          </div>
        </div>
      </aside>
    </>
  );
}

export function Topbar({ user, onLogout, setActiveTab, searchQuery, onSearchChange }) {
  return (
    <header className="topbar">
      <input
        className="search-box"
        type="text"
        placeholder="Search commodity, brand or label..."
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
      />

      <div className="topbar-actions">
        <button className="icon-btn" type="button" aria-label="Notifications" title="System Notifications">
          <Bell size={16} />
        </button>

        {!user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                color: 'var(--sage-deep)',
                background: 'var(--sage-soft)',
                border: '1px solid rgba(93, 143, 111, 0.25)',
                padding: '0.25rem 0.65rem',
                borderRadius: '9999px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
              title="Operating in Guest Mode. Scans are processed in memory and not saved to account history."
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--sage-deep)' }}></span>
              Guest Mode
            </span>
            <button
              className="btn secondary"
              onClick={() => setActiveTab('login')}
              type="button"
              style={{ minHeight: '34px', padding: '0 12px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
            >
              <LogIn size={14} />
              <span>Sign In</span>
            </button>
          </div>
        ) : (
          <button
            className="profile-btn"
            onClick={onLogout}
            title="Click to sign out"
            type="button"
          >
            <span className="profile-avatar">{user.username?.substring(0, 2).toUpperCase() || 'IA'}</span>
            <span>{user.username}</span>
          </button>
        )}
      </div>
    </header>
  );
}
