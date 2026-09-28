const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const gamificationService = {
  /**
   * Fetch authenticated user's gamification profile
   */
  async getGamification(token) {
    const response = await fetch(`${API_BASE_URL}/api/v1/gamification`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch gamification data');
    }

    return await response.json();
  },
};
