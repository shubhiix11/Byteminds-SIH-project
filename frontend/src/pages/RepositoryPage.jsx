import React, { useState, useEffect } from 'react';
import { Search, Database, FileText, ChevronRight, ArrowLeft, Download, Building, Tag, ShieldCheck } from 'lucide-react';
import { fetchScans, getReportDownloadUrl } from '../services/api';

const STATUS_COLOR_MAP = {
  COMPLIANT: 'var(--sage-deep)',
  NON_COMPLIANT: '#b55246',
  NEEDS_REVIEW: '#d9a25d'
};

export default function RepositoryPage({ user, onViewScanResult, externalSearch = '', onNavigateLogin, onStartScan }) {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(Boolean(user));
  const [search, setSearch] = useState(externalSearch);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productHistory, setProductHistory] = useState([]);

  // Sync with external search query if provided by topbar
  useEffect(() => {
    if (externalSearch !== undefined && externalSearch !== search) {
      setSearch(externalSearch);
    }
  }, [externalSearch]);

  const loadScans = async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const scanList = await fetchScans({ search, status: statusFilter });
      setScans(scanList || []);
    } catch (err) {
      console.error("Failed to load repository scans:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScans();
  }, [search, statusFilter, user]);

  if (!user) {
    return (
      <div style={{ maxWidth: '640px', margin: '3rem auto 0', padding: '0 1rem' }}>
        <div className="panel" style={{ padding: '2.8rem 2rem', textAlign: 'center' }}>
          <div style={{
            width: '60px',
            height: '60px',
            borderRadius: '18px',
            background: 'var(--sage-soft)',
            color: 'var(--sage-deep)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '1.25rem',
            boxShadow: '0 6px 16px rgba(93, 143, 111, 0.15)'
          }}>
            <Database size={30} />
          </div>

          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text)', marginBottom: '0.5rem' }}>
            Inspection history is available after signing in.
          </h2>

          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', lineHeight: '1.6', maxWidth: '480px', margin: '0 auto 1.8rem' }}>
            Sign in with your Inspector ID to access permanent commodity records, audit trails, and certified inspection reports. Guest scans are processed in-memory and are not saved to the public repository.
          </p>

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            {onNavigateLogin && (
              <button
                type="button"
                className="btn primary"
                onClick={onNavigateLogin}
                style={{ minHeight: '42px', padding: '0 22px' }}
              >
                <span>Sign In to Access Repository</span>
              </button>
            )}
            {onStartScan && (
              <button
                type="button"
                className="btn secondary"
                onClick={onStartScan}
                style={{ minHeight: '42px', padding: '0 18px' }}
              >
                <span>Perform Guest Scan</span>
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Group scans by product name to show aggregated commodity cards
  const groupedProducts = scans.reduce((acc, scan) => {
    const key = (scan.product_name || 'Unknown Commodity').toLowerCase().trim();
    if (!acc[key]) {
      acc[key] = {
        name: scan.product_name || 'Unknown Commodity',
        brand: scan.brand || 'Generic Brand',
        category: scan.category || 'Packaged Commodity',
        barcode: scan.barcode || 'N/A',
        manufacturer: scan.manufacturer || 'Unknown Manufacturer',
        latestStatus: scan.overall_status,
        lastInspection: scan.created_at,
        scans: [scan]
      };
    } else {
      acc[key].scans.push(scan);
    }
    return acc;
  }, {});

  const productList = Object.values(groupedProducts);

  const openProductDetails = (prod) => {
    setSelectedProduct(prod);
    setProductHistory(prod.scans || []);
  };

  return (
    <div>
      {/* Page Title Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <span className="eyebrow">Commodity Registry Database</span>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.04em', color: 'var(--text)', margin: '4px 0 6px' }}>
          Packaged Commodity Inspection Repository
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '0.94rem' }}>
          Searchable enforcement database of inspected commodities, statutory compliance records, and historical PDF reports.
        </p>
      </div>

      {/* Search & Filter Bar */}
      <div className="panel" style={{ padding: '1.1rem 1.4rem', marginBottom: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ flex: 1, position: 'relative', minWidth: '260px' }}>
          <Search size={17} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)' }} />
          <input
            type="text"
            placeholder="Search by commodity name, brand, barcode, manufacturer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-box"
            style={{ width: '100%', paddingLeft: '2.6rem' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {['ALL', 'COMPLIANT', 'NON_COMPLIANT', 'NEEDS_REVIEW'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`btn ${statusFilter === st ? 'primary' : 'secondary'}`}
              style={{ minHeight: '36px', padding: '0 12px', fontSize: '0.78rem' }}
              type="button"
            >
              {st === 'ALL' ? 'All Statuses' : st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid or Loading / Empty state */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
          <div className="spinner" style={{ margin: '0 auto 1rem', width: '32px', height: '32px' }}></div>
          <p style={{ color: 'var(--muted)', fontSize: '0.92rem' }}>Querying product repository...</p>
        </div>
      ) : productList.length === 0 ? (
        <div className="panel" style={{ textAlign: 'center', padding: '3.5rem 2rem', maxWidth: '500px', margin: '2rem auto' }}>
          <Database size={44} style={{ color: 'var(--muted)', marginBottom: '0.75rem' }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '0.4rem' }}>No Inspection Records Found</h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.88rem' }}>
            No commodity records match your current search and status filters. Try refining your keywords or status filter.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {productList.map((prod, idx) => {
            const statusClass = prod.latestStatus === 'COMPLIANT' ? 'ok' : (prod.latestStatus === 'NON_COMPLIANT' ? 'flag' : 'review');
            return (
              <div
                key={idx}
                className="panel"
                onClick={() => openProductDetails(prod)}
                style={{
                  padding: '1.35rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  borderLeft: `4px solid ${STATUS_COLOR_MAP[prod.latestStatus] || 'var(--accent-amber)'}`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.6rem' }}>
                  <div>
                    <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      {prod.brand}
                    </span>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginTop: '0.15rem', color: 'var(--text)' }}>
                      {prod.name}
                    </h3>
                  </div>
                  <span className={`status ${statusClass}`}>
                    {prod.latestStatus === 'COMPLIANT' ? 'PASS' : (prod.latestStatus === 'NON_COMPLIANT' ? 'FLAG' : 'REVIEW')}
                  </span>
                </div>

                <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Building size={14} />
                    <span>{prod.manufacturer}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Tag size={14} />
                    <span>Barcode: {prod.barcode}</span>
                  </div>
                </div>

                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingTop: '0.75rem',
                  borderTop: '1px solid var(--border)',
                  fontSize: '0.8rem',
                  color: 'var(--muted)'
                }}>
                  <span>Inspections: <strong>{prod.scans.length}</strong></span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: 'var(--sage-deep)', fontWeight: 700 }}>
                    View History <ChevronRight size={14} />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Product Details & Inspection History Drawer */}
      {selectedProduct && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(19, 28, 25, 0.35)',
          backdropFilter: 'blur(6px)',
          zIndex: 200,
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '560px',
            background: 'var(--panel)',
            height: '100%',
            overflowY: 'auto',
            padding: '2rem',
            borderLeft: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '-10px 0 30px rgba(0,0,0,0.1)'
          }}>
            <button
              onClick={() => setSelectedProduct(null)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--muted)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                cursor: 'pointer',
                marginBottom: '1.5rem',
                fontWeight: 700,
                fontSize: '0.88rem'
              }}
              type="button"
            >
              <ArrowLeft size={16} />
              <span>Back to Repository</span>
            </button>

            <div style={{ marginBottom: '1.5rem' }}>
              <span className="eyebrow">{selectedProduct.brand}</span>
              <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text)', marginTop: '0.2rem' }}>
                {selectedProduct.name}
              </h2>
              <p style={{ color: 'var(--muted)', fontSize: '0.88rem', marginTop: '0.3rem' }}>
                Manufacturer: {selectedProduct.manufacturer} • Barcode: {selectedProduct.barcode}
              </p>
            </div>

            <h3 style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--sage-deep)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Inspection History Timeline ({productHistory.length})
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', flex: 1 }}>
              {productHistory.map((scanItem) => {
                const statusClass = scanItem.overall_status === 'COMPLIANT' ? 'ok' : (scanItem.overall_status === 'NON_COMPLIANT' ? 'flag' : 'review');
                return (
                  <div
                    key={scanItem.scan_id}
                    className="panel"
                    style={{ padding: '1.25rem', borderLeft: `4px solid ${STATUS_COLOR_MAP[scanItem.overall_status] || 'var(--accent-amber)'}` }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--sage-deep)' }} className="mono-text">
                        #{scanItem.scan_id}
                      </span>
                      <span className={`status ${statusClass}`}>
                        {scanItem.overall_status}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginBottom: '0.8rem' }}>
                      Date: {scanItem.created_at?.substring(0, 10) || '2026-09-12'} • Inspector: {scanItem.inspector || user?.username || 'Inspector'}
                    </div>

                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                      <button
                        className="btn secondary"
                        onClick={() => {
                          setSelectedProduct(null);
                          onViewScanResult(scanItem);
                        }}
                        style={{ padding: '0 12px', minHeight: '34px', fontSize: '0.78rem' }}
                        type="button"
                      >
                        <FileText size={14} />
                        <span>View Inspection Data</span>
                      </button>

                      <a
                        href={getReportDownloadUrl(scanItem.scan_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn primary"
                        style={{ padding: '0 12px', minHeight: '34px', fontSize: '0.78rem', textDecoration: 'none' }}
                      >
                        <Download size={14} />
                        <span>PDF Report</span>
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
