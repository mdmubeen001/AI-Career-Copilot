import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

export default function Dashboard() {
  const { user, profile } = useAuth();

  const skillsList = Array.isArray(profile?.skills) ? profile.skills : [];
  const interestsList = Array.isArray(profile?.interests) ? profile.interests : [];

  return (
    <div className="dashboard-page">
      {/* Welcome Banner */}
      <section className="welcome-banner">
        <div className="welcome-content">
          <div className="status-chip">
            <span className="status-dot"></span> Phase 1 — Foundation Active
          </div>
          <h1>
            Hello, <span className="highlight-text">{profile?.full_name || user?.email}</span>
          </h1>
          <p>
            Welcome to your AI Multi-Agent Life &amp; Career Copilot. Your secure authentication and profile core are active.
          </p>
        </div>
        <div className="welcome-actions">
          <Link to="/career-analysis" className="btn btn-primary">
            ⚡ Analyze My Career
          </Link>
          <Link to="/profile" className="btn btn-outline">
            Edit Full Profile
          </Link>
        </div>
      </section>

      {/* Overview Cards Grid */}
      <div className="dashboard-grid">
        {/* Profile Card */}
        <div className="dashboard-card">
          <div className="card-header">
            <div className="card-icon">🎓</div>
            <div>
              <h3>Education &amp; Credentials</h3>
              <p>Your academic background</p>
            </div>
          </div>
          <div className="card-body">
            {profile?.college || profile?.degree ? (
              <div className="data-list">
                <div className="data-row">
                  <span className="data-label">College / University:</span>
                  <span className="data-value">{profile.college || 'Not set'}</span>
                </div>
                <div className="data-row">
                  <span className="data-label">Degree:</span>
                  <span className="data-value">{profile.degree || 'Not set'}</span>
                </div>
                <div className="data-row">
                  <span className="data-label">Graduation Year:</span>
                  <span className="data-value">{profile.graduation_year || 'Not set'}</span>
                </div>
              </div>
            ) : (
              <div className="empty-notice">
                <p>No education details added yet.</p>
                <Link to="/profile" className="btn btn-outline btn-sm">
                  Complete Profile
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Career Goal Card */}
        <div className="dashboard-card">
          <div className="card-header">
            <div className="card-icon">🎯</div>
            <div>
              <h3>Target Career Goal</h3>
              <p>Your dream role &amp; path</p>
            </div>
          </div>
          <div className="card-body">
            {profile?.career_goal ? (
              <div className="career-goal-box">
                <p className="goal-quote">&ldquo;{profile.career_goal}&rdquo;</p>
                <div className="goal-actions-row">
                  <span className="goal-status">AI Readiness Analysis Ready</span>
                  <Link to="/career-analysis" className="btn btn-primary btn-sm">
                    Analyze My Career
                  </Link>
                </div>
              </div>
            ) : (
              <div className="empty-notice">
                <p>Set a career goal to guide your AI learning roadmap.</p>
                <Link to="/career-analysis" className="btn btn-primary btn-sm">
                  Analyze My Career
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Skills Card */}
        <div className="dashboard-card">
          <div className="card-header">
            <div className="card-icon">⚡</div>
            <div>
              <h3>Skills ({skillsList.length})</h3>
              <p>Current competencies</p>
            </div>
          </div>
          <div className="card-body">
            {skillsList.length > 0 ? (
              <div className="tags-container">
                {skillsList.map((skill, index) => (
                  <span key={index} className="tag tag-skill">
                    {skill}
                  </span>
                ))}
              </div>
            ) : (
              <div className="empty-notice">
                <p>No skills listed yet.</p>
                <Link to="/profile" className="btn btn-outline btn-sm">
                  Add Skills
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Interests Card */}
        <div className="dashboard-card">
          <div className="card-header">
            <div className="card-icon">💡</div>
            <div>
              <h3>Interests ({interestsList.length})</h3>
              <p>Topics you want to explore</p>
            </div>
          </div>
          <div className="card-body">
            {interestsList.length > 0 ? (
              <div className="tags-container">
                {interestsList.map((interest, index) => (
                  <span key={index} className="tag tag-interest">
                    {interest}
                  </span>
                ))}
              </div>
            ) : (
              <div className="empty-notice">
                <p>No interests added yet.</p>
                <Link to="/profile" className="btn btn-outline btn-sm">
                  Add Interests
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Architecture Roadmap Info */}
      <section className="architecture-section">
        <div className="arch-card">
          <div className="arch-header">
            <span className="arch-icon">🤖</span>
            <div>
              <h3>AI Multi-Agent System Architecture</h3>
              <p>Platform Core &amp; Upcoming Modules (from PRD v2.0)</p>
            </div>
          </div>
          <div className="agents-grid">
            <div className="agent-item active">
              <span className="agent-badge">Phase 1 (Active)</span>
              <h4>Django Auth &amp; Profile API</h4>
              <p>Secure JWT session, AbstractUser, and Profile data store</p>
            </div>
            <div className="agent-item active">
              <span className="agent-badge">Phase 2 (Active)</span>
              <h4>Supervisor &amp; Career Agent</h4>
              <p>LangGraph orchestration &amp; personalized career trajectory matching</p>
            </div>
            <div className="agent-item upcoming">
              <span className="agent-badge">Phase 2</span>
              <h4>Skill Gap &amp; Roadmap Agent</h4>
              <p>Adaptive timelines and dynamic learning tasks</p>
            </div>
            <div className="agent-item upcoming">
              <span className="agent-badge">Phase 3-4</span>
              <h4>Resume, Interview &amp; RAG</h4>
              <p>Document ingestion, ChromaDB vector search &amp; mock interviews</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
