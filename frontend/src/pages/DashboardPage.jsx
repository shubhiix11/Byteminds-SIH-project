import React, { useState, useEffect } from 'react';
import { LayoutDashboard, CheckCircle2, XCircle, AlertTriangle, HelpCircle, FileText, AlertCircle, Download, ArrowUpRight, TrendingUp } from 'lucide-react';

const STATUS_COLOR_MAP = {
  COMPLIANT: 'var(--accent-emerald)',
  NON_COMPLIANT: 'var(--accent-rose)',
  NEEDS_REVIEW: 'var(--accent-amber)'
};

export default function DashboardPage({ onViewScanResult }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:5001/api/dashboard');
      const json = await res.json();
      if (json.success) {
        setData(json.dashboard);
      }
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '5rem 1rem' }}>
        <div className="spinner" style={{ margin: '0 auto 1rem', width: '32px', height: '32px' }}></div>
        <p style={{ color: 'var(--text-muted)' }}>Loading enforcement dashboard analytics...</p>
      </div>
    );
  }

  const { total_inspections, compliant_count, non_compliant_count, needs_review_count, common_violations, recent_scans, attention_products } = data || {};

  return (
    <div className="container">
      {/* Title */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="title-gradient" style={{ fontSize: '2.2rem', fontWeight: 800 }}>
          Legal Metrology Enforcement Dashboard
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1rem', marginTop: '0.4rem' }}>
          Real-time analytics and enforcement monitoring derived from persistent database scan records.
        </p>
      </div>

      {/* KPI Cards Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Total Inspections
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, marginTop: '0.2rem' }}>
            {total_inspections || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.4rem' }}>
            Recorded in database
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem', borderColor: 'rgba(16, 185, 129, 0.3)' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-emerald)', textTransform: 'uppercase' }}>
            Compliant
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--accent-emerald)', marginTop: '0.2rem' }}>
            {compliant_count || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.4rem' }}>
            Passed all mandatory checks
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem', borderColor: 'rgba(244, 63, 94, 0.3)' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-rose)', textTransform: 'uppercase' }}>
            Non-Compliant
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--accent-rose)', marginTop: '0.2rem' }}>
            {non_compliant_count || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.4rem' }}>
            Failed at least 1 mandatory rule
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem', borderColor: 'rgba(245, 158, 11, 0.3)' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-amber)', textTransform: 'uppercase' }}>
            Needs Review
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--accent-amber)', marginTop: '0.2rem' }}>
            {needs_review_count || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.4rem' }}>
            Unverifiable evidence required
          </div>
        </div>
      </div>

      {/* Main Grid: Common Violations & Priority Products */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        
        {/* Left Column: Common Violations Breakdown */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TrendingUp size={20} style={{ color: 'var(--accent-rose)' }} />
            <span>Common Rule Violations</span>
          </h3>

          {common_violations && common_violations.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {common_violations.map((v, idx) => (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem', fontWeight: 600, marginBottom: '0.3rem' }}>
                    <span>{v.violation}</span>
                    <span style={{ color: 'var(--accent-rose)', fontWeight: 700 }}>{v.count} incident(s)</span>
                  </div>
                  <div style={{ width: '100%', background: 'rgba(255,255,255,0.05)', borderRadius: '9999px', height: '8px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${Math.min(100, (v.count / Math.max(1, non_compliant_count + needs_review_count)) * 100)}%`,
                      background: 'linear-gradient(90deg, #f43f5e 0%, #f59e0b 100%)',
                      height: '100%'
                    }}></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic', padding: '2rem 0', textAlign: 'center' }}>
              No rule violations recorded in database yet.
            </div>
          )}
        </div>

        {/* Right Column: Products Requiring Attention */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={20} style={{ color: 'var(--accent-amber)' }} />
            <span>Products Requiring Attention</span>
          </h3>

          {attention_products && attention_products.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {attention_products.slice(0, 5).map((item) => (
                <div
                  key={item.scan_id}
                  style={{
                    background: 'rgba(0,0,0,0.3)',
                    padding: '0.85rem 1rem',
                    borderRadius: '10px',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>{item.product_name}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{item.brand} • {item.created_at?.substring(0, 10)}</div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      padding: '0.2rem 0.6rem',
                      borderRadius: '9999px',
                      color: STATUS_COLOR_MAP[item.overall_status] || 'var(--accent-amber)',
                      background: `rgba(${item.overall_status === 'NON_COMPLIANT' ? '244, 63, 94' : '245, 158, 11'}, 0.15)`
                    }}>
                      {item.overall_status}
                    </span>

                    <button
                      className="btn-secondary"
                      onClick={() => onViewScanResult(item)}
                      style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                    >
                      <ArrowUpRight size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic', padding: '2rem 0', textAlign: 'center' }}>
              All inspected products are currently fully compliant.
            </div>
          )}
        </div>
      </div>

      {/* Recent Inspections Feed Table */}
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
          Recent Inspection Records
        </h3>

        {recent_scans && recent_scans.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.75rem' }}>Scan ID</th>
                  <th style={{ padding: '0.75rem' }}>Product Name</th>
                  <th style={{ padding: '0.75rem' }}>Brand</th>
                  <th style={{ padding: '0.75rem' }}>Status</th>
                  <th style={{ padding: '0.75rem' }}>Date</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recent_scans.map((scan) => (
                  <tr key={scan.scan_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 700, color: 'var(--accent-cyan)' }} className="mono-text">
                      #{scan.scan_id}
                    </td>
                    <td style={{ padding: '0.75rem', fontWeight: 600 }}>{scan.product_name}</td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>{scan.brand}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: 800,
                        padding: '0.2rem 0.6rem',
                        borderRadius: '9999px',
                        color: STATUS_COLOR_MAP[scan.overall_status] || 'var(--accent-amber)',
                        background: `rgba(${scan.overall_status === 'COMPLIANT' ? '16, 185, 129' : scan.overall_status === 'NON_COMPLIANT' ? '244, 63, 94' : '245, 158, 11'}, 0.15)`
                      }}>
                        {scan.overall_status}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
                      {scan.created_at?.substring(0, 10) || '2026-09-11'}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                        <button
                          className="btn-secondary"
                          onClick={() => onViewScanResult(scan)}
                          style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                        >
                          <FileText size={14} />
                        </button>
                        <a
                          href={`http://localhost:5001/api/reports/${scan.scan_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-primary"
                          style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem', textDecoration: 'none' }}
                        >
                          <Download size={14} />
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', padding: '2rem' }}>
            No recent scans recorded.
          </div>
        )}
      </div>
    </div>
  );
}
