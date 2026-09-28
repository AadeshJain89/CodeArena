const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const skillsService = {
  async getSkills(token) {
    const response = await fetch(`${API_BASE_URL}/api/v1/skills`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch skill profiles');
    }

    return await response.json();
  },

  async getTopicSkill(token, topicId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/skills/${topicId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch topic skill profile');
    }

    return await response.json();
  },
};
