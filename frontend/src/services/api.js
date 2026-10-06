/**
 * REST API client integration for Canary Deployment Simulator (P71).
 * Communicates with FastAPI backend, manages JWT authentication tokens,
 * and provides typed async handlers for all deployment and telemetry endpoints.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('canary_jwt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to catch unauthorized responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token if expired
      localStorage.removeItem('canary_jwt_token');
    }
    return Promise.reject(error);
  }
);

export const api = {
  // System Health
  getHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  getHealthDetails: async () => {
    const res = await apiClient.get('/health/details');
    return res.data;
  },

  // Authentication
  login: async (email, password) => {
    const res = await apiClient.post('/auth/login', { email, password });
    if (res.data.access_token) {
      localStorage.setItem('canary_jwt_token', res.data.access_token);
      localStorage.setItem('canary_user_email', res.data.user.email);
      localStorage.setItem('canary_user_role', res.data.user.role);
    }
    return res.data;
  },

  loginDefaultAdmin: async () => {
    return api.login('admin@canary.local', 'AdminSecurePassword123!');
  },

  logout: () => {
    localStorage.removeItem('canary_jwt_token');
    localStorage.removeItem('canary_user_email');
    localStorage.removeItem('canary_user_role');
  },

  getAuthUser: () => {
    const token = localStorage.getItem('canary_jwt_token');
    const email = localStorage.getItem('canary_user_email');
    const role = localStorage.getItem('canary_user_role');
    return token ? { token, email, role } : null;
  },

  // Deployments
  getDeployments: async () => {
    const res = await apiClient.get('/deployments');
    return res.data;
  },

  getDeployment: async (id) => {
    const res = await apiClient.get(`/deployments/${id}`);
    return res.data;
  },

  createDeployment: async (data) => {
    const res = await apiClient.post('/deployments', data);
    return res.data;
  },

  startDeployment: async (id) => {
    const res = await apiClient.post(`/deployments/${id}/start`);
    return res.data;
  },

  deleteDeployment: async (id) => {
    const res = await apiClient.delete(`/deployments/${id}`);
    return res.data;
  },

  // Traffic Control
  shiftTraffic: async (id, stablePercentage, canaryPercentage) => {
    const res = await apiClient.post(`/deployments/${id}/traffic`, {
      stable_percentage: stablePercentage,
      canary_percentage: canaryPercentage,
    });
    return res.data;
  },

  getTraffic: async (id) => {
    const res = await apiClient.get(`/deployments/${id}/traffic`);
    return res.data;
  },

  // Client Simulation
  simulateRoutedTraffic: async (id, count = 25, payload = {}) => {
    const res = await apiClient.post(`/deployments/${id}/simulate`, {
      count,
      payload,
    });
    return res.data;
  },

  simulateVersionTraffic: async (id, versionType, count = 10) => {
    const res = await apiClient.post(`/deployments/${id}/simulate/version/${versionType}`, {
      count,
    });
    return res.data;
  },

  // Controlled Failure Injection (Phase 10)
  injectFailure: async (id, failureRate, errorType = 'HTTP_500', affectedVersion = 'CANARY', latencyMs = null) => {
    const body = {
      failure_rate: failureRate,
      error_type: errorType,
      affected_version: affectedVersion,
    };
    if (latencyMs) body.latency_ms = latencyMs;
    const res = await apiClient.post(`/deployments/${id}/failure`, body);
    return res.data;
  },

  clearFailure: async (id) => {
    const res = await apiClient.delete(`/deployments/${id}/failure`);
    return res.data;
  },

  // Rollback Controls (Phase 9)
  manualRollback: async (id, reason = 'Operator triggered emergency rollback') => {
    const res = await apiClient.post(`/deployments/${id}/rollback`, { reason });
    return res.data;
  },

  // Telemetry, Logs & Audit (Phase 8)
  getMetrics: async (id) => {
    const res = await apiClient.get(`/deployments/${id}/metrics`);
    return res.data;
  },

  getLogs: async (id, level = null, source = null, limit = 50) => {
    const params = { limit };
    if (level) params.level = level;
    if (source) params.source = source;
    const res = await apiClient.get(`/deployments/${id}/logs`, { params });
    return res.data;
  },

  getHistory: async (id) => {
    const res = await apiClient.get(`/deployments/${id}/history`);
    return res.data;
  },
};

export default api;
