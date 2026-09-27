import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';

export function ProfilePage() {
  const { user, token, logout } = useAuth();
  const [adminTestResult, setAdminTestResult] = useState(null);
  const [adminTestLoading, setAdminTestLoading] = useState(false);
  const [adminTestError, setAdminTestError] = useState(null);

  const handleTestAdminEndpoint = async () => {
    setAdminTestLoading(true);
    setAdminTestResult(null);
    setAdminTestError(null);

    try {
      const res = await authService.testAdminEndpoint(token);
      setAdminTestResult(res);
    } catch (err) {
      setAdminTestError(err.message);
    } finally {
      setAdminTestLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="container">
      <div className="profile-grid">
        {/* Profile Card */}
        <div className="card">
          <div className="profile-header">
            <div className="avatar">{user.username.charAt(0).toUpperCase()}</div>
            <div>
              <h2 className="profile-name">{user.username}</h2>
              <span className={`badge ${user.role === 'ADMIN' ? 'badge-admin' : 'badge-user'}`}>
                {user.role} ROLE
              </span>
            </div>
          </div>

          <div className="profile-details">
            <div className="detail-item">
              <span className="detail-label">User ID</span>
              <span className="detail-value">{user.id}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Email Address</span>
              <span className="detail-value">{user.email}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Account Status</span>
              <span className="detail-value status-active">
                {user.is_active ? '● Active' : '● Inactive'}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Member Since</span>
              <span className="detail-value">
                {new Date(user.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </span>
            </div>
          </div>

          <div style={{ marginTop: '2rem' }}>
            <button onClick={logout} className="btn btn-danger btn-block">
              Logout
            </button>
          </div>
        </div>

        {/* Authorization & Admin Test Card */}
        <div className="card">
          <h3 className="card-title">Role-Based Authorization Test</h3>
          <p className="card-desc">
            Test backend endpoint protection. Standard <strong>USER</strong> accounts should receive a 403 Forbidden error, while <strong>ADMIN</strong> accounts are granted access.
          </p>

          <button
            onClick={handleTestAdminEndpoint}
            className="btn btn-secondary btn-block"
            disabled={adminTestLoading}
          >
            {adminTestLoading ? 'Testing Authorization...' : 'Call GET /api/v1/admin/test'}
          </button>

          {adminTestResult && (
            <div className="alert alert-success" style={{ marginTop: '1.25rem' }}>
              <strong>HTTP 200 OK — Access Granted!</strong>
              <pre className="code-block" style={{ marginTop: '0.5rem' }}>
                {JSON.stringify(adminTestResult, null, 2)}
              </pre>
            </div>
          )}

          {adminTestError && (
            <div className="alert alert-error" style={{ marginTop: '1.25rem' }}>
              <strong>HTTP 403 Forbidden — Access Denied!</strong>
              <p style={{ marginTop: '0.25rem' }}>{adminTestError}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
