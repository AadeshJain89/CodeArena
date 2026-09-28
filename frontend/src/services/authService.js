const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const authService = {
  /**
   * Register a new USER account
   */
  async register(username, email, password) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Registration failed');
    }
    return data;
  },

  /**
   * Authenticate user & retrieve JWT token
   */
  async login(credentials, password) {
    const isObject = typeof credentials === 'object' && credentials !== null;
    const loginValue = isObject ? (credentials.login || credentials.username) : credentials;
    const passwordValue = isObject ? credentials.password : password;

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        login: loginValue,
        password: passwordValue,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }
    return data;
  },

  /**
   * Get current authenticated user profile
   */
  async getMe(token) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to fetch user profile');
    }
    return data;
  },

  /**
   * Test protected admin endpoint
   */
  async testAdminEndpoint(token) {
    const response = await fetch(`${API_BASE_URL}/api/v1/admin/test`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Admin access forbidden');
    }
    return data;
  },
};
