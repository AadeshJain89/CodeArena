import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ProfilePage } from './pages/ProfilePage';
import { ProblemsPage } from './pages/ProblemsPage';
import { ProblemDetailPage } from './pages/ProblemDetailPage';
import { SubmissionsPage } from './pages/SubmissionsPage';
import { DiagnosticPage } from './pages/DiagnosticPage';
import { SkillsPage } from './pages/SkillsPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { GamificationPage } from './pages/GamificationPage';
import { DashboardPage } from './pages/DashboardPage';
import './App.css';

function HomePage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user } = useAuth();

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    async function checkHealth() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) {
          throw new Error(`HTTP error ${res.status}`);
        }
        const data = await res.json();
        setHealth(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    checkHealth();
  }, [API_BASE]);

  return (
    <div className="container">
      {/* Hero Section */}
      <section className="hero">
        <h2 className="hero-title">
          Welcome to <span className="hero-gradient-text">CodeArena</span>
        </h2>
        <p className="hero-subtitle">
          Module 3: Problem Bank & Topic Hierarchy (12 Topics &bull; 36 Problems &bull; Test Cases) Active.
        </p>

        <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <Link to="/problems" className="btn btn-primary">
            Explore Problems &rarr;
          </Link>
          {user ? (
            <Link to="/me" className="btn btn-secondary">
              Profile ({user.username})
            </Link>
          ) : (
            <Link to="/login" className="btn btn-secondary">
              Sign In
            </Link>
          )}
        </div>
      </section>

      {/* Infrastructure & Module Status Grid */}
      <div className="cards-grid">
        {/* Problems Module Card */}
        <div className="card">
          <div className="card-icon">📚</div>
          <h3 className="card-title">Problem System</h3>
          <p className="card-desc">36 Challenges across 12 topics (Arrays, DP, Graphs, etc.) with public/hidden test cases.</p>
          <div className="card-status">
            <span>Module Status</span>
            <span className="status-indicator status-active">● Active</span>
          </div>
        </div>

        {/* Auth Module Card */}
        <div className="card">
          <div className="card-icon">🔐</div>
          <h3 className="card-title">Authentication Module</h3>
          <p className="card-desc">JWT Access Tokens + Argon2 Password Hashing with USER / ADMIN role checks.</p>
          <div className="card-status">
            <span>Module Status</span>
            <span className="status-indicator status-active">● Active</span>
          </div>
        </div>

        {/* Backend Card */}
        <div className="card">
          <div className="card-icon">⚡</div>
          <h3 className="card-title">FastAPI Backend</h3>
          <p className="card-desc">Python 3 async backend framework with Pydantic & CORS setup.</p>
          <div className="card-status">
            <span>Status</span>
            <span className="status-indicator">
              {loading ? (
                <span className="status-pending">Checking...</span>
              ) : error ? (
                <span className="status-error">● Offline ({error})</span>
              ) : (
                <span className="status-active">● Connected</span>
              )}
            </span>
          </div>
        </div>

        {/* PostgreSQL Card */}
        <div className="card">
          <div className="card-icon">🐘</div>
          <h3 className="card-title">PostgreSQL Database</h3>
          <p className="card-desc">SQLAlchemy 2.x & Alembic schema for topics, problems, and test cases.</p>
          <div className="card-status">
            <span>Status</span>
            <span className="status-indicator">
              {loading ? (
                <span className="status-pending">Checking...</span>
              ) : health?.services?.database?.status === 'connected' ? (
                <span className="status-active">● Connected (Port 5432)</span>
              ) : (
                <span className="status-error">● Disconnected</span>
              )}
            </span>
          </div>
        </div>
      </div>

      <footer className="footer">
        CodeArena Platform &bull; Module 3 Problems & Topics &bull; Academic Mini-Project
      </footer>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div id="root">
          <Navbar />
          <main style={{ flex: 1 }}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/problems" element={<ProblemsPage />} />
              <Route path="/problems/:id" element={<ProblemDetailPage />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/diagnostic"
                element={
                  <ProtectedRoute>
                    <DiagnosticPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/skills"
                element={
                  <ProtectedRoute>
                    <SkillsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/recommendations"
                element={
                  <ProtectedRoute>
                    <RecommendationsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/gamification"
                element={
                  <ProtectedRoute>
                    <GamificationPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/submissions"
                element={
                  <ProtectedRoute>
                    <SubmissionsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/me"
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
