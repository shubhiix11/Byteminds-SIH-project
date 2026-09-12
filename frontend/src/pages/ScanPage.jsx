import React, { useState, useRef } from 'react';
import { Camera, Sparkles, X, AlertTriangle, FileImage, ShieldCheck, CheckCircle2, Barcode } from 'lucide-react';
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
  const [barcode, setBarcode] = useState('');
  const [barcodeError, setBarcodeError] = useState(null);
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

  const handleBarcodeChange = (e) => {
    const rawVal = e.target.value;
    setBarcode(rawVal);

    const cleanVal = rawVal.trim().replace(/\s+/g, '');
    if (!cleanVal) {
      setBarcodeError(null);
      return;
    }

    if (!/^\d+$/.test(cleanVal)) {
      setBarcodeError('Barcode should contain only numeric digits (e.g., EAN, UPC, GTIN).');
    } else if (cleanVal.length < 6 || cleanVal.length > 18) {
      setBarcodeError('Enter a valid numeric barcode (typically 8, 12, 13, or 14 digits).');
    } else {
      setBarcodeError(null);
    }
  };

  const handleUploadAndScan = async () => {
    // 1. IMAGE IS COMPULSORY
    if (!selectedFile) {
      setError('Please upload a package image to perform the compliance scan.');
      return;
    }

    // 2. OPTIONAL BARCODE VALIDATION
    const cleanBarcode = barcode.trim().replace(/\s+/g, '');
    if (cleanBarcode && !/^\d+$/.test(cleanBarcode)) {
      setError('Please enter a valid numeric barcode, or leave the barcode field empty.');
      return;
    }

    setIsScanning(true);
    setError(null);
    setScanStepIndex(0);

    const stepInterval = setInterval(() => {
      setScanStepIndex((prev) => (prev < SCAN_STEPS.length - 1 ? prev + 1 : prev));
    }, 450);

    try {
      const result = await scanImage(selectedFile, cleanBarcode || null);
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
          Upload packaged commodity package images to extract mandatory declarations, verify Legal Metrology (Packaged Commodities) Rules, and optionally corroborate with Open Food Facts.
        </p>
      </div>

      <div className="panel" style={{ padding: '24px' }}>
        
        {/* SECTION 1: UPLOAD PACKAGE LABEL * (COMPULSORY) */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span>Upload Package Label</span>
              <span style={{ color: '#b55246', fontWeight: 800 }}>*</span>
            </label>
            <span style={{ fontSize: '0.74rem', color: 'var(--muted)', fontWeight: 600 }}>
              Primary Evidence Source (Compulsory)
            </span>
          </div>

          {!selectedFile ? (
            <div
              className="dropzone"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{ minHeight: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
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
              <p style={{ color: 'var(--muted)', fontSize: '0.88rem', maxWidth: '420px', marginBottom: '1.4rem', textAlign: 'center' }}>
                Supports JPG, PNG, WEBP, TIFF images up to 10MB. Label image is required for Legal Metrology printed declaration verification.
              </p>

              <button className="btn secondary" type="button" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}>
                <FileImage size={16} />
                <span>Choose Image</span>
              </button>
            </div>
          ) : (
            <div className="stage" style={{ maxHeight: '420px', position: 'relative' }}>
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
          )}
        </div>

        {/* SECTION 2: BARCODE NUMBER (OPTIONAL) */}
        <div style={{
          marginBottom: '1.5rem',
          padding: '1.1rem 1.25rem',
          background: 'var(--panel-soft)',
          borderRadius: '16px',
          border: '1px solid var(--border)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <label htmlFor="manual-barcode-input" style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Barcode size={16} style={{ color: 'var(--sage-deep)' }} />
              <span>Barcode Number (Optional)</span>
            </label>
            <span style={{ fontSize: '0.72rem', color: 'var(--muted)', fontWeight: 600 }}>
              Optional Product Lookup
            </span>
          </div>

          <div style={{ position: 'relative', marginTop: '0.4rem' }}>
            <input
              id="manual-barcode-input"
              type="text"
              value={barcode}
              onChange={handleBarcodeChange}
              placeholder="Enter barcode / GTIN"
              disabled={isScanning}
              className="input-field"
              style={{
                width: '100%',
                padding: '0.65rem 1rem 0.65rem 2.5rem',
                borderRadius: '10px',
                border: barcodeError ? '1px solid #b55246' : '1px solid var(--border)',
                background: '#ffffff',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.9rem',
                color: 'var(--text)',
                letterSpacing: '0.05em'
              }}
            />
            <Barcode
              size={18}
              style={{
                position: 'absolute',
                left: '0.85rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--muted)',
                pointerEvents: 'none'
              }}
            />
            {barcode && (
              <button
                type="button"
                onClick={() => { setBarcode(''); setBarcodeError(null); }}
                disabled={isScanning}
                aria-label="Clear barcode"
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.2rem'
                }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.4rem', fontSize: '0.75rem', flexWrap: 'wrap', gap: '0.4rem' }}>
            <span style={{ color: 'var(--muted)' }}>
              Optional — used to retrieve product information from Open Food Facts.
            </span>
            {barcode && !barcodeError && (
              <span style={{ color: 'var(--sage-deep)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <CheckCircle2 size={12} /> {barcode.trim().replace(/\s+/g, '').length} digits
              </span>
            )}
          </div>

          {barcodeError && (
            <div style={{ color: '#b55246', fontSize: '0.75rem', fontWeight: 600, marginTop: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <AlertTriangle size={12} />
              <span>{barcodeError}</span>
            </div>
          )}
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

        {/* SECTION 3: ACTIONS BAR */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
          <div>
            {selectedFile ? (
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>Selected Commodity File</span>
                <div style={{ fontSize: '0.92rem', fontWeight: 800, color: 'var(--text)' }}>{selectedFile.name}</div>
              </div>
            ) : (
              <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                No image selected. <span style={{ color: '#b55246', fontWeight: 700 }}>Package label photo is compulsory.</span>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            {selectedFile && (
              <button
                className="btn secondary"
                onClick={clearSelection}
                disabled={isScanning}
                type="button"
              >
                Change Image
              </button>
            )}

            <button
              className="btn primary"
              onClick={handleUploadAndScan}
              disabled={isScanning}
              type="button"
              style={{ padding: '0.65rem 1.4rem' }}
            >
              {isScanning ? (
                <>
                  <div className="spinner" style={{ width: '16px', height: '16px', borderColor: 'rgba(255,255,255,0.3)', borderTopColor: '#ffffff' }}></div>
                  <span>Analyzing Package...</span>
                </>
              ) : (
                <>
                  <Sparkles size={17} />
                  <span>Scan Label for Compliance</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Notice */}
        {error && (
          <div className="alert-box" style={{ marginTop: '1.5rem' }}>
            <div>
              <strong>Inspection Request Notice</strong>
              <span>{error}</span>
            </div>
            <div className="alert-tag">Action Needed</div>
          </div>
        )}
      </div>
    </div>
  );
}
