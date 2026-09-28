const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const adminService = {
  async getProblems(token, params = {}) {
    const query = new URLSearchParams();
    if (params.topic_id) query.append('topic_id', params.topic_id);
    if (params.difficulty) query.append('difficulty', params.difficulty);
    if (params.search) query.append('search', params.search);
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size || 10);

    const res = await fetch(`${API_BASE_URL}/api/v1/admin/problems?${query.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch admin problems');
    }
    return await res.json();
  },

  async getProblemDetail(token, problemId) {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/problems/${problemId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch admin problem detail');
    }
    return await res.json();
  },

  async createProblem(token, data) {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/problems`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create problem');
    }
    return await res.json();
  },

  async updateProblem(token, problemId, data) {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/problems/${problemId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update problem');
    }
    return await res.json();
  },

  async deleteProblem(token, problemId) {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/problems/${problemId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete problem');
    }
    return await res.json();
  },

  async getTestCases(token, problemId) {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/problems/${problemId}/test-cases`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch test cases');
    }
    return await res.json();
  },

  async createTestCase(token, problemId, data) {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/problems/${problemId}/test-cases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create test case');
    }
    return await res.json();
  },

  async updateTestCase(token, testCaseId, data) {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/test-cases/${testCaseId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update test case');
    }
    return await res.json();
  },

  async deleteTestCase(token, testCaseId) {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/test-cases/${testCaseId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete test case');
    }
    return await res.json();
  },
};
