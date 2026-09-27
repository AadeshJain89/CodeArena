const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const submissionService = {
  /**
   * Submit code solution for evaluation & persistence
   */
  async createSubmission(token, { problemId, language, sourceCode }) {
    const response = await fetch(`${API_BASE_URL}/api/v1/submissions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        problem_id: parseInt(problemId, 10),
        language,
        source_code: sourceCode,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Code submission failed');
    }
    return data;
  },

  /**
   * Fetch authenticated user's submission history
   */
  async getUserSubmissions(token) {
    const response = await fetch(`${API_BASE_URL}/api/v1/submissions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to fetch submissions history');
    }
    return data;
  },

  /**
   * Fetch details for a specific submission
   */
  async getSubmissionDetail(token, submissionId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/submissions/${submissionId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to fetch submission details');
    }
    return data;
  },
};
