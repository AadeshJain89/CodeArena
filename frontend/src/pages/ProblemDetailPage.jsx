import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { problemService } from '../services/problemService';
import { executionService } from '../services/executionService';
import { useAuth } from '../context/AuthContext';

const DEFAULT_STARTER = {
  python: `# Write your Python 3 solution below
import sys

def solve():
    # Read input from standard input
    # Example: line = sys.stdin.read().split()
    pass

if __name__ == "__main__":
    solve()
`,
  cpp: `// Write your C++ solution below
#include <iostream>
#include <vector>
#include <string>

using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    // Write solution here
    return 0;
}
`,
};

export function ProblemDetailPage() {
  const { id } = useParams();
  const { user, token } = useAuth();

  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Execution state
  const [language, setLanguage] = useState('python');
  const [sourceCode, setSourceCode] = useState('');
  const [executing, setExecuting] = useState(false);
  const [execError, setExecError] = useState(null);
  const [execResult, setExecResult] = useState(null);

  useEffect(() => {
    async function loadProblemDetail() {
      setLoading(true);
      setError(null);
      try {
        const data = await problemService.getProblemDetail(id);
        setProblem(data);
        if (data.starter_code) {
          setSourceCode(data.starter_code);
        } else {
          setSourceCode(DEFAULT_STARTER.python);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadProblemDetail();
  }, [id]);

  const handleLanguageChange = (e) => {
    const newLang = e.target.value;
    setLanguage(newLang);
    if (problem?.starter_code && newLang === 'python') {
      setSourceCode(problem.starter_code);
    } else {
      setSourceCode(DEFAULT_STARTER[newLang] || '');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = e.target.selectionStart;
      const end = e.target.selectionEnd;
      const newValue = sourceCode.substring(0, start) + '    ' + sourceCode.substring(end);
      setSourceCode(newValue);
      setTimeout(() => {
        e.target.selectionStart = e.target.selectionEnd = start + 4;
      }, 0);
    }
  };

  const handleRunCode = async () => {
    if (!token) {
      setExecError('Please log in to execute code.');
      return;
    }
    if (!sourceCode.trim()) {
      setExecError('Source code cannot be empty.');
      return;
    }

    setExecuting(true);
    setExecError(null);
    setExecResult(null);

    try {
      const result = await executionService.executeCode(token, {
        problemId: id,
        language,
        sourceCode,
      });
      setExecResult(result);
    } catch (err) {
      setExecError(err.message);
    } finally {
      setExecuting(false);
    }
  };

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
    <div className="container" style={{ maxWidth: '1300px' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <Link to="/problems" className="text-muted nav-link">
          &laquo; Back to Problems
        </Link>
      </div>

      <div className="editor-split-layout">
        {/* LEFT COLUMN: Problem Details */}
        <div className="problem-detail-card" style={{ height: '100%', overflowY: 'auto' }}>
          <div className="problem-detail-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <h1 className="problem-detail-title">{problem.title}</h1>
              <span className={`diff-badge ${getDifficultyClass(problem.difficulty)}`}>
                {problem.difficulty}
              </span>
            </div>

            <div className="topic-tags" style={{ marginTop: '0.75rem' }}>
              {problem.topics?.map((t) => (
                <span key={t.id} className="topic-pill">
                  {t.name}
                </span>
              ))}
            </div>
          </div>

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

        {/* RIGHT COLUMN: Code Editor & Execution Panel */}
        <div className="editor-panel">
          <div className="editor-toolbar">
            <div className="editor-toolbar-title">
              <span>⚡ Code Editor</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <select
                className="filter-select"
                value={language}
                onChange={handleLanguageChange}
                style={{ padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
              >
                <option value="python">Python 3.12</option>
                <option value="cpp">C++ 17</option>
              </select>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleRunCode}
                disabled={executing}
              >
                {executing ? (
                  <>
                    <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }}></div>
                    Running...
                  </>
                ) : (
                  '▶ Run Code'
                )}
              </button>
            </div>
          </div>

          <textarea
            className="code-textarea"
            value={sourceCode}
            onChange={(e) => setSourceCode(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your solution here..."
            spellCheck="false"
          />

          {/* Execution Error Banner */}
          {execError && (
            <div className="alert alert-error" style={{ marginBottom: 0 }}>
              {execError}
            </div>
          )}

          {/* User Not Logged In Notice */}
          {!user && !execError && (
            <div className="alert alert-info" style={{ marginBottom: 0 }}>
              💡 Please log in or register to execute your code against sandboxed Docker containers.
            </div>
          )}

          {/* Execution Result Area */}
          {execResult && (
            <div className="execution-results-card">
              <div className="execution-results-header">
                <div>
                  <span className={`status-badge ${getStatusBadgeClass(execResult.status)}`}>
                    {execResult.status}
                  </span>
                </div>
                <div className="metrics-row">
                  <div className="metric-item">
                    Tests Passed: <strong>{execResult.passed_tests} / {execResult.total_tests}</strong>
                  </div>
                  <div className="metric-item">
                    Time: <strong>{execResult.execution_time_ms} ms</strong>
                  </div>
                  {execResult.memory_used_mb > 0 && (
                    <div className="metric-item">
                      Memory: <strong>{execResult.memory_used_mb.toFixed(2)} MB</strong>
                    </div>
                  )}
                </div>
              </div>

              {/* Individual Test Results */}
              <div className="test-case-list" style={{ marginTop: '1rem' }}>
                <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-muted)' }}>
                  Test Case Results:
                </h4>
                {execResult.test_results?.map((res) => (
                  <div key={res.test_number} className="test-item-card">
                    <div className="test-item-header">
                      <div className="test-item-title">
                        Test #{res.test_number} {res.is_public ? '(Public)' : '(Hidden)'}
                      </div>
                      <span className={`status-badge ${getStatusBadgeClass(res.status)}`} style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}>
                        {res.status}
                      </span>
                    </div>

                    {res.execution_time_ms > 0 && (
                      <div className="text-muted" style={{ fontSize: '0.8rem', marginBottom: '0.4rem' }}>
                        Execution time: {res.execution_time_ms} ms
                      </div>
                    )}

                    {/* Output for Public Test Cases */}
                    {res.is_public ? (
                      <div style={{ fontSize: '0.82rem', marginTop: '0.5rem' }}>
                        {res.actual_output !== undefined && res.actual_output !== null && (
                          <div style={{ marginBottom: '0.3rem' }}>
                            <span className="text-muted">Your Output:</span>
                            <pre className="code-block" style={{ padding: '0.4rem', marginTop: '0.2rem', fontSize: '0.8rem' }}>
                              {res.actual_output || '(empty)'}
                            </pre>
                          </div>
                        )}
                        {res.expected_output !== undefined && res.expected_output !== null && (
                          <div>
                            <span className="text-muted">Expected Output:</span>
                            <pre className="code-block" style={{ padding: '0.4rem', marginTop: '0.2rem', fontSize: '0.8rem' }}>
                              {res.expected_output}
                            </pre>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-muted" style={{ fontSize: '0.8rem', fontStyle: 'italic', marginTop: '0.4rem' }}>
                        🔒 Input and expected output for hidden test cases are masked for security.
                      </div>
                    )}

                    {/* Error message snippet if available */}
                    {res.error_message && (
                      <div style={{ marginTop: '0.5rem' }}>
                        <span style={{ color: '#ff5252', fontSize: '0.8rem', fontWeight: 600 }}>Error Details:</span>
                        <pre className="code-block" style={{ padding: '0.4rem', marginTop: '0.2rem', fontSize: '0.8rem', color: '#ff5252', borderColor: 'rgba(255,82,82,0.3)' }}>
                          {res.error_message}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

