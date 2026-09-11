import React, { useState, useRef } from 'react';
import { UploadCloud, Sparkles, X, AlertCircle } from 'lucide-react';
import { scanImage } from '../services/api';

const SCAN_STEPS = [
  "Reading package image...",
  "Detecting declarations & bounding boxes...",
  "Normalizing unit values...",
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
      setError('Please select a valid image file (JPG, PNG, WEBP, etc.)');
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
    <div className="container" style={{ maxWidth: '800px' }}>
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <h1 className="title-gradient" style={{ fontSize: '2.2rem', fontWeight: 800 }}>
          Legal Metrology Commodity Scanner
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1rem', marginTop: '0.5rem' }}>
          Upload packaged commodity label image to extract declarations, verify legal rules & measure evidence.
        </p>
      </div>

      <div className="glass-panel" style={{ padding: '2rem' }}>
        {!selectedFile ? (
          <div
            className="dropzone"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
              accept="image/*"
              style={{ display: 'none' }}
            />
            <div style={{
              display: 'inline-flex',
              padding: '1.2rem',
              borderRadius: '20px',
              background: 'rgba(0, 242, 254, 0.1)',
              color: 'var(--accent-cyan)',
              marginBottom: '1rem'
            }}>
              <UploadCloud size={44} />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.4rem' }}>
              Drag & Drop Package Label Image
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Supports JPG, PNG, WEBP, TIFF images up to 10MB
            </p>
            <button className="btn-secondary" style={{ marginTop: '1.5rem' }}>
              Browse Image Files
            </button>
          </div>
        ) : (
          <div>
            <div style={{
              position: 'relative',
              borderRadius: '16px',
              overflow: 'hidden',
              background: 'rgba(0,0,0,0.4)',
              border: '1px solid var(--border-color)',
              marginBottom: '1.5rem',
              maxHeight: '400px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <img
                src={previewUrl}
                alt="Selected Package Label"
                style={{ maxWidth: '100%', maxHeight: '400px', objectFit: 'contain' }}
              />
              <button
                onClick={clearSelection}
                disabled={isScanning}
                style={{
                  position: 'absolute',
                  top: '1rem',
                  right: '1rem',
                  background: 'rgba(0,0,0,0.75)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '36px',
                  height: '36px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer'
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Progress Step Banner when Scanning */}
            {isScanning && (
              <div style={{
                background: 'rgba(0, 242, 254, 0.1)',
                border: '1px solid rgba(0, 242, 254, 0.3)',
                borderRadius: '12px',
                padding: '1rem',
                marginBottom: '1.5rem',
                textAlign: 'center'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <div className="spinner" style={{ width: '22px', height: '22px' }}></div>
                  <span style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '0.95rem' }}>
                    {SCAN_STEPS[scanStepIndex]}
                  </span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Step {scanStepIndex + 1} of {SCAN_STEPS.length}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '0.95rem', fontWeight: 700 }}>{selectedFile.name}</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button className="btn-secondary" onClick={clearSelection} disabled={isScanning}>
                  Choose Different Image
                </button>

                <button
                  className="btn-primary"
                  onClick={handleUploadAndScan}
                  disabled={isScanning}
                >
                  {isScanning ? (
                    <span>Analyzing Package...</span>
                  ) : (
                    <>
                      <Sparkles size={18} />
                      <span>Process & Verify Compliance</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div style={{
            marginTop: '1.5rem',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: '12px',
            padding: '1rem',
            color: 'var(--accent-rose)',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem'
          }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}
