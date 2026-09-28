import { useAuth } from '../context/AuthContext';

export function ProfilePage() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="container" style={{ maxWidth: '600px' }}>
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
    </div>
  );
}
