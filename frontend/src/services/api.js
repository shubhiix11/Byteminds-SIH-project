const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    if (!res.ok) return { connected: false };
    const data = await res.json();
    return {
      connected: data.status === 'ok',
      ...data
    };
  } catch (err) {
    return { connected: false };
  }
}

async function resizeImageIfNeeded(file, maxDimension = 1024) {
  if (!file || !file.type || !file.type.startsWith('image/')) return file;
  return new Promise((resolve) => {
    try {
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => {
        URL.revokeObjectURL(url);
        const { width, height } = img;
        if (width <= maxDimension && height <= maxDimension) {
          return resolve(file);
        }
        let newW = width;
        let newH = height;
        if (width > height) {
          newH = Math.round((height * maxDimension) / width);
          newW = maxDimension;
        } else {
          newW = Math.round((width * maxDimension) / height);
          newH = maxDimension;
        }
        const canvas = document.createElement('canvas');
        canvas.width = newW;
        canvas.height = newH;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, newW, newH);
        canvas.toBlob((blob) => {
          if (!blob) return resolve(file);
          try {
            const fileName = file.name || 'commodity_label.jpg';
            const optimizedFile = new File([blob], fileName, {
              type: 'image/jpeg',
              lastModified: Date.now()
            });
            resolve(optimizedFile);
          } catch (e) {
            // Mobile Safari / Android WebView fallback when new File([blob]) is unsupported
            resolve(blob);
          }
        }, 'image/jpeg', 0.90);
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        resolve(file);
      };
      img.src = url;
    } catch (err) {
      resolve(file);
    }
  });
}

export async function scanImage(imageFile, barcode = null, options = {}) {
  const { persist = true, inspector = null } = options;
  const optimizedImage = await resizeImageIfNeeded(imageFile, 1024);
  const formData = new FormData();
  const safeFileName = imageFile.name || 'commodity_label.jpg';
  formData.append('image', optimizedImage, safeFileName);
  formData.append('persist', String(persist !== false));
  if (inspector) {
    formData.append('inspector', inspector);
  }
  
  const cleanBarcode = barcode && typeof barcode === 'string' ? barcode.trim().replace(/\s+/g, '') : null;
  if (cleanBarcode) {
    formData.append('barcode', cleanBarcode);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/scan`, {
      method: 'POST',
      body: formData,
    });
  } catch (netErr) {
    throw new Error('Could not connect to the inspection backend server. Please check your network connection or verify that the backend is awake.');
  }

  let data;
  try {
    data = await response.json();
  } catch (parseErr) {
    throw new Error(`Server returned status ${response.status} (${response.statusText || 'Unknown Error'})`);
  }

  if (!response.ok) {
    throw new Error(data.error || data.details || 'Failed to scan image');
  }

  // If a manual barcode was supplied and backend's image-level decoder didn't find one on the label surface,
  // query the backend's existing /api/openfoodfacts endpoint to enrich with real Open Food Facts product data
  if (cleanBarcode && (!data.openfoodfacts || data.openfoodfacts.status === 'NO_BARCODE' || !data.openfoodfacts.product)) {
    try {
      const offRes = await fetch(`${API_BASE_URL}/api/openfoodfacts/${encodeURIComponent(cleanBarcode)}`);
      const offData = await offRes.json();
      if (offData && offData.status) {
        data.openfoodfacts = {
          available: offData.status === 'FOUND',
          status: offData.status,
          barcode: cleanBarcode,
          product: offData.product,
          source_url: offData.source_url,
          retrieved_at: offData.retrieved_at,
          disclaimer: offData.disclaimer,
          source: 'OPEN_FOOD_FACTS'
        };
        data.openfoodfacts_product = offData.product;
        data.openfoodfacts_status = offData.status;
        data.openfoodfacts_source_url = offData.source_url;
        data.openfoodfacts_retrieved_at = offData.retrieved_at;
        data.barcode = cleanBarcode;
        data.barcode_source = 'MANUAL_ENTRY';
      }
    } catch (offErr) {
      console.warn('Manual barcode Open Food Facts lookup notice:', offErr);
    }
  }

  if (cleanBarcode && !data.barcode_source) {
    data.barcode_source = (data.barcode_decoding?.detected && data.barcode_decoding?.barcode === cleanBarcode)
      ? 'IMAGE_DETECTED'
      : 'MANUAL_ENTRY';
  } else if (!data.barcode_source) {
    data.barcode_source = data.barcode_decoding?.detected ? 'IMAGE_DETECTED' : 'NONE';
  }

  return data;
}


export async function fetchScans(filters = {}) {
  const queryParams = new URLSearchParams();
  if (filters.search) queryParams.append('search', filters.search);
  if (filters.status && filters.status !== 'ALL') queryParams.append('status', filters.status);
  if (filters.category) queryParams.append('category', filters.category);

  const queryStr = queryParams.toString();
  const url = queryStr ? `${API_BASE_URL}/api/scans?${queryStr}` : `${API_BASE_URL}/api/scans`;

  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to fetch scan history');
  }
  return data.scans || [];
}

export async function fetchScanById(id) {
  const response = await fetch(`${API_BASE_URL}/api/scans/${id}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to fetch scan details');
  }
  return data.scan;
}

export async function fetchDashboardMetrics() {
  const response = await fetch(`${API_BASE_URL}/api/dashboard`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to fetch dashboard metrics');
  }
  return data.dashboard;
}

export function getReportDownloadUrl(scanId) {
  if (!scanId) return '#';
  return `${API_BASE_URL}/api/reports/${scanId}`;
}

export function getUploadUrl(path) {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return `${API_BASE_URL}${path.startsWith('/') ? '' : '/'}${path}`;
}

export async function saveScanRecord(scanData, inspector = 'Inspector') {
  const response = await fetch(`${API_BASE_URL}/api/scans/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scan_id: scanData.scan_id,
      scan: scanData,
      inspector: inspector
    })
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to save scan record');
  }
  return data;
}

