const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const diagnosticService = {
  /**
   * Start a new diagnostic assessment
   */
  async startAssessment(token) {
    const response = await fetch(`${API_BASE_URL}/api/v1/diagnostic/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to start diagnostic assessment');
    }
    return data;
  },

  /**
   * Fetch assessment by ID
   */
  async getAssessment(token, assessmentId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/diagnostic/${assessmentId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to fetch diagnostic assessment');
    }
    return data;
  },

  /**
   * Submit diagnostic assessment answers
   */
  async submitAssessment(token, assessmentId, answers) {
    const response = await fetch(`${API_BASE_URL}/api/v1/diagnostic/${assessmentId}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ answers }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to submit diagnostic assessment');
    }
    return data;
  },
};
