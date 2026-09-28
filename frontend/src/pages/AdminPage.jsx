import { useState, useEffect } from 'react';
import { adminService } from '../services/adminService';
import { problemService } from '../services/problemService';
import { useAuth } from '../context/AuthContext';

export function AdminPage() {
  const { token, user } = useAuth();

  // State
  const [topics, setTopics] = useState([]);
  const [problems, setProblems] = useState([]);
  const [totalProblems, setTotalProblems] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchFilter, setSearchFilter] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('');
  const [topicFilter, setTopicFilter] = useState('');

  // Selected Problem & Test Cases
  const [selectedProblem, setSelectedProblem] = useState(null);
  const [testCases, setTestCases] = useState([]);
  const [testCasesLoading, setTestCasesLoading] = useState(false);

  // Modals / Forms
  const [showProblemModal, setShowProblemModal] = useState(false);
  const [editingProblem, setEditingProblem] = useState(null);
  const [problemFormData, setProblemFormData] = useState({
    title: '',
    slug: '',
    description: '',
    difficulty: 'EASY',
    constraints: '',
    input_format: '',
    output_format: '',
    topic_ids: [],
  });

  const [showTestCaseModal, setShowTestCaseModal] = useState(false);
  const [editingTestCase, setEditingTestCase] = useState(null);
  const [testCaseFormData, setTestCaseFormData] = useState({
    input: '',
    expected_output: '',
    is_hidden: false,
    time_limit_override: '',
    memory_limit_override: '',
  });

  const [formError, setFormError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Fetch topics once
  useEffect(() => {
    async function loadTopics() {
      try {
        const data = await problemService.getTopics();
        setTopics(data || []);
      } catch (err) {
        console.error('Failed to load topics:', err);
      }
    }
    loadTopics();
  }, []);

  // Fetch problems when filters / page change
  const fetchProblems = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await adminService.getProblems(token, {
        page,
        page_size: 10,
        search: searchFilter,
        difficulty: difficultyFilter,
        topic_id: topicFilter,
      });
      setProblems(res.items || []);
      setTotalProblems(res.total || 0);
      setTotalPages(res.total_pages || 1);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProblems();
  }, [token, page, difficultyFilter, topicFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchProblems();
  };

  // Select problem & load test cases
  const handleSelectProblem = async (prob) => {
    try {
      setTestCasesLoading(true);
      const detail = await adminService.getProblemDetail(token, prob.id);
      setSelectedProblem(detail);
      setTestCases(detail.test_cases || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setTestCasesLoading(false);
    }
  };

  // Open Create Problem Modal
  const handleOpenCreateProblem = () => {
    setEditingProblem(null);
    setProblemFormData({
      title: '',
      slug: '',
      description: '',
      difficulty: 'EASY',
      constraints: '',
      input_format: '',
      output_format: '',
      topic_ids: [],
    });
    setFormError(null);
    setShowProblemModal(true);
  };

  // Open Edit Problem Modal
  const handleOpenEditProblem = async (prob) => {
    try {
      const detail = await adminService.getProblemDetail(token, prob.id);
      setEditingProblem(detail);
      setProblemFormData({
        title: detail.title || '',
        slug: detail.slug || '',
        description: detail.description || '',
        difficulty: detail.difficulty || 'EASY',
        constraints: detail.constraints || '',
        input_format: detail.input_format || '',
        output_format: detail.output_format || '',
        topic_ids: detail.topics ? detail.topics.map((t) => t.id) : [],
      });
      setFormError(null);
      setShowProblemModal(true);
    } catch (err) {
      setError(err.message);
    }
  };

  // Save Problem (Create or Update)
  const handleSaveProblem = async (e) => {
    e.preventDefault();
    setFormError(null);
    try {
      const payload = {
        title: problemFormData.title,
        slug: problemFormData.slug || undefined,
        description: problemFormData.description,
        difficulty: problemFormData.difficulty,
        constraints: problemFormData.constraints || undefined,
        input_format: problemFormData.input_format || undefined,
        output_format: problemFormData.output_format || undefined,
        topic_ids: problemFormData.topic_ids,
      };

      if (editingProblem) {
        await adminService.updateProblem(token, editingProblem.id, payload);
        setActionSuccess(`Problem #${editingProblem.id} updated successfully!`);
      } else {
        await adminService.createProblem(token, payload);
        setActionSuccess('New problem created successfully!');
      }

      setShowProblemModal(false);
      fetchProblems();
      if (selectedProblem && editingProblem && selectedProblem.id === editingProblem.id) {
        handleSelectProblem(editingProblem);
      }
    } catch (err) {
      setFormError(err.message);
    }
  };

  // Delete Problem
  const handleDeleteProblem = async (problemId) => {
    if (!window.confirm(`Are you sure you want to delete problem #${problemId}?`)) return;
    try {
      await adminService.deleteProblem(token, problemId);
      setActionSuccess(`Problem #${problemId} deleted successfully!`);
      if (selectedProblem?.id === problemId) {
        setSelectedProblem(null);
        setTestCases([]);
      }
      fetchProblems();
    } catch (err) {
      setError(err.message);
    }
  };

  // Open Create Test Case Modal
  const handleOpenCreateTestCase = () => {
    setEditingTestCase(null);
    setTestCaseFormData({
      input: '',
      expected_output: '',
      is_hidden: false,
      time_limit_override: '',
      memory_limit_override: '',
    });
    setFormError(null);
    setShowTestCaseModal(true);
  };

  // Open Edit Test Case Modal
  const handleOpenEditTestCase = (tc) => {
    setEditingTestCase(tc);
    setTestCaseFormData({
      input: tc.input || '',
      expected_output: tc.expected_output || '',
      is_hidden: tc.is_hidden || false,
      time_limit_override: tc.time_limit_override != null ? tc.time_limit_override : '',
      memory_limit_override: tc.memory_limit_override != null ? tc.memory_limit_override : '',
    });
    setFormError(null);
    setShowTestCaseModal(true);
  };

  // Save Test Case
  const handleSaveTestCase = async (e) => {
    e.preventDefault();
    if (!selectedProblem) return;
    setFormError(null);
    try {
      const payload = {
        input: testCaseFormData.input,
        expected_output: testCaseFormData.expected_output,
        is_hidden: testCaseFormData.is_hidden,
        time_limit_override: testCaseFormData.time_limit_override ? parseFloat(testCaseFormData.time_limit_override) : undefined,
        memory_limit_override: testCaseFormData.memory_limit_override ? parseInt(testCaseFormData.memory_limit_override, 10) : undefined,
      };

      if (editingTestCase) {
        await adminService.updateTestCase(token, editingTestCase.test_case_id, payload);
        setActionSuccess(`Test case #${editingTestCase.test_case_id} updated successfully!`);
      } else {
        await adminService.createTestCase(token, selectedProblem.id, payload);
        setActionSuccess('New test case created successfully!');
      }

      setShowTestCaseModal(false);
      handleSelectProblem(selectedProblem);
    } catch (err) {
      setFormError(err.message);
    }
  };

  // Delete Test Case
  const handleDeleteTestCase = async (testCaseId) => {
    if (!window.confirm(`Delete test case #${testCaseId}?`)) return;
    try {
      await adminService.deleteTestCase(token, testCaseId);
      setActionSuccess(`Test case #${testCaseId} deleted!`);
      if (selectedProblem) {
        handleSelectProblem(selectedProblem);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  if (user?.role !== 'ADMIN') {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <div style={{ background: 'rgba(255, 77, 77, 0.1)', border: '1px solid rgba(255, 77, 77, 0.3)', padding: '2rem', borderRadius: 'var(--radius-md)', color: '#ff4d4d', maxWidth: '500px', margin: '0 auto' }}>
          <h2 style={{ marginTop: 0 }}>Access Denied</h2>
          <p>Operation not permitted. Required role: ADMIN.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ maxWidth: '1200px' }}>
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <h1 className="page-title">Admin Problem Management</h1>
          <p className="page-subtitle">
            Manage practice challenges, topic associations, and public/hidden test cases.
          </p>
        </div>
        <button onClick={handleOpenCreateProblem} className="btn btn-primary">
          + Create New Problem
        </button>
      </div>

      {actionSuccess && (
        <div style={{ background: 'rgba(0, 242, 254, 0.15)', border: '1px solid rgba(0, 242, 254, 0.4)', padding: '0.8rem 1.2rem', borderRadius: 'var(--radius-sm)', color: 'var(--accent-cyan)', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between' }}>
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', cursor: 'pointer' }}>✕</button>
        </div>
      )}

      {error && (
        <div style={{ background: 'rgba(255, 77, 77, 0.15)', border: '1px solid rgba(255, 77, 77, 0.4)', padding: '0.8rem 1.2rem', borderRadius: 'var(--radius-sm)', color: '#ff4d4d', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between' }}>
          <span>Error: {error}</span>
          <button onClick={() => setError(null)} style={{ background: 'none', border: 'none', color: '#ff4d4d', cursor: 'pointer' }}>✕</button>
        </div>
      )}

      {/* Filter Toolbar */}
      <form onSubmit={handleSearchSubmit} className="card" style={{ padding: '1rem 1.5rem', marginBottom: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Search by title or slug..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          style={{ flex: '1 1 200px', padding: '0.6rem 1rem', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)', color: '#ffffff', borderRadius: 'var(--radius-sm)' }}
        />

        <select
          value={difficultyFilter}
          onChange={(e) => { setDifficultyFilter(e.target.value); setPage(1); }}
          style={{ padding: '0.6rem 1rem', background: 'rgba(18, 24, 36, 0.9)', border: '1px solid var(--border-color)', color: '#ffffff', borderRadius: 'var(--radius-sm)' }}
        >
          <option value="">All Difficulties</option>
          <option value="EASY">EASY</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="HARD">HARD</option>
        </select>

        <select
          value={topicFilter}
          onChange={(e) => { setTopicFilter(e.target.value); setPage(1); }}
          style={{ padding: '0.6rem 1rem', background: 'rgba(18, 24, 36, 0.9)', border: '1px solid var(--border-color)', color: '#ffffff', borderRadius: 'var(--radius-sm)' }}
        >
          <option value="">All Topics</option>
          {topics.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>

        <button type="submit" className="btn btn-secondary btn-sm">
          Filter
        </button>
      </form>

      {/* Split Layout: Problems List (Left) & Test Cases Detail (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '2rem' }}>
        {/* Problems Column */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.2rem', color: '#ffffff', marginTop: 0, marginBottom: '1rem' }}>
            Problems ({totalProblems})
          </h3>

          {loading ? (
            <p style={{ color: 'var(--text-muted)' }}>Loading problems...</p>
          ) : problems.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '0.6rem' }}>ID</th>
                    <th style={{ padding: '0.6rem' }}>Title</th>
                    <th style={{ padding: '0.6rem' }}>Difficulty</th>
                    <th style={{ padding: '0.6rem' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {problems.map((prob) => {
                    const isSelected = selectedProblem?.id === prob.id;
                    return (
                      <tr
                        key={prob.id}
                        style={{
                          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                          background: isSelected ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                        }}
                      >
                        <td style={{ padding: '0.6rem', color: 'var(--text-muted)' }}>#{prob.id}</td>
                        <td style={{ padding: '0.6rem', fontWeight: '600' }}>
                          <span
                            onClick={() => handleSelectProblem(prob)}
                            style={{ cursor: 'pointer', color: isSelected ? 'var(--accent-cyan)' : '#ffffff' }}
                          >
                            {prob.title}
                          </span>
                        </td>
                        <td style={{ padding: '0.6rem' }}>
                          <span
                            className={`status-indicator ${
                              prob.difficulty === 'EASY'
                                ? 'status-passed'
                                : prob.difficulty === 'MEDIUM'
                                ? 'status-timeout'
                                : 'status-failed'
                            }`}
                            style={{ fontSize: '0.75rem' }}
                          >
                            {prob.difficulty}
                          </span>
                        </td>
                        <td style={{ padding: '0.6rem', display: 'flex', gap: '0.4rem' }}>
                          <button
                            onClick={() => handleSelectProblem(prob)}
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                          >
                            Test Cases
                          </button>
                          <button
                            onClick={() => handleOpenEditProblem(prob)}
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteProblem(prob.id)}
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem', color: '#ff4d4d', borderColor: 'rgba(255,77,77,0.3)' }}
                          >
                            Del
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Pagination */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem' }}>
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="btn btn-secondary btn-sm"
                >
                  &larr; Previous
                </button>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Page {page} of {totalPages}
                </span>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="btn btn-secondary btn-sm"
                >
                  Next &rarr;
                </button>
              </div>
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No problems found.</p>
          )}
        </div>

        {/* Selected Problem & Test Cases Column */}
        <div className="card" style={{ padding: '1.5rem' }}>
          {selectedProblem ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.2rem', color: '#ffffff', margin: 0 }}>
                    #{selectedProblem.id}: {selectedProblem.title}
                  </h3>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Topics: {selectedProblem.topics?.map((t) => t.name).join(', ') || 'None'}
                  </div>
                </div>
                <button onClick={handleOpenCreateTestCase} className="btn btn-primary btn-sm">
                  + Add Test Case
                </button>
              </div>

              {testCasesLoading ? (
                <p style={{ color: 'var(--text-muted)' }}>Loading test cases...</p>
              ) : testCases.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {testCases.map((tc) => (
                    <div
                      key={tc.test_case_id}
                      style={{
                        padding: '0.85rem',
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid var(--border-color)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                        <span style={{ fontWeight: '700', color: 'var(--accent-cyan)', fontSize: '0.85rem' }}>
                          Test Case #{tc.test_case_id}
                        </span>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <span className={`status-indicator ${tc.is_hidden ? 'status-pending' : 'status-passed'}`} style={{ fontSize: '0.7rem' }}>
                            {tc.is_hidden ? '🔒 Hidden' : '🌐 Public'}
                          </span>
                          <button onClick={() => handleOpenEditTestCase(tc)} className="btn btn-secondary btn-sm" style={{ padding: '0.15rem 0.4rem', fontSize: '0.7rem' }}>
                            Edit
                          </button>
                          <button onClick={() => handleDeleteTestCase(tc.test_case_id)} className="btn btn-secondary btn-sm" style={{ padding: '0.15rem 0.4rem', fontSize: '0.7rem', color: '#ff4d4d' }}>
                            Del
                          </button>
                        </div>
                      </div>

                      <div style={{ fontSize: '0.8rem', fontFamily: 'monospace', color: '#ffffff', background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px', marginBottom: '0.4rem' }}>
                        <div><strong>Input:</strong> {tc.input || '(empty)'}</div>
                        <div><strong>Expected:</strong> {tc.expected_output || '(empty)'}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  No test cases for this problem yet. Click "+ Add Test Case" above.
                </p>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
              <p>👈 Select a problem from the list on the left to view and manage its test cases.</p>
            </div>
          )}
        </div>
      </div>

      {/* Problem Modal */}
      {showProblemModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '1rem' }}>
          <div className="card" style={{ maxWidth: '650px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.3rem', color: '#ffffff', marginTop: 0 }}>
              {editingProblem ? `Edit Problem #${editingProblem.id}` : 'Create New Problem'}
            </h3>

            {formError && (
              <div style={{ color: '#ff4d4d', background: 'rgba(255,77,77,0.1)', padding: '0.6rem 1rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {formError}
              </div>
            )}

            <form onSubmit={handleSaveProblem} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Title *</label>
                <input
                  type="text"
                  required
                  value={problemFormData.title}
                  onChange={(e) => setProblemFormData({ ...problemFormData, title: e.target.value })}
                  style={{ width: '100%', padding: '0.6rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '4px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Slug (optional)</label>
                <input
                  type="text"
                  value={problemFormData.slug}
                  onChange={(e) => setProblemFormData({ ...problemFormData, slug: e.target.value })}
                  style={{ width: '100%', padding: '0.6rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '4px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Difficulty *</label>
                <select
                  value={problemFormData.difficulty}
                  onChange={(e) => setProblemFormData({ ...problemFormData, difficulty: e.target.value })}
                  style={{ width: '100%', padding: '0.6rem', background: 'rgba(18,24,36,0.9)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '4px' }}
                >
                  <option value="EASY">EASY</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HARD">HARD</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Description / Problem Statement *</label>
                <textarea
                  required
                  rows={4}
                  value={problemFormData.description}
                  onChange={(e) => setProblemFormData({ ...problemFormData, description: e.target.value })}
                  style={{ width: '100%', padding: '0.6rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '4px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Topics</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0.5rem', maxHeight: '150px', overflowY: 'auto', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '4px' }}>
                  {topics.map((t) => {
                    const checked = problemFormData.topic_ids.includes(t.id);
                    return (
                      <label key={t.id} style={{ fontSize: '0.8rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setProblemFormData({ ...problemFormData, topic_ids: [...problemFormData.topic_ids, t.id] });
                            } else {
                              setProblemFormData({ ...problemFormData, topic_ids: problemFormData.topic_ids.filter((id) => id !== t.id) });
                            }
                          }}
                        />
                        {t.name}
                      </label>
                    );
                  })}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                <button type="button" onClick={() => setShowProblemModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Problem
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Test Case Modal */}
      {showTestCaseModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '1rem' }}>
          <div className="card" style={{ maxWidth: '550px', width: '100%', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.3rem', color: '#ffffff', marginTop: 0 }}>
              {editingTestCase ? `Edit Test Case #${editingTestCase.test_case_id}` : 'Create Test Case'}
            </h3>

            {formError && (
              <div style={{ color: '#ff4d4d', background: 'rgba(255,77,77,0.1)', padding: '0.6rem 1rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {formError}
              </div>
            )}

            <form onSubmit={handleSaveTestCase} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Input *</label>
                <textarea
                  required
                  rows={3}
                  value={testCaseFormData.input}
                  onChange={(e) => setTestCaseFormData({ ...testCaseFormData, input: e.target.value })}
                  style={{ width: '100%', padding: '0.6rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '4px', fontFamily: 'monospace' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Expected Output *</label>
                <textarea
                  required
                  rows={3}
                  value={testCaseFormData.expected_output}
                  onChange={(e) => setTestCaseFormData({ ...testCaseFormData, expected_output: e.target.value })}
                  style={{ width: '100%', padding: '0.6rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '4px', fontFamily: 'monospace' }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="checkbox"
                  id="is_hidden_cb"
                  checked={testCaseFormData.is_hidden}
                  onChange={(e) => setTestCaseFormData({ ...testCaseFormData, is_hidden: e.target.checked })}
                />
                <label htmlFor="is_hidden_cb" style={{ fontSize: '0.85rem', color: '#fff', cursor: 'pointer' }}>
                  Is Hidden Test Case? (Hidden test cases are not shown to normal users)
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                <button type="button" onClick={() => setShowTestCaseModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Test Case
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
