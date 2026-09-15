import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { careerService } from '../services/careerService';
import { profileService } from '../services/profileService';
import { formatApiError } from '../utils/errorHandler';

export default function CareerAnalysis() {
  const { user } = useAuth();

  // Profile Context State
  const [profileData, setProfileData] = useState({
    full_name: '',
    education: '',
    current_role: '',
    target_role: '',
    experience_level: '',
    skills: [],
  });

  // Analysis Form & Data State
  const [careerGoalInput, setCareerGoalInput] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Fetch candidate profile context and any existing analysis on mount
  useEffect(() => {
    let isMounted = true;

    async function initPage() {
      try {
        setLoadingInitial(true);
        setErrorMsg('');

        const [accProfile, carProfile, userSkills] = await Promise.all([
          profileService.getProfile().catch(() => ({})),
          careerService.getCareerProfile().catch(() => ({})),
          careerService.getUserSkills().catch(() => []),
        ]);

        if (!isMounted) return;

        const skillsList = Array.isArray(userSkills) && userSkills.length > 0
          ? userSkills.map((s) => s.skill_name || s.name)
          : (Array.isArray(accProfile.skills) ? accProfile.skills : []);

        const initialTargetGoal =
          carProfile.target_role || accProfile.career_goal || 'Full Stack Developer';

        setProfileData({
          full_name: accProfile.full_name || user?.full_name || '',
          education: accProfile.education || accProfile.degree || 'Not specified',
          current_role: carProfile.current_role || 'Not specified',
          target_role: initialTargetGoal,
          experience_level: carProfile.experience_level || 'Entry-level (0-2 years)',
          skills: skillsList,
        });

        setCareerGoalInput(initialTargetGoal);

        // Fetch latest analysis if previously run
        try {
          const latestAnalysis = await careerService.getLatestAnalysis();
          if (isMounted && latestAnalysis) {
            setAnalysis(latestAnalysis);
          }
        } catch {
          // No prior analysis exists yet, which is expected for new users
        }
      } catch (err) {
        if (!isMounted) return;
        setErrorMsg(formatApiError(err));
      } finally {
        if (isMounted) setLoadingInitial(false);
      }
    }

    initPage();

    return () => {
      isMounted = false;
    };
  }, [user]);

  const handleRunAnalysis = async (e) => {
    if (e) e.preventDefault();
    const goalToAnalyze = careerGoalInput.trim() || profileData.target_role || 'Full Stack Developer';

    try {
      setAnalyzing(true);
      setErrorMsg('');
      setSuccessMsg('');

      const result = await careerService.analyzeCareer({ career_goal: goalToAnalyze });
      setAnalysis(result);
      setSuccessMsg(`Career Analysis for '${result.career_goal}' generated successfully!`);
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setAnalyzing(false);
    }
  };

  const getReadinessColor = (score) => {
    if (score >= 75) return 'var(--accent-emerald)';
    if (score >= 50) return 'var(--accent-cyan)';
    return 'var(--accent-rose)';
  };

  const getReadinessLabel = (score) => {
    if (score >= 80) return 'High Trajectory Alignment';
    if (score >= 60) return 'Solid Foundation — Minor Gaps';
    if (score >= 40) return 'Emerging Readiness — Development Needed';
    return 'Early Exploration Stage';
  };

  if (loadingInitial) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading your career intelligence context...</p>
      </div>
    );
  }

  return (
    <div className="career-analysis-page">
      {/* Header Banner */}
      <div className="page-header-banner">
        <div className="badge-pill">
          <span className="dot-pulse"></span> Supervisor &amp; Career Analysis Agent
        </div>
        <h1>AI Career Trajectory &amp; Readiness Analysis</h1>
        <p>
          Our specialized Career Agent analyzes your current credentials, skill sets, and experience level
          against market demand to generate an accurate readiness rating and strategic roadmap.
        </p>
      </div>

      {errorMsg && (
        <div className="alert alert-error" role="alert">
          <span className="alert-icon">⚠️</span>
          <div className="alert-content">{errorMsg}</div>
        </div>
      )}

      {successMsg && (
        <div className="alert alert-success" role="alert">
          <span className="alert-icon">✅</span>
          <div className="alert-content">{successMsg}</div>
        </div>
      )}

      {/* Grid: Context Card & Analysis Trigger Form */}
      <div className="analysis-grid-top">
        {/* User Context Summary Card */}
        <div className="dashboard-card profile-summary-card">
          <div className="card-header">
            <div className="card-icon">👤</div>
            <div>
              <h3>Candidate Baseline Context</h3>
              <p>Current background used by the Career Agent</p>
            </div>
          </div>
          <div className="card-body">
            <div className="data-list">
              <div className="data-row">
                <span className="data-label">Candidate:</span>
                <span className="data-value">{profileData.full_name || user?.email}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Current Role:</span>
                <span className="data-value">{profileData.current_role}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Education:</span>
                <span className="data-value">{profileData.education}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Experience:</span>
                <span className="data-value">{profileData.experience_level}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Logged Skills ({profileData.skills.length}):</span>
                <div className="skills-inline-list">
                  {profileData.skills.length > 0 ? (
                    profileData.skills.map((s, idx) => (
                      <span key={idx} className="tag tag-skill tag-sm">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="data-value text-muted">No skills logged yet</span>
                  )}
                </div>
              </div>
            </div>
            <div className="card-footer-action">
              <Link to="/profile" className="btn btn-outline btn-sm">
                Update Skills &amp; Profile
              </Link>
            </div>
          </div>
        </div>

        {/* Trigger Analysis Card */}
        <div className="dashboard-card analysis-trigger-card">
          <div className="card-header">
            <div className="card-icon">⚡</div>
            <div>
              <h3>Target Role Evaluation</h3>
              <p>Specify the career goal you want to assess</p>
            </div>
          </div>
          <div className="card-body">
            <form onSubmit={handleRunAnalysis} className="analysis-form">
              <div className="form-group">
                <label htmlFor="career_goal">Target Career Goal / Role</label>
                <input
                  id="career_goal"
                  type="text"
                  value={careerGoalInput}
                  onChange={(e) => setCareerGoalInput(e.target.value)}
                  placeholder="e.g. Senior AI Systems Engineer, Full Stack Developer"
                  disabled={analyzing}
                  required
                />
                <span className="input-hint">
                  The Supervisor Agent will benchmark your skills against market requirements for this position.
                </span>
              </div>

              <div className="quick-suggestions">
                <span className="suggestion-label">Popular Goals:</span>
                {['Full Stack Developer', 'AI/ML Engineer', 'Backend Architect', 'Cloud DevOps Engineer'].map(
                  (goal) => (
                    <button
                      key={goal}
                      type="button"
                      className="suggestion-chip"
                      onClick={() => setCareerGoalInput(goal)}
                      disabled={analyzing}
                    >
                      {goal}
                    </button>
                  )
                )}
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block btn-lg"
                disabled={analyzing || !careerGoalInput.trim()}
              >
                {analyzing ? (
                  <span className="btn-loading">
                    <span className="spinner-sm"></span> Career Agent Analyzing...
                  </span>
                ) : (
                  '🚀 Analyze My Career'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Analysis Results Display */}
      {analysis && (
        <div className="analysis-results-container">
          {/* Readiness Score Banner */}
          <div className="readiness-banner">
            <div className="readiness-score-box">
              <span className="score-number" style={{ color: getReadinessColor(analysis.career_readiness) }}>
                {analysis.career_readiness}%
              </span>
              <span className="score-subtext">Career Readiness</span>
            </div>

            <div className="readiness-details">
              <div className="readiness-tag" style={{ borderColor: getReadinessColor(analysis.career_readiness), color: getReadinessColor(analysis.career_readiness) }}>
                {getReadinessLabel(analysis.career_readiness)}
              </div>
              <h2>Target: {analysis.career_goal}</h2>
              <div className="progress-bar-track">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${analysis.career_readiness}%`,
                    background: `linear-gradient(90deg, var(--accent-primary), ${getReadinessColor(analysis.career_readiness)})`,
                  }}
                ></div>
              </div>
              <p className="readiness-date">
                Evaluated:{' '}
                {analysis.created_at
                  ? `${new Date(analysis.created_at).toLocaleDateString()} at ${new Date(analysis.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
                  : 'Recent session'}
              </p>
            </div>
          </div>

          {/* Recommended Career Paths */}
          {analysis.recommended_paths && analysis.recommended_paths.length > 0 && (
            <div className="analysis-section-card">
              <div className="section-card-header">
                <span className="section-card-icon">🧭</span>
                <div>
                  <h3>Recommended &amp; Adjacent Career Paths</h3>
                  <p>Alternative trajectories aligned with your current competencies</p>
                </div>
              </div>
              <div className="paths-grid">
                {analysis.recommended_paths.map((path, idx) => (
                  <div key={idx} className="path-item">
                    <span className="path-bullet">⚡</span>
                    <span className="path-title">{path}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Strengths & Weaknesses 2-Column Grid */}
          <div className="sw-grid">
            {/* Strengths */}
            <div className="analysis-section-card strength-card">
              <div className="section-card-header">
                <span className="section-card-icon">💪</span>
                <div>
                  <h3>Demonstrated Strengths</h3>
                  <p>Core competencies in your candidate profile</p>
                </div>
              </div>
              <div className="sw-list">
                {analysis.strengths && analysis.strengths.length > 0 ? (
                  analysis.strengths.map((s, idx) => (
                    <div key={idx} className="sw-pill strength-pill">
                      <span className="pill-icon">✓</span>
                      <span>{s}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-muted">No specific strengths flagged.</p>
                )}
              </div>
            </div>

            {/* Weaknesses / Gaps */}
            <div className="analysis-section-card gap-card">
              <div className="section-card-header">
                <span className="section-card-icon">🎯</span>
                <div>
                  <h3>Skill &amp; Knowledge Gaps</h3>
                  <p>High-leverage areas to develop for this goal</p>
                </div>
              </div>
              <div className="sw-list">
                {analysis.weaknesses && analysis.weaknesses.length > 0 ? (
                  analysis.weaknesses.map((w, idx) => (
                    <div key={idx} className="sw-pill gap-pill">
                      <span className="pill-icon">!</span>
                      <span>{w}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-muted">No critical gaps detected.</p>
                )}
              </div>
            </div>
          </div>

          {/* AI Strategic Reasoning & Commentary */}
          {analysis.analysis && (
            <div className="analysis-section-card">
              <div className="section-card-header">
                <span className="section-card-icon">🤖</span>
                <div>
                  <h3>Career Agent Analysis &amp; Strategic Reasoning</h3>
                  <p>Autonomous multi-agent evaluation breakdown</p>
                </div>
              </div>
              <div className="narrative-box">
                <p>{analysis.analysis}</p>
              </div>
            </div>
          )}

          {/* Recommended Next Actions */}
          {analysis.next_actions && analysis.next_actions.length > 0 && (
            <div className="analysis-section-card">
              <div className="section-card-header">
                <span className="section-card-icon">📋</span>
                <div>
                  <h3>Recommended Strategic Next Actions</h3>
                  <p>Concrete steps recommended by the Supervisor Agent to elevate readiness</p>
                </div>
              </div>
              <div className="actions-list">
                {analysis.next_actions.map((act, idx) => (
                  <div key={idx} className="action-item">
                    <span className="action-step-number">{idx + 1}</span>
                    <span className="action-text">{act}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
