import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { recommendationService } from '../services/recommendationService';
import { useAuth } from '../context/AuthContext';

export function RecommendationsPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedReasons, setExpandedReasons] = useState({});

  useEffect(() => {
    async function fetchRecommendations() {
      setLoading(true);
      setError(null);
      try {
        const data = await recommendationService.getRecommendations(token);
        setRecommendations(data || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (token) {
      fetchRecommendations();
    }
  }, [token]);

  const toggleReasons = (recId) => {
    setExpandedReasons((prev) => ({
      ...prev,
      [recId]: !prev[recId],
    }));
  };

  const getDifficultyBadgeClass = (diff) => {
    switch (diff?.toUpperCase()) {
      case 'EASY':
        return 'badge-easy';
      case 'MEDIUM':
        return 'badge-medium';
      case 'HARD':
        return 'badge-hard';
      default:
        return 'status-badge';
    }
  };

  return (
    <div className="container" style={{ maxWidth: '900px' }}>
      <div className="page-header" style={{ textAlign: 'center' }}>
        <h1 className="page-title">Recommended For You</h1>
        <p className="page-subtitle">
          Personalized practice based on your current skill profile.
        </p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner" style={{ width: '32px', height: '32px', borderWidth: '3px', margin: '0 auto 1rem auto' }}></div>
          <p className="text-muted">Analyzing your skill profile and generating top recommendations...</p>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="card" style={{ padding: '2.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>💡</div>
          <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>No recommendations available yet</h3>
          <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
            Complete the diagnostic assessment to unlock personalized recommendations tailored to your skill gaps.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <Link to="/diagnostic" className="btn btn-primary">
              🧠 Take Diagnostic Assessment
            </Link>
            <Link to="/problems" className="btn btn-secondary">
              💻 Explore All Problems
            </Link>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginBottom: '2rem' }}>
          {recommendations.map((rec) => {
            const prob = rec.problem;
            const topicsStr = prob.topics && prob.topics.length > 0
              ? prob.topics.map((t) => t.name).join(' • ')
              : 'General';
            const isReasonsOpen = expandedReasons[rec.recommendation_id] !== false; // Default open for clear explainability

            return (
              <div
                key={rec.recommendation_id}
                className="card"
                style={{
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  borderLeft: rec.rank === 1 ? '4px solid var(--accent-cyan)' : '4px solid var(--border-color)',
                }}
              >
                {/* Header Row: Rank, Title, Badges */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span
                      style={{
                        background: rec.rank === 1 ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.1)',
                        color: rec.rank === 1 ? '#000' : 'var(--text-main)',
                        fontWeight: 800,
                        fontSize: '0.9rem',
                        padding: '0.25rem 0.6rem',
                        borderRadius: '6px',
                      }}
                    >
                      #{rec.rank}
                    </span>
                    <div>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>{prob.title}</h3>
                      <span className="text-muted" style={{ fontSize: '0.85rem' }}>{topicsStr}</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className={`status-badge ${getDifficultyBadgeClass(prob.difficulty)}`}>
                      {prob.difficulty}
                    </span>
                  </div>
                </div>

                {/* Description Snippet */}
                <p className="text-muted" style={{ fontSize: '0.9rem', margin: 0, lineHeight: 1.5 }}>
                  {prob.description?.length > 160 ? `${prob.description.substring(0, 160)}...` : prob.description}
                </p>

                {/* Explainable Reasons Section */}
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <button
                    onClick={() => toggleReasons(rec.recommendation_id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--accent-cyan)',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      padding: 0,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      width: '100%',
                      textAlign: 'left',
                    }}
                  >
                    <span>Why this problem?</span>
                    <span>{isReasonsOpen ? '▲' : '▼'}</span>
                  </button>

                  {isReasonsOpen && (
                    <ul style={{ margin: '0.5rem 0 0 1.25rem', padding: 0, fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                      {rec.reasons?.map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Action Footer */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.25rem' }}>
                  <button
                    onClick={() => navigate(`/problems/${prob.id}`)}
                    className="btn btn-primary"
                    style={{ fontSize: '0.9rem', padding: '0.5rem 1.25rem' }}
                  >
                    Solve Challenge &rarr;
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
