import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { analyticsService } from '../services/analyticsService';
import { useAuth } from '../context/AuthContext';

const BADGE_DESCRIPTIONS = {
  FIRST_SOLVE: { title: 'First Solve', icon: '🚀', desc: 'Solved your first coding problem' },
  FIVE_SOLVES: { title: 'High Five', icon: '🌟', desc: 'Solved 5 unique problems' },
  TEN_SOLVES: { title: 'Problem Master', icon: '🏆', desc: 'Solved 10 unique problems' },
  THREE_DAY_STREAK: { title: 'On Fire', icon: '🔥', desc: 'Maintained a 3-day coding streak' },
  SEVEN_DAY_STREAK: { title: 'Unstoppable', icon: '⚡', desc: 'Maintained a 7-day coding streak' },
};

export function DashboardPage() {
  const { token, user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyticsService.getDashboard(token);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchDashboard();
    }
  }, [token]);

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>Loading user analytics dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <div style={{ background: 'rgba(255, 77, 77, 0.1)', border: '1px solid rgba(255, 77, 77, 0.3)', padding: '1.5rem', borderRadius: 'var(--radius-md)', color: '#ff4d4d', maxWidth: '600px', margin: '0 auto' }}>
          <h3 style={{ marginTop: 0 }}>Error Loading Dashboard</h3>
          <p>{error}</p>
          <button onClick={fetchDashboard} className="btn btn-primary" style={{ marginTop: '1rem' }}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  const { overview, diagnostic, skills, submissions, recommendations, gamification } = data || {};

  const getStatusBadgeClass = (status) => {
    switch (status?.toUpperCase()) {
      case 'PASSED':
        return 'status-passed';
      case 'FAILED':
      case 'WRONG_ANSWER':
      case 'COMPILATION_ERROR':
      case 'RUNTIME_ERROR':
        return 'status-failed';
      case 'TIME_LIMIT_EXCEEDED':
        return 'status-timeout';
      default:
        return 'status-pending';
    }
  };

  const getSkillLevelBadgeClass = (level) => {
    switch (level?.toUpperCase()) {
      case 'EXPERT':
        return 'status-passed';
      case 'ADVANCED':
        return 'status-passed';
      case 'INTERMEDIATE':
        return 'status-timeout';
      case 'NOVICE':
      default:
        return 'status-pending';
    }
  };

  const getDifficultyBadgeClass = (diff) => {
    switch (diff?.toUpperCase()) {
      case 'EASY':
        return 'status-passed';
      case 'MEDIUM':
        return 'status-timeout';
      case 'HARD':
        return 'status-failed';
      default:
        return 'status-pending';
    }
  };

  return (
    <div className="container" style={{ maxWidth: '1100px' }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <h1 className="page-title">User Analytics & Performance Dashboard</h1>
        <p className="page-subtitle">
          Welcome back, <strong style={{ color: '#ffffff' }}>{user?.username}</strong>! Track your skill progression, submissions, diagnostic scores, and personalized recommendations.
        </p>
      </div>

      {/* Overview Metric Cards */}
      <div className="cards-grid" style={{ marginBottom: '2.5rem' }}>
        <div className="card">
          <div className="card-icon">🎯</div>
          <h3 className="card-title">Problems Solved</h3>
          <p className="card-desc" style={{ fontSize: '2rem', fontWeight: '800', color: '#ffffff', margin: '0.4rem 0' }}>
            {overview?.total_problems_solved || 0}
          </p>
          <div className="card-status">
            <span>Attempted</span>
            <span className="status-indicator status-passed">{overview?.total_problems_attempted || 0} Unique Problems</span>
          </div>
        </div>

        <div className="card">
          <div className="card-icon">📊</div>
          <h3 className="card-title">Submissions</h3>
          <p className="card-desc" style={{ fontSize: '2rem', fontWeight: '800', color: '#ffffff', margin: '0.4rem 0' }}>
            {overview?.total_submissions || 0}
          </p>
          <div className="card-status">
            <span>Passed / Failed</span>
            <span className="status-indicator status-active">
              {overview?.successful_submissions || 0} Passed • {overview?.failed_submissions || 0} Failed
            </span>
          </div>
        </div>

        <div className="card">
          <div className="card-icon">📈</div>
          <h3 className="card-title">Success Rate</h3>
          <p className="card-desc" style={{ fontSize: '2rem', fontWeight: '800', color: '#ffffff', margin: '0.4rem 0' }}>
            {overview?.success_rate || 0}%
          </p>
          <div className="card-status">
            <span>Accuracy</span>
            <span className="status-indicator status-passed">Accepted Submissions</span>
          </div>
        </div>

        <div className="card">
          <div className="card-icon">🔥</div>
          <h3 className="card-title">Current Streak</h3>
          <p className="card-desc" style={{ fontSize: '2rem', fontWeight: '800', color: '#ffffff', margin: '0.4rem 0' }}>
            {overview?.current_streak || 0} {overview?.current_streak === 1 ? 'Day' : 'Days'}
          </p>
          <div className="card-status">
            <span>Longest Streak</span>
            <span className="status-indicator status-active">{overview?.longest_streak || 0} Days</span>
          </div>
        </div>

        <div className="card">
          <div className="card-icon">⚡</div>
          <h3 className="card-title">Rank & Level</h3>
          <p className="card-desc" style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--accent-cyan)', margin: '0.4rem 0' }}>
            Level {overview?.current_level || 1}
          </p>
          <div className="card-status">
            <span>Experience Points</span>
            <span className="status-indicator status-passed">{overview?.xp || 0} XP</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Diagnostic & Gamification Summaries */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
        {/* Diagnostic Card */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#ffffff', marginTop: 0, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>📝</span> Diagnostic Assessment
          </h3>

          {diagnostic?.has_completed_diagnostic ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <div style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--accent-cyan)' }}>
                    {diagnostic.score}%
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Overall Diagnostic Score</div>
                </div>
                <span className="status-indicator status-passed" style={{ fontSize: '0.85rem' }}>
                  Completed
                </span>
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                Correct Answers: <strong>{diagnostic.correct_answers} / {diagnostic.total_questions}</strong>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Completed At: {diagnostic.completed_at ? new Date(diagnostic.completed_at).toLocaleDateString() : 'N/A'}
              </div>
              <div style={{ marginTop: '1rem' }}>
                <Link to="/diagnostic" className="btn btn-secondary btn-sm" style={{ width: '100%', textAlign: 'center' }}>
                  Retake Diagnostic Assessment
                </Link>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '1rem 0' }}>
              <p style={{ color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                No diagnostic completed yet. Complete a 10-question diagnostic assessment to establish your baseline topic skill profiles!
              </p>
              <Link to="/diagnostic" className="btn btn-primary btn-sm">
                Start Diagnostic Assessment &rarr;
              </Link>
            </div>
          )}
        </div>

        {/* Gamification Progress & Badges Card */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#ffffff', marginTop: 0, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>🏅</span> Progression & Achievements
          </h3>

          <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
              <span>Level {gamification?.level || 1}</span>
              <span>{gamification?.xp_for_next_level || 100} XP to Level {(gamification?.level || 1) + 1}</span>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${(gamification?.xp || 0) % 100}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-purple))',
                }}
              />
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.6rem' }}>
              Unlocked Badges ({gamification?.badges?.length || 0})
            </div>
            {gamification?.badges && gamification.badges.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {gamification.badges.map((badgeKey) => {
                  const info = BADGE_DESCRIPTIONS[badgeKey] || { title: badgeKey, icon: '🏅' };
                  return (
                    <span
                      key={badgeKey}
                      style={{
                        fontSize: '0.8rem',
                        padding: '0.3rem 0.6rem',
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(0, 242, 254, 0.15)',
                        border: '1px solid rgba(0, 242, 254, 0.3)',
                        color: '#ffffff',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                      title={info.desc}
                    >
                      <span>{info.icon}</span>
                      <span>{info.title}</span>
                    </span>
                  );
                })}
              </div>
            ) : (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic', margin: 0 }}>
                No badges unlocked yet. Solve coding problems to earn your first badge!
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Topic Skill Profiles Section */}
      <div className="card" style={{ padding: '2rem', marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.35rem', color: '#ffffff', margin: 0 }}>Topic Skill Mastery</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
              Real-time skill estimates across all 12 CodeArena algorithm & data structure topics.
            </p>
          </div>
          <Link to="/skills" className="btn btn-secondary btn-sm">
            View Skill Profile Details &rarr;
          </Link>
        </div>

        {skills && skills.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.25rem' }}>
            {skills.map((item) => (
              <div
                key={item.topic_id}
                style={{
                  padding: '1rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: '700', color: '#ffffff', fontSize: '0.95rem' }}>
                    {item.topic_name}
                  </span>
                  <span className={`status-indicator ${getSkillLevelBadgeClass(item.skill_level)}`} style={{ fontSize: '0.75rem' }}>
                    {item.skill_level}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                  <span>Score: {item.skill_score} / 100</span>
                  <span>Conf: {Math.round(item.confidence * 100)}%</span>
                </div>

                <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min(100, Math.max(0, item.skill_score))}%`,
                      height: '100%',
                      background: 'var(--accent-cyan)',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
            Start solving problems to build your topic skill profiles.
          </p>
        )}
      </div>

      {/* Recommendations Summary Section */}
      <div className="card" style={{ padding: '2rem', marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.35rem', color: '#ffffff', margin: 0 }}>Top Recommended Problems</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
              Personalized practice recommendations generated specifically for your skill level.
            </p>
          </div>
          <Link to="/recommendations" className="btn btn-primary btn-sm">
            View All Recommendations &rarr;
          </Link>
        </div>

        {recommendations?.recommendations && recommendations.recommendations.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {recommendations.recommendations.map((rec) => (
              <div
                key={rec.problem_id}
                style={{
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                  padding: '1rem 1.25rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-color)',
                  flexWrap: 'wrap',
                  gap: '1rem',
                }}
              >
                <div style={{ flex: 1, minWidth: '240px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.3rem' }}>
                    <span style={{ fontWeight: '800', color: 'var(--accent-cyan)' }}>#{rec.rank}</span>
                    <Link to={`/problems/${rec.problem_id}`} style={{ fontWeight: '700', color: '#ffffff', textDecoration: 'none' }}>
                      {rec.problem_title}
                    </Link>
                    <span className={`status-indicator ${getDifficultyBadgeClass(rec.difficulty)}`} style={{ fontSize: '0.75rem' }}>
                      {rec.difficulty}
                    </span>
                  </div>
                  {rec.reasons && rec.reasons.length > 0 && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      💡 {rec.reasons[0]}
                    </div>
                  )}
                </div>
                <Link to={`/problems/${rec.problem_id}`} className="btn btn-secondary btn-sm">
                  Solve Challenge &rarr;
                </Link>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
            No recommendations available yet. Start solving problems or complete the diagnostic assessment!
          </div>
        )}
      </div>

      {/* Recent Submissions Activity Section */}
      <div className="card" style={{ padding: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.35rem', color: '#ffffff', margin: 0 }}>Recent Submission Activity</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
              Your 10 most recent code submissions and evaluation status.
            </p>
          </div>
          <Link to="/submissions" className="btn btn-secondary btn-sm">
            View All Submissions &rarr;
          </Link>
        </div>

        {submissions?.recent_submissions && submissions.recent_submissions.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.75rem' }}>Problem</th>
                  <th style={{ padding: '0.75rem' }}>Language</th>
                  <th style={{ padding: '0.75rem' }}>Status</th>
                  <th style={{ padding: '0.75rem' }}>Execution Time</th>
                  <th style={{ padding: '0.75rem' }}>Date</th>
                </tr>
              </thead>
              <tbody>
                {submissions.recent_submissions.map((sub) => (
                  <tr key={sub.submission_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                    <td style={{ padding: '0.75rem', fontWeight: '600' }}>
                      <Link to={`/problems/${sub.problem_id}`} style={{ color: '#ffffff', textDecoration: 'none' }}>
                        {sub.problem_title}
                      </Link>
                    </td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>
                      {sub.language}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <span className={`status-indicator ${getStatusBadgeClass(sub.status)}`} style={{ fontSize: '0.75rem' }}>
                        {sub.status}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>
                      {sub.execution_time_ms != null ? `${sub.execution_time_ms} ms` : 'N/A'}
                    </td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {sub.submitted_at ? new Date(sub.submitted_at).toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
            No submissions recorded yet. Pick a problem from the Problem Bank to submit your first solution!
          </div>
        )}
      </div>
    </div>
  );
}
