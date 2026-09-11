const API_BASE_URL = 'http://localhost:5001';

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

export async function fetchScans() {
  const response = await fetch(`${API_BASE_URL}/api/scans`);
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

export function getUploadUrl(path) {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return `${API_BASE_URL}${path.startsWith('/') ? '' : '/'}${path}`;
}
