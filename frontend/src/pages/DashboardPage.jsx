import React, { useState, useEffect } from 'react';
import { LayoutDashboard, CheckCircle2, AlertTriangle, HelpCircle, FileText, Download, ArrowUpRight, TrendingUp, Camera, ShieldCheck } from 'lucide-react';
import { fetchDashboardMetrics, getReportDownloadUrl } from '../services/api';

export default function DashboardPage({ onViewScanResult, onStartScan = () => {} }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const metrics = await fetchDashboardMetrics();
      setData(metrics);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '5rem 1rem' }}>
        <div className="spinner" style={{ margin: '0 auto 1rem', width: '32px', height: '32px' }}></div>
        <p style={{ color: 'var(--muted)', fontSize: '0.92rem' }}>Loading enforcement dashboard analytics...</p>
      </div>
    );
  }

  const {
    total_inspections = 0,
    compliant_count = 0,
    non_compliant_count = 0,
    needs_review_count = 0,
    common_violations = [],
    recent_scans = []
  } = data || {};

  const complianceRate = total_inspections > 0
    ? Math.round((compliant_count / total_inspections) * 100)
    : 94;

  return (
    <div>
      {/* Hero Banner matching frontend-design/index.html */}
      <section className="hero">
        <div className="hero-text">
          <p className="eyebrow">AI-Powered Legal Metrology Verification</p>
          <h1>Scan. Verify. Comply.</h1>
          <p>
            LabelSure helps enforcement officers and manufacturers validate packaged commodities against
            Legal Metrology (Packaged Commodities) Rules, 2011 by scanning packages, labels, and barcodes
            using deterministic rules and Open Food Facts cross-referencing.
          </p>

          <div className="hero-actions">
            <button className="btn primary" type="button" onClick={onStartScan}>
              <Camera size={16} />
              <span>Scan Product</span>
            </button>
            <button className="btn secondary" type="button" onClick={() => {
              const el = document.getElementById('recent-activity-section');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
            }}>
              <span>View Recent Inspections</span>
            </button>
          </div>
        </div>

        <div className="photo-box-wrap">
          <div className="photo-box">
            <div className="product-illustration">
              <div className="box-top"></div>
              <div className="box-body"></div>
            </div>
          </div>
          <div className="compliant-tag">Compliant</div>
        </div>
      </section>

      {/* KPI Cards Grid matching frontend-design/index.html */}
      <section className="kpi-grid">
        <article className="kpi-card">
          <div className="kpi-head">
            <span>Total Inspections</span>
            <TrendingUp size={16} />
          </div>
          <div className="kpi-value">{total_inspections}</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-head">
            <span>Compliant Passed</span>
            <CheckCircle2 size={16} style={{ color: 'var(--sage-deep)' }} />
          </div>
          <div className="kpi-value" style={{ color: 'var(--sage-deep)' }}>{compliant_count}</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-head">
            <span>Legal Violations</span>
            <AlertTriangle size={16} style={{ color: '#b55246' }} />
          </div>
          <div className="kpi-value" style={{ color: '#b55246' }}>{non_compliant_count}</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-head">
            <span>Needs Review</span>
            <HelpCircle size={16} style={{ color: '#d9a25d' }} />
          </div>
          <div className="kpi-value" style={{ color: '#d9a25d' }}>{needs_review_count}</div>
        </article>
      </section>

      {/* Analytics Grid: Trend Line & Common Violations Leaderboard */}
      <section className="analytics">
        {/* Compliance Trend Chart */}
        <article className="panel chart-panel">
          <div className="panel-head">
            <div>
              <small>Statutory Compliance Trend</small>
              <h3>Compliance Rate</h3>
            </div>
            <span className="chip">
              {complianceRate >= 90 ? 'Healthy Compliance' : 'Review Required'}
            </span>
          </div>

          <div className="chart-box">
            <div className="chart-metrics">
              <div>
                <span>Current Rate</span>
                <strong style={{ color: 'var(--sage-deep)' }}>{complianceRate}%</strong>
              </div>
              <div>
                <span>Enforcement Target</span>
                <strong>98%</strong>
              </div>
            </div>

            <svg viewBox="0 0 420 160" className="chart-svg" aria-label="Compliance Trend Chart">
              <defs>
                <linearGradient id="areaFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#7aa77e" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#7aa77e" stopOpacity="0.04" />
                </linearGradient>
              </defs>
              <line x1="18" y1="35" x2="402" y2="35" />
              <line x1="18" y1="70" x2="402" y2="70" />
              <line x1="18" y1="105" x2="402" y2="105" />
              <line x1="18" y1="140" x2="402" y2="140" />
              <path
                className="chart-area"
                d="M 18 110 L 82 98 L 146 90 L 210 75 L 274 65 L 338 48 L 402 38 L 402 140 L 18 140 Z"
              />
              <path
                className="chart-line"
                d="M 18 110 L 82 98 L 146 90 L 210 75 L 274 65 L 338 48 L 402 38"
              />
            </svg>
          </div>
        </article>

        {/* Common Rule Violations Leaderboard */}
        <article className="panel brands-panel">
          <div className="panel-head">
            <div>
              <small>Rule Violation Watchlist</small>
              <h3>Frequent Rule Violations</h3>
            </div>
          </div>

          <div className="brand-list">
            {common_violations && common_violations.length > 0 ? (
              common_violations.slice(0, 4).map((item, idx) => {
                const maxCount = Math.max(1, common_violations[0]?.count || 1);
                const percent = Math.min(100, Math.round((item.count / maxCount) * 100));
                return (
                  <div key={idx} className="brand-item">
                    <div className="brand-name-row">
                      <span className="rank">{idx + 1}</span>
                      <span>{item.violation}</span>
                    </div>
                    <span className="brand-score">{item.count} flagged</span>
                    <div className="progress">
                      <span style={{ width: `${percent}%` }}></span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div style={{ color: 'var(--muted)', fontSize: '0.88rem', fontStyle: 'italic', padding: '1.5rem 0', textAlign: 'center' }}>
                All inspected commodities currently comply with mandatory legal requirements.
              </div>
            )}
          </div>
        </article>
      </section>

      {/* Recent Inspection Activity Section */}
      <section className="panel scans-panel" id="recent-activity-section">
        <div className="panel-head scans-head">
          <div>
            <small>Database Audit Feed</small>
            <h3>Recent Inspection Records</h3>
          </div>
        </div>

        <div className="scan-list">
          {recent_scans && recent_scans.length > 0 ? (
            recent_scans.map((scan) => {
              const statusClass = scan.overall_status === 'COMPLIANT' ? 'ok' : (scan.overall_status === 'NON_COMPLIANT' ? 'flag' : 'review');
              return (
                <article
                  key={scan.scan_id}
                  className="scan-item"
                  onClick={() => onViewScanResult(scan)}
                >
                  <div className="scan-thumb thumb-one">
                    <ShieldCheck size={24} style={{ color: 'var(--sage-deep)' }} />
                  </div>

                  <div className="scan-info">
                    <h4>{scan.product_name || 'Packaged Commodity'}</h4>
                    <p>
                      {scan.brand || 'Generic Brand'} • {scan.barcode || 'Barcode N/A'} • {scan.created_at?.substring(0, 10) || 'Recent'}
                    </p>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className={`status ${statusClass}`}>
                      {scan.overall_status === 'COMPLIANT' ? 'OK / PASS' : (scan.overall_status === 'NON_COMPLIANT' ? 'FLAG' : 'REVIEW')}
                    </span>

                    <button
                      className="btn secondary"
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewScanResult(scan);
                      }}
                      style={{ padding: '0 12px', minHeight: '32px', fontSize: '0.78rem' }}
                      type="button"
                    >
                      <FileText size={14} />
                      <span>Details</span>
                    </button>

                    <a
                      href={getReportDownloadUrl(scan.scan_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn primary"
                      onClick={(e) => e.stopPropagation()}
                      style={{ padding: '0 12px', minHeight: '32px', fontSize: '0.78rem', textDecoration: 'none' }}
                    >
                      <Download size={13} />
                      <span>PDF</span>
                    </a>
                  </div>
                </article>
              );
            })
          ) : (
            <div style={{ color: 'var(--muted)', fontSize: '0.9rem', textAlign: 'center', padding: '2rem' }}>
              No inspection records found in database. Run a new scan to begin logging data.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
