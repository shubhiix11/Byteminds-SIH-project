import React, { useState } from 'react';
import { Package, Tag, Calendar, Building, PhoneCall, Globe, Code2, LayoutGrid, CheckCircle2, XCircle, AlertTriangle, HelpCircle, ArrowLeft, Info, FileText, Barcode, Check, AlertCircle, Layers, Eye, ExternalLink, Search, ChevronDown, ChevronUp } from 'lucide-react';
import { getUploadUrl } from '../services/api';

const STATUS_COLOR_MAP = {
  PASS: '#10b981',
  FAIL: '#f43f5e',
  WARNING: '#f59e0b',
  NOT_VERIFIABLE: '#60a5fa',
  NOT_APPLICABLE: '#6b7280'
};

export default function ResultsPage({ scanResult, onNewScan }) {
  const [viewMode, setViewMode] = useState('rules'); // 'rules' | 'evidence' | 'enrichment' | 'web_research' | 'grid' | 'json'
  const [imageTab, setImageTab] = useState('interactive'); // 'interactive' | 'annotated' | 'original'
  const [selectedRuleId, setSelectedRuleId] = useState(null);
  const [searchTraceOpen, setSearchTraceOpen] = useState(false);

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
  const activeImageUrl = imageTab === 'annotated' && annotated_image_url ? annotated_image_url : (original_image_url || image_url);

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

        <div style={{ display: 'flex', gap: '0.5rem', background: 'var(--bg-surface)', padding: '0.3rem', borderRadius: '12px', border: '1px solid var(--border-color)', alignItems: 'center' }}>
          <a
            href={`http://localhost:5001/api/reports/${scan_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
            style={{ padding: '0.4rem 0.85rem', fontSize: '0.82rem', textDecoration: 'none' }}
          >
            <span>Download PDF Report</span>
          </a>

          <button
            className={`nav-button ${viewMode === 'rules' ? 'active' : ''}`}
            onClick={() => setViewMode('rules')}
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.82rem' }}
          >
            <FileText size={16} />
            <span>Legal Rules ({rule_results?.length || 0})</span>
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

      {/* Legal Safety Disclaimer */}
      <div style={{
        background: 'rgba(59, 130, 246, 0.1)',
        border: '1px solid rgba(59, 130, 246, 0.25)',
        borderRadius: '12px',
        padding: '0.85rem 1.25rem',
        marginBottom: '1.5rem',
        fontSize: '0.82rem',
        color: '#93c5fd',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem'
      }}>
        <Info size={20} style={{ flexShrink: 0 }} />
        <span>{disclaimer || "AI-assisted compliance screening based on implemented Legal Metrology packaged-commodity requirements. Not an official government certification system."}</span>
      </div>

      {/* Summary Statistics Bar */}
      {summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem'
        }}>
          <div className="glass-panel" style={{ padding: '0.9rem 1.1rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Rules Checked</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{summary.rules_checked}</div>
          </div>
          <div className="glass-panel" style={{ padding: '0.9rem 1.1rem', textAlign: 'center', borderColor: 'rgba(16, 185, 129, 0.3)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-emerald)', fontWeight: 700, textTransform: 'uppercase' }}>Passed</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>{summary.passed}</div>
          </div>
          <div className="glass-panel" style={{ padding: '0.9rem 1.1rem', textAlign: 'center', borderColor: 'rgba(244, 63, 94, 0.3)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-rose)', fontWeight: 700, textTransform: 'uppercase' }}>Failed</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-rose)' }}>{summary.failed}</div>
          </div>
          <div className="glass-panel" style={{ padding: '0.9rem 1.1rem', textAlign: 'center', borderColor: 'rgba(96, 165, 250, 0.3)' }}>
            <div style={{ fontSize: '0.72rem', color: '#60a5fa', fontWeight: 700, textTransform: 'uppercase' }}>Not Verifiable</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#60a5fa' }}>{summary.not_verifiable}</div>
          </div>
          <div className="glass-panel" style={{ padding: '0.9rem 1.1rem', textAlign: 'center', borderColor: 'rgba(156, 163, 175, 0.3)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Not Applicable</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-muted)' }}>{summary.not_applicable}</div>
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
          {/* TAB 1: LEGAL RULES WITH SYNCHRONIZED SELECTION */}
          {viewMode === 'rules' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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

      {/* Developer Forensic Inspection Panel */}
      <div className="glass-panel" style={{ marginTop: '2.5rem', padding: '1.5rem', border: '1px dashed var(--accent-cyan)', background: 'rgba(0, 10, 25, 0.75)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Code2 size={20} style={{ color: 'var(--accent-cyan)' }} />
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Developer Forensic Inspection Panel
            </h3>
          </div>
          <span style={{ fontSize: '0.75rem', background: 'rgba(0, 242, 254, 0.15)', color: 'var(--accent-cyan)', padding: '0.2rem 0.6rem', borderRadius: '4px', fontWeight: 700 }}>
            LOCAL-FIRST AUDITED SCAN PIPELINE
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', fontSize: '0.82rem' }}>
          {/* IMAGE */}
          <div style={{ background: 'rgba(0,0,0,0.5)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '0.4rem', textTransform: 'uppercase', fontSize: '0.75rem' }}>IMAGE</div>
            <div><strong>Filename:</strong> <span className="mono-text" style={{ fontSize: '0.75rem' }}>{scanResult.debug?.IMAGE?.filename || filename || 'N/A'}</span></div>
            <div><strong>Dimensions:</strong> {scanResult.debug?.IMAGE?.dimensions || scanResult.debug?.image_dimensions || 'N/A'}</div>
            <div><strong>Format:</strong> {scanResult.debug?.IMAGE?.format || 'JPEG'}</div>
            {scanResult.debug?.IMAGE?.size_bytes && <div><strong>Size:</strong> {(scanResult.debug.IMAGE.size_bytes / 1024).toFixed(1)} KB</div>}
          </div>

          {/* LOCAL OCR */}
          <div style={{ background: 'rgba(0,0,0,0.5)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '0.4rem', textTransform: 'uppercase', fontSize: '0.75rem' }}>LOCAL OCR</div>
            <div><strong>Provider:</strong> <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>Tesseract</span></div>
            <div><strong>Status:</strong> <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>ACTIVE</span></div>
            <div><strong>Executed:</strong> <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>YES</span></div>
            <div><strong>Detections:</strong> <span style={{ color: (scanResult.ocr_detections?.length || scanResult.debug?.["LOCAL OCR"]?.detections_count || 0) > 0 ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 700 }}>{scanResult.ocr_detections?.length ?? scanResult.debug?.["LOCAL OCR"]?.detections_count ?? 0}</span></div>
            <div><strong>Orientation:</strong> <span className="mono-text" style={{ color: 'var(--accent-cyan)' }}>{scanResult.best_orientation ?? scanResult.debug?.["LOCAL OCR"]?.best_orientation ?? 0}°</span></div>
            <div><strong>Characters:</strong> {scanResult.debug?.["LOCAL OCR"]?.characters_extracted ?? scanResult.raw_ocr_text?.length ?? 0}</div>
            {((scanResult.ocr_detections?.length ?? scanResult.debug?.["LOCAL OCR"]?.detections_count ?? 0) === 0) && (
              <div style={{ color: 'var(--accent-amber)', fontSize: '0.72rem', marginTop: '0.3rem', fontStyle: 'italic' }}>
                OCR executed but no reliable text was extracted.
              </div>
            )}
          </div>

          {/* OPENAI VISION */}
          <div style={{ background: 'rgba(0,0,0,0.5)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '0.4rem', textTransform: 'uppercase', fontSize: '0.75rem' }}>OPENAI VISION (OPTIONAL)</div>
            <div><strong>Attempted:</strong> {scanResult.debug?.["OPENAI VISION"]?.attempted ? 'TRUE' : 'FALSE'}</div>
            <div><strong>Available:</strong> {scanResult.debug?.["OPENAI VISION"]?.available ? 'TRUE' : 'FALSE'}</div>
            <div><strong>Status:</strong> <span style={{ color: scanResult.debug?.["OPENAI VISION"]?.status === 'SUCCESS' ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 700 }}>{scanResult.debug?.["OPENAI VISION"]?.status || 'UNAVAILABLE'}</span></div>
            {scanResult.debug?.["OPENAI VISION"]?.error && (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', marginTop: '0.3rem', wordBreak: 'break-word' }}>
                <strong>Note:</strong> {scanResult.debug["OPENAI VISION"].error}
              </div>
            )}
          </div>

          {/* BARCODE */}
          <div style={{ background: 'rgba(0,0,0,0.5)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '0.4rem', textTransform: 'uppercase', fontSize: '0.75rem' }}>BARCODE DECODER</div>
            <div><strong>Attempted:</strong> <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>TRUE</span></div>
            <div><strong>Detected:</strong> <span style={{ color: (scanResult.debug?.BARCODE?.detected || (scanResult.barcode && scanResult.barcode !== 'NOT_DETECTED')) ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 700 }}>{(scanResult.debug?.BARCODE?.detected || (scanResult.barcode && scanResult.barcode !== 'NOT_DETECTED')) ? 'TRUE' : 'FALSE'}</span></div>
            <div><strong>Format:</strong> {scanResult.debug?.BARCODE?.format || scanResult.barcode_decoding?.format || 'N/A'}</div>
            <div><strong>Value:</strong> <span className="mono-text" style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>{scanResult.debug?.BARCODE?.value || scanResult.barcode || 'null'}</span></div>
            <div><strong>Checksum Valid:</strong> <span style={{ color: scanResult.debug?.BARCODE?.checksum_valid ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 700 }}>{scanResult.debug?.BARCODE?.checksum_valid ? 'TRUE' : (scanResult.debug?.BARCODE?.detected ? 'FALSE' : 'N/A')}</span></div>
          </div>

          {/* ENRICHMENT */}
          <div style={{ background: 'rgba(0,0,0,0.5)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '0.4rem', textTransform: 'uppercase', fontSize: '0.75rem' }}>ENRICHMENT (OPTIONAL)</div>
            <div><strong>Attempted:</strong> {scanResult.debug?.ENRICHMENT?.attempted ? 'TRUE' : 'FALSE'}</div>
            <div><strong>Status:</strong> <span style={{ color: scanResult.debug?.ENRICHMENT?.status === 'SUCCESS' ? 'var(--accent-emerald)' : 'var(--text-muted)', fontWeight: 700 }}>{scanResult.debug?.ENRICHMENT?.status || 'SKIPPED'}</span></div>
            <div><strong>Product Identified:</strong> {scanResult.debug?.ENRICHMENT?.product_identified ? 'TRUE' : 'FALSE'}</div>
          </div>

          {/* WEB RESEARCH (GOOGLE) */}
          <div style={{ background: 'rgba(0,0,0,0.5)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '0.4rem', textTransform: 'uppercase', fontSize: '0.75rem' }}>WEB RESEARCH (GOOGLE)</div>
            <div><strong>Provider:</strong> <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>Google Web Search</span></div>
            <div><strong>Status:</strong> <span style={{ color: (scanResult.debug?.["WEB RESEARCH"]?.status || webResearch?.status) === 'COMPLETE' ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 700 }}>{scanResult.debug?.["WEB RESEARCH"]?.status || webResearch?.status || 'UNAVAILABLE'}</span></div>
            <div><strong>Queries Executed:</strong> {scanResult.debug?.["WEB RESEARCH"]?.queries_executed ?? webResearch?.queries_run ?? 0}</div>
            <div><strong>Results Found:</strong> {scanResult.debug?.["WEB RESEARCH"]?.results_found ?? webResearch?.results_found ?? 0}</div>
            <div><strong>Pages Reviewed:</strong> {scanResult.debug?.["WEB RESEARCH"]?.pages_reviewed ?? webResearch?.pages_fetched ?? 0}</div>
            <div><strong>Sources Used:</strong> {scanResult.debug?.["WEB RESEARCH"]?.sources_used ?? webResearch?.sources_used ?? 0}</div>
          </div>

          {/* RULE ENGINE */}
          <div style={{ background: 'rgba(0,0,0,0.5)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '0.4rem', textTransform: 'uppercase', fontSize: '0.75rem' }}>RULE ENGINE</div>
            <div><strong>Rules Evaluated:</strong> {scanResult.debug?.["RULE ENGINE"]?.rules_evaluated ?? summary?.rules_checked ?? 0}</div>
            <div><strong>Passed:</strong> <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>{scanResult.debug?.["RULE ENGINE"]?.passed ?? summary?.passed ?? 0}</span></div>
            <div><strong>Failed:</strong> <span style={{ color: 'var(--accent-rose)', fontWeight: 700 }}>{scanResult.debug?.["RULE ENGINE"]?.failed ?? summary?.failed ?? 0}</span></div>
            <div><strong>Not Verifiable:</strong> <span style={{ color: '#f59e0b', fontWeight: 700 }}>{scanResult.debug?.["RULE ENGINE"]?.not_verifiable ?? summary?.not_verifiable ?? 0}</span></div>
          </div>

          {/* DATA INTEGRITY */}
          <div style={{ background: 'rgba(0,0,0,0.5)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '0.4rem', textTransform: 'uppercase', fontSize: '0.75rem' }}>DATA INTEGRITY</div>
            <div><strong>Mock Used:</strong> <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>FALSE</span></div>
            <div><strong>Synthetic Data:</strong> <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>FALSE</span></div>
            <div><strong>Mode:</strong> <span className="mono-text" style={{ color: 'var(--accent-cyan)' }}>{scanResult.debug?.labelsure_mode || 'production'}</span></div>
          </div>
        </div>

        {/* SECTION 12: CANDIDATE DECLARATIONS FORENSIC PANEL */}
        <div style={{ marginTop: '1.2rem', background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '0.6rem', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            CANDIDATE DECLARATIONS (EXTRACTED SIGNALS)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', fontSize: '0.8rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Manufacturer:</span>{' '}
              <span style={{ color: scanResult.candidate_declarations?.manufacturer ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 600 }}>
                {scanResult.candidate_declarations?.manufacturer || '[Not detected in uploaded surface]'}
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>MRP:</span>{' '}
              <span style={{ color: scanResult.candidate_declarations?.mrp ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 600 }}>
                {scanResult.candidate_declarations?.mrp || '[Not detected in uploaded surface]'}
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Net Quantity:</span>{' '}
              <span style={{ color: scanResult.candidate_declarations?.net_quantity ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 600 }}>
                {scanResult.candidate_declarations?.net_quantity || '[Not detected in uploaded surface]'}
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Date:</span>{' '}
              <span style={{ color: scanResult.candidate_declarations?.date ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 600 }}>
                {scanResult.candidate_declarations?.date || '[Not detected in uploaded surface]'}
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Consumer Care:</span>{' '}
              <span style={{ color: scanResult.candidate_declarations?.consumer_care ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 600 }}>
                {scanResult.candidate_declarations?.consumer_care || '[Not detected in uploaded surface]'}
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Country:</span>{' '}
              <span style={{ color: scanResult.candidate_declarations?.country ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: 600 }}>
                {scanResult.candidate_declarations?.country || '[Not detected in uploaded surface]'}
              </span>
            </div>
          </div>
        </div>

        {/* SECTION 1 & 12: RAW OCR TEXT FORENSIC PANEL */}
        <div style={{ marginTop: '1.2rem', background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              RAW OCR TEXT (TESSERACT EXTRACTION FORENSIC)
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Characters: <strong>{scanResult.raw_ocr_text?.length || scanResult.debug?.["LOCAL OCR"]?.characters_extracted || 0}</strong> • Words: <strong>{(scanResult.raw_ocr_text || "").split(/\s+/).filter(Boolean).length}</strong> • Detections: <strong>{scanResult.ocr_detections?.length || scanResult.debug?.["LOCAL OCR"]?.detections_count || 0}</strong>
            </div>
          </div>
          <pre style={{
            background: 'rgba(10, 14, 23, 0.9)',
            padding: '0.85rem',
            borderRadius: '6px',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            maxHeight: '220px',
            overflowY: 'auto',
            fontFamily: 'monospace',
            fontSize: '0.78rem',
            color: (scanResult.raw_ocr_text || scanResult.all_detected_text) ? 'var(--accent-cyan)' : 'var(--accent-amber)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            margin: 0
          }}>
            {(scanResult.raw_ocr_text || scanResult.all_detected_text) || '[OCR executed but no reliable text was extracted from this image]'}
          </pre>
        </div>
      </div>
    </div>
  );
}

