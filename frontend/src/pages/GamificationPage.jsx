import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { gamificationService } from '../services/gamificationService';
import { useAuth } from '../context/AuthContext';

const BADGE_INFO = {
  FIRST_SOLVE: { title: 'First Solve', icon: '🚀', desc: 'Solved your first coding problem' },
  FIVE_SOLVES: { title: 'High Five', icon: '🌟', desc: 'Solved 5 unique problems' },
  TEN_SOLVES: { title: 'Problem Master', icon: '🏆', desc: 'Solved 10 unique problems' },
  THREE_DAY_STREAK: { title: 'On Fire', icon: '🔥', desc: 'Maintained a 3-day coding streak' },
  SEVEN_DAY_STREAK: { title: 'Unstoppable', icon: '⚡', desc: 'Maintained a 7-day coding streak' },
};

export function GamificationPage() {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchGamification() {
      setLoading(true);
      setError(null);
      try {
        const res = await gamificationService.getGamification(token);
        setData(res);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    if (token) {
      fetchGamification();
    }
  }, [token]);

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading gamification profile...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <div style={{ background: 'rgba(255, 77, 77, 0.1)', border: '1px solid rgba(255, 77, 77, 0.3)', padding: '1.5rem', borderRadius: 'var(--radius-md)', color: '#ff4d4d' }}>
          <p>Failed to load gamification stats: {error}</p>
        </div>
      </div>
    );
  }

  const xp = data?.xp || 0;
  const level = data?.level || 1;
  const xpInCurrentLevel = xp % 100;
  const xpForNextLevel = 100 - xpInCurrentLevel;
  const progressPct = xpInCurrentLevel; // Each level requires 100 XP
  const userBadges = new Set(data?.badges || []);

  return (
    <div className="container" style={{ maxWidth: '1000px' }}>
      <div className="page-header" style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <h1 className="page-title">User Progression & Gamification</h1>
        <p className="page-subtitle">
          Track your experience points, streak, solved problems, and earned achievements.
        </p>
      </div>

      {/* Main Level & XP Progress Card */}
      <div className="card" style={{ marginBottom: '2rem', padding: '2rem', background: 'linear-gradient(135deg, rgba(18, 24, 36, 0.95), rgba(30, 41, 59, 0.9))' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <span style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Current Rank
            </span>
            <h2 style={{ fontSize: '2.2rem', margin: '0.25rem 0', color: '#ffffff' }}>
              Level {level} Explorer
            </h2>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--accent-cyan)' }}>
              {xp} XP
            </span>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {xpForNextLevel} XP needed for Level {level + 1}
            </div>
          </div>
        </div>

        {/* XP Progress Bar */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span>Level {level} ({ (level - 1) * 100 } XP)</span>
            <span>{xpInCurrentLevel} / 100 XP</span>
            <span>Level {level + 1} ({ level * 100 } XP)</span>
          </div>
          <div style={{ width: '100%', height: '12px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '6px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${progressPct}%`,
                height: '100%',
                background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-purple))',
                borderRadius: '6px',
                transition: 'width 0.4s ease',
              }}
            />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="cards-grid" style={{ marginBottom: '2.5rem' }}>
        <div className="card">
          <div className="card-icon">🔥</div>
          <h3 className="card-title">Current Streak</h3>
          <p className="card-desc" style={{ fontSize: '1.8rem', fontWeight: '800', color: '#ffffff', margin: '0.5rem 0' }}>
            {data?.current_streak || 0} {data?.current_streak === 1 ? 'Day' : 'Days'}
          </p>
          <div className="card-status">
            <span>Last Activity</span>
            <span className="status-indicator status-active">
              {data?.last_activity_date || 'No activity yet'}
            </span>
          </div>
        </div>

        <div className="card">
          <div className="card-icon">⚡</div>
          <h3 className="card-title">Longest Streak</h3>
          <p className="card-desc" style={{ fontSize: '1.8rem', fontWeight: '800', color: '#ffffff', margin: '0.5rem 0' }}>
            {data?.longest_streak || 0} {data?.longest_streak === 1 ? 'Day' : 'Days'}
          </p>
          <div className="card-status">
            <span>Personal Best</span>
            <span className="status-indicator status-passed">Record</span>
          </div>
        </div>

        <div className="card">
          <div className="card-icon">🎯</div>
          <h3 className="card-title">Problems Solved</h3>
          <p className="card-desc" style={{ fontSize: '1.8rem', fontWeight: '800', color: '#ffffff', margin: '0.5rem 0' }}>
            {data?.problems_solved || 0}
          </p>
          <div className="card-status">
            <span>Unique Solves</span>
            <span className="status-indicator status-passed">First-time solves</span>
          </div>
        </div>

        <div className="card">
          <div className="card-icon">✅</div>
          <h3 className="card-title">Passed Submissions</h3>
          <p className="card-desc" style={{ fontSize: '1.8rem', fontWeight: '800', color: '#ffffff', margin: '0.5rem 0' }}>
            {data?.successful_submissions || 0}
          </p>
          <div className="card-status">
            <span>Total Accepted</span>
            <span className="status-indicator status-passed">All successful runs</span>
          </div>
        </div>
      </div>

      {/* Badges / Achievements Section */}
      <div className="card" style={{ padding: '2rem' }}>
        <h3 style={{ fontSize: '1.4rem', color: '#ffffff', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>🏅</span> Achievements & Badges
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1.25rem' }}>
          {Object.entries(BADGE_INFO).map(([badgeKey, info]) => {
            const isEarned = userBadges.has(badgeKey);
            return (
              <div
                key={badgeKey}
                style={{
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  background: isEarned ? 'rgba(0, 242, 254, 0.08)' : 'rgba(255, 255, 255, 0.02)',
                  border: isEarned ? '1px solid rgba(0, 242, 254, 0.3)' : '1px dashed var(--border-color)',
                  opacity: isEarned ? 1 : 0.5,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  textAlign: 'center',
                  transition: 'transform 0.2s ease',
                }}
              >
                <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>
                  {info.icon}
                </div>
                <div style={{ fontWeight: '700', color: isEarned ? '#ffffff' : 'var(--text-muted)', marginBottom: '0.25rem' }}>
                  {info.title}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  {info.desc}
                </div>
                <span
                  className={`status-indicator ${isEarned ? 'status-passed' : 'status-pending'}`}
                  style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}
                >
                  {isEarned ? 'Unlocked' : 'Locked'}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
