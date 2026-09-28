const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const analyticsService = {
  /**
   * Fetch authenticated user's dashboard analytics
   */
  async getDashboard(token) {
    const response = await fetch(`${API_BASE_URL}/api/v1/analytics/dashboard`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch dashboard analytics');
    }

    return await response.json();
  },
};
