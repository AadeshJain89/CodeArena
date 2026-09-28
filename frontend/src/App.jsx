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
import { AdminPage } from './pages/AdminPage';
import './App.css';

function HomePage() {
  const { user } = useAuth();

  return (
    <div className="container">
      {/* Hero Section */}
      <section className="hero">
        <h1 className="hero-title" style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '1rem' }}>
          Master Algorithmic Problem Solving with <span className="hero-gradient-text">CodeArena</span>
        </h1>
        <p className="hero-subtitle" style={{ fontSize: '1.15rem', color: 'var(--text-muted)', maxWidth: '750px', margin: '0 auto 2rem auto', lineHeight: 1.6 }}>
          Practice coding problems, evaluate your solutions securely, understand your skills, and get personalized problem recommendations.
        </p>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          {user ? (
            <>
              <Link to="/dashboard" className="btn btn-primary">
                📊 Go to Dashboard
              </Link>
              <Link to="/diagnostic" className="btn btn-secondary">
                🧠 Take Skill Diagnostic
              </Link>
            </>
          ) : (
            <>
              <Link to="/register" className="btn btn-primary">
                🚀 Get Started
              </Link>
              <Link to="/problems" className="btn btn-secondary">
                💻 Explore Problems
              </Link>
            </>
          )}
        </div>
      </section>

      {/* Quick Platform Metrics Banner */}
      <div
        style={{
          display: 'flex',
          justify: 'center',
          gap: '2.5rem',
          flexWrap: 'wrap',
          margin: '2rem auto 3rem auto',
          padding: '1.25rem',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          maxWidth: '800px',
          textAlign: 'center',
        }}
      >
        <div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>12 Core Topics</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Arrays to Dynamic Programming</div>
        </div>
        <div style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: '2.5rem' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>36 Practice Problems</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Easy, Medium &amp; Hard Challenges</div>
        </div>
        <div style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: '2.5rem' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>Python &amp; C++</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Isolated Docker Execution</div>
        </div>
      </div>

      {/* Feature Cards Grid */}
      <div className="cards-grid" style={{ marginBottom: '3rem' }}>
        {/* Adaptive Recommendations Card */}
        <div className="card">
          <div className="card-icon">🎯</div>
          <h3 className="card-title">Adaptive Recommendations</h3>
          <p className="card-desc">
            Get personalized problem suggestions based on your skill gaps, confidence, and solving history.
          </p>
        </div>

        {/* Diagnostic Skill Assessment Card */}
        <div className="card">
          <div className="card-icon">🧠</div>
          <h3 className="card-title">Diagnostic Skill Assessment</h3>
          <p className="card-desc">
            Assess your programming skills across core data structure and algorithm topics.
          </p>
        </div>

        {/* Isolated Code Execution Card */}
        <div className="card">
          <div className="card-icon">⚡</div>
          <h3 className="card-title">Isolated Code Execution</h3>
          <p className="card-desc">
            Run Python and C++ solutions in isolated Docker containers with automated test-case evaluation.
          </p>
        </div>

        {/* Progress & Gamification Card */}
        <div className="card">
          <div className="card-icon">🏆</div>
          <h3 className="card-title">Progress &amp; Gamification</h3>
          <p className="card-desc">
            Track your skills, submissions, XP, levels, streaks, and achievement badges.
          </p>
        </div>
      </div>

      <footer className="footer">
        CodeArena &bull; Secure Programming Practice &amp; Skill Evaluation Platform
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
                path="/admin"
                element={
                  <ProtectedRoute>
                    <AdminPage />
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
