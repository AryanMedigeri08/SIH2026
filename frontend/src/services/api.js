/**
 * api.js — REST API Client for Udyam Saathi Platform with Token-Aware Fetcher.
 */

const API_BASE = '/api/v2';

// Helper for authenticated HTTP requests
async function authFetch(url, token, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch (_) {}
    const error = new Error(errorDetail);
    error.status = res.status;
    throw error;
  }

  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return await res.json();
  }
  return await res.text();
}

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) return await res.json();
    return { status: 'degraded', database_connected: false };
  } catch (err) {
    return { status: 'offline', database_connected: false };
  }
}

// --- User Authentication & Profile API ---
export const authApi = {
  async registerProfile(token, profileData) {
    return await authFetch(`${API_BASE}/auth/register`, token, {
      method: 'POST',
      body: JSON.stringify(profileData),
    });
  },

  async syncSession(token) {
    return await authFetch(`${API_BASE}/auth/session`, token, {
      method: 'POST',
    });
  },

  async getMyProfile(token) {
    return await authFetch(`${API_BASE}/auth/me`, token, {
      method: 'GET',
    });
  },

  async updateMyProfile(token, updateData) {
    return await authFetch(`${API_BASE}/auth/me`, token, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  },

  async logout(token) {
    try {
      return await authFetch(`${API_BASE}/auth/logout`, token, {
        method: 'POST',
      });
    } catch (e) {
      return null;
    }
  },

  async deleteAccount(token) {
    return await authFetch(`${API_BASE}/auth/me`, token, {
      method: 'DELETE',
    });
  },
};

// --- Projects State Persistence API (Owner-Grounded) ---
export const projectsApi = {
  async createProject(token, projectData) {
    return await authFetch(`${API_BASE}/projects`, token, {
      method: 'POST',
      body: JSON.stringify(projectData),
    });
  },

  async createAndAnalyze(token, projectData) {
    return await authFetch(`${API_BASE}/projects/create-and-analyze`, token, {
      method: 'POST',
      body: JSON.stringify(projectData),
    });
  },

  async listProjects(token) {
    return await authFetch(`${API_BASE}/projects`, token, {
      method: 'GET',
    });
  },

  async getProject(token, projectId) {
    return await authFetch(`${API_BASE}/projects/${projectId}`, token, {
      method: 'GET',
    });
  },

  async getStatus(token, projectId) {
    return await authFetch(`${API_BASE}/projects/${projectId}/status`, token, {
      method: 'GET',
    });
  },

  async analyzeProject(token, projectId) {
    return await authFetch(`${API_BASE}/projects/${projectId}/analyze`, token, {
      method: 'POST',
    });
  },

  async updateProject(token, projectId, updateData) {
    return await authFetch(`${API_BASE}/projects/${projectId}`, token, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  },

  async getProjectDpr(token, projectId, format = 'json') {
    return await authFetch(`${API_BASE}/projects/${projectId}/dpr?format=${format}`, token, {
      method: 'GET',
    });
  },

  async deleteProject(token, projectId) {
    return await authFetch(`${API_BASE}/projects/${projectId}`, token, {
      method: 'DELETE',
    });
  },
};

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

export async function fetchOdopProduct(stateName, districtName) {
  try {
    const params = new URLSearchParams();
    if (stateName) params.append('state_name', stateName);
    if (districtName) params.append('district_name', districtName);
    const res = await fetch(`${API_BASE}/locations/odop?${params.toString()}`);
    if (res.ok) return await res.json();
  } catch (e) {}

  // Fallback ODOP mapping for offline / mock resilience
  const d = (districtName || '').toLowerCase();
  if (d.includes('bankura')) {
    return {
      has_odop_record: true,
      district_name: 'Bankura',
      state_name: 'West Bengal',
      odop_product: 'Terracotta Pottery & Dokra Metal Craft',
      secondary_product: 'Baluchari Handloom Silk Sarees',
      category: 'Handicrafts & Handlooms',
      matching_sectors: ['artisan_trades', 'apparel'],
      pmfme_eligible: false,
      gem_category: 'Handicrafts, Terracotta Artefacts & Silk Textiles',
      cfc_available: true,
      key_benefits: [
        'GI-tagged Bankura Terracotta Horse & Baluchari provenance protection',
        'Access to Bishnupur & Bikna Common Facility Centre (CFC)',
        'GeM ODOP seller portal direct onboarding without minimum turnover criteria',
        'KVIC / SFURTI artisan cluster capital assistance'
      ]
    };
  }
  if (d.includes('bulandshahr')) {
    return {
      has_odop_record: true,
      district_name: 'Bulandshahr',
      state_name: 'Uttar Pradesh',
      odop_product: 'Khurja Glazed Pottery & Ceramic Ware',
      category: 'Ceramics & Handicrafts',
      matching_sectors: ['fabrication', 'artisan_trades', 'manufacturing'],
      pmfme_eligible: false,
      gem_category: 'Ceramics, Tableware & Insulators',
      cfc_available: true,
      key_benefits: [
        'UP ODOP Margin Money Scheme (up to 20% state subsidy convergence)',
        'Access to Central Glass & Ceramic Research Institute (CGCRI) Khurja Centre',
        'Energy-efficient PNG furnace conversion grants',
        'GeM ODOP National Portal listing for public institutional procurement'
      ]
    };
  }
  if (d.includes('ujjain')) {
    return {
      has_odop_record: true,
      district_name: 'Ujjain',
      state_name: 'Madhya Pradesh',
      odop_product: 'Bhairavgarh Batik Print Textiles',
      category: 'Handloom & Textiles',
      matching_sectors: ['apparel', 'artisan_trades'],
      pmfme_eligible: false,
      gem_category: 'Batik Printed Sarees, Bedcovers & Fabrics',
      cfc_available: true,
      key_benefits: [
        'Bhairavgarh Batik GI tag brand recognition',
        'Mrignayani MP Government Emporium marketing corridor',
        'Common dying & wastewater treatment facility access',
        'GeM ODOP textile listing'
      ]
    };
  }
  return {
    has_odop_record: false,
    district_name: districtName || 'District',
    state_name: stateName || 'State',
    odop_product: 'Regional Agro & MSME Products',
    category: 'General Commercial MSME',
    matching_sectors: ['general'],
    pmfme_eligible: false,
    gem_category: 'Standard MSME Portal',
    cfc_available: false,
    key_benefits: ['PMEGP 25-35% Capital Subsidy', 'MUDRA Collateral-free Credit']
  };
}

// --- Feasibility Analysis & DPR Endpoints ---
export async function generateFeasibility(formData, token = null) {
  return await authFetch(`${API_BASE}/feasibility/generate`, token, {
    method: 'POST',
    body: JSON.stringify(formData),
  });
}

export async function fetchFeasibilityReport(reportId, token = null) {
  return await authFetch(`${API_BASE}/feasibility/${reportId}`, token, {
    method: 'GET',
  });
}

export async function fetchDprDocument(reportId, format = 'json', token = null, lang = 'en') {
  const langParam = lang ? `&lang=${encodeURIComponent(lang)}` : '';
  return await authFetch(`${API_BASE}/feasibility/${reportId}/dpr?format=${format}${langParam}`, token, {
    method: 'GET',
  });
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

// --- Google Cloud Translation & Multilingual API ---
export const translationApi = {
  async translateText(text, targetLanguage, sourceLanguage = 'en') {
    try {
      const res = await fetch(`${API_BASE}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          target_language: targetLanguage,
          source_language: sourceLanguage,
        }),
      });
      if (res.ok) return await res.json();
    } catch (e) {}
    return { translated_text: text, target_language: targetLanguage, provider: 'fallback' };
  },

  async translateBatch(texts, targetLanguage, sourceLanguage = 'en') {
    try {
      const res = await fetch(`${API_BASE}/translate/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          texts,
          target_language: targetLanguage,
          source_language: sourceLanguage,
        }),
      });
      if (res.ok) return await res.json();
    } catch (e) {}
    return texts.map((t) => ({ translated_text: t, target_language: targetLanguage, provider: 'fallback' }));
  },

  async translateDictionary(dictionary, targetLanguage, sourceLanguage = 'en') {
    try {
      const res = await fetch(`${API_BASE}/translate/dictionary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dictionary,
          target_language: targetLanguage,
          source_language: sourceLanguage,
        }),
      });
      if (res.ok) return await res.json();
    } catch (e) {}
    return dictionary;
  },

  async fetchSupportedLanguages() {
    try {
      const res = await fetch(`${API_BASE}/translate/languages`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return { status: 'active', supported_languages: [] };
  },
};

// --- Groq Chatbot & Conversational AI Advisor API ---
export const chatApi = {
  async sendChatMessage(messages, context = null, language = 'en', token = null) {
    return await authFetch(`${API_BASE}/chat`, token, {
      method: 'POST',
      body: JSON.stringify({
        messages,
        context,
        language,
      }),
    });
  },

  async sendVoiceAudio(audioBlob, context = null, language = 'en', history = [], token = null) {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');
    formData.append('language', language || 'en');
    if (context) {
      formData.append('context', JSON.stringify(context));
    }
    if (history && history.length > 0) {
      formData.append('history', JSON.stringify(history));
    }

    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}/chat/audio`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Voice chat failed: ${errText || res.statusText}`);
    }
    return await res.json();
  },

  async transcribeAudio(audioBlob, language = 'en') {
    const formData = new FormData();
    formData.append('file', audioBlob, 'wake_word.webm');
    formData.append('language', language || 'en');
    const res = await fetch(`${API_BASE}/chat/stt`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Audio transcription failed: ${errText || res.statusText}`);
    }
    return await res.json();
  },

  async generateTts(text, language = 'en', token = null) {
    return await authFetch(`${API_BASE}/chat/tts`, token, {
      method: 'POST',
      body: JSON.stringify({
        text,
        language,
      }),
    });
  },

  async checkChatHealth() {
    try {
      const res = await fetch(`${API_BASE}/chat/health`);
      if (res.ok) return await res.json();
      return { status: 'fallback_ready', provider: 'deterministic_fallback' };
    } catch (e) {
      return { status: 'offline', provider: 'deterministic_fallback' };
    }
  },
};

// --- Alternative Enterprise Recommendations API ---
export const recommendationsApi = {
  async fetchRecommendations(formData, token = null) {
    return await authFetch(`${API_BASE}/feasibility/recommendations`, token, {
      method: 'POST',
      body: JSON.stringify(formData),
    });
  },

  async fetchRecommendationsFromReport(reportId, token = null) {
    return await authFetch(`${API_BASE}/feasibility/recommendations/from-report?report_id=${encodeURIComponent(reportId)}`, token, {
      method: 'POST',
    });
  },
};

// --- MSME Market Intelligence & Opportunity Analysis API (Documents 2 & 4) ---
export const marketOpportunityApi = {
  async analyzeOpportunity(payload, token = null) {
    return await authFetch(`${API_BASE}/market-analysis/opportunity`, token, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async compareCategories(payload, token = null) {
    return await authFetch(`${API_BASE}/market-analysis/compare`, token, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getIntents(token = null) {
    return await authFetch(`${API_BASE}/market-analysis/intents`, token, {
      method: 'GET',
    });
  },

  async getSources(token = null) {
    return await authFetch(`${API_BASE}/market-analysis/sources`, token, {
      method: 'GET',
    });
  },

  async getCategories(token = null) {
    return await authFetch(`${API_BASE}/market-analysis/categories`, token, {
      method: 'GET',
    });
  },

  /** Document 5: Ecosystem Graph / Map endpoint */
  async getEcosystemGraph(payload, token = null) {
    return await authFetch(`${API_BASE}/market-analysis/ecosystem-graph`, token, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

