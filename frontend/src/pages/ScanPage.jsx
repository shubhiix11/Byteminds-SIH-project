import React, { useState, useRef } from 'react';
import { Camera, Sparkles, X, AlertTriangle, FileImage, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { scanImage } from '../services/api';

const SCAN_STEPS = [
  "Reading package image...",
  "Decoding barcode from image pixels...",
  "Querying Open Food Facts API v3 for product details...",
  "Detecting declarations & bounding boxes...",
  "Checking Legal Metrology rules...",
  "Measuring character height & scale...",
  "Preparing annotated evidence..."
];

export default function ScanPage({ onScanComplete }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanStepIndex, setScanStepIndex] = useState(0);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError('Please select a valid image file (JPG, PNG, WEBP, TIFF, etc.)');
      return;
    }
    setError(null);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleUploadAndScan = async () => {
    if (!selectedFile) return;
    setIsScanning(true);
    setError(null);
    setScanStepIndex(0);

    // Progress step animation interval
    const stepInterval = setInterval(() => {
      setScanStepIndex((prev) => (prev < SCAN_STEPS.length - 1 ? prev + 1 : prev));
    }, 450);

    try {
      const result = await scanImage(selectedFile);
      clearInterval(stepInterval);
      onScanComplete(result);
    } catch (err) {
      clearInterval(stepInterval);
      console.error(err);
      setError(err.message || 'Failed to scan image. Please check backend API server.');
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto' }}>
      {/* Header Eyebrow & Title */}
      <div style={{ marginBottom: '1.5rem' }}>
        <span className="eyebrow">Commodity Label Verification</span>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.04em', color: 'var(--text)', margin: '4px 0 8px' }}>
          Scan & Verify Legal Metrology Compliance
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '0.94rem', lineHeight: '1.6' }}>
          Upload packaged commodity package images to extract mandatory declarations, verify Legal Metrology (Packaged Commodities) Rules, and corroborate with Open Food Facts.
        </p>
      </div>

      <div className="panel" style={{ padding: '24px' }}>
        {!selectedFile ? (
          <div>
            {/* Viewfinder Dropzone */}
            <div
              className="dropzone"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{ minHeight: '340px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
                accept="image/*"
                style={{ display: 'none' }}
              />

              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '20px',
                background: 'var(--sage-soft)',
                color: 'var(--sage-deep)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.2rem',
                boxShadow: '0 8px 16px rgba(93, 143, 111, 0.15)'
              }}>
                <Camera size={32} />
              </div>

              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text)', marginBottom: '0.4rem' }}>
                Drag & Drop Package Label Image
              </h3>
              <p style={{ color: 'var(--muted)', fontSize: '0.88rem', maxWidth: '420px', marginBottom: '1.4rem' }}>
                Supports JPG, PNG, WEBP, TIFF images up to 10MB. Our local OCR pipeline automatically analyzes declarations, fonts, and barcodes.
              </p>

              <button className="btn secondary" type="button" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}>
                <FileImage size={16} />
                <span>Browse Image Files</span>
              </button>
            </div>
          </div>
        ) : (
          <div>
            {/* Camera Stage Viewfinder (matching frontend-design/mobile-camera.html) */}
            <div className="stage" style={{ marginBottom: '1.5rem', maxHeight: '440px' }}>
              <div className="tag">
                {isScanning ? 'Analyzing Label' : 'Ready for Inspection'}
              </div>

              <div className="label-box">
                <img
                  src={previewUrl}
                  alt="Selected Package Label"
                  style={{ width: '100%', height: '100%', objectFit: 'contain', borderRadius: '16px' }}
                />
              </div>

              {isScanning && <div className="scan-line"></div>}

              <div className="scan-cards">
                <div className="scan-pill">
                  {selectedFile.name.length > 25 ? `${selectedFile.name.substring(0, 22)}...` : selectedFile.name}
                </div>
                <div className="scan-pill">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </div>
              </div>

              <button
                onClick={clearSelection}
                disabled={isScanning}
                aria-label="Remove image"
                style={{
                  position: 'absolute',
                  top: '14px',
                  right: '14px',
                  background: 'rgba(255, 255, 255, 0.85)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  borderRadius: '50%',
                  width: '36px',
                  height: '36px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  zIndex: 10
                }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Scanning Progress Banner */}
            {isScanning && (
              <div style={{
                background: 'rgba(122, 167, 126, 0.12)',
                border: '1px solid rgba(122, 167, 126, 0.3)',
                borderRadius: '16px',
                padding: '1.2rem',
                marginBottom: '1.5rem',
                textAlign: 'center'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
                  <div className="spinner"></div>
                  <span style={{ fontWeight: 800, color: 'var(--sage-deep)', fontSize: '0.95rem' }}>
                    {SCAN_STEPS[scanStepIndex]}
                  </span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--muted)', fontWeight: 600 }}>
                  Step {scanStepIndex + 1} of {SCAN_STEPS.length} • Deterministic Metrology Engine
                </div>
              </div>
            )}

            {/* Actions Bar */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>Selected Commodity File</span>
                <div style={{ fontSize: '0.95rem', fontWeight: 800 }}>{selectedFile.name}</div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  className="btn secondary"
                  onClick={clearSelection}
                  disabled={isScanning}
                  type="button"
                >
                  Change Image
                </button>

                <button
                  className="btn primary"
                  onClick={handleUploadAndScan}
                  disabled={isScanning}
                  type="button"
                >
                  {isScanning ? (
                    <>
                      <div className="spinner" style={{ width: '16px', height: '16px', borderColor: 'rgba(255,255,255,0.3)', borderTopColor: '#ffffff' }}></div>
                      <span>Analyzing Package...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles size={17} />
                      <span>Process & Verify Compliance</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error Notice */}
        {error && (
          <div className="alert-box" style={{ marginTop: '1.5rem' }}>
            <div>
              <strong>Inspection Request Error</strong>
              <span>{error}</span>
            </div>
            <div className="alert-tag">Action Needed</div>
          </div>
        )}
      </div>
    </div>
  );
}
