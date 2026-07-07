/**
 * REST API Client with JWT Authorization & Central Error Handling
 */
const API_BASE_URL = window.location.origin.includes(':5000') 
  ? window.location.origin 
  : 'http://localhost:5000';

class ApiClient {
  static getToken() {
    return localStorage.getItem('turbine_token');
  }

  static setToken(token) {
    localStorage.setItem('turbine_token', token);
  }

  static clearToken() {
    localStorage.removeItem('turbine_token');
    localStorage.removeItem('turbine_user');
  }

  static getUser() {
    try {
      return JSON.parse(localStorage.getItem('turbine_user'));
    } catch {
      return null;
    }
  }

  static setUser(user) {
    localStorage.setItem('turbine_user', JSON.stringify(user));
  }

  static async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = options.headers || {};

    const token = ApiClient.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (response.status === 401 && !endpoint.includes('/api/auth/login')) {
        // Token expired or invalid
        ApiClient.clearToken();
        window.location.href = 'login.html';
        return null;
      }

      // Check if CSV/blob response
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('text/csv')) {
        return await response.text();
      }

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.error?.message || `HTTP Error ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  }

  // Auth endpoints
  static login(username, password) {
    return ApiClient.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
  }

  static getMe() {
    return ApiClient.request('/api/auth/me');
  }

  // Dashboard & Health
  static getHealth() {
    return ApiClient.request('/api/health');
  }

  static getDashboard() {
    return ApiClient.request('/api/dashboard');
  }

  // Units
  static getUnits(includeInactive = false) {
    return ApiClient.request(`/api/units?include_inactive=${includeInactive}`);
  }

  static getUnit(unitId) {
    return ApiClient.request(`/api/units/${unitId}`);
  }

  static createUnit(payload) {
    return ApiClient.request('/api/units', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  static updateUnit(unitId, payload) {
    return ApiClient.request(`/api/units/${unitId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  }

  static deleteUnit(unitId) {
    return ApiClient.request(`/api/units/${unitId}`, {
      method: 'DELETE'
    });
  }

  // Parameters
  static getUnitParameters(unitId) {
    return ApiClient.request(`/api/units/${unitId}/parameters`);
  }

  static createParameter(unitId, payload) {
    return ApiClient.request(`/api/units/${unitId}/parameters`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  static updateParameter(parameterId, payload) {
    return ApiClient.request(`/api/parameters/${parameterId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  }

  // Readings
  static addReading(unitId, payload) {
    return ApiClient.request(`/api/units/${unitId}/readings`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  static getCurrentReadings(unitId) {
    return ApiClient.request(`/api/units/${unitId}/readings`);
  }

  static getParameterHistory(unitId, parameterId, limit = 100) {
    return ApiClient.request(`/api/units/${unitId}/parameters/${parameterId}/history?limit=${limit}`);
  }

  // Predictions
  static predictParameter(unitId, parameterId, inputs = null) {
    const options = { method: 'POST' };
    if (inputs && Array.isArray(inputs)) {
      options.body = JSON.stringify({ inputs });
    }
    return ApiClient.request(`/api/units/${unitId}/parameters/${parameterId}/predict`, options);
  }

  static directForecast(payload) {
    return ApiClient.request('/api/forecast', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  static getSampleForecastInputs() {
    return ApiClient.request('/api/forecast/sample');
  }

  static predictUnit(unitId) {
    return ApiClient.request(`/api/units/${unitId}/predict`, {
      method: 'POST'
    });
  }

  static getParameterPredictions(unitId, parameterId) {
    return ApiClient.request(`/api/units/${unitId}/parameters/${parameterId}/predictions`);
  }

  // Alerts
  static getAlerts(params = {}) {
    const query = new URLSearchParams(params).toString();
    return ApiClient.request(`/api/alerts?${query}`);
  }

  static acknowledgeAlert(alertId) {
    return ApiClient.request(`/api/alerts/${alertId}/acknowledge`, { method: 'PUT' });
  }

  static resolveAlert(alertId) {
    return ApiClient.request(`/api/alerts/${alertId}/resolve`, { method: 'PUT' });
  }

  // Reports
  static getUnitReport(unitId) {
    return ApiClient.request(`/api/reports/units/${unitId}`);
  }

  static exportCsv(unitId, paramId = null) {
    const url = paramId 
      ? `/api/reports/units/${unitId}/export/csv?parameter_id=${paramId}` 
      : `/api/reports/units/${unitId}/export/csv`;
    return ApiClient.request(url);
  }

  // Simulation
  static triggerSimulation(unitId, count = 60, trend = 'normal') {
    return ApiClient.request(`/api/system/simulate/${unitId}`, {
      method: 'POST',
      body: JSON.stringify({ count, trend })
    });
  }

  // Models
  static getModels() {
    return ApiClient.request('/api/models');
  }

  static trainModel(parameterId) {
    return ApiClient.request(`/api/models/train/${parameterId}`, { method: 'POST' });
  }

  // Users
  static getUsers() {
    return ApiClient.request('/api/users');
  }

  static createUser(payload) {
    return ApiClient.request('/api/users', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
}

window.ApiClient = ApiClient;
