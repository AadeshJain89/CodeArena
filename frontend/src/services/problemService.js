const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const problemService = {
  /**
   * Fetch all topics
   */
  async getTopics() {
    const response = await fetch(`${API_BASE_URL}/api/v1/topics`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to fetch topics');
    }
    return data;
  },

  /**
   * Fetch list of problems with filtering and pagination
   */
  async getProblems({ topic = '', difficulty = '', page = 1, pageSize = 10 } = {}) {
    const params = new URLSearchParams();
    if (topic) params.append('topic', topic);
    if (difficulty) params.append('difficulty', difficulty);
    params.append('page', page);
    params.append('page_size', pageSize);

    const response = await fetch(`${API_BASE_URL}/api/v1/problems?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to fetch problems');
    }
    return data;
  },

  /**
   * Fetch problem detail by ID
   */
  async getProblemDetail(problemId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/problems/${problemId}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to fetch problem detail');
    }
    return data;
  },
};
