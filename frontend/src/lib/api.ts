import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const api = {
  // Health
  getHealth: async () => {
    const { data } = await client.get('/health');
    return data;
  },

  // Dashboard
  getDashboard: async () => {
    try {
      const { data } = await client.get('/api/v1/dashboard');
      return data;
    } catch {
      // Return mock data if API unavailable
      return {
        compliance_score: 85,
        facilities_count: 3,
        regulations_count: 12,
        gaps_summary: {
          critical: 1,
          high: 2,
          medium: 4,
          low: 6,
          total: 13,
        },
        alerts_count: 3,
        recent_alerts: [],
      };
    }
  },

  // Facilities
  getFacilities: async () => {
    try {
      const { data } = await client.get('/api/v1/facilities');
      return data;
    } catch {
      // Return mock data
      return [
        {
          facility_id: 'permian-001',
          name: 'Permian Basin Production Facility 1',
          facility_type: 'production',
          state: 'TX',
          county: 'Midland',
          operator: 'Demo Oil & Gas Co.',
          is_major_source: false,
          title_v_applicable: false,
          metadata: {
            total_potential_emissions_tpy: {
              VOC: 45.5,
              NOx: 12.3,
              CO: 8.7,
              HAP: 3.2,
              CO2e: 15000,
            },
          },
        },
        {
          facility_id: 'bakken-001',
          name: 'Bakken Gathering Station',
          facility_type: 'gathering',
          state: 'ND',
          county: 'McKenzie',
          operator: 'Demo Oil & Gas Co.',
          is_major_source: true,
          title_v_applicable: true,
          metadata: {
            total_potential_emissions_tpy: {
              VOC: 125.0,
              NOx: 85.0,
              CO: 45.0,
              HAP: 12.5,
              CO2e: 45000,
            },
          },
        },
        {
          facility_id: 'wyoming-001',
          name: 'Wyoming Gas Processing Plant',
          facility_type: 'processing',
          state: 'WY',
          county: 'Sublette',
          operator: 'Demo Oil & Gas Co.',
          is_major_source: true,
          title_v_applicable: true,
          metadata: {
            total_potential_emissions_tpy: {
              VOC: 250.0,
              NOx: 150.0,
              CO: 95.0,
              HAP: 25.0,
              CO2e: 120000,
            },
          },
        },
      ];
    }
  },

  getFacility: async (id: string) => {
    try {
      const { data } = await client.get(`/api/v1/facilities/${id}`);
      return data;
    } catch {
      const facilities = await api.getFacilities();
      return facilities.find((f: any) => f.facility_id === id);
    }
  },

  createFacility: async (facility: any) => {
    const { data } = await client.post('/api/v1/facilities', facility);
    return data;
  },

  // Gaps
  getGaps: async (params?: { facility_id?: string; severity?: string }) => {
    try {
      const { data } = await client.get('/api/v1/analysis/gaps', { params });
      return data;
    } catch {
      return { gaps: [], summary: {} };
    }
  },

  // Analysis
  runAnalysis: async (request: {
    facility_ids?: string[];
    lookback_days?: number;
    report_types?: string[];
  }) => {
    const { data } = await client.post('/api/v1/analysis/run', request);
    return data;
  },

  // Reports
  generateReport: async (request: {
    report_type: string;
    facility_ids?: string[];
  }) => {
    const { data } = await client.post('/api/v1/reports/generate', request);
    return data;
  },

  getReports: async () => {
    try {
      const { data } = await client.get('/api/v1/reports');
      return data;
    } catch {
      return [];
    }
  },

  // Regulations
  getRegulations: async (params?: { regulation_type?: string; limit?: number }) => {
    try {
      const { data } = await client.get('/api/v1/regulations', { params });
      return data;
    } catch {
      return [];
    }
  },

  searchRegulations: async (query: string) => {
    try {
      const { data } = await client.get('/api/v1/regulations/search', {
        params: { query },
      });
      return data;
    } catch {
      return { results: [], query, count: 0 };
    }
  },

  // Monitoring
  scanRegulations: async (lookback_days: number = 30) => {
    const { data } = await client.post('/api/v1/monitor/scan', null, {
      params: { lookback_days },
    });
    return data;
  },
};

export default api;
