import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { problemService } from '../services/problemService';

export function ProblemsPage() {
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const [problemsData, setProblemsData] = useState({ items: [], total: 0, total_pages: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch topics on load
  useEffect(() => {
    async function loadTopics() {
      try {
        const data = await problemService.getTopics();
        setTopics(data);
      } catch (err) {
        console.error('Failed to load topics:', err);
      }
    }
    loadTopics();
  }, []);

  // Fetch problems whenever filters or page change
  useEffect(() => {
    async function loadProblems() {
      setLoading(true);
      setError(null);
      try {
        const data = await problemService.getProblems({
          topic: selectedTopic,
          difficulty: selectedDifficulty,
          page,
          pageSize,
        });
        setProblemsData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadProblems();
  }, [selectedTopic, selectedDifficulty, page]);

  const handleTopicChange = (e) => {
    setSelectedTopic(e.target.value);
    setPage(1);
  };

  const handleDifficultyChange = (e) => {
    setSelectedDifficulty(e.target.value);
    setPage(1);
  };

  const getDifficultyClass = (diff) => {
    switch (diff) {
      case 'EASY':
        return 'diff-easy';
      case 'MEDIUM':
        return 'diff-medium';
      case 'HARD':
        return 'diff-hard';
      default:
        return '';
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1 className="page-title">Problem Arena</h1>
        <p className="page-subtitle">Practice programming challenges across 12 core topics</p>
      </div>

      {/* Filter Bar */}
      <div className="filter-bar">
        <div className="filter-group">
          <label htmlFor="topic-select">Filter Topic:</label>
          <select id="topic-select" value={selectedTopic} onChange={handleTopicChange}>
            <option value="">All Topics</option>
            {topics.map((t) => (
              <option key={t.id} value={t.name}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="diff-select">Filter Difficulty:</label>
          <select id="diff-select" value={selectedDifficulty} onChange={handleDifficultyChange}>
            <option value="">All Difficulties</option>
            <option value="EASY">Easy</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
          </select>
        </div>

        {(selectedTopic || selectedDifficulty) && (
          <button
            onClick={() => {
              setSelectedTopic('');
              setSelectedDifficulty('');
              setPage(1);
            }}
            className="btn btn-secondary btn-sm"
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Problem List */}
      {loading ? (
        <div className="center-screen" style={{ minHeight: '300px' }}>
          <div className="spinner"></div>
          <p className="text-muted" style={{ marginTop: '1rem' }}>Loading problems...</p>
        </div>
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : problemsData.items.length === 0 ? (
        <div className="card text-center" style={{ padding: '3rem' }}>
          <h3>No problems found</h3>
          <p className="text-muted">Try adjusting your topic or difficulty filter.</p>
        </div>
      ) : (
        <>
          <div className="problems-list">
            {problemsData.items.map((p) => (
              <div key={p.id} className="problem-row-card">
                <div className="problem-info">
                  <span className="problem-id">#{p.id}</span>
                  <Link to={`/problems/${p.id}`} className="problem-title-link">
                    {p.title}
                  </Link>
                  <div className="topic-tags">
                    {p.topics.map((t) => (
                      <span key={t.id} className="topic-pill">
                        {t.name}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="problem-actions">
                  <span className={`diff-badge ${getDifficultyClass(p.difficulty)}`}>
                    {p.difficulty}
                  </span>
                  <Link to={`/problems/${p.id}`} className="btn btn-secondary btn-sm">
                    Solve Challenge
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination Controls */}
          {problemsData.total_pages > 1 && (
            <div className="pagination-bar">
              <button
                onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                disabled={page === 1}
                className="btn btn-secondary btn-sm"
              >
                &laquo; Previous
              </button>
              <span className="page-info">
                Page {problemsData.page} of {problemsData.total_pages} ({problemsData.total} problems)
              </span>
              <button
                onClick={() => setPage((prev) => Math.min(prev + 1, problemsData.total_pages))}
                disabled={page === problemsData.total_pages}
                className="btn btn-secondary btn-sm"
              >
                Next &raquo;
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
