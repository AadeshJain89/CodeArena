import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  const checkHealth = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/health`)
      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`)
      }
      const data = await res.json()
      setHealth(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkHealth()
  }, [])

  return (
    <div className="container">
      {/* Header */}
      <header className="header">
        <div className="brand">
          <div className="brand-icon">⚡</div>
          <h1 className="brand-title">CodeArena</h1>
        </div>
        <div className="badge badge-online">
          <span className="badge-dot"></span>
          Frontend Running
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <h2 className="hero-title">
          Welcome to <span className="hero-gradient-text">CodeArena</span>
        </h2>
        <p className="hero-subtitle">
          Initial project foundation initialized successfully. Ready for incremental module development.
        </p>
      </section>

      {/* Infrastructure Status Grid */}
      <div className="cards-grid">
        {/* Frontend Card */}
        <div className="card">
          <div className="card-icon">💻</div>
          <h3 className="card-title">Frontend App</h3>
          <p className="card-desc">React 18 + Vite development server with pure CSS styling system.</p>
          <div className="card-status">
            <span>Status</span>
            <span className="status-indicator status-active">
              ● Running (Port 5173)
            </span>
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
          <p className="card-desc">SQLAlchemy 2.x & Alembic migration framework configuration.</p>
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

        {/* Redis Card */}
        <div className="card">
          <div className="card-icon">🔴</div>
          <h3 className="card-title">Redis Cache</h3>
          <p className="card-desc">Async Redis client configuration for session & execution queueing.</p>
          <div className="card-status">
            <span>Status</span>
            <span className="status-indicator">
              {loading ? (
                <span className="status-pending">Checking...</span>
              ) : health?.services?.redis?.status === 'connected' ? (
                <span className="status-active">● Connected (Port 6379)</span>
              ) : (
                <span className="status-error">● Disconnected</span>
              )}
            </span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="footer">
        CodeArena Platform &bull; Foundation Module &bull; Academic Mini-Project
      </footer>
    </div>
  )
}

export default App
