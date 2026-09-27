import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { submissionService } from '../services/submissionService';
import { useAuth } from '../context/AuthContext';

export function SubmissionsPage() {
  const { token } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    async function loadSubmissions() {
      setLoading(true);
      setError(null);
      try {
        const data = await submissionService.getUserSubmissions(token);
        setSubmissions(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    if (token) {
      loadSubmissions();
    }
  }, [token]);

  const handleSelectSubmission = async (subId) => {
    if (selectedSubmission?.id === subId) {
      setSelectedSubmission(null);
      return;
    }
    setLoadingDetail(true);
    try {
      const detail = await submissionService.getSubmissionDetail(token, subId);
      setSelectedSubmission(detail);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoadingDetail(false);
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'PASSED':
        return 'status-passed';
      case 'FAILED':
        return 'status-failed';
      case 'TIME_LIMIT_EXCEEDED':
      case 'MEMORY_LIMIT_EXCEEDED':
      case 'OUTPUT_LIMIT_EXCEEDED':
        return 'status-timeout';
      case 'RUNTIME_ERROR':
      case 'COMPILATION_ERROR':
      default:
        return 'status-error';
    }
  };

  if (loading) {
    return (
      <div className="center-screen">
        <div className="spinner"></div>
        <p className="text-muted" style={{ marginTop: '1rem' }}>Loading submission history...</p>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="page-header">
        <h1 className="page-title">Submission History</h1>
        <p className="page-subtitle">View your past submissions and detailed evaluation metrics.</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {submissions.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
            You haven't submitted any solutions yet.
          </p>
          <Link to="/problems" className="btn btn-primary">
            Explore Problems &rarr;
          </Link>
        </div>
      ) : (
        <div className="table-responsive">
          <table className="problems-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Problem</th>
                <th>Language</th>
                <th>Status</th>
                <th>Tests Passed</th>
                <th>Time (ms)</th>
                <th>Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {submissions.map((sub) => (
                <tr key={sub.id}>
                  <td className="text-muted" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                    #{sub.id}
                  </td>
                  <td>
                    <Link to={`/problems/${sub.problem_id}`} className="problem-link">
                      {sub.problem_title}
                    </Link>
                  </td>
                  <td>
                    <span className="topic-pill" style={{ fontSize: '0.8rem' }}>
                      {sub.language.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${getStatusBadgeClass(sub.status)}`} style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem' }}>
                      {sub.status}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.9rem', fontWeight: 600 }}>
                    {sub.passed_tests} / {sub.total_tests}
                  </td>
                  <td className="text-muted" style={{ fontSize: '0.85rem' }}>
                    {sub.execution_time_ms} ms
                  </td>
                  <td className="text-muted" style={{ fontSize: '0.85rem' }}>
                    {new Date(sub.created_at).toLocaleString()}
                  </td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleSelectSubmission(sub.id)}
                    >
                      {selectedSubmission?.id === sub.id ? 'Close' : 'View Details'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Submission Detail Modal/Panel */}
      {selectedSubmission && (
        <div className="card" style={{ marginTop: '2rem', border: '1px solid var(--accent-cyan)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              Submission #{selectedSubmission.id} - {selectedSubmission.problem_title}
            </h3>
            <span className={`status-badge ${getStatusBadgeClass(selectedSubmission.status)}`}>
              {selectedSubmission.status}
            </span>
          </div>

          <div className="metrics-row" style={{ marginBottom: '1rem' }}>
            <div className="metric-item">
              Language: <strong>{selectedSubmission.language.toUpperCase()}</strong>
            </div>
            <div className="metric-item">
              Tests Passed: <strong>{selectedSubmission.passed_tests} / {selectedSubmission.total_tests}</strong>
            </div>
            <div className="metric-item">
              Time: <strong>{selectedSubmission.execution_time_ms} ms</strong>
            </div>
            <div className="metric-item">
              Submitted: <strong>{new Date(selectedSubmission.created_at).toLocaleString()}</strong>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Submitted Code:</h4>
            <pre className="code-block" style={{ maxHeight: '250px', overflowY: 'auto' }}>
              {selectedSubmission.source_code}
            </pre>
          </div>

          <div>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>Evaluation Results:</h4>
            {selectedSubmission.test_results?.map((res) => (
              <div key={res.id} className="test-item-card" style={{ marginBottom: '0.5rem' }}>
                <div className="test-item-header">
                  <div className="test-item-title">
                    Test #{res.test_case_id} {res.is_hidden ? '(Hidden)' : '(Public)'}
                  </div>
                  <span className={`status-badge ${getStatusBadgeClass(res.status)}`} style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem' }}>
                    {res.status}
                  </span>
                </div>
                {res.is_hidden ? (
                  <p className="text-muted" style={{ fontSize: '0.8rem', fontStyle: 'italic', margin: 0 }}>
                    🔒 Hidden test inputs and outputs are masked for security.
                  </p>
                ) : (
                  <div style={{ fontSize: '0.82rem' }}>
                    {res.actual_output !== null && (
                      <div><span className="text-muted">Actual Output:</span> <code>{res.actual_output || '(empty)'}</code></div>
                    )}
                    {res.expected_output !== null && (
                      <div><span className="text-muted">Expected Output:</span> <code>{res.expected_output}</code></div>
                    )}
                  </div>
                )}
                {res.error_message && (
                  <pre className="code-block" style={{ color: '#ff5252', marginTop: '0.4rem', fontSize: '0.8rem' }}>
                    {res.error_message}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
