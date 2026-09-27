import { useState } from 'react';
import { Link } from 'react-router-dom';
import { diagnosticService } from '../services/diagnosticService';
import { useAuth } from '../context/AuthContext';

export function DiagnosticPage() {
  const { token } = useAuth();
  const [assessment, setAssessment] = useState(null);
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleStartAssessment = async () => {
    setLoading(true);
    setError(null);
    setSelectedAnswers({});
    setCurrentQuestionIdx(0);
    try {
      const data = await diagnosticService.startAssessment(token);
      setAssessment(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOptionSelect = (problemId, option) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [problemId]: option,
    }));
  };

  const handleSubmitAssessment = async () => {
    if (!assessment) return;
    setSubmitting(true);
    setError(null);

    const answersList = assessment.questions.map((q) => ({
      problem_id: q.problem_id,
      selected_answer: selectedAnswers[q.problem_id] || '',
    }));

    try {
      const result = await diagnosticService.submitAssessment(
        token,
        assessment.assessment_id,
        answersList
      );
      setAssessment(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // 1. Initial State (Pre-start Screen)
  if (!assessment) {
    return (
      <div className="container" style={{ maxWidth: '800px' }}>
        <div className="page-header" style={{ textAlign: 'center' }}>
          <h1 className="page-title">Diagnostic Assessment</h1>
          <p className="page-subtitle">
            Evaluate your core computer science and algorithm knowledge across 10 essential topics.
          </p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="card" style={{ padding: '2.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🧠</div>
          <h3 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.75rem' }}>
            Ready to test your knowledge?
          </h3>
          <p className="text-muted" style={{ maxWidth: '550px', margin: '0 auto 2rem auto', lineHeight: 1.6 }}>
            The diagnostic assessment presents 10 multiple-choice questions covering Arrays, Strings, Hashing, Two Pointers, Sliding Window, Stack & Queue, Linked List, Binary Search, Trees, and Graphs.
          </p>

          <button
            className="btn btn-primary"
            onClick={handleStartAssessment}
            disabled={loading}
            style={{ padding: '0.85rem 2rem', fontSize: '1rem' }}
          >
            {loading ? (
              <>
                <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div>
                Preparing Assessment...
              </>
            ) : (
              '⚡ Start Assessment Now'
            )}
          </button>
        </div>
      </div>
    );
  }

  // 2. Assessment In-Progress Screen
  if (assessment.status === 'IN_PROGRESS') {
    const questions = assessment.questions || [];
    const currentQ = questions[currentQuestionIdx];
    const totalQ = questions.length;
    const answeredCount = Object.keys(selectedAnswers).filter((k) => selectedAnswers[k]).length;
    const progressPercent = totalQ > 0 ? Math.round(((currentQuestionIdx + 1) / totalQ) * 100) : 0;

    return (
      <div className="container" style={{ maxWidth: '850px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <span className="text-muted" style={{ fontSize: '0.9rem', fontWeight: 600 }}>
            Question {currentQuestionIdx + 1} of {totalQ}
          </span>
          <span className="topic-pill" style={{ fontSize: '0.85rem' }}>
            {currentQ?.topic_name || 'General'}
          </span>
        </div>

        {/* Progress Bar */}
        <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', marginBottom: '2rem', overflow: 'hidden' }}>
          <div
            style={{
              width: `${progressPercent}%`,
              height: '100%',
              background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-blue))',
              transition: 'width 0.3s ease',
            }}
          />
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {/* Question Card */}
        {currentQ && (
          <div className="card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem' }}>
              {currentQ.title}
            </h2>
            <p className="problem-text" style={{ fontSize: '0.95rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>
              {currentQ.description}
            </p>

            {/* MCQ Options */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {currentQ.options?.map((opt, idx) => {
                const isSelected = selectedAnswers[currentQ.problem_id] === opt;
                return (
                  <label
                    key={idx}
                    className="example-box"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.85rem',
                      padding: '0.85rem 1.1rem',
                      cursor: 'pointer',
                      border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--border-color)',
                      background: isSelected ? 'rgba(0, 242, 254, 0.1)' : 'rgba(18, 24, 36, 0.6)',
                      transition: 'all 0.2s ease',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <input
                      type="radio"
                      name={`question_${currentQ.problem_id}`}
                      checked={isSelected}
                      onChange={() => handleOptionSelect(currentQ.problem_id, opt)}
                      style={{ accentColor: 'var(--accent-cyan)', width: '16px', height: '16px' }}
                    />
                    <span style={{ fontSize: '0.92rem', color: isSelected ? 'var(--text-main)' : 'var(--text-muted)' }}>
                      {opt}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>
        )}

        {/* Navigation Toolbar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentQuestionIdx((prev) => Math.max(0, prev - 1))}
            disabled={currentQuestionIdx === 0}
          >
            &laquo; Previous
          </button>

          <span className="text-muted" style={{ fontSize: '0.85rem' }}>
            Answered: <strong>{answeredCount} / {totalQ}</strong>
          </span>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            {currentQuestionIdx < totalQ - 1 ? (
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setCurrentQuestionIdx((prev) => Math.min(totalQ - 1, prev + 1))}
              >
                Next &raquo;
              </button>
            ) : null}

            <button
              className="btn btn-primary btn-sm"
              onClick={handleSubmitAssessment}
              disabled={submitting}
            >
              {submitting ? (
                <>
                  <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }}></div>
                  Evaluating...
                </>
              ) : (
                '🚀 Submit Assessment'
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 3. Assessment Results Screen (Status COMPLETED)
  return (
    <div className="container" style={{ maxWidth: '900px' }}>
      <div className="page-header" style={{ textAlign: 'center' }}>
        <h1 className="page-title">Diagnostic Results</h1>
        <p className="page-subtitle">Your diagnostic evaluation metrics and topic mastery summary.</p>
      </div>

      {/* Overview Score Card */}
      <div className="card" style={{ textAlign: 'center', padding: '2.5rem', marginBottom: '2rem' }}>
        <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-cyan)', marginBottom: '0.5rem' }}>
          {assessment.score}%
        </div>
        <p className="text-muted" style={{ fontSize: '1rem', marginBottom: '1.5rem' }}>
          Overall Diagnostic Accuracy
        </p>

        <div className="metrics-row" style={{ justifyContent: 'center', gap: '2.5rem' }}>
          <div className="metric-item">
            Correct Answers: <strong>{assessment.correct_answers} / {assessment.total_questions}</strong>
          </div>
          <div className="metric-item">
            Questions Answered: <strong>{assessment.answered_questions} / {assessment.total_questions}</strong>
          </div>
          <div className="metric-item">
            Completed: <strong>{new Date(assessment.completed_at || Date.now()).toLocaleTimeString()}</strong>
          </div>
        </div>
      </div>

      {/* Topic Breakdown Table */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
          Topic-wise Performance Breakdown
        </h3>

        <div className="table-responsive">
          <table className="problems-table">
            <thead>
              <tr>
                <th>Topic</th>
                <th>Questions</th>
                <th>Correct</th>
                <th>Topic Score</th>
              </tr>
            </thead>
            <tbody>
              {assessment.topic_results?.map((tr) => (
                <tr key={tr.topic_id}>
                  <td style={{ fontWeight: 600 }}>{tr.topic_name}</td>
                  <td>{tr.questions}</td>
                  <td style={{ color: tr.correct > 0 ? 'var(--accent-green)' : 'var(--text-muted)' }}>
                    {tr.correct}
                  </td>
                  <td>
                    <span className={`status-badge ${tr.score >= 70 ? 'status-passed' : tr.score >= 40 ? 'status-timeout' : 'status-failed'}`}>
                      {tr.score}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div style={{ textAlign: 'center', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
        <button className="btn btn-secondary" onClick={handleStartAssessment}>
          🔄 Retake Diagnostic Assessment
        </button>
        <Link to="/problems" className="btn btn-primary">
          Explore Practice Problems &rarr;
        </Link>
      </div>
    </div>
  );
}
