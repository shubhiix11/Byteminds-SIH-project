import React, { useState, useEffect } from 'react';
import { Search, Filter, Database, Calendar, FileText, ChevronRight, CheckCircle2, XCircle, HelpCircle, Package, ArrowLeft, Download, Building, Tag } from 'lucide-react';
import { fetchScans, getUploadUrl } from '../services/api';

const STATUS_COLOR_MAP = {
  COMPLIANT: 'var(--accent-emerald)',
  NON_COMPLIANT: 'var(--accent-rose)',
  NEEDS_REVIEW: 'var(--accent-amber)'
};

export default function RepositoryPage({ onViewScanResult }) {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productHistory, setProductHistory] = useState([]);

  const loadScans = async () => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams();
      if (search) queryParams.append('search', search);
      if (statusFilter !== 'ALL') queryParams.append('status', statusFilter);

      const res = await fetch(`http://localhost:5001/api/scans?${queryParams.toString()}`);
      const data = await res.json();
      if (data.success) {
        setScans(data.scans || []);
      }
    } catch (err) {
      console.error("Failed to load repository scans:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScans();
  }, [search, statusFilter]);

  // Group scans by product name to show aggregated product cards
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
    <div className="container">
      {/* Page Title */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="title-gradient" style={{ fontSize: '2.2rem', fontWeight: 800 }}>
          Packaged Commodity Product Repository
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1rem', marginTop: '0.4rem' }}>
          Searchable enforcement database of inspected commodities and historical compliance reports.
        </p>
      </div>

      {/* Search & Filter Bar */}
      <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ flex: 1, position: 'relative', minWidth: '280px' }}>
          <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
          <input
            type="text"
            placeholder="Search by product name, brand, barcode, manufacturer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '0.7rem 1rem 0.7rem 2.75rem',
              borderRadius: '10px',
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-main)',
              fontSize: '0.9rem',
              outline: 'none'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {['ALL', 'COMPLIANT', 'NON_COMPLIANT', 'NEEDS_REVIEW'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`nav-button ${statusFilter === st ? 'active' : ''}`}
              style={{ padding: '0.5rem 1rem', fontSize: '0.82rem' }}
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
          <p style={{ color: 'var(--text-muted)' }}>Querying product repository...</p>
        </div>
      ) : productList.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem 2rem', maxWidth: '500px', margin: '0 auto' }}>
          <Database size={48} style={{ color: 'var(--text-dim)', marginBottom: '1rem' }} />
          <h3 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.5rem' }}>No Inspection Records Found</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            No commodity records match your current search and status filters.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
          {productList.map((prod, idx) => (
            <div
              key={idx}
              className="glass-panel"
              onClick={() => openProductDetails(prod)}
              style={{
                padding: '1.5rem',
                cursor: 'pointer',
                transition: 'all 0.25s ease',
                borderLeft: `4px solid ${STATUS_COLOR_MAP[prod.latestStatus] || 'var(--accent-amber)'}`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', uppercase: 'true' }}>
                    {prod.brand}
                  </span>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 800, marginTop: '0.2rem', color: 'var(--text-main)' }}>
                    {prod.name}
                  </h3>
                </div>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  padding: '0.3rem 0.75rem',
                  borderRadius: '9999px',
                  background: `rgba(${prod.latestStatus === 'COMPLIANT' ? '16, 185, 129' : prod.latestStatus === 'NON_COMPLIANT' ? '244, 63, 94' : '245, 158, 11'}, 0.15)`,
                  color: STATUS_COLOR_MAP[prod.latestStatus] || 'var(--accent-amber)',
                  border: `1px solid ${STATUS_COLOR_MAP[prod.latestStatus] || 'var(--accent-amber)'}`
                }}>
                  {prod.latestStatus}
                </span>
              </div>

              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
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
                justify: 'space-between',
                alignItems: 'center',
                paddingTop: '0.75rem',
                borderTop: '1px solid var(--border-color)',
                fontSize: '0.8rem',
                color: 'var(--text-dim)'
              }}>
                <span>Inspections: <strong>{prod.scans.length}</strong></span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: 'var(--accent-cyan)' }}>
                  View History <ChevronRight size={14} />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Product Details & Inspection History Drawer / Modal */}
      {selectedProduct && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(8px)',
          zIndex: 200,
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '560px',
            background: 'var(--bg-surface)',
            height: '100%',
            overflowY: 'auto',
            padding: '2rem',
            borderLeft: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <button
              onClick={() => setSelectedProduct(null)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                cursor: 'pointer',
                marginBottom: '1.5rem',
                fontWeight: 600
              }}
            >
              <ArrowLeft size={16} />
              <span>Back to Repository</span>
            </button>

            <div style={{ marginBottom: '1.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                {selectedProduct.brand}
              </span>
              <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '0.2rem' }}>
                {selectedProduct.name}
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '0.3rem' }}>
                Manufacturer: {selectedProduct.manufacturer} • Barcode: {selectedProduct.barcode}
              </p>
            </div>

            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '1rem', textTransform: 'uppercase' }}>
              Inspection History Timeline ({productHistory.length})
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', flex: 1 }}>
              {productHistory.map((scanItem) => (
                <div
                  key={scanItem.scan_id}
                  className="glass-panel"
                  style={{ padding: '1.25rem', borderLeft: `4px solid ${STATUS_COLOR_MAP[scanItem.overall_status] || 'var(--accent-amber)'}` }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--accent-cyan)' }} className="mono-text">
                      #{scanItem.scan_id}
                    </span>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 800,
                      padding: '0.2rem 0.6rem',
                      borderRadius: '9999px',
                      color: STATUS_COLOR_MAP[scanItem.overall_status] || 'var(--accent-amber)',
                      background: `rgba(${scanItem.overall_status === 'COMPLIANT' ? '16, 185, 129' : scanItem.overall_status === 'NON_COMPLIANT' ? '244, 63, 94' : '245, 158, 11'}, 0.15)`
                    }}>
                      {scanItem.overall_status}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.8rem' }}>
                    Date: {scanItem.created_at?.substring(0, 10) || '2026-09-11'} • Inspector: {scanItem.inspector || 'Inspector Alpha'}
                  </div>

                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button
                      className="btn-secondary"
                      onClick={() => {
                        setSelectedProduct(null);
                        onViewScanResult(scanItem);
                      }}
                      style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                    >
                      <FileText size={14} />
                      <span>View Inspection Data</span>
                    </button>

                    <a
                      href={`http://localhost:5001/api/reports/${scanItem.scan_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-primary"
                      style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', textDecoration: 'none' }}
                    >
                      <Download size={14} />
                      <span>PDF Report</span>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
