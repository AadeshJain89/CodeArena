import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { skillsService } from '../services/skillsService';
import { useAuth } from '../context/AuthContext';

export function SkillsPage() {
  const { token } = useAuth();
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchSkills() {
      setLoading(true);
      setError(null);
      try {
        const data = await skillsService.getSkills(token);
        setSkills(data || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    if (token) {
      fetchSkills();
    }
  }, [token]);

  const totalSolved = skills.reduce((sum, s) => sum + (s.problems_solved || 0), 0);
  const totalPoints = skills.reduce((sum, s) => sum + (s.total_points || 0), 0);
  const avgScore = skills.length > 0 ? (skills.reduce((sum, s) => sum + (s.skill_score || 0), 0) / skills.length).toFixed(1) : 0;

  const getBadgeClass = (level) => {
    switch (level?.toUpperCase()) {
      case 'EXPERT':
        return 'status-passed';
      case 'ADVANCED':
        return 'status-passed';
      case 'INTERMEDIATE':
        return 'status-timeout';
      case 'NOVICE':
        return 'status-failed';
      default:
        return 'status-failed';
    }
  };

  const getConfidenceLabel = (conf) => {
    const pct = Math.round((conf || 0) * 100);
    if (pct >= 70) return `High (${pct}%)`;
    if (pct >= 30) return `Medium (${pct}%)`;
    return `Low (${pct}%)`;
  };

  return (
    <div className="container" style={{ maxWidth: '1000px' }}>
      <div className="page-header" style={{ textAlign: 'center' }}>
        <h1 className="page-title">Skill Profile & Mastery</h1>
        <p className="page-subtitle">
          Estimated proficiency and evidence scores across all 12 CodeArena algorithm topics.
        </p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner" style={{ width: '32px', height: '32px', borderWidth: '3px', margin: '0 auto 1rem auto' }}></div>
          <p className="text-muted">Loading your skill profiles...</p>
        </div>
      ) : (
        <>
          {/* Summary Overview Card */}
          <div className="card" style={{ padding: '2rem', marginBottom: '2rem' }}>
            <div className="metrics-row" style={{ justifyContent: 'space-around', gap: '1.5rem', textAlign: 'center' }}>
              <div className="metric-item">
                <span className="text-muted" style={{ fontSize: '0.85rem', display: 'block', marginBottom: '0.25rem' }}>Average Skill Score</span>
                <strong style={{ fontSize: '1.75rem', color: 'var(--accent-cyan)' }}>{avgScore} / 100</strong>
              </div>
              <div className="metric-item">
                <span className="text-muted" style={{ fontSize: '0.85rem', display: 'block', marginBottom: '0.25rem' }}>Total Problems Solved</span>
                <strong style={{ fontSize: '1.75rem', color: 'var(--accent-green)' }}>{totalSolved}</strong>
              </div>
              <div className="metric-item">
                <span className="text-muted" style={{ fontSize: '0.85rem', display: 'block', marginBottom: '0.25rem' }}>Total Skill Points</span>
                <strong style={{ fontSize: '1.75rem', color: 'var(--accent-purple, #a855f7)' }}>{totalPoints} pts</strong>
              </div>
            </div>
          </div>

          {/* 12 Topic Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
            {skills.map((s) => (
              <div key={s.topic_id} className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>{s.topic_name}</h3>
                    <span className={`status-badge ${getBadgeClass(s.skill_level)}`} style={{ fontSize: '0.75rem' }}>
                      {s.skill_level}
                    </span>
                  </div>

                  {/* Progress Bar for Skill Score */}
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                      <span>Score</span>
                      <strong style={{ color: 'var(--text-main)' }}>{s.skill_score} / 100</strong>
                    </div>
                    <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${Math.min(100, Math.max(0, s.skill_score))}%`,
                          height: '100%',
                          background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-blue))',
                        }}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Problems Solved:</span>
                      <strong style={{ color: 'var(--text-main)' }}>{s.problems_solved}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Total Points:</span>
                      <strong style={{ color: 'var(--text-main)' }}>{s.total_points}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Evidence / Confidence:</span>
                      <strong style={{ color: 'var(--accent-cyan)' }}>{getConfidenceLabel(s.confidence)}</strong>
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)', textAlign: 'right' }}>
                  <Link to={`/problems?topic=${s.topic_id}`} className="text-muted" style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', textDecoration: 'none' }}>
                    Practice Topic &rarr;
                  </Link>
                </div>
              </div>
            ))}
          </div>

          <div style={{ textAlign: 'center' }}>
            <Link to="/diagnostic" className="btn btn-secondary" style={{ marginRight: '1rem' }}>
              🧠 Take Diagnostic Assessment
            </Link>
            <Link to="/problems" className="btn btn-primary">
              💻 Explore All Problems
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
