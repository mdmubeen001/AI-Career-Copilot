import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { careerService } from '../services/careerService';
import { resumeService } from '../services/resumeService';
import { formatApiError } from '../utils/errorHandler';

export default function ResumeAnalyzer() {
  const { user } = useAuth();

  // Target role context
  const [targetRole, setTargetRole] = useState('');
  const [customRoleInput, setCustomRoleInput] = useState('');

  // Upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  // Resumes list and active resume state
  const [resumes, setResumes] = useState([]);
  const [activeResumeId, setActiveResumeId] = useState(null);
  const [activeResume, setActiveResume] = useState(null);
  const [showRawText, setShowRawText] = useState(false);

  // Status & Feedback
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const fileInputRef = useRef(null);

  // Fetch full details of an active resume
  const fetchResumeDetails = useCallback(async (id) => {
    try {
      const data = await resumeService.getResume(id);
      setActiveResume(data);
      if (data.analysis?.target_role) {
        setTargetRole(data.analysis.target_role);
        setCustomRoleInput(data.analysis.target_role);
      }
    } catch (err) {
      setErrorMsg(formatApiError(err));
    }
  }, []);

  // Fetch initial data: user career profile and existing resumes
  useEffect(() => {
    let isMounted = true;

    async function initPage() {
      try {
        setLoadingInitial(true);
        setErrorMsg('');

        const [careerProfile, userResumes] = await Promise.all([
          careerService.getCareerProfile().catch(() => ({})),
          resumeService.getResumes().catch(() => []),
        ]);

        if (!isMounted) return;

        const defaultGoal = careerProfile.target_role || 'Full Stack Engineer';
        setTargetRole(defaultGoal);
        setCustomRoleInput(defaultGoal);

        const resumeList = Array.isArray(userResumes) ? userResumes : [];
        setResumes(resumeList);

        if (resumeList.length > 0) {
          const firstId = resumeList[0].id;
          setActiveResumeId(firstId);
          fetchResumeDetails(firstId);
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
  }, [user, fetchResumeDetails]);

  const handleSelectResume = (id) => {
    setActiveResumeId(id);
    setErrorMsg('');
    setSuccessMsg('');
    fetchResumeDetails(id);
  };

  // Drag and drop handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateFile = (file) => {
    if (!file) return false;
    const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const ext = file.name.split('.').pop().toLowerCase();

    if (!['pdf', 'docx'].includes(ext) && !allowed.includes(file.type)) {
      setErrorMsg('Invalid file format. Only PDF (.pdf) and Microsoft Word (.docx) documents are supported.');
      return false;
    }

    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      setErrorMsg('File size exceeds the 5MB maximum limit. Please upload a smaller document.');
      return false;
    }

    setErrorMsg('');
    return true;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  // Upload and analyze flow
  const handleUploadAndAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!selectedFile) {
      setErrorMsg('Please select a resume file (.pdf or .docx) to upload.');
      return;
    }

    const roleToUse = customRoleInput.trim() || targetRole || 'Software Engineer';

    try {
      setUploading(true);
      setAnalyzing(true);
      setErrorMsg('');
      setSuccessMsg('');

      const result = await resumeService.uploadResume(selectedFile, roleToUse, true);

      // Refresh list
      const updatedList = await resumeService.getResumes();
      setResumes(updatedList);
      setActiveResumeId(result.id);
      setActiveResume(result);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';

      setSuccessMsg(`Resume "${result.original_filename}" parsed and analyzed successfully!`);
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setUploading(false);
      setAnalyzing(false);
    }
  };

  // Re-run analysis on active resume with customized role
  const handleReanalyze = async (e) => {
    if (e) e.preventDefault();
    if (!activeResumeId) return;

    const roleToUse = customRoleInput.trim() || targetRole || 'Software Engineer';

    try {
      setAnalyzing(true);
      setErrorMsg('');
      setSuccessMsg('');

      await resumeService.analyzeResume(activeResumeId, roleToUse);
      await fetchResumeDetails(activeResumeId);

      // Refresh list to update ATS score badge
      const updatedList = await resumeService.getResumes();
      setResumes(updatedList);

      setSuccessMsg(`ATS Evaluation re-calculated for target role "${roleToUse}"!`);
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setAnalyzing(false);
    }
  };

  // Delete resume
  const handleDeleteResume = async (id, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) return;

    try {
      setErrorMsg('');
      await resumeService.deleteResume(id);

      const updatedList = resumes.filter((r) => r.id !== id);
      setResumes(updatedList);

      if (activeResumeId === id) {
        if (updatedList.length > 0) {
          setActiveResumeId(updatedList[0].id);
          fetchResumeDetails(updatedList[0].id);
        } else {
          setActiveResumeId(null);
          setActiveResume(null);
        }
      }
      setSuccessMsg('Resume removed successfully.');
    } catch (err) {
      setErrorMsg(formatApiError(err));
    }
  };

  // Helper for ATS score color styles
  const getScoreColorClass = (score) => {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Strong ATS Alignment';
    if (score >= 60) return 'Moderate Keyword Fit';
    return 'Keyword Optimization Needed';
  };

  if (loadingInitial) {
    return (
      <div className="resume-analyzer-page">
        <div className="loading-container">
          <div className="cyber-spinner"></div>
          <p>Loading Resume Analyzer environment...</p>
        </div>
      </div>
    );
  }

  const analysis = activeResume?.analysis;

  return (
    <div className="resume-analyzer-page">
      {/* Page Header */}
      <header className="page-header">
        <div className="header-breadcrumbs">
          <Link to="/dashboard">Dashboard</Link>
          <span className="separator">/</span>
          <span className="current">Resume Analyzer</span>
        </div>
        <div className="header-title-row">
          <div>
            <div className="status-chip mb-2">
              <span className="status-dot"></span> Phase 3 — Document Intelligence
            </div>
            <h1>AI Resume &amp; ATS Compatibility Analyzer</h1>
            <p className="header-subtitle">
              Upload your resume in PDF or DOCX format to receive estimated ATS compatibility scoring,
              skill detection, gap identification, and tailored keyword recommendations.
            </p>
          </div>
        </div>
      </header>

      {/* Mandatory ATS AI Estimation Notice */}
      <div className="ats-disclaimer-banner">
        <div className="disclaimer-icon">ℹ️</div>
        <div className="disclaimer-content">
          <h4>AI-Estimated ATS Benchmark Notice</h4>
          <p>
            The ATS compatibility score and section evaluations provided here are <strong>AI-generated estimates</strong> designed
            to help you benchmark your resume keywords against modern industry job requirements. They do not represent
            an official or proprietary algorithm of any specific applicant tracking system or employer.
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

      {/* Top Grid: Upload Card & Target Role Customizer */}
      <div className="resume-top-grid">
        {/* Upload Card */}
        <div className="dashboard-card upload-card">
          <div className="card-header">
            <div className="card-icon">📄</div>
            <div>
              <h3>Upload Resume</h3>
              <p>Supports .PDF and .DOCX up to 5MB</p>
            </div>
          </div>

          <form onSubmit={handleUploadAndAnalyze} className="upload-form">
            <div
              className={`dropzone-container ${dragActive ? 'active' : ''} ${selectedFile ? 'has-file' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />

              {selectedFile ? (
                <div className="selected-file-info">
                  <span className="file-icon">{selectedFile.name.endsWith('.docx') ? '📝' : '📑'}</span>
                  <div className="file-details">
                    <span className="file-name">{selectedFile.name}</span>
                    <span className="file-meta">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.name.split('.').pop().toUpperCase()}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="btn btn-outline-danger btn-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(null);
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }}
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="dropzone-prompt">
                  <div className="dropzone-icon">☁️</div>
                  <p className="dropzone-text">
                    <strong>Drag and drop</strong> your resume here, or <span>browse files</span>
                  </p>
                  <span className="dropzone-hint">Accepted formats: PDF or Word DOCX (selectable text)</span>
                </div>
              )}
            </div>

            <div className="target-role-bar">
              <label htmlFor="targetRoleInput" className="role-label">
                Target Role for ATS Keyword Matching:
              </label>
              <div className="role-input-group">
                <input
                  id="targetRoleInput"
                  type="text"
                  className="form-control"
                  placeholder="e.g. Senior Full Stack Engineer, DevOps Engineer"
                  value={customRoleInput}
                  onChange={(e) => setCustomRoleInput(e.target.value)}
                  disabled={uploading || analyzing}
                />
              </div>
            </div>

            <div className="upload-actions">
              <button
                type="submit"
                className="btn btn-primary btn-block"
                disabled={!selectedFile || uploading || analyzing}
              >
                {uploading || analyzing ? (
                  <>
                    <span className="spinner-inline"></span> Parsing &amp; Analyzing Resume...
                  </>
                ) : (
                  '🚀 Upload &amp; Analyze Resume'
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Resumes Library / Switcher */}
        <div className="dashboard-card resumes-library-card">
          <div className="card-header">
            <div className="card-icon">🗂️</div>
            <div>
              <h3>Your Resumes ({resumes.length})</h3>
              <p>Select a document to inspect or re-evaluate</p>
            </div>
          </div>

          <div className="card-body">
            {resumes.length === 0 ? (
              <div className="empty-notice py-4">
                <p>No resumes uploaded yet.</p>
                <span className="text-muted">Upload a resume above to unlock AI ATS analysis.</span>
              </div>
            ) : (
              <div className="resumes-list">
                {resumes.map((item) => {
                  const isCurrent = item.id === activeResumeId;
                  const dateStr = item.uploaded_at ? new Date(item.uploaded_at).toLocaleDateString() : '';
                  const score = item.ats_score_estimate;

                  return (
                    <div
                      key={item.id}
                      className={`resume-list-item ${isCurrent ? 'active' : ''}`}
                      onClick={() => handleSelectResume(item.id)}
                    >
                      <div className="item-main">
                        <span className="item-icon">{item.file_type === 'docx' ? '📝' : '📑'}</span>
                        <div className="item-meta">
                          <span className="item-name" title={item.original_filename}>
                            {item.original_filename}
                          </span>
                          <span className="item-sub">
                            Uploaded {dateStr} • {(item.file_size / 1024).toFixed(0)} KB
                          </span>
                        </div>
                      </div>

                      <div className="item-actions">
                        {score !== null && score !== undefined && (
                          <span className={`score-badge ${getScoreColorClass(score)}`}>
                            {score}% ATS
                          </span>
                        )}
                        <button
                          type="button"
                          className="btn-icon-danger"
                          title="Delete Resume"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteResume(item.id, item.original_filename);
                          }}
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Analysis Results View */}
      {activeResume && (
        <section className="resume-analysis-container mt-4">
          {/* Active Resume Sub-header */}
          <div className="active-resume-banner">
            <div className="banner-left">
              <span className="badge badge-primary">{activeResume.file_type?.toUpperCase()}</span>
              <h2>{activeResume.original_filename}</h2>
            </div>
            <div className="banner-actions">
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => setShowRawText(!showRawText)}
              >
                {showRawText ? 'Hide Parsed Text' : '🔍 View Parsed ATS Text'}
              </button>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={handleReanalyze}
                disabled={analyzing}
              >
                {analyzing ? (
                  <>
                    <span className="spinner-inline"></span> Re-evaluating...
                  </>
                ) : (
                  '🔄 Re-evaluate ATS Score'
                )}
              </button>
            </div>
          </div>

          {/* Raw Text Accordion */}
          {showRawText && (
            <div className="raw-text-viewer dashboard-card mt-3">
              <div className="viewer-header">
                <h4>Extracted Plain Text (What ATS Parsers See)</h4>
                <span className="text-muted">{activeResume.extracted_text?.length || 0} characters</span>
              </div>
              <pre className="raw-text-content">{activeResume.extracted_text || 'No text extracted.'}</pre>
            </div>
          )}

          {/* Analysis Content or Empty Prompt */}
          {analysis ? (
            <div className="analysis-dashboard-grid mt-4">
              {/* ATS Score & Overview Card */}
              <div className="dashboard-card score-overview-card">
                <div className="score-flex-row">
                  <div className={`ats-gauge-circle ${getScoreColorClass(analysis.ats_score_estimate)}`}>
                    <span className="gauge-number">{analysis.ats_score_estimate}%</span>
                    <span className="gauge-label">ATS ESTIMATE</span>
                  </div>
                  <div className="score-details-col">
                    <div className="badge-role-tag">
                      Target Role: <strong>{analysis.target_role || targetRole || 'General Tech'}</strong>
                    </div>
                    <h3 className={getScoreColorClass(analysis.ats_score_estimate)}>
                      {getScoreLabel(analysis.ats_score_estimate)}
                    </h3>
                    <p className="score-summary-text">{analysis.summary}</p>
                  </div>
                </div>
              </div>

              {/* Skills Intelligence Grid */}
              <div className="skills-intelligence-grid">
                {/* Detected Competencies */}
                <div className="dashboard-card skills-card">
                  <div className="card-header">
                    <div className="card-icon">✅</div>
                    <div>
                      <h3>Detected Skills ({analysis.detected_skills?.length || 0})</h3>
                      <p>Found in your resume keywords</p>
                    </div>
                  </div>
                  <div className="card-body">
                    {analysis.detected_skills && analysis.detected_skills.length > 0 ? (
                      <div className="tags-container">
                        {analysis.detected_skills.map((skill, idx) => (
                          <span key={idx} className="tag tag-skill-detected">
                            ✓ {skill}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted">No specific technical keywords detected.</p>
                    )}
                  </div>
                </div>

                {/* Missing / High-Impact Keywords */}
                <div className="dashboard-card skills-card">
                  <div className="card-header">
                    <div className="card-icon">⚡</div>
                    <div>
                      <h3>Missing Keywords ({analysis.missing_skills?.length || 0})</h3>
                      <p>Recommended for {analysis.target_role || 'Target Role'}</p>
                    </div>
                  </div>
                  <div className="card-body">
                    {analysis.missing_skills && analysis.missing_skills.length > 0 ? (
                      <div className="tags-container">
                        {analysis.missing_skills.map((skill, idx) => (
                          <span key={idx} className="tag tag-skill-missing">
                            + {skill}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted">High keyword coverage! All target benchmark competencies present.</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Strengths & Weaknesses Grid */}
              <div className="strengths-weaknesses-grid">
                {/* Strengths Card */}
                <div className="dashboard-card strengths-card">
                  <div className="card-header">
                    <div className="card-icon text-emerald">💪</div>
                    <div>
                      <h3>Resume Strengths</h3>
                      <p>High-scoring resume attributes</p>
                    </div>
                  </div>
                  <div className="card-body">
                    <ul className="attribute-list">
                      {analysis.strengths?.map((item, idx) => (
                        <li key={idx} className="strength-item">
                          <span className="item-bullet">✓</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Weaknesses / Improvements Card */}
                <div className="dashboard-card weaknesses-card">
                  <div className="card-header">
                    <div className="card-icon text-rose">🎯</div>
                    <div>
                      <h3>Areas for Improvement</h3>
                      <p>Vulnerabilities that lower parsing score</p>
                    </div>
                  </div>
                  <div className="card-body">
                    <ul className="attribute-list">
                      {analysis.weaknesses?.map((item, idx) => (
                        <li key={idx} className="weakness-item">
                          <span className="item-bullet">!</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Section-by-Section Evaluations */}
              <div className="dashboard-card sections-eval-card">
                <div className="card-header">
                  <div className="card-icon">📋</div>
                  <div>
                    <h3>Section Breakdown &amp; Content Evaluation</h3>
                    <p>Analysis of experience, education, and technical projects</p>
                  </div>
                </div>
                <div className="card-body">
                  <div className="section-eval-grid">
                    <div className="section-eval-item">
                      <div className="eval-title">
                        <span className="eval-icon">💼</span>
                        <h4>Experience Summary</h4>
                      </div>
                      <p>{analysis.experience_summary || 'Experience evaluation unavailable.'}</p>
                    </div>

                    <div className="section-eval-item">
                      <div className="eval-title">
                        <span className="eval-icon">🎓</span>
                        <h4>Education Summary</h4>
                      </div>
                      <p>{analysis.education_summary || 'Education credentials evaluation unavailable.'}</p>
                    </div>

                    <div className="section-eval-item">
                      <div className="eval-title">
                        <span className="eval-icon">🚀</span>
                        <h4>Projects Summary</h4>
                      </div>
                      <p>{analysis.project_summary || 'Projects evaluation unavailable.'}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actionable Recommendations */}
              <div className="dashboard-card recommendations-card">
                <div className="card-header">
                  <div className="card-icon">💡</div>
                  <div>
                    <h3>Actionable Recommendations for ATS Optimization</h3>
                    <p>Step-by-step guidance to raise your resume score</p>
                  </div>
                </div>
                <div className="card-body">
                  <div className="recommendations-list">
                    {analysis.recommendations?.map((rec, idx) => (
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
          ) : (
            <div className="dashboard-card text-center py-5 mt-4">
              <div className="empty-state-icon">🤖</div>
              <h3>Resume Ready for AI Analysis</h3>
              <p className="text-muted max-w-md mx-auto mb-4">
                We have extracted the plain text from <strong>{activeResume.original_filename}</strong>.
                Click below to compute the ATS compatibility evaluation.
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleReanalyze}
                disabled={analyzing}
              >
                {analyzing ? 'Computing ATS Score...' : 'Run ATS Evaluation Now'}
              </button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
