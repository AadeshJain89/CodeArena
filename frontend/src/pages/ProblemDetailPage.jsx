import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { problemService } from '../services/problemService';

export function ProblemDetailPage() {
  const { id } = useParams();
  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadProblemDetail() {
      setLoading(true);
      setError(null);
      try {
        const data = await problemService.getProblemDetail(id);
        setProblem(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadProblemDetail();
  }, [id]);

  const getDifficultyClass = (diff) => {
    switch (diff) {
      case 'EASY':
        return 'diff-easy';
      case 'MEDIUM':
        return 'diff-medium';
      case 'HARD':
        return 'diff-hard';
      default:
        return '';
    }
  };

  if (loading) {
    return (
      <div className="center-screen">
        <div className="spinner"></div>
        <p className="text-muted" style={{ marginTop: '1rem' }}>Loading problem details...</p>
      </div>
    );
  }

  if (error || !problem) {
    return (
      <div className="container">
        <div className="alert alert-error">
          {error || 'Problem not found'}
        </div>
        <Link to="/problems" className="btn btn-secondary">
          &laquo; Back to Problems
        </Link>
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <Link to="/problems" className="text-muted nav-link">
          &laquo; Back to Problems
        </Link>
      </div>

      <div className="problem-detail-card">
        {/* Header */}
        <div className="problem-detail-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <h1 className="problem-detail-title">{problem.title}</h1>
            <span className={`diff-badge ${getDifficultyClass(problem.difficulty)}`}>
              {problem.difficulty}
            </span>
          </div>

          <div className="topic-tags" style={{ marginTop: '0.75rem' }}>
            {problem.topics.map((t) => (
              <span key={t.id} className="topic-pill">
                {t.name}
              </span>
            ))}
          </div>
        </div>

        {/* Problem Body */}
        <div className="problem-section">
          <h3 className="section-title">Description</h3>
          <p className="problem-text">{problem.description}</p>
        </div>

        {problem.input_format && (
          <div className="problem-section">
            <h3 className="section-title">Input Format</h3>
            <p className="problem-text">{problem.input_format}</p>
          </div>
        )}

        {problem.output_format && (
          <div className="problem-section">
            <h3 className="section-title">Output Format</h3>
            <p className="problem-text">{problem.output_format}</p>
          </div>
        )}

        {problem.constraints && (
          <div className="problem-section">
            <h3 className="section-title">Constraints</h3>
            <pre className="code-block">{problem.constraints}</pre>
          </div>
        )}

        {/* Examples / Public Test Cases */}
        {problem.examples && problem.examples.length > 0 && (
          <div className="problem-section">
            <h3 className="section-title">Examples</h3>
            {problem.examples.map((ex, idx) => (
              <div key={idx} className="example-box">
                <div className="example-field">
                  <span className="example-label">Input:</span>
                  <pre className="code-block">{ex.input}</pre>
                </div>
                <div className="example-field">
                  <span className="example-label">Output:</span>
                  <pre className="code-block">{ex.output}</pre>
                </div>
                {ex.explanation && (
                  <div className="example-field">
                    <span className="example-label">Explanation:</span>
                    <p className="text-muted" style={{ fontSize: '0.9rem' }}>{ex.explanation}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Public Test Cases Section */}
        {problem.public_test_cases && problem.public_test_cases.length > 0 && (
          <div className="problem-section">
            <h3 className="section-title">Public Test Cases</h3>
            {problem.public_test_cases.map((tc, idx) => (
              <div key={tc.test_case_id} className="example-box">
                <span className="text-muted" style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                  Test Case #{idx + 1}
                </span>
                <div className="example-field" style={{ marginTop: '0.5rem' }}>
                  <span className="example-label">Input:</span>
                  <pre className="code-block">{tc.input}</pre>
                </div>
                <div className="example-field">
                  <span className="example-label">Expected Output:</span>
                  <pre className="code-block">{tc.expected_output}</pre>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
