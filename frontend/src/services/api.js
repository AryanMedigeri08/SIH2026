/**
 * api.js — REST API Client for Udyam Saathi Platform.
 */

const API_BASE = '/api/v2';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) return await res.json();
    return { status: 'degraded', database_connected: false };
  } catch (err) {
    return { status: 'offline', database_connected: false };
  }
}

// --- LGD 4-Tier Location Endpoints ---

export async function fetchStates() {
  try {
    const res = await fetch(`${API_BASE}/locations/states`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return [
    { state_code: 19, state_name: "West Bengal" },
    { state_code: 29, state_name: "Karnataka" },
    { state_code: 9, state_name: "Uttar Pradesh" },
    { state_code: 23, state_name: "Madhya Pradesh" },
    { state_code: 27, state_name: "Maharashtra" },
    { state_code: 8, state_name: "Rajasthan" },
    { state_code: 33, state_name: "Tamil Nadu" },
    { state_code: 24, state_name: "Gujarat" },
    { state_code: 10, state_name: "Bihar" },
  ];
}

export async function fetchDistricts(stateName, stateCode) {
  try {
    const params = new URLSearchParams();
    if (stateCode) params.append('state_code', stateCode);
    if (stateName) params.append('state_name', stateName);
    const res = await fetch(`${API_BASE}/locations/districts?${params.toString()}`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return [
    { district_code: 312, district_name: "Bankura", state_code: 19 },
    { district_code: 584, district_name: "Ramanagara", state_code: 29 },
    { district_code: 195, district_name: "Varanasi", state_code: 9 },
    { district_code: 435, district_name: "Ujjain", state_code: 23 },
    { district_code: 142, district_name: "Bulandshahr", state_code: 9 },
    { district_code: 490, district_name: "Pune", state_code: 27 },
  ];
}

export async function fetchBlocks(districtName, districtCode) {
  try {
    const params = new URLSearchParams();
    if (districtCode) params.append('district_code', districtCode);
    if (districtName) params.append('district_name', districtName);
    const res = await fetch(`${API_BASE}/locations/blocks?${params.toString()}`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return [
    { development_block_code: 101, development_block_name: districtName ? `${districtName} Central` : "Central Block", district_code: districtCode || 312 },
    { development_block_code: 102, development_block_name: districtName ? `${districtName} North` : "North Block", district_code: districtCode || 312 },
    { development_block_code: 103, development_block_name: districtName ? `${districtName} Rural` : "Rural Block", district_code: districtCode || 312 },
  ];
}

export async function fetchVillages(districtName, blockName, districtCode, blockCode) {
  try {
    const params = new URLSearchParams();
    if (districtCode) params.append('district_code', districtCode);
    if (blockCode) params.append('block_code', blockCode);
    if (districtName) params.append('district_name', districtName);
    if (blockName) params.append('block_name', blockName);
    const res = await fetch(`${API_BASE}/locations/villages?${params.toString()}`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return [
    { id: 1, village_code: 1001, village_name: "Gram Joypur", district_code: districtCode || 312, pincode: "722138" },
    { id: 2, village_code: 1002, village_name: "Gram Kalyanpur", district_code: districtCode || 312, pincode: "722139" },
    { id: 3, village_code: 1003, village_name: "Gram Shivpur", district_code: districtCode || 312, pincode: "722140" },
  ];
}

// --- Feasibility Analysis & DPR Endpoints ---

export async function generateFeasibility(formData) {
  try {
    const res = await fetch(`${API_BASE}/feasibility/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    if (res.ok) return await res.json();
    const err = await res.json();
    throw new Error(err.detail || 'Feasibility analysis failed.');
  } catch (err) {
    throw err;
  }
}

export async function fetchFeasibilityReport(reportId) {
  const res = await fetch(`${API_BASE}/feasibility/${reportId}`);
  if (!res.ok) throw new Error(`Report ${reportId} not found`);
  return await res.json();
}

export async function fetchDprDocument(reportId, format = 'json') {
  const res = await fetch(`${API_BASE}/feasibility/${reportId}/dpr?format=${format}`);
  if (!res.ok) throw new Error('DPR Document not available');
  if (format === 'html' || format === 'markdown') return await res.text();
  return await res.json();
}

export async function calculateFinancials(payload) {
  try {
    const res = await fetch(`${API_BASE}/financial/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.ok) return await res.json();
  } catch (e) {}
  return null;
}

// --- Data Source & Schemes Catalog Endpoints ---

export async function fetchDataSources() {
  try {
    const res = await fetch(`${API_BASE}/data-sources`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return [];
}

export async function fetchSchemesCatalog() {
  try {
    const res = await fetch(`${API_BASE}/data-sources/schemes`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return [];
}

export async function fetchSystemStats() {
  try {
    const res = await fetch(`${API_BASE}/data-sources/stats`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return null;
}

