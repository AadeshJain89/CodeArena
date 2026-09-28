const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const recommendationService = {
  /**
   * Get authenticated user's top 5 recommendations
   */
  async getRecommendations(token) {
    const response = await fetch(`${API_BASE_URL}/api/v1/recommendations`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch recommendations');
    }

    return await response.json();
  },
};
