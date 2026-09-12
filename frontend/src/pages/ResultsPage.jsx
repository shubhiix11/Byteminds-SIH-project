import React, { useState } from 'react';
import { Package, Tag, Calendar, Building, PhoneCall, Globe, Code2, LayoutGrid, CheckCircle2, XCircle, AlertTriangle, HelpCircle, ArrowLeft, Info, FileText, Barcode, Check, AlertCircle, Layers, Eye, ExternalLink, Search, ChevronDown, ChevronUp, Apple, ShoppingBag } from 'lucide-react';
import { getUploadUrl, getReportDownloadUrl, saveScanRecord } from '../services/api';

const STATUS_COLOR_MAP = {
  PASS: '#10b981',
  FAIL: '#f43f5e',
  WARNING: '#f59e0b',
  NOT_VERIFIABLE: '#60a5fa',
  NOT_APPLICABLE: '#6b7280'
};

export default function ResultsPage({ scanResult, onNewScan, user, onNavigateLogin, onScanSaved }) {
  const [viewMode, setViewMode] = useState(
    (scanResult?.openfoodfacts?.status === 'FOUND' || scanResult?.openfoodfacts_product || scanResult?.barcode)
      ? 'openfoodfacts'
      : 'rules'
  );
  const [imageTab, setImageTab] = useState('interactive'); // 'interactive' | 'annotated' | 'original'
  const [selectedRuleId, setSelectedRuleId] = useState(null);
  const [searchTraceOpen, setSearchTraceOpen] = useState(false);
  const [dismissedGuestCta, setDismissedGuestCta] = useState(false);
  const [isSaved, setIsSaved] = useState(Boolean(scanResult?.persisted));
  const [saving, setSaving] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState(null);

  const handleSaveScan = async () => {
    if (!user) {
      if (onNavigateLogin) onNavigateLogin();
      return;
    }
    setSaving(true);
    try {
      await saveScanRecord(scanResult, user.username);
      setIsSaved(true);
      setSaveSuccessMsg(`Inspection #${scanResult.scan_id} saved to your repository!`);
      if (onScanSaved) {
        onScanSaved({ ...scanResult, persisted: true, is_guest: false, inspector: user.username });
      }
    } catch (err) {
      console.error(err);
      alert(err.message || 'Failed to save scan record.');
    } finally {
      setSaving(false);
    }
  };

  if (!scanResult) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '5rem 1rem' }}>
        <div className="glass-panel" style={{ padding: '3rem', maxWidth: '500px', margin: '0 auto' }}>
          <Package size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.5rem' }}>No Scan Selected</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Upload a commodity package label to view extracted Legal Metrology declarations and evidence.
          </p>
          <button className="btn-primary" onClick={onNewScan}>
            <span>Scan Package Label</span>
          </button>
        </div>
      </div>
    );
  }

  const {
    scan_id, filename, image_url, original_image_url, annotated_image_url,
    overall_status, summary, rule_results, detected_declarations,
    product_enrichment, cross_check, measurements, annotations,
    rule_set_version, inspection_date, disclaimer, web_research
  } = scanResult;

  const declarations = detected_declarations || scanResult.extracted_facts?.declarations || {};
  const enrichmentData = product_enrichment?.enrichment || scanResult.enrichment?.enrichment || {};
  const webResearch = web_research || scanResult.webResearch || {};
  const openFoodFacts = scanResult.openfoodfacts || (scanResult.openfoodfacts_product ? {
    available: scanResult.openfoodfacts_status === 'FOUND',
    status: scanResult.openfoodfacts_status,
    product: scanResult.openfoodfacts_product,
    source_url: scanResult.openfoodfacts_source_url,
    retrieved_at: scanResult.openfoodfacts_retrieved_at,
    cross_check: scanResult.openfoodfacts_cross_check
  } : null);
  const offProduct = openFoodFacts?.product || null;
  const offCrossCheck = openFoodFacts?.cross_check || scanResult.openfoodfacts_cross_check || null;

  const activeImageUrl = imageTab === 'annotated' && annotated_image_url ? annotated_image_url : (original_image_url || image_url);

  const resolvedBarcodeSource = scanResult.barcode_source || (
    scanResult.barcode_decoding?.detected ? 'IMAGE_DETECTED' : (scanResult.barcode && scanResult.barcode !== 'NOT_DETECTED' ? 'MANUAL_ENTRY' : null)
  );
  const barcodeSourceText = resolvedBarcodeSource === 'IMAGE_DETECTED'
    ? 'Barcode source: Image detected'
    : (resolvedBarcodeSource === 'MANUAL_ENTRY' ? 'Barcode source: Manually entered' : null);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PASS':
        return <span className="status-pill online" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.3)' }}><CheckCircle2 size={13} /> PASS</span>;
      case 'FAIL':
        return <span className="status-pill offline" style={{ background: 'rgba(244, 63, 94, 0.15)', color: '#f43f5e', border: '1px solid rgba(244, 63, 94, 0.3)' }}><XCircle size={13} /> FAIL</span>;
      case 'WARNING':
        return <span className="status-pill" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.3)' }}><AlertTriangle size={13} /> WARNING</span>;
      case 'NOT_VERIFIABLE':
        return <span className="status-pill" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}><HelpCircle size={13} /> NOT VERIFIABLE</span>;
      case 'NOT_APPLICABLE':
      default:
        return <span className="status-pill" style={{ background: 'rgba(156, 163, 175, 0.15)', color: '#9ca3af', border: '1px solid rgba(156, 163, 175, 0.3)' }}>N/A</span>;
    }
  };

  const getOverallColor = (status) => {
    if (status === 'COMPLIANT') return 'var(--accent-emerald)';
    if (status === 'NON_COMPLIANT') return 'var(--accent-rose)';
    return 'var(--accent-amber)';
  };

  return (
    <div className="container">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <button
            onClick={onNewScan}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--accent-cyan)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              marginBottom: '0.4rem'
            }}
          >
            <ArrowLeft size={16} />
            <span>New Package Scan</span>
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Scan Report #{scan_id || 'DEMO'}</h1>
            <div style={{
              background: `rgba(${overall_status === 'COMPLIANT' ? '16, 185, 129' : overall_status === 'NON_COMPLIANT' ? '244, 63, 94' : '245, 158, 11'}, 0.15)`,
              border: `1px solid ${getOverallColor(overall_status)}`,
              color: getOverallColor(overall_status),
              padding: '0.35rem 0.9rem',
              borderRadius: '9999px',
              fontWeight: 800,
              fontSize: '0.85rem',
              letterSpacing: '0.05em'
            }}>
              {overall_status || 'NEEDS_REVIEW'}
            </div>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
            File: {filename} • Rule Set: {rule_set_version || '2026.1-PC-RULES'} • Date: {inspection_date || '2026-09-11'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', background: 'var(--panel)', padding: '0.35rem', borderRadius: '14px', border: '1px solid var(--border)', alignItems: 'center' }}>
          <a
            href={getReportDownloadUrl(scan_id)}
            target="_blank"
            rel="noopener noreferrer"
            className="btn primary"
            style={{ padding: '0.4rem 0.85rem', fontSize: '0.82rem', textDecoration: 'none', minHeight: '36px' }}
          >
            <span>Download PDF Report</span>
          </a>

          <button
            className={`nav-button ${viewMode === 'rules' ? 'active' : ''}`}
            onClick={() => setViewMode('rules')}
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.82rem' }}
          >
            <FileText size={16} />
            <span>Package Label Analysis ({rule_results?.length || 0})</span>
          </button>

          <button
            className={`nav-button ${viewMode === 'openfoodfacts' ? 'active' : ''}`}
            onClick={() => setViewMode('openfoodfacts')}
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <Apple size={16} style={{ color: openFoodFacts?.status === 'FOUND' ? 'var(--accent-emerald)' : 'inherit' }} />
            <span>Open Food Facts Product Data</span>
            {openFoodFacts?.status === 'FOUND' && (
              <span style={{
                background: 'rgba(16, 185, 129, 0.2)',
                color: 'var(--accent-emerald)',
                fontSize: '0.62rem',
                padding: '0.1rem 0.4rem',
                borderRadius: '4px',
                fontWeight: 800
              }}>
                FOUND
              </span>
            )}
            {openFoodFacts?.status === 'NOT_FOUND' && (
              <span style={{
                background: 'rgba(245, 158, 11, 0.2)',
                color: 'var(--accent-amber)',
                fontSize: '0.62rem',
                padding: '0.1rem 0.4rem',
                borderRadius: '4px',
                fontWeight: 700
              }}>
                NOT FOUND
              </span>
            )}
          </button>

          <button
            className={`nav-button ${viewMode === 'enrichment' ? 'active' : ''}`}
            onClick={() => setViewMode('enrichment')}
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.82rem' }}
          >
            <Barcode size={16} />
            <span>Product & Barcode</span>
          </button>

          <button
            className={`nav-button ${viewMode === 'web_research' ? 'active' : ''}`}
            onClick={() => setViewMode('web_research')}
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.82rem' }}
          >
            <Globe size={16} />
            <span>Web Research</span>
          </button>

          <button
            className={`nav-button ${viewMode === 'grid' ? 'active' : ''}`}
            onClick={() => setViewMode('grid')}
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.82rem' }}
          >
            <LayoutGrid size={16} />
            <span>Extracted Facts</span>
          </button>

          <button
            className={`nav-button ${viewMode === 'json' ? 'active' : ''}`}
            onClick={() => setViewMode('json')}
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.82rem' }}
          >
            <Code2 size={16} />
            <span>Raw JSON</span>
          </button>
        </div>
      </div>

      {/* Subtle Call-to-Action for Guest Scans (Requirement 6) */}
      {(!user || (!isSaved && scanResult?.is_guest)) && !dismissedGuestCta && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(122, 167, 126, 0.12), rgba(255, 253, 251, 0.95))',
          border: '1px solid rgba(122, 167, 126, 0.35)',
          borderRadius: '16px',
          padding: '1.1rem 1.4rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.2rem' }}>
              <span className="status-pill online" style={{ fontSize: '0.7rem', padding: '0.1rem 0.5rem' }}>
                Guest Inspection
              </span>
              <strong style={{ fontSize: '0.92rem', color: 'var(--text)' }}>
                Want to save this inspection?
              </strong>
            </div>
            <p style={{ color: 'var(--muted)', fontSize: '0.82rem', margin: 0, lineHeight: '1.4' }}>
              Sign in to keep this scan, report, and inspection history in your permanent repository.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn primary"
              onClick={handleSaveScan}
              disabled={saving}
              style={{ minHeight: '36px', padding: '0 14px', fontSize: '0.82rem' }}
            >
              {saving ? 'Saving...' : (user ? 'Save to Repository' : 'Sign In to Save')}
            </button>
            <button
              type="button"
              className="btn secondary"
              onClick={() => setDismissedGuestCta(true)}
              style={{ minHeight: '36px', padding: '0 12px', fontSize: '0.82rem' }}
            >
              Continue Viewing
            </button>
          </div>
        </div>
      )}

      {saveSuccessMsg && (
        <div className="alert-box" style={{ marginBottom: '1.5rem', background: 'var(--sage-soft)', borderColor: 'var(--sage-deep)' }}>
          <div style={{ color: 'var(--sage-deep)', fontSize: '0.86rem', fontWeight: 600 }}>
            ✓ {saveSuccessMsg}
          </div>
        </div>
      )}

      {/* Legal Safety Notice & Alert Box from consumer-safety.html */}
      {overall_status === 'NON_COMPLIANT' ? (
        <div className="alert-box">
          <div>
            <strong>Action Needed: Non-Compliant Declarations Detected</strong>
            <span>Package label exhibits {summary?.failed || 1} rule failure(s) under Legal Metrology (Packaged Commodities) Rules, 2011.</span>
          </div>
          <div className="alert-tag">Action Needed</div>
        </div>
      ) : overall_status === 'COMPLIANT' ? (
        <div className="alert-box" style={{ background: 'linear-gradient(135deg, #f1f8f3, #ffffff)', borderColor: 'rgba(93, 143, 111, 0.3)' }}>
          <div>
            <strong style={{ color: 'var(--sage-deep)' }}>All Mandatory Declarations Compliant</strong>
            <span>Commodity label satisfies evaluated statutory declaration requirements.</span>
          </div>
          <div className="alert-tag" style={{ background: 'var(--sage-soft)', color: 'var(--sage-deep)' }}>Safe / Compliant</div>
        </div>
      ) : (
        <div className="alert-box" style={{ background: 'linear-gradient(135deg, #fdf8f0, #ffffff)', borderColor: 'rgba(217, 162, 93, 0.4)' }}>
          <div>
            <strong style={{ color: '#b57930' }}>Manual Review Suggested</strong>
            <span>Some declarations require additional physical package inspection for full verification.</span>
          </div>
          <div className="alert-tag" style={{ background: '#fdf1dc', color: '#b57930' }}>Review</div>
        </div>
      )}

      {/* Summary Statistics Bar */}
      {summary && (
        <div className="kpi-grid" style={{ marginBottom: '1.5rem' }}>
          <div className="kpi-card" style={{ padding: '1rem', textAlign: 'center' }}>
            <div className="kpi-head" style={{ justifyContent: 'center', marginBottom: '0.35rem' }}>Rules Checked</div>
            <div className="kpi-value" style={{ fontSize: '1.6rem' }}>{summary.rules_checked}</div>
          </div>
          <div className="kpi-card" style={{ padding: '1rem', textAlign: 'center', borderColor: 'rgba(93, 143, 111, 0.3)' }}>
            <div className="kpi-head" style={{ justifyContent: 'center', marginBottom: '0.35rem', color: 'var(--sage-deep)' }}>Passed</div>
            <div className="kpi-value" style={{ fontSize: '1.6rem', color: 'var(--sage-deep)' }}>{summary.passed}</div>
          </div>
          <div className="kpi-card" style={{ padding: '1rem', textAlign: 'center', borderColor: 'rgba(213, 155, 130, 0.4)' }}>
            <div className="kpi-head" style={{ justifyContent: 'center', marginBottom: '0.35rem', color: '#b55246' }}>Failed</div>
            <div className="kpi-value" style={{ fontSize: '1.6rem', color: '#b55246' }}>{summary.failed}</div>
          </div>
          <div className="kpi-card" style={{ padding: '1rem', textAlign: 'center', borderColor: 'rgba(217, 162, 93, 0.4)' }}>
            <div className="kpi-head" style={{ justifyContent: 'center', marginBottom: '0.35rem', color: '#d9a25d' }}>Not Verifiable</div>
            <div className="kpi-value" style={{ fontSize: '1.6rem', color: '#d9a25d' }}>{summary.not_verifiable}</div>
          </div>
        </div>
      )}


      {/* Main Layout Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '420px 1fr', gap: '1.5rem' }}>
        
        {/* Left Column: Interactive Image Evidence Viewer */}
        <div>
          <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Annotated Label Evidence
              </h3>
              
              {/* Image View Mode Toggle */}
              <div style={{ display: 'flex', gap: '0.25rem', background: 'rgba(0,0,0,0.3)', padding: '0.2rem', borderRadius: '8px' }}>
                <button
                  onClick={() => setImageTab('interactive')}
                  style={{
                    background: imageTab === 'interactive' ? 'var(--accent-cyan)' : 'transparent',
                    color: imageTab === 'interactive' ? '#0a0e17' : 'var(--text-muted)',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  Interactive
                </button>
                {annotated_image_url && (
                  <button
                    onClick={() => setImageTab('annotated')}
                    style={{
                      background: imageTab === 'annotated' ? 'var(--accent-cyan)' : 'transparent',
                      color: imageTab === 'annotated' ? '#0a0e17' : 'var(--text-muted)',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '0.25rem 0.5rem',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    Annotated
                  </button>
                )}
                <button
                  onClick={() => setImageTab('original')}
                  style={{
                    background: imageTab === 'original' ? 'var(--accent-cyan)' : 'transparent',
                    color: imageTab === 'original' ? '#0a0e17' : 'var(--text-muted)',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  Original
                </button>
              </div>
            </div>

            {/* Interactive Image Container */}
            <div style={{
              position: 'relative',
              borderRadius: '10px',
              overflow: 'hidden',
              border: '1px solid var(--border-color)',
              background: '#000',
              minHeight: '300px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <img
                src={getUploadUrl(activeImageUrl)}
                alt="Package Label Evidence"
                style={{ width: '100%', maxHeight: '450px', objectFit: 'contain', display: 'block' }}
              />

              {/* Interactive SVG Bounding Box Overlay */}
              {imageTab === 'interactive' && rule_results && (
                <svg
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    pointerEvents: 'auto'
                  }}
                  viewBox="0 0 800 600"  /* Standard coordinate space fallback */
                  preserveAspectRatio="xMidYMid meet"
                >
                  {rule_results.map((rule) => {
                    if (!rule.bbox || rule.bbox.length !== 4) return null;
                    const [x, y, w, h] = rule.bbox;
                    const isSelected = selectedRuleId === rule.rule_id;
                    const color = STATUS_COLOR_MAP[rule.status] || '#60a5fa';

                    return (
                      <g
                        key={rule.rule_id}
                        onClick={() => setSelectedRuleId(rule.rule_id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <rect
                          x={x}
                          y={y}
                          width={w}
                          height={h}
                          fill={color}
                          fillOpacity={isSelected ? 0.35 : 0.15}
                          stroke={color}
                          strokeWidth={isSelected ? 4 : 2}
                        />
                        <rect
                          x={x}
                          y={Math.max(0, y - 20)}
                          width={Math.min(w, 140)}
                          height={20}
                          fill={color}
                          fillOpacity={0.9}
                        />
                        <text
                          x={x + 4}
                          y={Math.max(14, y - 5)}
                          fill="#ffffff"
                          fontSize="11"
                          fontWeight="bold"
                        >
                          [{rule.status}] {rule.rule_number}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              )}
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.6rem', textAlign: 'center' }}>
              Click any bounding box on the image or rule card below to cross-highlight evidence.
            </div>
          </div>
        </div>

        {/* Right Column: Rule Results / Enrichment / Grid / JSON */}
        <div>
          {/* TAB 1: SECTION 1: PACKAGE LABEL ANALYSIS */}
          {viewMode === 'rules' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="glass-panel" style={{ padding: '1.25rem', border: '1px solid rgba(93, 143, 111, 0.25)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                      Package Label Analysis
                    </h3>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                      Source: <strong>Uploaded Package Image</strong> (Physical printed label evidence for Legal Metrology compliance)
                    </div>
                  </div>
                  <span style={{
                    background: 'rgba(16, 185, 129, 0.15)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    color: 'var(--accent-emerald)',
                    padding: '0.3rem 0.75rem',
                    borderRadius: '9999px',
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    letterSpacing: '0.04em'
                  }}>
                    PRIMARY EVIDENCE SOURCE
                  </span>
                </div>

                {/* OCR Detected Declarations Overview */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.6rem', marginTop: '0.75rem' }}>
                  <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Printed MRP</div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 700, color: declarations.max_retail_price ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
                      {declarations.max_retail_price ? `${declarations.max_retail_price.currency || '₹'} ${declarations.max_retail_price.value}` : 'Not Detected'}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Net Quantity</div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 700, color: declarations.net_quantity ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                      {declarations.net_quantity ? `${declarations.net_quantity.value} ${declarations.net_quantity.unit}` : 'Not Detected'}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Mfg / Pkd Date</div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 700, color: (declarations.date_of_manufacture?.value || declarations.date_of_manufacture) ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                      {declarations.date_of_manufacture?.value || declarations.date_of_manufacture || 'Not Detected'}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Country of Origin</div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {declarations.country_of_origin?.value || declarations.country_of_origin || 'Domestic (India)'}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', gridColumn: 'span 2' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Manufacturer / Packer / Importer</div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {declarations.manufacturer?.name || declarations.manufacturer?.address || 'Not Detected'}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', gridColumn: 'span 2' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Consumer Care Details</div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {declarations.consumer_care?.details || declarations.consumer_care?.email || declarations.consumer_care?.phone || 'Not Detected'}
                    </div>
                  </div>
                </div>
              </div>

              {rule_results && rule_results.map((rule, idx) => {
                const isSelected = selectedRuleId === rule.rule_id;
                const measurement_item = measurements ? measurements.find(m => m.declaration && rule.title.toLowerCase().includes(m.declaration.toLowerCase())) : null;

                return (
                  <div
                    key={rule.rule_id || idx}
                    className="glass-panel"
                    onClick={() => setSelectedRuleId(rule.rule_id)}
                    style={{
                      padding: '1.25rem',
                      cursor: 'pointer',
                      borderLeft: `5px solid ${STATUS_COLOR_MAP[rule.status] || '#6b7280'}`,
                      background: isSelected ? 'rgba(0, 242, 254, 0.08)' : 'var(--glass-bg)',
                      borderColor: isSelected ? 'var(--accent-cyan)' : 'var(--glass-border)',
                      boxShadow: isSelected ? '0 0 15px rgba(0, 242, 254, 0.2)' : 'none',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <span className="mono-text" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                          {rule.rule_number}
                        </span>
                        <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>{rule.title}</h4>
                      </div>
                      {getStatusBadge(rule.status)}
                    </div>

                    <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginBottom: '0.6rem' }}>
                      {rule.reason}
                    </p>

                    {/* Evidence & Measurement Bar */}
                    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.6rem' }}>
                      {rule.detected_text && (
                        <div style={{ fontSize: '0.78rem', background: 'rgba(0,0,0,0.3)', padding: '0.35rem 0.75rem', borderRadius: '6px', color: '#38bdf8', flex: 1 }}>
                          <span style={{ color: 'var(--text-dim)' }}>Evidence: </span>"{rule.detected_text}"
                        </div>
                      )}
                      
                      {rule.normalized_value?.estimated_mm_height && (
                        <div style={{ fontSize: '0.78rem', background: 'rgba(16, 185, 129, 0.1)', padding: '0.35rem 0.75rem', borderRadius: '6px', color: 'var(--accent-emerald)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                          <span>Character Height: </span><strong>{rule.normalized_value.estimated_mm_height} mm</strong> (Req: &gt;={rule.normalized_value.required_mm_height}mm)
                        </div>
                      )}
                    </div>

                    <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <Info size={12} />
                      <span>Source: {rule.source_reference} ({rule.source_title})</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* TAB 2: PRODUCT & BARCODE ENRICHMENT */}
          {viewMode === 'enrichment' && (
            <div>
              <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <Barcode size={22} style={{ color: 'var(--accent-cyan)' }} />
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Product & Barcode Enrichment</h3>
                  </div>
                  <span style={{ fontSize: '0.75rem', padding: '0.25rem 0.75rem', borderRadius: '9999px', background: 'rgba(0, 242, 254, 0.1)', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 242, 254, 0.3)', fontWeight: 600 }}>
                    SOURCE: {product_enrichment?.source_type || 'AI_ENRICHMENT'}
                  </span>
                </div>

                {enrichmentData && (product_enrichment?.available || scanResult.enrichment?.available) ? (
                  <div className="facts-grid">
                    <div className="fact-card">
                      <div className="fact-label"><span>Barcode</span><span className="mono-text" style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)' }}>[AI / Scanner]</span></div>
                      <div className="fact-value mono-text" style={{ fontSize: '1rem', color: 'var(--accent-cyan)' }}>{enrichmentData.barcode || 'N/A'}</div>
                    </div>
                    <div className="fact-card">
                      <div className="fact-label"><span>Product Name</span><span style={{ fontSize: '0.65rem', color: 'var(--accent-blue)' }}>[AI Enrichment]</span></div>
                      <div className="fact-value">{enrichmentData.product_name || 'N/A'}</div>
                    </div>
                    <div className="fact-card">
                      <div className="fact-label"><span>Brand Name</span><span style={{ fontSize: '0.65rem', color: 'var(--accent-emerald)' }}>[AI Enrichment]</span></div>
                      <div className="fact-value">{enrichmentData.brand || 'N/A'}</div>
                    </div>
                    <div className="fact-card">
                      <div className="fact-label"><span>Manufacturer</span><span style={{ fontSize: '0.65rem', color: 'var(--accent-amber)' }}>[AI Enrichment]</span></div>
                      <div className="fact-value">{enrichmentData.manufacturer || 'N/A'}</div>
                    </div>
                    <div className="fact-card">
                      <div className="fact-label"><span>Category</span></div>
                      <div className="fact-value">{enrichmentData.category || 'N/A'}</div>
                    </div>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic', padding: '1rem' }}>
                    {product_enrichment?.reason || "Product enrichment is currently unavailable."}
                  </div>
                )}
              </div>

              {/* Cross-Check Results Section */}
              <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <CheckCircle2 size={20} style={{ color: 'var(--accent-emerald)' }} />
                    <span>Product Detail Cross-Check</span>
                  </h3>
                  {cross_check && cross_check.available && (
                    <span style={{
                      fontSize: '0.78rem',
                      fontWeight: 700,
                      color: cross_check.details_consistent ? 'var(--accent-emerald)' : 'var(--accent-amber)',
                      background: cross_check.details_consistent ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      padding: '0.3rem 0.75rem',
                      borderRadius: '9999px',
                      border: `1px solid ${cross_check.details_consistent ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
                    }}>
                      {cross_check.details_consistent ? '✓ Details Consistent' : `⚠ ${cross_check.mismatches_found} Information Mismatch(es)`}
                    </span>
                  )}
                </div>

                {cross_check && cross_check.available && cross_check.field_checks ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {cross_check.field_checks.map((chk, idx) => (
                      <div key={idx} style={{
                        background: 'rgba(0,0,0,0.3)',
                        padding: '0.9rem 1.1rem',
                        borderRadius: '10px',
                        border: `1px solid ${chk.status === 'CONSISTENT' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.3)'}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                      }}>
                        <div>
                          <div style={{ fontSize: '0.88rem', fontWeight: 700 }}>{chk.field}</div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                            {chk.explanation}
                          </div>
                        </div>
                        <div style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          color: chk.status === 'CONSISTENT' ? 'var(--accent-emerald)' : 'var(--accent-amber)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.3rem'
                        }}>
                          {chk.status === 'CONSISTENT' ? <Check size={14} /> : <AlertCircle size={14} />}
                          <span>{chk.status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                    Cross-check information unavailable.
                  </div>
                )}
              </div>

              {/* Dual-OCR Cross-Check Section (OpenAI vs Local Tesseract) */}
              {scanResult.ocr_cross_check && scanResult.ocr_cross_check.available && (
                <div className="glass-panel" style={{ padding: '1.5rem', marginTop: '1.5rem', border: '1px solid rgba(0, 242, 254, 0.25)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Layers size={20} style={{ color: 'var(--accent-cyan)' }} />
                      <span>Dual-OCR Provider Cross-Check (OpenAI Vision + Tesseract)</span>
                    </h3>
                    <span style={{
                      fontSize: '0.78rem',
                      fontWeight: 700,
                      color: !scanResult.ocr_cross_check.has_disagreement ? 'var(--accent-emerald)' : 'var(--accent-amber)',
                      background: !scanResult.ocr_cross_check.has_disagreement ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      padding: '0.3rem 0.75rem',
                      borderRadius: '9999px',
                      border: `1px solid ${!scanResult.ocr_cross_check.has_disagreement ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
                    }}>
                      {!scanResult.ocr_cross_check.has_disagreement ? '✓ Dual OCR Consensus (Evidence Strengthened)' : `⚠ Uncertainty: ${scanResult.ocr_cross_check.disagreement_count} Disagreement(s) Flagged`}
                    </span>
                  </div>

                  {scanResult.ocr_cross_check.comparisons && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {scanResult.ocr_cross_check.comparisons.map((c, idx) => (
                        <div key={idx} style={{
                          background: 'rgba(0,0,0,0.3)',
                          padding: '0.9rem 1.1rem',
                          borderRadius: '10px',
                          border: `1px solid ${c.status === 'AGREED' ? 'rgba(16, 185, 129, 0.25)' : (c.status === 'DISAGREEMENT' ? 'rgba(244, 63, 94, 0.4)' : 'rgba(255,255,255,0.08)')}`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          flexWrap: 'wrap',
                          gap: '0.8rem'
                        }}>
                          <div style={{ flex: '1 1 300px' }}>
                            <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>{c.field}</div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>{c.explanation}</div>
                            <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.4rem', fontSize: '0.78rem' }}>
                              <span><strong>OpenAI:</strong> <code style={{ color: 'var(--accent-cyan)' }}>{c.openai_value}</code></span>
                              <span><strong>Tesseract:</strong> <code style={{ color: 'var(--accent-emerald)' }}>{c.tesseract_value}</code></span>
                            </div>
                          </div>
                          <div style={{
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            color: c.status === 'AGREED' ? 'var(--accent-emerald)' : (c.status === 'DISAGREEMENT' ? 'var(--accent-rose)' : 'var(--text-muted)'),
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.3rem',
                            background: c.status === 'AGREED' ? 'rgba(16, 185, 129, 0.1)' : (c.status === 'DISAGREEMENT' ? 'rgba(244, 63, 94, 0.15)' : 'rgba(255,255,255,0.05)'),
                            padding: '0.3rem 0.6rem',
                            borderRadius: '6px'
                          }}>
                            {c.status === 'AGREED' ? <Check size={14} /> : (c.status === 'DISAGREEMENT' ? <AlertCircle size={14} /> : <Info size={14} />)}
                            <span>{c.status === 'AGREED' ? 'VERIFIED MATCH' : (c.status === 'DISAGREEMENT' ? 'UNCERTAINTY' : 'SINGLE PROVIDER')}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB: WEB PRODUCT RESEARCH & MARKET INTELLIGENCE */}
          {viewMode === 'web_research' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              
              {/* Header Status & Search Stats Banner */}
              <div className="glass-panel" style={{ padding: '1.5rem', border: '1px solid rgba(0, 242, 254, 0.25)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <Globe size={22} style={{ color: 'var(--accent-cyan)' }} />
                    <h3 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>Google Web Research & Product Intelligence</h3>
                  </div>

                  <span style={{
                    fontSize: '0.8rem',
                    padding: '0.35rem 0.85rem',
                    borderRadius: '9999px',
                    fontWeight: 700,
                    letterSpacing: '0.04em',
                    background: webResearch?.status === 'COMPLETE' ? 'rgba(16, 185, 129, 0.15)' : (webResearch?.status === 'UNAVAILABLE' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(96, 165, 250, 0.15)'),
                    color: webResearch?.status === 'COMPLETE' ? 'var(--accent-emerald)' : (webResearch?.status === 'UNAVAILABLE' ? 'var(--accent-amber)' : '#60a5fa'),
                    border: `1px solid ${webResearch?.status === 'COMPLETE' ? 'rgba(16, 185, 129, 0.4)' : (webResearch?.status === 'UNAVAILABLE' ? 'rgba(245, 158, 11, 0.4)' : 'rgba(96, 165, 250, 0.4)')}`
                  }}>
                    {webResearch?.status === 'COMPLETE' ? '✓ RESEARCH COMPLETE' : (webResearch?.status === 'UNAVAILABLE' ? '⚠ GOOGLE SEARCH UNAVAILABLE' : (webResearch?.status === 'NO_RELEVANT_RESULTS' ? 'ℹ NO RELEVANT RESULTS' : 'NOT CONFIGURED'))}
                  </span>
                </div>

                {/* Research Execution Statistics */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.85rem' }}>
                  <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Queries Run</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>{webResearch?.queries_run ?? 0}</div>
                  </div>
                  <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Results Found</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#60a5fa' }}>{webResearch?.results_found ?? 0}</div>
                  </div>
                  <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Pages Reviewed</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>{webResearch?.pages_fetched ?? 0}</div>
                  </div>
                  <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Sources Cited</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-amber)' }}>{webResearch?.sources_used ?? 0}</div>
                  </div>
                </div>

                {/* Status Notice if UNAVAILABLE */}
                {webResearch?.status === 'UNAVAILABLE' && (
                  <div style={{
                    marginTop: '1.25rem',
                    background: 'rgba(245, 158, 11, 0.08)',
                    border: '1px solid rgba(245, 158, 11, 0.25)',
                    borderRadius: '8px',
                    padding: '0.9rem 1.1rem',
                    fontSize: '0.82rem',
                    color: '#fde68a'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, marginBottom: '0.3rem' }}>
                      <AlertTriangle size={16} style={{ color: 'var(--accent-amber)' }} />
                      <span>Google Web Search Provider Not Configured</span>
                    </div>
                    <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.78rem', lineHeight: '1.4' }}>
                      {webResearch.reason || "Google Custom Search JSON API credentials (GOOGLE_WEB_SEARCH_API_KEY / GOOGLE_CLIENT_ID) are not configured. To preserve strict data integrity, LabelSure will NEVER synthesize fake search results. Local OCR and deterministic Legal Metrology rules executed normally."}
                    </p>
                  </div>
                )}
              </div>

              {/* Product Identity Resolution Card */}
              {webResearch?.product_identity && (
                <div className="glass-panel" style={{ padding: '1.5rem', position: 'relative' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                    <div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>
                        RESOLVED PRODUCT IDENTITY
                      </div>
                      <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.25rem 0 0 0' }}>
                        {webResearch.product_identity.resolved_name || 'Unresolved Commodity'}
                      </h2>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: 800,
                        padding: '0.25rem 0.65rem',
                        borderRadius: '6px',
                        background: webResearch.product_identity.resolution_status === 'RESOLVED' ? 'rgba(16, 185, 129, 0.2)' : (webResearch.product_identity.resolution_status === 'PARTIAL' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255, 255, 255, 0.08)'),
                        color: webResearch.product_identity.resolution_status === 'RESOLVED' ? 'var(--accent-emerald)' : (webResearch.product_identity.resolution_status === 'PARTIAL' ? 'var(--accent-amber)' : 'var(--text-muted)'),
                        border: `1px solid ${webResearch.product_identity.resolution_status === 'RESOLVED' ? 'rgba(16, 185, 129, 0.4)' : (webResearch.product_identity.resolution_status === 'PARTIAL' ? 'rgba(245, 158, 11, 0.4)' : 'rgba(255, 255, 255, 0.1)')}`
                      }}>
                        STATUS: {webResearch.product_identity.resolution_status}
                      </span>
                      {webResearch.product_identity.confidence > 0 && (
                        <span style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.25rem 0.65rem',
                          borderRadius: '6px',
                          background: 'rgba(0, 242, 254, 0.15)',
                          color: 'var(--accent-cyan)',
                          border: '1px solid rgba(0, 242, 254, 0.3)'
                        }}>
                          Confidence: {Math.round(webResearch.product_identity.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="facts-grid" style={{ marginTop: '1rem' }}>
                    <div className="fact-card">
                      <div className="fact-label"><span>Brand</span></div>
                      <div className="fact-value" style={{ color: 'var(--accent-emerald)' }}>{webResearch.product_identity.brand || 'N/A'}</div>
                    </div>
                    <div className="fact-card">
                      <div className="fact-label"><span>Manufacturer / Marketer</span></div>
                      <div className="fact-value">{webResearch.product_identity.manufacturer || 'N/A'}</div>
                    </div>
                    <div className="fact-card">
                      <div className="fact-label"><span>Barcode (GTIN/EAN)</span></div>
                      <div className="fact-value mono-text" style={{ color: 'var(--accent-cyan)' }}>{webResearch.product_identity.barcode || 'N/A'}</div>
                    </div>
                    <div className="fact-card">
                      <div className="fact-label"><span>Category</span></div>
                      <div className="fact-value">{webResearch.product_identity.category || 'N/A'}</div>
                    </div>
                    <div className="fact-card">
                      <div className="fact-label"><span>Pack Size / Net Qty</span></div>
                      <div className="fact-value">{webResearch.product_identity.pack_size || 'N/A'}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Structured Product Details (4 Categories) with Source Citations */}
              {webResearch?.details && Object.keys(webResearch.details).length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {Object.entries(webResearch.details).map(([catKey, factList]) => {
                    const catTitles = {
                      basic_details: 'Basic Product Details',
                      manufacturer_details: 'Manufacturer & Marketing Details',
                      packaging_and_price: 'Packaging, Measurements & Price',
                      product_information: 'Product Information & Composition'
                    };
                    const title = catTitles[catKey] || catKey.replace(/_/g, ' ').toUpperCase();

                    return (
                      <div key={catKey} className="glass-panel" style={{ padding: '1.25rem' }}>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          {title} ({factList?.length || 0})
                        </h4>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                          {factList && factList.map((fact, fIdx) => (
                            <div key={fIdx} style={{
                              background: 'rgba(0,0,0,0.3)',
                              padding: '0.75rem 1rem',
                              borderRadius: '8px',
                              border: '1px solid rgba(255,255,255,0.06)',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              flexWrap: 'wrap',
                              gap: '0.75rem'
                            }}>
                              <div style={{ flex: '1 1 240px' }}>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                                  {fact.field?.replace(/_/g, ' ')}
                                </div>
                                <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.15rem' }}>
                                  {fact.value}
                                </div>
                                {fact.evidence && (
                                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontStyle: 'italic', marginTop: '0.2rem' }}>
                                    "{fact.evidence}"
                                  </div>
                                )}
                              </div>

                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <span style={{
                                  fontSize: '0.7rem',
                                  padding: '0.2rem 0.5rem',
                                  borderRadius: '4px',
                                  background: 'rgba(255,255,255,0.06)',
                                  color: 'var(--text-muted)',
                                  border: '1px solid rgba(255,255,255,0.1)'
                                }}>
                                  {fact.source_domain}
                                </span>
                                {fact.source_url && (
                                  <a
                                    href={fact.source_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '0.25rem',
                                      fontSize: '0.72rem',
                                      color: 'var(--accent-cyan)',
                                      textDecoration: 'none',
                                      padding: '0.2rem 0.5rem',
                                      borderRadius: '4px',
                                      background: 'rgba(0, 242, 254, 0.1)'
                                    }}
                                  >
                                    <span>Source</span>
                                    <ExternalLink size={12} />
                                  </a>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Image Evidence vs Web Comparison */}
              {webResearch?.image_comparisons && webResearch.image_comparisons.length > 0 && (
                <div className="glass-panel" style={{ padding: '1.25rem' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Layers size={18} style={{ color: 'var(--accent-emerald)' }} />
                    <span>Physical Package Evidence vs. Web Sourced Values</span>
                  </h4>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                    {webResearch.image_comparisons.map((cmp, cIdx) => (
                      <div key={cIdx} style={{
                        background: 'rgba(0,0,0,0.3)',
                        padding: '0.8rem 1rem',
                        borderRadius: '8px',
                        border: `1px solid ${cmp.status === 'MATCH' ? 'rgba(16, 185, 129, 0.25)' : (cmp.status === 'MISMATCH' ? 'rgba(244, 63, 94, 0.35)' : 'rgba(255,255,255,0.06)')}`,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: '0.75rem'
                      }}>
                        <div style={{ flex: '1 1 240px' }}>
                          <div style={{ fontSize: '0.82rem', fontWeight: 700 }}>{cmp.field}</div>
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                            Package OCR: <strong style={{ color: 'var(--text-primary)' }}>{cmp.image_value}</strong> • Web Sourced: <strong style={{ color: 'var(--accent-cyan)' }}>{cmp.web_value}</strong>
                          </div>
                          {cmp.note && (
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>{cmp.note}</div>
                          )}
                        </div>

                        <span style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '0.25rem 0.65rem',
                          borderRadius: '6px',
                          background: cmp.status === 'MATCH' ? 'rgba(16, 185, 129, 0.15)' : (cmp.status === 'MISMATCH' ? 'rgba(244, 63, 94, 0.15)' : 'rgba(255,255,255,0.05)'),
                          color: cmp.status === 'MATCH' ? 'var(--accent-emerald)' : (cmp.status === 'MISMATCH' ? 'var(--accent-rose)' : 'var(--text-muted)'),
                          border: `1px solid ${cmp.status === 'MATCH' ? 'rgba(16, 185, 129, 0.3)' : (cmp.status === 'MISMATCH' ? 'rgba(244, 63, 94, 0.3)' : 'rgba(255,255,255,0.1)')}`
                        }}>
                          {cmp.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Source-to-Source Conflicts Section */}
              {webResearch?.conflicts && webResearch.conflicts.length > 0 && (
                <div className="glass-panel" style={{ padding: '1.25rem', border: '1px solid rgba(244, 63, 94, 0.3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.85rem' }}>
                    <AlertCircle size={18} style={{ color: 'var(--accent-rose)' }} />
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-rose)', margin: 0 }}>
                      Conflicting Web Source Declarations Detected ({webResearch.conflicts.length})
                    </h4>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                    {webResearch.conflicts.map((cnf, cnfIdx) => (
                      <div key={cnfIdx} style={{
                        background: 'rgba(244, 63, 94, 0.08)',
                        padding: '0.8rem 1rem',
                        borderRadius: '8px',
                        border: '1px solid rgba(244, 63, 94, 0.2)'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#fda4af' }}>{cnf.field} Disagreement</span>
                          <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.45rem', borderRadius: '4px', background: 'rgba(244, 63, 94, 0.2)', color: '#fda4af', fontWeight: 700 }}>
                            {cnf.severity || 'HIGH'}
                          </span>
                        </div>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0 0 0.5rem 0' }}>{cnf.note}</p>
                        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                          {cnf.citations?.map((cit, citIdx) => (
                            <div key={citIdx} style={{ fontSize: '0.72rem', background: 'rgba(0,0,0,0.3)', padding: '0.25rem 0.55rem', borderRadius: '4px' }}>
                              <strong>{cit.source_domain}:</strong> <code style={{ color: 'var(--accent-cyan)' }}>{cit.value}</code>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sources Reviewed List */}
              {webResearch?.sources && webResearch.sources.length > 0 && (
                <div className="glass-panel" style={{ padding: '1.25rem' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
                    Sources Reviewed ({webResearch.sources.length})
                  </h4>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {webResearch.sources.map((src, sIdx) => (
                      <div key={sIdx} style={{
                        background: 'rgba(0,0,0,0.3)',
                        padding: '0.85rem 1rem',
                        borderRadius: '8px',
                        border: '1px solid rgba(255,255,255,0.06)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        gap: '1rem',
                        flexWrap: 'wrap'
                      }}>
                        <div style={{ flex: '1 1 300px' }}>
                          <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>{src.title || src.domain}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', margin: '0.2rem 0' }}>{src.domain}</div>
                          {src.snippet && (
                            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0', lineHeight: '1.3' }}>
                              {src.snippet}
                            </p>
                          )}
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                          <span style={{
                            fontSize: '0.7rem',
                            padding: '0.2rem 0.5rem',
                            borderRadius: '4px',
                            background: src.status === 'EXTRACTED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255,255,255,0.05)',
                            color: src.status === 'EXTRACTED' ? 'var(--accent-emerald)' : 'var(--text-muted)'
                          }}>
                            {src.status === 'EXTRACTED' ? `${src.facts_count || 0} Facts` : src.status}
                          </span>
                          {src.url && (
                            <a
                              href={src.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="btn-primary"
                              style={{ padding: '0.35rem 0.7rem', fontSize: '0.75rem', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                            >
                              <span>Open Source</span>
                              <ExternalLink size={12} />
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Collapsible Search Trace */}
              {webResearch?.search_trace && webResearch.search_trace.length > 0 && (
                <div className="glass-panel" style={{ padding: '1.25rem' }}>
                  <button
                    onClick={() => setSearchTraceOpen(!searchTraceOpen)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      width: '100%',
                      background: 'none',
                      border: 'none',
                      color: 'var(--accent-cyan)',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      padding: 0
                    }}
                  >
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Search size={16} />
                      <span>Search Query Trace ({webResearch.search_trace.length} targeted queries)</span>
                    </span>
                    {searchTraceOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>

                  {searchTraceOpen && (
                    <div style={{ marginTop: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      {webResearch.search_trace.map((q, qIdx) => (
                        <div key={qIdx} style={{
                          background: 'rgba(0,0,0,0.4)',
                          padding: '0.5rem 0.75rem',
                          borderRadius: '6px',
                          fontSize: '0.78rem',
                          fontFamily: 'monospace',
                          color: 'var(--accent-cyan)',
                          border: '1px solid rgba(255,255,255,0.05)'
                        }}>
                          {q}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Safety & Compliance Layer Notice */}
              <div style={{
                background: 'rgba(59, 130, 246, 0.08)',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                borderRadius: '8px',
                padding: '0.85rem 1.15rem',
                fontSize: '0.78rem',
                color: '#93c5fd',
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem'
              }}>
                <Info size={18} style={{ flexShrink: 0 }} />
                <span>
                  <strong>Informational & Evidence Layer Only:</strong> Web research results provide market intelligence and evidence corroboration. Under the Legal Metrology (Packaged Commodities) Rules, final compliance verdicts are strictly determined by declarations physically present on the package label.
                </span>
              </div>

            </div>
          )}

          {/* TAB: OPEN FOOD FACTS PRODUCT DATA */}
          {viewMode === 'openfoodfacts' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

              {/* 1. PRIMARY COMPLIANCE: LEGAL METROLOGY PACKAGED COMMODITIES RULE EVALUATION */}
              <div className="glass-panel" style={{ padding: '1.5rem', border: '1px solid rgba(93, 143, 111, 0.35)', background: 'var(--panel)' }}>
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--sage-deep)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                      Statutory Audit • Legal Metrology Act, 2009
                    </div>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text)' }}>
                      <FileText size={22} style={{ color: 'var(--sage-deep)' }} />
                      <span>LEGAL METROLOGY PACKAGED COMMODITIES RULE EVALUATION</span>
                    </h2>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '0.25rem' }}>
                      Rule-by-rule statutory compliance evaluation under the Legal Metrology (Packaged Commodities) Rules, 2011.
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{
                      background: 'rgba(93, 143, 111, 0.12)',
                      color: 'var(--sage-deep)',
                      border: '1px solid rgba(93, 143, 111, 0.3)',
                      padding: '0.35rem 0.8rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 700
                    }}>
                      {rule_set_version || '2026.1-PC-RULES'}
                    </span>
                  </div>
                </div>

                {/* Top Summary Row */}
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.75rem 1.25rem',
                  alignItems: 'center',
                  padding: '0.85rem 1.15rem',
                  background: 'var(--panel-soft)',
                  borderRadius: '12px',
                  border: '1px solid var(--border)',
                  marginBottom: '1.25rem',
                  fontSize: '0.82rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ color: 'var(--muted)', fontWeight: 600 }}>Rules Checked:</span>
                    <strong style={{ color: 'var(--text)', fontWeight: 800 }}>{summary?.rules_checked ?? rule_results?.length ?? 0}</strong>
                  </div>
                  <span style={{ color: 'var(--border)' }}>•</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ color: 'var(--muted)', fontWeight: 600 }}>Passed:</span>
                    <strong style={{ color: 'var(--sage-deep)', fontWeight: 800 }}>{summary?.passed ?? rule_results?.filter(r => r.status === 'PASS').length ?? 0}</strong>
                  </div>
                  <span style={{ color: 'var(--border)' }}>•</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ color: 'var(--muted)', fontWeight: 600 }}>Failed:</span>
                    <strong style={{ color: '#b55246', fontWeight: 800 }}>{summary?.failed ?? rule_results?.filter(r => r.status === 'FAIL').length ?? 0}</strong>
                  </div>
                  <span style={{ color: 'var(--border)' }}>•</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ color: 'var(--muted)', fontWeight: 600 }}>Warnings:</span>
                    <strong style={{ color: '#d9a25d', fontWeight: 800 }}>{summary?.warnings ?? rule_results?.filter(r => r.status === 'WARNING').length ?? 0}</strong>
                  </div>
                  <span style={{ color: 'var(--border)' }}>•</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ color: 'var(--muted)', fontWeight: 600 }}>Not Verifiable:</span>
                    <strong style={{ color: '#5b82a6', fontWeight: 800 }}>{summary?.not_verifiable ?? rule_results?.filter(r => r.status === 'NOT_VERIFIABLE').length ?? 0}</strong>
                  </div>
                  <span style={{ color: 'var(--border)' }}>•</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ color: 'var(--muted)', fontWeight: 600 }}>Not Applicable:</span>
                    <strong style={{ color: 'var(--muted)', fontWeight: 800 }}>{summary?.not_applicable ?? rule_results?.filter(r => r.status === 'NOT_APPLICABLE').length ?? 0}</strong>
                  </div>
                </div>

                {/* Rules Evaluation Table */}
                <div style={{ overflowX: 'auto' }}>
                  <table className="metrology-eval-table">
                    <thead>
                      <tr>
                        <th style={{ width: '135px' }}>Rule Number</th>
                        <th style={{ minWidth: '190px' }}>Requirement / Rule</th>
                        <th style={{ minWidth: '180px' }}>Detected Value</th>
                        <th style={{ width: '135px', textAlign: 'center' }}>Status</th>
                        <th style={{ minWidth: '240px' }}>Reason / Legal Basis</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rule_results && rule_results.length > 0 ? (
                        rule_results.map((rule, idx) => {
                          let detectedVal = null;
                          if (rule.normalized_value?.estimated_mm_height) {
                            detectedVal = `${rule.normalized_value.estimated_mm_height} mm`;
                          } else if (rule.normalized_value?.value && rule.normalized_value?.unit) {
                            detectedVal = `${rule.normalized_value.value} ${rule.normalized_value.unit}`;
                          } else if (rule.normalized_value?.name || rule.normalized_value?.address) {
                            detectedVal = [rule.normalized_value.name, rule.normalized_value.address].filter(Boolean).filter((v, i, a) => a.indexOf(v) === i).join(' • ');
                          } else if (rule.detected_text && typeof rule.detected_text === 'string' && !rule.detected_text.trim().startsWith('{')) {
                            detectedVal = rule.detected_text;
                          } else if (rule.normalized_value?.raw) {
                            detectedVal = rule.normalized_value.raw;
                          } else if (rule.detected_text) {
                            try {
                              const match = rule.detected_text.match(/['"](?:text|name|raw)['"]\s*:\s*['"]([^'"]+)['"]/);
                              detectedVal = match ? match[1] : rule.detected_text;
                            } catch (e) {
                              detectedVal = rule.detected_text;
                            }
                          }

                          return (
                            <tr key={rule.rule_id || idx}>
                              <td data-label="Rule Number">
                                <span className="mono-text" style={{ fontWeight: 800, color: 'var(--sage-deep)', fontSize: '0.88rem' }}>
                                  {rule.rule_number}
                                </span>
                                {rule.mandatory && (
                                  <span style={{ display: 'inline-block', fontSize: '0.65rem', color: '#b55246', fontWeight: 800, marginLeft: '0.35rem', background: 'rgba(181, 82, 70, 0.1)', padding: '0.1rem 0.35rem', borderRadius: '4px' }}>
                                    MANDATORY
                                  </span>
                                )}
                              </td>
                              <td data-label="Requirement / Rule" style={{ fontWeight: 600, color: 'var(--text)' }}>
                                {rule.title}
                              </td>
                              <td data-label="Detected Value">
                                {detectedVal ? (
                                  <span className="mono-text" style={{
                                    color: 'var(--text)',
                                    fontWeight: 600,
                                    background: 'var(--panel-soft)',
                                    border: '1px solid var(--border)',
                                    padding: '0.25rem 0.5rem',
                                    borderRadius: '6px',
                                    display: 'inline-block',
                                    wordBreak: 'break-word',
                                    fontSize: '0.82rem'
                                  }}>
                                    {detectedVal}
                                  </span>
                                ) : (
                                  <span style={{ color: 'var(--muted)', fontStyle: 'italic', fontSize: '0.82rem' }}>
                                    Not detected
                                  </span>
                                )}
                                {rule.normalized_value?.estimated_mm_height && (
                                  <div style={{ fontSize: '0.72rem', color: 'var(--sage-deep)', marginTop: '0.2rem', fontWeight: 600 }}>
                                    Height: {rule.normalized_value.estimated_mm_height} mm (Req: ≥{rule.normalized_value.required_mm_height || 1.0} mm)
                                  </div>
                                )}
                              </td>
                              <td data-label="Status" style={{ textAlign: 'center' }}>
                                {rule.status === 'PASS' && (
                                  <span className="status-pill online" style={{ background: 'rgba(93, 143, 111, 0.15)', color: 'var(--sage-deep)', border: '1px solid rgba(93, 143, 111, 0.35)', fontWeight: 800, fontSize: '0.72rem' }}>
                                    <CheckCircle2 size={12} /> PASS
                                  </span>
                                )}
                                {rule.status === 'FAIL' && (
                                  <span className="status-pill offline" style={{ background: 'rgba(181, 82, 70, 0.15)', color: '#b55246', border: '1px solid rgba(181, 82, 70, 0.35)', fontWeight: 800, fontSize: '0.72rem' }}>
                                    <XCircle size={12} /> FAIL
                                  </span>
                                )}
                                {rule.status === 'WARNING' && (
                                  <span className="status-pill" style={{ background: 'rgba(217, 162, 93, 0.15)', color: '#d9a25d', border: '1px solid rgba(217, 162, 93, 0.35)', fontWeight: 800, fontSize: '0.72rem' }}>
                                    <AlertTriangle size={12} /> WARNING
                                  </span>
                                )}
                                {rule.status === 'NOT_VERIFIABLE' && (
                                  <span className="status-pill" style={{ background: 'rgba(91, 130, 166, 0.15)', color: '#5b82a6', border: '1px solid rgba(91, 130, 166, 0.35)', fontWeight: 800, fontSize: '0.72rem' }}>
                                    <HelpCircle size={12} /> NOT VERIFIABLE
                                  </span>
                                )}
                                {(!rule.status || rule.status === 'NOT_APPLICABLE') && (
                                  <span className="status-pill" style={{ background: 'rgba(102, 117, 109, 0.15)', color: 'var(--muted)', border: '1px solid rgba(102, 117, 109, 0.3)', fontWeight: 700, fontSize: '0.72rem' }}>
                                    NOT APPLICABLE
                                  </span>
                                )}
                              </td>
                              <td data-label="Reason / Legal Basis">
                                <div style={{ color: 'var(--text)', fontSize: '0.84rem', lineHeight: '1.45', marginBottom: '0.35rem' }}>
                                  {rule.reason}
                                </div>
                                <div style={{ fontSize: '0.72rem', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                  <Info size={11} style={{ flexShrink: 0 }} />
                                  <span>Ref: {rule.source_reference} ({rule.source_title})</span>
                                </div>
                              </td>
                            </tr>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)', fontStyle: 'italic' }}>
                            No Legal Metrology rule results available for this scan.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 2. PRODUCT ENRICHMENT: OPEN FOOD FACTS PRODUCT DATA */}

              {/* Section Header & Official Source Attribution */}
              <div className="glass-panel" style={{ padding: '1.5rem', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
                      <Apple size={24} style={{ color: 'var(--accent-emerald)' }} />
                      <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0 }}>Open Food Facts Product Data</h2>
                    </div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      Product information retrieved from Open Food Facts • Official API v3 • Barcode: <strong className="mono-text" style={{ color: 'var(--accent-cyan)' }}>{scanResult.barcode || 'N/A'}</strong>
                      {barcodeSourceText && (
                        <span style={{ marginLeft: '0.5rem', background: 'var(--panel-soft)', border: '1px solid var(--border)', padding: '0.15rem 0.45rem', borderRadius: '4px', fontSize: '0.72rem', color: 'var(--sage-deep)', fontWeight: 700 }}>
                          {barcodeSourceText}
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <div style={{
                      background: 'rgba(16, 185, 129, 0.15)',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      color: 'var(--accent-emerald)',
                      padding: '0.35rem 0.85rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 800,
                      letterSpacing: '0.04em'
                    }}>
                      SOURCE: OPEN FOOD FACTS
                    </div>

                    {openFoodFacts?.source_url && (
                      <a
                        href={openFoodFacts.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-primary"
                        style={{ padding: '0.35rem 0.8rem', fontSize: '0.75rem', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                      >
                        <span>View on Open Food Facts</span>
                        <ExternalLink size={13} />
                      </a>
                    )}
                  </div>
                </div>

                {/* Subtitle & Community Source Disclaimer */}
                <div style={{
                  background: 'rgba(0, 242, 254, 0.06)',
                  border: '1px solid rgba(0, 242, 254, 0.2)',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  fontSize: '0.78rem',
                  color: 'var(--accent-cyan)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <Info size={16} style={{ flexShrink: 0 }} />
                  <span>
                    <strong>Product information retrieved from Open Food Facts:</strong> Open Food Facts is a community-maintained database. Information is not government verified or guaranteed correct. Legal Metrology compliance verdicts are strictly determined by physical package label evidence using the deterministic rule engine.
                  </span>
                </div>
              </div>

              {/* Status State Cards */}
              {(!openFoodFacts || openFoodFacts.status === 'NO_BARCODE') && (
                <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', borderColor: 'rgba(156, 163, 175, 0.3)' }}>
                  <Barcode size={42} style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }} />
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.4rem' }}>Open Food Facts Product Enrichment Unavailable</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', maxWidth: '500px', margin: '0 auto' }}>
                    A barcode was not detected on the label or entered manually. Open Food Facts product enrichment is optional; Legal Metrology printed label compliance evaluation remains fully verified from the uploaded package image.
                  </p>
                </div>
              )}

              {openFoodFacts && openFoodFacts.status === 'NOT_FOUND' && (
                <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', borderColor: 'rgba(245, 158, 11, 0.35)' }}>
                  <AlertTriangle size={42} style={{ color: 'var(--accent-amber)', marginBottom: '0.75rem' }} />
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--accent-amber)', marginBottom: '0.4rem' }}>Product Not Found</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '550px', margin: '0 auto 0.6rem' }}>
                    Barcode (<strong className="mono-text" style={{ color: 'var(--text-primary)' }}>{openFoodFacts.barcode || scanResult.barcode}</strong>) was not found in Open Food Facts.
                  </p>
                  <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', maxWidth: '550px', margin: '0 auto 1.25rem' }}>
                    Open Food Facts product enrichment unavailable. Legal Metrology compliance scan remains fully evaluated from the uploaded package image.
                  </p>
                  {openFoodFacts.source_url && (
                    <a
                      href={openFoodFacts.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-primary"
                      style={{ padding: '0.45rem 1rem', fontSize: '0.82rem', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
                    >
                      <span>Check Open Food Facts Database</span>
                      <ExternalLink size={14} />
                    </a>
                  )}
                </div>
              )}

              {openFoodFacts && openFoodFacts.status === 'UNAVAILABLE' && (
                <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', borderColor: 'rgba(244, 63, 94, 0.35)' }}>
                  <AlertCircle size={42} style={{ color: 'var(--accent-rose)', marginBottom: '0.75rem' }} />
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--accent-rose)', marginBottom: '0.4rem' }}>Service Temporarily Unavailable</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', maxWidth: '550px', margin: '0 auto' }}>
                    Open Food Facts API could not be reached. Local OCR extraction and Legal Metrology compliance screening continue normally.
                  </p>
                </div>
              )}

              {/* FOUND PRODUCT DATA */}
              {openFoodFacts && openFoodFacts.status === 'FOUND' && offProduct && (
                <>
                  {/* Primary Product Specifications Grid */}
                  <div className="glass-panel" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <ShoppingBag size={18} style={{ color: 'var(--accent-emerald)' }} />
                        <span>Core Product Specifications</span>
                      </h3>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                        Retrieved: {openFoodFacts.retrieved_at ? new Date(openFoodFacts.retrieved_at).toLocaleString() : 'Just now'}
                      </span>
                    </div>

                    <div className="facts-grid">
                      <div className="fact-card">
                        <div className="fact-label"><span>Barcode</span><span className="mono-text" style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)' }}>[Open Food Facts]</span></div>
                        <div className="fact-value mono-text" style={{ fontSize: '1rem', color: 'var(--accent-cyan)' }}>{offProduct.code || scanResult.barcode || 'Not available'}</div>
                        {barcodeSourceText && (
                          <div style={{ fontSize: '0.7rem', color: 'var(--sage-deep)', fontWeight: 600, marginTop: '0.25rem' }}>
                            {barcodeSourceText}
                          </div>
                        )}
                      </div>

                      <div className="fact-card" style={{ gridColumn: 'span 2' }}>
                        <div className="fact-label"><span>Product Name</span><span style={{ fontSize: '0.65rem', color: 'var(--accent-emerald)' }}>[Open Food Facts]</span></div>
                        <div className="fact-value" style={{ fontSize: '1.1rem', fontWeight: 700, color: offProduct.product_name ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                          {offProduct.product_name || 'Not available in Open Food Facts'}
                        </div>
                        {offProduct.generic_name && (
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
                            Generic: {offProduct.generic_name}
                          </div>
                        )}
                      </div>

                      <div className="fact-card">
                        <div className="fact-label"><span>Brand</span><span style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)' }}>[Open Food Facts]</span></div>
                        <div className="fact-value" style={{ color: offProduct.brands ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
                          {offProduct.brands || 'Not available in Open Food Facts'}
                        </div>
                      </div>

                      <div className="fact-card">
                        <div className="fact-label"><span>Category</span></div>
                        <div className="fact-value" style={{ color: offProduct.categories ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                          {offProduct.categories || 'Not available in Open Food Facts'}
                        </div>
                      </div>

                      <div className="fact-card">
                        <div className="fact-label"><span>Quantity / Pack Size</span></div>
                        <div className="fact-value" style={{ color: offProduct.quantity ? 'var(--accent-amber)' : 'var(--text-muted)' }}>
                          {offProduct.quantity || 'Not available in Open Food Facts'}
                        </div>
                      </div>

                      <div className="fact-card">
                        <div className="fact-label"><span>Packaging</span></div>
                        <div className="fact-value" style={{ color: offProduct.packaging ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                          {offProduct.packaging || 'Not available in Open Food Facts'}
                        </div>
                      </div>

                      <div className="fact-card">
                        <div className="fact-label"><span>Countries</span></div>
                        <div className="fact-value" style={{ color: offProduct.countries ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                          {offProduct.countries || (offProduct.countries_hierarchy?.join(', ')) || 'Not available in Open Food Facts'}
                        </div>
                      </div>

                      <div className="fact-card">
                        <div className="fact-label"><span>Manufacturing Places</span></div>
                        <div className="fact-value" style={{ color: offProduct.manufacturing_places ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                          {offProduct.manufacturing_places || 'Not available in Open Food Facts'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Nutrition Information — Product Enrichment */}
                  <div className="glass-panel" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
                      <h4 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem', margin: 0 }}>
                        <ShoppingBag size={16} style={{ color: 'var(--accent-emerald)' }} />
                        <span>Nutrition Facts (per 100g)</span>
                      </h4>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                        Source: Open Food Facts Product Enrichment
                      </span>
                    </div>

                    {offProduct.nutriments ? (
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                          <thead>
                            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', textAlign: 'left' }}>
                              <th style={{ padding: '0.5rem 0.75rem' }}>Nutrient</th>
                              <th style={{ padding: '0.5rem 0.75rem' }}>Amount</th>
                              <th style={{ padding: '0.5rem 0.75rem' }}>Source</th>
                            </tr>
                          </thead>
                          <tbody>
                            {[
                              { label: 'Energy', val: offProduct.nutriments['energy-kcal_100g'] ? `${offProduct.nutriments['energy-kcal_100g']} kcal` : (offProduct.nutriments.energy_100g ? `${offProduct.nutriments.energy_100g} kJ` : null) },
                              { label: 'Total Fat', val: offProduct.nutriments['fat_100g'] !== undefined ? `${offProduct.nutriments['fat_100g']} g` : null },
                              { label: 'Saturated Fat', val: offProduct.nutriments['saturated-fat_100g'] !== undefined ? `${offProduct.nutriments['saturated-fat_100g']} g` : null },
                              { label: 'Carbohydrates', val: offProduct.nutriments['carbohydrates_100g'] !== undefined ? `${offProduct.nutriments['carbohydrates_100g']} g` : null },
                              { label: 'Sugars', val: offProduct.nutriments['sugars_100g'] !== undefined ? `${offProduct.nutriments['sugars_100g']} g` : null },
                              { label: 'Proteins', val: offProduct.nutriments['proteins_100g'] !== undefined ? `${offProduct.nutriments['proteins_100g']} g` : null },
                              { label: 'Salt', val: offProduct.nutriments['salt_100g'] !== undefined ? `${offProduct.nutriments['salt_100g']} g` : null },
                              { label: 'Sodium', val: offProduct.nutriments['sodium_100g'] !== undefined ? `${offProduct.nutriments['sodium_100g']} g` : null }
                            ].map((item, nIdx) => (
                              <tr key={nIdx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                <td style={{ padding: '0.45rem 0.75rem', fontWeight: 600 }}>{item.label}</td>
                                <td style={{ padding: '0.45rem 0.75rem', color: item.val ? 'var(--text-primary)' : 'var(--text-muted)', fontStyle: item.val ? 'normal' : 'italic' }}>
                                  {item.val || 'Not available in Open Food Facts'}
                                </td>
                                <td style={{ padding: '0.45rem 0.75rem', color: 'var(--accent-cyan)', fontSize: '0.72rem' }}>
                                  OPEN FOOD FACTS
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.88rem', padding: '1rem 0' }}>
                        Not available in Open Food Facts
                      </div>
                    )}
                  </div>

                  {/* Ingredients & Allergens */}
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
                    <div className="glass-panel" style={{ padding: '1.5rem' }}>
                      <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.75rem' }}>
                        Ingredients Text
                      </h4>
                      {offProduct.ingredients_text ? (
                        <div style={{
                          background: 'rgba(0,0,0,0.3)',
                          padding: '1rem',
                          borderRadius: '8px',
                          fontSize: '0.82rem',
                          lineHeight: '1.5',
                          color: 'var(--text-primary)',
                          border: '1px solid var(--border-color)',
                          whiteSpace: 'pre-line',
                          maxHeight: '220px',
                          overflowY: 'auto'
                        }}>
                          {offProduct.ingredients_text}
                        </div>
                      ) : (
                        <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.88rem' }}>
                          Not available in Open Food Facts
                        </div>
                      )}
                    </div>

                    <div className="glass-panel" style={{ padding: '1.5rem' }}>
                      <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.75rem' }}>
                        Allergens & Labels
                      </h4>
                      <div style={{ marginBottom: '1rem' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '0.35rem' }}>Allergens</div>
                        <div style={{ fontSize: '0.85rem', color: offProduct.allergens ? 'var(--accent-rose)' : 'var(--text-muted)', fontStyle: offProduct.allergens ? 'normal' : 'italic' }}>
                          {offProduct.allergens || 'Not available in Open Food Facts'}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '0.35rem' }}>Labels / Certifications</div>
                        <div style={{ fontSize: '0.85rem', color: offProduct.labels ? 'var(--text-primary)' : 'var(--text-muted)', fontStyle: offProduct.labels ? 'normal' : 'italic' }}>
                          {offProduct.labels || 'Not available in Open Food Facts'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Product Images Gallery */}
                  <div className="glass-panel" style={{ padding: '1.5rem' }}>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <Eye size={16} style={{ color: 'var(--accent-cyan)' }} />
                      <span>Product Images from Open Food Facts</span>
                    </h4>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                      {[
                        { title: 'Front Package Label', url: offProduct.image_front_url || offProduct.image_front_small_url },
                        { title: 'Ingredients Label', url: offProduct.image_ingredients_url },
                        { title: 'Nutrition Label', url: offProduct.image_nutrition_url }
                      ].map((img, iIdx) => (
                        <div key={iIdx} style={{
                          background: 'rgba(0,0,0,0.3)',
                          borderRadius: '10px',
                          border: '1px solid var(--border-color)',
                          padding: '0.9rem',
                          textAlign: 'center'
                        }}>
                          <div style={{ fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.6rem' }}>{img.title}</div>
                          {img.url ? (
                            <div>
                              <img
                                src={img.url}
                                alt={img.title}
                                style={{ maxHeight: '180px', maxWidth: '100%', objectFit: 'contain', borderRadius: '6px', marginBottom: '0.6rem' }}
                              />
                              <div>
                                <a
                                  href={img.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{ color: 'var(--accent-cyan)', fontSize: '0.75rem', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}
                                >
                                  <span>View High-Res Image</span>
                                  <ExternalLink size={12} />
                                </a>
                              </div>
                            </div>
                          ) : (
                            <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.82rem', padding: '2rem 0' }}>
                              Not available in Open Food Facts
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Section 9: Image OCR + Open Food Facts Cross-Check */}
                  <div className="glass-panel" style={{ padding: '1.5rem', border: '1px solid rgba(0, 242, 254, 0.25)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <div>
                        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
                          <CheckCircle2 size={20} style={{ color: 'var(--accent-cyan)' }} />
                          <span>Image OCR vs Open Food Facts Cross-Check</span>
                        </h3>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                          Informational consistency comparison between physically detected image text and community database records.
                        </div>
                      </div>

                      {offCrossCheck && offCrossCheck.available && (
                        <span style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          color: offCrossCheck.details_consistent ? 'var(--accent-emerald)' : 'var(--accent-amber)',
                          background: offCrossCheck.details_consistent ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                          padding: '0.3rem 0.75rem',
                          borderRadius: '9999px',
                          border: `1px solid ${offCrossCheck.details_consistent ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
                        }}>
                          {offCrossCheck.details_consistent ? '✓ All Checked Fields Match' : `⚠ ${offCrossCheck.mismatches_found} Field Difference(s)`}
                        </span>
                      )}
                    </div>

                    {offCrossCheck && offCrossCheck.field_checks && offCrossCheck.field_checks.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {offCrossCheck.field_checks.map((chk, idx) => (
                          <div key={idx} style={{
                            background: 'rgba(0,0,0,0.3)',
                            padding: '0.9rem 1.1rem',
                            borderRadius: '10px',
                            border: `1px solid ${chk.status === 'MATCH' ? 'rgba(16, 185, 129, 0.25)' : (chk.status === 'POSSIBLE MISMATCH' ? 'rgba(245, 158, 11, 0.35)' : 'rgba(255,255,255,0.08)')}`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            flexWrap: 'wrap',
                            gap: '0.75rem'
                          }}>
                            <div style={{ flex: '1 1 300px' }}>
                              <div style={{ fontSize: '0.88rem', fontWeight: 700 }}>{chk.field}</div>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                                {chk.explanation}
                              </div>
                              <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.35rem', fontSize: '0.78rem' }}>
                                <span><strong>Image OCR:</strong> <code style={{ color: 'var(--accent-emerald)' }}>{chk.ocr_value}</code></span>
                                <span><strong>Open Food Facts:</strong> <code style={{ color: 'var(--accent-cyan)' }}>{chk.off_value}</code></span>
                              </div>
                            </div>

                            <span style={{
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              padding: '0.3rem 0.7rem',
                              borderRadius: '6px',
                              background: chk.status === 'MATCH' ? 'rgba(16, 185, 129, 0.15)' : (chk.status === 'POSSIBLE MISMATCH' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255,255,255,0.06)'),
                              color: chk.status === 'MATCH' ? 'var(--accent-emerald)' : (chk.status === 'POSSIBLE MISMATCH' ? 'var(--accent-amber)' : 'var(--text-muted)'),
                              border: `1px solid ${chk.status === 'MATCH' ? 'rgba(16, 185, 129, 0.3)' : (chk.status === 'POSSIBLE MISMATCH' ? 'rgba(245, 158, 11, 0.3)' : 'rgba(255,255,255,0.1)')}`
                            }}>
                              {chk.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic' }}>
                        Cross-check data is not available.
                      </div>
                    )}

                    {/* Section 9 Rule engine isolation alert */}
                    <div style={{
                      marginTop: '1rem',
                      background: 'rgba(245, 158, 11, 0.08)',
                      border: '1px solid rgba(245, 158, 11, 0.25)',
                      borderRadius: '8px',
                      padding: '0.75rem 1rem',
                      fontSize: '0.75rem',
                      color: 'var(--accent-amber)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}>
                      <AlertTriangle size={15} style={{ flexShrink: 0 }} />
                      <span>
                        <strong>Legal Isolation:</strong> Differences between Image OCR and Open Food Facts do NOT alter Legal Metrology compliance determinations. Legal compliance is assessed exclusively against official rule criteria using physical packaging evidence.
                      </span>
                    </div>
                  </div>

                  {/* Section 10: Multiple Data Sources Separation Grid */}
                  <div className="glass-panel" style={{ padding: '1.5rem' }}>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem' }}>
                      Multi-Source Data Provenance & Separation
                    </h4>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
                      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--accent-emerald)', fontWeight: 800 }}>SOURCE 1</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 700, marginTop: '0.2rem' }}>IMAGE OCR</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>Local Tesseract Engine with pixel OCR bounding boxes.</div>
                      </div>

                      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)', fontWeight: 800 }}>SOURCE 2</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 700, marginTop: '0.2rem' }}>BARCODE DECODER</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>ZXing / OpenCV pixel barcode decoder with Modulo-10 validation.</div>
                      </div>

                      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: '0.7rem', color: '#60a5fa', fontWeight: 800 }}>SOURCE 3</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 700, marginTop: '0.2rem' }}>OPEN FOOD FACTS</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>Public community-maintained crowdsourced product database.</div>
                      </div>

                      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--accent-purple)', fontWeight: 800 }}>SOURCE 4</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 700, marginTop: '0.2rem' }}>AI PRODUCT ENRICHMENT</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>AI vision / catalog enrichment provider layer.</div>
                      </div>

                      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--accent-amber)', fontWeight: 800 }}>SOURCE 5</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 700, marginTop: '0.2rem' }}>USER / INSPECTOR INPUT</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>Inspector Terminal manual measurements and overrides.</div>
                      </div>
                    </div>
                  </div>
                </>
              )}

            </div>
          )}

          {/* TAB 3: EXTRACTED FACTS GRID */}
          {viewMode === 'grid' && (
            <div className="facts-grid">
              <div className="fact-card" style={{ gridColumn: 'span 2' }}>
                <div className="fact-label"><Package size={16} style={{ color: 'var(--accent-cyan)' }} /><span>Commodity Name</span><span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>[Image OCR]</span></div>
                <div className="fact-value" style={{ fontSize: '1.2rem', color: 'var(--accent-cyan)' }}>{declarations.commodity_name || 'N/A'}</div>
              </div>
              <div className="fact-card">
                <div className="fact-label"><Tag size={16} style={{ color: 'var(--accent-blue)' }} /><span>Net Quantity</span><span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>[Image OCR]</span></div>
                <div className="fact-value">{declarations.net_quantity ? `${declarations.net_quantity.value} ${declarations.net_quantity.unit}` : 'N/A'}</div>
              </div>
              <div className="fact-card">
                <div className="fact-label"><Tag size={16} style={{ color: 'var(--accent-emerald)' }} /><span>Maximum Retail Price (MRP)</span><span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>[Image OCR]</span></div>
                <div className="fact-value" style={{ color: 'var(--accent-emerald)' }}>{declarations.max_retail_price ? `${declarations.max_retail_price.currency || '₹'} ${declarations.max_retail_price.value}` : 'N/A'}</div>
              </div>
              <div className="fact-card">
                <div className="fact-label"><Calendar size={16} style={{ color: 'var(--accent-purple)' }} /><span>Date of Mfg</span><span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>[Image OCR]</span></div>
                <div className="fact-value">{declarations.date_of_manufacture?.value || declarations.date_of_manufacture || 'N/A'}</div>
              </div>
              <div className="fact-card">
                <div className="fact-label"><Globe size={16} style={{ color: 'var(--accent-cyan)' }} /><span>Country of Origin</span><span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>[Image OCR]</span></div>
                <div className="fact-value">{declarations.country_of_origin?.value || declarations.country_of_origin || 'N/A (Domestic)'}</div>
              </div>
              <div className="fact-card" style={{ gridColumn: 'span 2' }}>
                <div className="fact-label"><Building size={16} style={{ color: 'var(--accent-amber)' }} /><span>Manufacturer / Packer</span><span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>[Image OCR]</span></div>
                <div className="fact-value">{declarations.manufacturer?.name || 'N/A'}</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>{declarations.manufacturer?.address || ''}</div>
              </div>
            </div>
          )}

          {/* TAB 4: RAW JSON */}
          {viewMode === 'json' && (
            <pre className="json-view">
              {JSON.stringify(scanResult, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}


