const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const executionService = {
  /**
   * Execute code against problem test cases
   */
  async executeCode(token, { problemId, language, sourceCode }) {
    const response = await fetch(`${API_BASE_URL}/api/v1/execute`, {
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
      throw new Error(data.detail || 'Code execution request failed');
    }
    return data;
  },
};
