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

export async function scanImage(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);

  const response = await fetch(`${API_BASE_URL}/api/scan`, {
    method: 'POST',
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || data.details || 'Failed to scan image');
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

