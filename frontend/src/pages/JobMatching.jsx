import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { jobService } from '../services/jobService';
import { resumeService } from '../services/resumeService';
import { formatApiError } from '../utils/errorHandler';

export default function JobMatching() {
  const { user } = useAuth();

  // Job Form State
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [description, setDescription] = useState('');

  // Saved Jobs & Active Job State
  const [savedJobs, setSavedJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);

  // Resumes State
  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState(null);

  // Matches State
  const [matches, setMatches] = useState([]);
  const [currentMatch, setCurrentMatch] = useState(null);

  // Processing & Feedback States
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [savingJob, setSavingJob] = useState(false);
  const [matching, setMatching] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Fetch match details by ID
  const handleViewMatchDetails = useCallback(async (matchId) => {
    try {
      setErrorMsg('');
      const data = await jobService.getJobMatch(matchId);
      setCurrentMatch(data);
      // Scroll to results section smoothly
      const resultsEl = document.getElementById('match-results-section');
      if (resultsEl) {
        resultsEl.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (err) {
      setErrorMsg(formatApiError(err));
    }
  }, []);

  // Fetch initial data: saved jobs, resumes, match history
  useEffect(() => {
    let isMounted = true;

    async function initPage() {
      try {
        setLoadingInitial(true);
        setErrorMsg('');

        const [jobsData, resumesData, matchesData] = await Promise.all([
          jobService.getJobDescriptions().catch(() => []),
          resumeService.getResumes().catch(() => []),
          jobService.getJobMatches().catch(() => []),
        ]);

        if (!isMounted) return;

        const jobList = Array.isArray(jobsData) ? jobsData : [];
        const resumeList = Array.isArray(resumesData) ? resumesData : [];
        const matchList = Array.isArray(matchesData) ? matchesData : [];

        setSavedJobs(jobList);
        setResumes(resumeList);
        setMatches(matchList);

        if (jobList.length > 0) {
          setSelectedJobId(jobList[0].id);
          setJobTitle(jobList[0].title);
          setCompany(jobList[0].company || '');
          setSourceUrl(jobList[0].source_url || '');
          setDescription(jobList[0].description);
        }

        if (resumeList.length > 0) {
          setSelectedResumeId(resumeList[0].id);
        }

        if (matchList.length > 0) {
          handleViewMatchDetails(matchList[0].id);
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
  }, [user, handleViewMatchDetails]);

  // Handle selecting an existing saved job description
  const handleSelectJob = (job) => {
    setSelectedJobId(job.id);
    setJobTitle(job.title);
    setCompany(job.company || '');
    setSourceUrl(job.source_url || '');
    setDescription(job.description);
    setErrorMsg('');
    setSuccessMsg('');
  };

  // Clear form to create a new job description
  const handleClearForm = () => {
    setSelectedJobId(null);
    setJobTitle('');
    setCompany('');
    setSourceUrl('');
    setDescription('');
    setErrorMsg('');
    setSuccessMsg('');
  };

  // Save new or update job description
  const handleSaveJob = async (e) => {
    if (e) e.preventDefault();

    if (!jobTitle.trim()) {
      setErrorMsg('Please provide a job title.');
      return;
    }
    if (!description.trim() || description.trim().length < 20) {
      setErrorMsg('Job description must be at least 20 characters long.');
      return;
    }

    try {
      setSavingJob(true);
      setErrorMsg('');
      setSuccessMsg('');

      const payload = {
        title: jobTitle.trim(),
        company: company.trim() || null,
        source_url: sourceUrl.trim() || null,
        description: description.trim(),
      };

      const newJob = await jobService.createJobDescription(payload);
      const updatedJobs = [newJob, ...savedJobs.filter((j) => j.id !== newJob.id)];
      setSavedJobs(updatedJobs);
      setSelectedJobId(newJob.id);
      setSuccessMsg(`Job description "${newJob.title}" saved successfully!`);
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setSavingJob(false);
    }
  };

  // Delete saved job description
  const handleDeleteJob = async (jobId, title) => {
    if (!window.confirm(`Are you sure you want to delete "${title}"?`)) return;

    try {
      setErrorMsg('');
      await jobService.deleteJobDescription(jobId);
      const remainingJobs = savedJobs.filter((j) => j.id !== jobId);
      setSavedJobs(remainingJobs);

      if (selectedJobId === jobId) {
        if (remainingJobs.length > 0) {
          handleSelectJob(remainingJobs[0]);
        } else {
          handleClearForm();
        }
      }
      setSuccessMsg(`Job "${title}" deleted.`);
    } catch (err) {
      setErrorMsg(formatApiError(err));
    }
  };

  // Trigger Job Matching Analysis
  const handleAnalyzeMatch = async (e) => {
    if (e) e.preventDefault();

    if (!selectedResumeId) {
      setErrorMsg('Please select an uploaded resume to evaluate.');
      return;
    }

    let activeJobId = selectedJobId;

    // If job is not saved yet, save it first
    if (!activeJobId) {
      if (!jobTitle.trim()) {
        setErrorMsg('Please enter a job title before matching.');
        return;
      }
      if (!description.trim() || description.trim().length < 20) {
        setErrorMsg('Please provide a job description of at least 20 characters.');
        return;
      }

      try {
        setSavingJob(true);
        const payload = {
          title: jobTitle.trim(),
          company: company.trim() || null,
          source_url: sourceUrl.trim() || null,
          description: description.trim(),
        };
        const saved = await jobService.createJobDescription(payload);
        setSavedJobs((prev) => [saved, ...prev]);
        setSelectedJobId(saved.id);
        activeJobId = saved.id;
      } catch (err) {
        setErrorMsg(formatApiError(err));
        setSavingJob(false);
        return;
      } finally {
        setSavingJob(false);
      }
    }

    try {
      setMatching(true);
      setErrorMsg('');
      setSuccessMsg('');

      const result = await jobService.matchJob(activeJobId, selectedResumeId);
      setCurrentMatch(result);

      // Refresh matches history
      const updatedMatches = await jobService.getJobMatches();
      setMatches(updatedMatches);

      setSuccessMsg(`Job match evaluation generated! Score: ${result.match_score_estimate}%.`);

      // Scroll to result
      setTimeout(() => {
        const resultsEl = document.getElementById('match-results-section');
        if (resultsEl) {
          resultsEl.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setMatching(false);
    }
  };

  const getScoreColorClass = (score) => {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Strong Role Fit';
    if (score >= 60) return 'Moderate Role Alignment';
    return 'Skills Gap Detected';
  };

  if (loadingInitial) {
    return (
      <div className="job-matching-page">
        <div className="loading-container">
          <div className="cyber-spinner"></div>
          <p>Loading Job Matching workspace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="job-matching-page">
      {/* Page Header */}
      <header className="page-header">
        <div className="header-breadcrumbs">
          <Link to="/dashboard">Dashboard</Link>
          <span className="separator">/</span>
          <span className="current">Job Matching</span>
        </div>
        <div className="header-title-row">
          <div>
            <div className="status-chip mb-2">
              <span className="status-dot"></span> Phase 4 — Job Intelligence &amp; Matching
            </div>
            <h1>AI Job Matching &amp; Alignment</h1>
            <p className="header-subtitle">
              Benchmark your resume and competencies against any target job description. Receive simulated AI match scores,
              skill overlap analysis, keyword gaps, and tailored recommendations.
            </p>
          </div>
        </div>
      </header>

      {/* Mandatory AI Estimation Disclaimer Notice */}
      <div className="ats-disclaimer-banner">
        <div className="disclaimer-icon">ℹ️</div>
        <div className="disclaimer-content">
          <h4>AI-Estimated Match Benchmark Notice</h4>
          <p>
            The Match Score Estimate is an <strong>AI-generated compatibility simulation</strong> designed to help you benchmark
            your resume keywords and experience against a job description. It is not an official ATS algorithm or guaranteed hiring probability score.
          </p>
        </div>
      </div>

      {/* Feedback Alerts */}
      {errorMsg && (
        <div className="alert alert-danger mb-4">
          <span className="alert-icon">⚠️</span>
          <div className="alert-text">{errorMsg}</div>
          <button type="button" className="alert-close" onClick={() => setErrorMsg('')}>×</button>
        </div>
      )}

      {successMsg && (
        <div className="alert alert-success mb-4">
          <span className="alert-icon">✓</span>
          <div className="alert-text">{successMsg}</div>
          <button type="button" className="alert-close" onClick={() => setSuccessMsg('')}>×</button>
        </div>
      )}

      {/* Two Column Setup Grid: Job Description & Resume Selector */}
      <div className="job-matching-setup-grid">
        {/* Left Column: Job Description Input & Library */}
        <div className="dashboard-card job-description-card">
          <div className="card-header">
            <div className="card-icon">💼</div>
            <div>
              <h3>1. Target Job Description</h3>
              <p>Paste a job posting or select a previously saved opportunity</p>
            </div>
          </div>

          <div className="card-body">
            {/* Quick Switcher for Saved Jobs */}
            {savedJobs.length > 0 && (
              <div className="saved-jobs-selector mb-3">
                <label className="text-secondary text-sm block mb-1">
                  Saved Jobs ({savedJobs.length}):
                </label>
                <div className="saved-jobs-pills">
                  {savedJobs.map((j) => (
                    <button
                      key={j.id}
                      type="button"
                      className={`saved-job-pill ${selectedJobId === j.id ? 'active' : ''}`}
                      onClick={() => handleSelectJob(j)}
                    >
                      <span className="pill-title">{j.title}</span>
                      {j.company && <span className="pill-company">@{j.company}</span>}
                    </button>
                  ))}
                  <button
                    type="button"
                    className="saved-job-pill new-job-pill"
                    onClick={handleClearForm}
                  >
                    + New Job
                  </button>
                </div>
              </div>
            )}

            <form onSubmit={handleSaveJob} className="job-form">
              <div className="form-row">
                <div className="form-group flex-1">
                  <label htmlFor="jobTitleInput">Job Title *</label>
                  <input
                    id="jobTitleInput"
                    type="text"
                    className="form-control"
                    placeholder="e.g. Senior Python / Django Developer"
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group flex-1">
                  <label htmlFor="companyInput">Company / Organization</label>
                  <input
                    id="companyInput"
                    type="text"
                    className="form-control"
                    placeholder="e.g. Stripe, Acme Corp"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="sourceUrlInput">Job Posting URL (Optional)</label>
                <input
                  id="sourceUrlInput"
                  type="url"
                  className="form-control"
                  placeholder="https://company.com/careers/job-id"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="descriptionInput">
                  Job Description Text * <span className="text-muted text-xs">(Min 20 characters)</span>
                </label>
                <textarea
                  id="descriptionInput"
                  className="form-control"
                  rows={8}
                  placeholder="Paste the full job description, role requirements, qualifications, and stack requirements here..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                />
              </div>

              <div className="form-actions-split">
                <div className="actions-left">
                  <button
                    type="submit"
                    className="btn btn-outline btn-sm"
                    disabled={savingJob || !jobTitle.trim() || description.trim().length < 20}
                  >
                    {savingJob ? 'Saving Job...' : '💾 Save Job Description'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline-secondary btn-sm"
                    onClick={handleClearForm}
                  >
                    Clear
                  </button>
                </div>

                {selectedJobId && (
                  <button
                    type="button"
                    className="btn btn-outline-danger btn-sm"
                    onClick={() => handleDeleteJob(selectedJobId, jobTitle)}
                  >
                    Delete Job
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: Resume Selection & Trigger Action */}
        <div className="dashboard-card resume-selector-card">
          <div className="card-header">
            <div className="card-icon">📄</div>
            <div>
              <h3>2. Select Candidate Resume</h3>
              <p>Choose which uploaded resume to evaluate against this role</p>
            </div>
          </div>

          <div className="card-body">
            {resumes.length === 0 ? (
              <div className="empty-notice py-4">
                <div className="empty-state-icon">⚠️</div>
                <h4>No Resumes Uploaded Yet</h4>
                <p className="text-muted mb-3">
                  Upload a resume first in Resume Analyzer to evaluate job match alignment.
                </p>
                <Link to="/resume-analyzer" className="btn btn-primary btn-sm">
                  Upload a Resume in Resume Analyzer
                </Link>
              </div>
            ) : (
              <>
                <div className="resumes-selection-list mb-4">
                  {resumes.map((r) => {
                    const isSelected = r.id === selectedResumeId;
                    const dateStr = r.uploaded_at ? new Date(r.uploaded_at).toLocaleDateString() : '';

                    return (
                      <div
                        key={r.id}
                        className={`resume-select-item ${isSelected ? 'selected' : ''}`}
                        onClick={() => setSelectedResumeId(r.id)}
                      >
                        <div className="resume-radio">
                          <input
                            type="radio"
                            name="resumeSelection"
                            checked={isSelected}
                            onChange={() => setSelectedResumeId(r.id)}
                          />
                        </div>
                        <div className="resume-item-info">
                          <span className="resume-title" title={r.original_filename}>
                            {r.original_filename}
                          </span>
                          <span className="resume-sub">
                            Uploaded {dateStr} • {r.file_type?.toUpperCase()}
                          </span>
                        </div>
                        {r.ats_score_estimate !== null && r.ats_score_estimate !== undefined && (
                          <span className="badge badge-secondary">
                            {r.ats_score_estimate}% ATS
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="action-trigger-box">
                  <button
                    type="button"
                    className="btn btn-primary btn-block btn-lg"
                    onClick={handleAnalyzeMatch}
                    disabled={
                      matching ||
                      !selectedResumeId ||
                      (!selectedJobId && (!jobTitle.trim() || description.trim().length < 20))
                    }
                  >
                    {matching ? (
                      <>
                        <span className="spinner-inline"></span> Analyzing Job Match Alignment...
                      </>
                    ) : (
                      '🚀 Analyze Job Match'
                    )}
                  </button>
                  <span className="text-muted text-xs block text-center mt-2">
                    Compares skills, credentials, and experience against the target role requirements.
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Section 4: Match Results Section */}
      {currentMatch && (
        <section id="match-results-section" className="match-results-container mt-4">
          <div className="section-header-banner">
            <div>
              <span className="badge badge-primary">EVALUATION RESULT</span>
              <h2>{currentMatch.job_title} {currentMatch.company ? `@ ${currentMatch.company}` : ''}</h2>
              <p className="text-secondary text-sm">
                Evaluated against resume: <strong>{currentMatch.resume_filename}</strong>
              </p>
            </div>
            <div className="match-score-badge-header">
              <span className={`score-badge-large ${getScoreColorClass(currentMatch.match_score_estimate)}`}>
                {currentMatch.match_score_estimate}% MATCH
              </span>
            </div>
          </div>

          <div className="results-grid mt-4">
            {/* Score & Summary Card */}
            <div className="dashboard-card score-summary-card">
              <div className="score-flex-row">
                <div className={`ats-gauge-circle ${getScoreColorClass(currentMatch.match_score_estimate)}`}>
                  <span className="gauge-number">{currentMatch.match_score_estimate}%</span>
                  <span className="gauge-label">AI MATCH ESTIMATE</span>
                </div>
                <div className="score-details-col">
                  <h3 className={getScoreColorClass(currentMatch.match_score_estimate)}>
                    {getScoreLabel(currentMatch.match_score_estimate)}
                  </h3>
                  <p className="score-summary-text">{currentMatch.summary}</p>
                </div>
              </div>
            </div>

            {/* Skills Overlap & Gaps */}
            <div className="skills-intelligence-grid">
              {/* Matching Skills */}
              <div className="dashboard-card skills-card">
                <div className="card-header">
                  <div className="card-icon">✅</div>
                  <div>
                    <h3>Matching Skills ({currentMatch.matching_skills?.length || 0})</h3>
                    <p>Competencies verified in your resume and profile</p>
                  </div>
                </div>
                <div className="card-body">
                  {currentMatch.matching_skills && currentMatch.matching_skills.length > 0 ? (
                    <div className="tags-container">
                      {currentMatch.matching_skills.map((skill, idx) => (
                        <span key={idx} className="tag tag-skill-detected">
                          ✓ {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted text-sm">No direct keyword overlap detected.</p>
                  )}
                </div>
              </div>

              {/* Missing Skills */}
              <div className="dashboard-card skills-card">
                <div className="card-header">
                  <div className="card-icon">⚡</div>
                  <div>
                    <h3>Missing Requirements ({currentMatch.missing_skills?.length || 0})</h3>
                    <p>Demanded by this job posting but missing from resume</p>
                  </div>
                </div>
                <div className="card-body">
                  {currentMatch.missing_skills && currentMatch.missing_skills.length > 0 ? (
                    <div className="tags-container">
                      {currentMatch.missing_skills.map((skill, idx) => (
                        <span key={idx} className="tag tag-skill-missing">
                          + {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted text-sm">High coverage! All primary competencies were detected.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Strengths & Gaps */}
            <div className="strengths-weaknesses-grid">
              {/* Strengths Card */}
              <div className="dashboard-card strengths-card">
                <div className="card-header">
                  <div className="card-icon text-emerald">💪</div>
                  <div>
                    <h3>Candidate Strengths</h3>
                    <p>Where your background aligns with this role</p>
                  </div>
                </div>
                <div className="card-body">
                  <ul className="attribute-list">
                    {currentMatch.strengths?.map((item, idx) => (
                      <li key={idx} className="strength-item">
                        <span className="item-bullet">✓</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Gaps Card */}
              <div className="dashboard-card weaknesses-card">
                <div className="card-header">
                  <div className="card-icon text-rose">🎯</div>
                  <div>
                    <h3>Alignment Gaps</h3>
                    <p>Discrepancies to address in application or interview</p>
                  </div>
                </div>
                <div className="card-body">
                  <ul className="attribute-list">
                    {currentMatch.gaps?.map((item, idx) => (
                      <li key={idx} className="weakness-item">
                        <span className="item-bullet">!</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Actionable Recommendations */}
            <div className="dashboard-card recommendations-card">
              <div className="card-header">
                <div className="card-icon">💡</div>
                <div>
                  <h3>Actionable Recommendations for this Role</h3>
                  <p>Concrete steps to increase alignment and interview callbacks</p>
                </div>
              </div>
              <div className="card-body">
                <div className="recommendations-list">
                  {currentMatch.recommendations?.map((rec, idx) => (
                    <div key={idx} className="rec-step-card">
                      <div className="step-number">{idx + 1}</div>
                      <div className="step-content">
                        <p>{rec}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Section 5: Match History */}
      <section className="match-history-section mt-5">
        <div className="section-title-row mb-3">
          <div>
            <h3>Previous Job Matches ({matches.length})</h3>
            <p className="text-secondary text-sm">Review your past evaluations and tailored feedback</p>
          </div>
        </div>

        {matches.length === 0 ? (
          <div className="dashboard-card text-center py-4">
            <p className="text-muted">No previous matches found. Analyze your first job description above.</p>
          </div>
        ) : (
          <div className="matches-history-grid">
            {matches.map((m) => {
              const dateStr = m.created_at ? new Date(m.created_at).toLocaleDateString() : '';
              const isCurrent = currentMatch?.id === m.id;

              return (
                <div
                  key={m.id}
                  className={`dashboard-card match-history-item ${isCurrent ? 'active' : ''}`}
                >
                  <div className="item-header">
                    <div className="item-title-col">
                      <h4>{m.job_title}</h4>
                      <span className="item-company">{m.company || 'Direct Posting'}</span>
                    </div>
                    <span className={`score-badge ${getScoreColorClass(m.match_score_estimate)}`}>
                      {m.match_score_estimate}%
                    </span>
                  </div>
                  <div className="item-body">
                    <span className="text-muted text-xs block mb-3">
                      Resume: {m.resume_filename} • Evaluated {dateStr}
                    </span>
                    <button
                      type="button"
                      className="btn btn-outline btn-sm btn-block"
                      onClick={() => handleViewMatchDetails(m.id)}
                    >
                      View Result
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
