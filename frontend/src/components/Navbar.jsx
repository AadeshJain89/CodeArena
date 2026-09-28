import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/" className="nav-logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">CodeArena</span>
        </Link>
      </div>

      <div className="nav-links">
        <Link to="/problems" className="nav-link">
          Problems
        </Link>

        {user ? (
          <>
            <Link to="/diagnostic" className="nav-link">
              Diagnostic
            </Link>
            <Link to="/skills" className="nav-link">
              Skill Profile
            </Link>
            <Link to="/recommendations" className="nav-link">
              Recommendations
            </Link>
            <Link to="/gamification" className="nav-link">
              Gamification
            </Link>
            <Link to="/submissions" className="nav-link">
              Submissions
            </Link>
            <Link to="/me" className="nav-link nav-profile">
              <span className="role-tag">{user.role}</span>
              <span>{user.username}</span>
            </Link>
            <button onClick={handleLogout} className="btn btn-secondary btn-sm">
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-link">
              Login
            </Link>
            <Link to="/register" className="btn btn-primary btn-sm">
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
