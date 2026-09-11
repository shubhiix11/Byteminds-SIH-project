import React from 'react';
import { ShieldCheck, ScanLine, LogIn, FileText, Database, LayoutDashboard } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, isConnected, healthData, scanResult, user, onLogout }) {
  const ocrDetections = scanResult?.ocr_detections?.length ?? scanResult?.debug?.["LOCAL OCR"]?.detections_count ?? null;
  const ocrExecuted = Boolean(scanResult);

  return (
    <nav className="navbar">
      <div className="nav-brand" onClick={() => setActiveTab('scan')} style={{ cursor: 'pointer' }}>
        <div style={{
          background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
          padding: '0.5rem',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#0a0e17'
        }}>
          <ShieldCheck size={24} strokeWidth={2.5} />
        </div>
        <div>
          <span>LabelSure</span>
          <div style={{ fontSize: '0.68rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            LEGAL METROLOGY PLATFORM
          </div>
        </div>
      </div>

      <div className="nav-links" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {/* Section 19 & 17 Status Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', flexWrap: 'wrap', marginRight: '0.5rem' }}>
          {/* Backend Status */}
          <div className={`status-pill ${isConnected ? 'online' : 'offline'}`} title="Backend API">
            <span className="pulse-dot"></span>
            <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>{isConnected ? 'Backend: CONNECTED' : 'Backend: OFFLINE'}</span>
          </div>

          {/* OCR Engine Status (Section 17) */}
          <div
            className="status-pill online"
            style={{
              background: (!ocrExecuted || ocrDetections > 0) ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.15)',
              color: (!ocrExecuted || ocrDetections > 0) ? 'var(--accent-emerald)' : 'var(--accent-amber)',
              border: `1px solid ${(!ocrExecuted || ocrDetections > 0) ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.4)'}`
            }}
            title={ocrExecuted && ocrDetections === 0 ? "OCR executed but no reliable text was extracted." : "Primary Local OCR Engine"}
          >
            <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>
              {ocrExecuted ? (
                ocrDetections > 0 ? (
                  `OCR: TESSERACT | Status: ACTIVE | Executed: YES | Detections: ${ocrDetections}`
                ) : (
                  "OCR executed but no reliable text was extracted."
                )
              ) : (
                'OCR: TESSERACT ACTIVE (LOCAL)'
              )}
            </span>
          </div>

          {/* OpenAI Vision Status */}
          <div className="status-pill" style={{
            background: healthData?.api_key_configured === 'YES' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(156, 163, 175, 0.12)',
            color: healthData?.api_key_configured === 'YES' ? 'var(--accent-cyan)' : 'var(--text-muted)',
            border: `1px solid ${healthData?.api_key_configured === 'YES' ? 'rgba(56, 189, 248, 0.3)' : 'rgba(156, 163, 175, 0.3)'}`
          }} title="Optional OpenAI Vision Layer">
            <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>OpenAI Vision: {healthData?.api_key_configured === 'YES' ? 'AVAILABLE' : 'UNAVAILABLE'}</span>
          </div>

          {/* Barcode Decoder Status */}
          <div className="status-pill online" style={{ background: 'rgba(16, 185, 129, 0.12)', color: 'var(--accent-emerald)', border: '1px solid rgba(16, 185, 129, 0.3)' }} title="Pixel Barcode Engine">
            <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>Barcode: READY</span>
          </div>
        </div>

        <button
          className={`nav-button ${activeTab === 'scan' ? 'active' : ''}`}
          onClick={() => setActiveTab('scan')}
        >
          <ScanLine size={18} />
          <span>Scan Label</span>
        </button>

        <button
          className={`nav-button ${activeTab === 'repository' ? 'active' : ''}`}
          onClick={() => setActiveTab('repository')}
        >
          <Database size={18} />
          <span>Repository</span>
        </button>

        <button
          className={`nav-button ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <LayoutDashboard size={18} />
          <span>Dashboard</span>
        </button>

        {user ? (
          <button
            className="nav-button"
            onClick={onLogout}
            style={{ color: 'var(--accent-rose)' }}
          >
            <span>Logout ({user.username})</span>
          </button>
        ) : (
          <button
            className={`nav-button ${activeTab === 'login' ? 'active' : ''}`}
            onClick={() => setActiveTab('login')}
          >
            <LogIn size={18} />
            <span>Inspector Login</span>
          </button>
        )}
      </div>
    </nav>
  );
}
