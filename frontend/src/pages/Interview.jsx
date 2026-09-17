import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { interviewService } from '../services/interviewService';
import { resumeService } from '../services/resumeService';
import { formatApiError } from '../utils/errorHandler';

export default function Interview() {
  const { profile } = useAuth();

  // Navigation / Mode: 'setup' | 'interview' | 'result'
  const [viewMode, setViewMode] = useState('setup');

  // Setup Form State
  const [targetRole, setTargetRole] = useState('');
  const [interviewType, setInterviewType] = useState('mixed');
  const [difficulty, setDifficulty] = useState('intermediate');
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [selectedResumeId, setSelectedResumeId] = useState('');

  // Available resumes & sessions history
  const [resumes, setResumes] = useState([]);
  const [historySessions, setHistorySessions] = useState([]);

  // Active Session State
  const [activeSession, setActiveSession] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // Active Question Answer & Evaluation State
  const [currentAnswerText, setCurrentAnswerText] = useState('');
  const [lastEvaluation, setLastEvaluation] = useState(null);

  // Final Result State
  const [sessionResult, setSessionResult] = useState(null);

  // Loading & Feedback States
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [startingSession, setStartingSession] = useState(false);
  const [evaluatingAnswer, setEvaluatingAnswer] = useState(false);
  const [completingSession, setCompletingSession] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Load Initial Data (Resumes + History)
  const loadInitialData = useCallback(async () => {
    try {
      setLoadingInitial(true);
      setErrorMsg('');

      const [resumesData, sessionsData] = await Promise.all([
        resumeService.getResumes().catch(() => []),
        interviewService.getInterviews().catch(() => []),
      ]);

      const resumeList = Array.isArray(resumesData) ? resumesData : [];
      setResumes(resumeList);
      if (resumeList.length > 0) {
        setSelectedResumeId((prev) => prev || resumeList[0].id);
      }

      const sessionList = Array.isArray(sessionsData) ? sessionsData : [];
      setHistorySessions(sessionList);

      setTargetRole((prev) => prev || profile?.career_goal || 'Python Django Developer');
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setLoadingInitial(false);
    }
  }, [profile]);

  useEffect(() => {
    let isMounted = true;

    async function initPage() {
      try {
        setLoadingInitial(true);
        setErrorMsg('');

        const [resumesData, sessionsData] = await Promise.all([
          resumeService.getResumes().catch(() => []),
          interviewService.getInterviews().catch(() => []),
        ]);

        if (!isMounted) return;

        const resumeList = Array.isArray(resumesData) ? resumesData : [];
        setResumes(resumeList);
        if (resumeList.length > 0) {
          setSelectedResumeId((prev) => prev || resumeList[0].id);
        }

        const sessionList = Array.isArray(sessionsData) ? sessionsData : [];
        setHistorySessions(sessionList);

        setTargetRole((prev) => prev || profile?.career_goal || 'Python Django Developer');
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
  }, [profile]);

  // Handle Starting a New Interview Session
  const handleStartInterview = async (e) => {
    e?.preventDefault();
    const cleanRole = targetRole.trim();
    if (!cleanRole) {
      setErrorMsg('Please specify a target role for your interview.');
      return;
    }

    try {
      setStartingSession(true);
      setErrorMsg('');
      setSuccessMsg('');

      // 1. Create session
      const payload = {
        target_role: cleanRole,
        interview_type: interviewType,
        difficulty,
        total_questions: Number(totalQuestions),
        resume_id: selectedResumeId ? Number(selectedResumeId) : null,
      };
      const createdSession = await interviewService.createInterview(payload);

      // 2. Start session (generate questions)
      const startedSession = await interviewService.startInterview(createdSession.id);
      setActiveSession(startedSession);

      // 3. Load questions
      const questionList = startedSession.questions || [];
      setQuestions(questionList);

      // Set index to first unanswered question
      const firstUnansweredIdx = questionList.findIndex((q) => !q.answer);
      const startIdx = firstUnansweredIdx !== -1 ? firstUnansweredIdx : 0;
      setCurrentQuestionIndex(startIdx);

      // Preload answer if already answered (resumed session)
      if (questionList[startIdx]?.answer) {
        setCurrentAnswerText(questionList[startIdx].answer.answer_text || '');
        setLastEvaluation(questionList[startIdx].answer);
      } else {
        setCurrentAnswerText('');
        setLastEvaluation(null);
      }

      setViewMode('interview');
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setStartingSession(false);
    }
  };

  // Resume an in-progress session or open a completed result
  const handleResumeSession = async (sessionId) => {
    try {
      setErrorMsg('');
      setStartingSession(true);

      const session = await interviewService.getInterview(sessionId);
      setActiveSession(session);

      if (session.status === 'completed') {
        const result = await interviewService.getInterviewResult(sessionId);
        setSessionResult(result);
        setViewMode('result');
        return;
      }

      // If not started yet, start it
      let activeSess = session;
      if (session.status === 'not_started') {
        activeSess = await interviewService.startInterview(sessionId);
      }

      const qList = await interviewService.getQuestions(sessionId);
      const questionList = Array.isArray(qList) ? qList : [];
      setQuestions(questionList);
      setActiveSession(activeSess);

      // Locate first unanswered question
      const firstUnansweredIdx = questionList.findIndex((q) => !q.answer);
      const startIdx = firstUnansweredIdx !== -1 ? firstUnansweredIdx : 0;
      setCurrentQuestionIndex(startIdx);

      if (questionList[startIdx]?.answer) {
        setCurrentAnswerText(questionList[startIdx].answer.answer_text || '');
        setLastEvaluation(questionList[startIdx].answer);
      } else {
        setCurrentAnswerText('');
        setLastEvaluation(null);
      }

      setViewMode('interview');
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setStartingSession(false);
    }
  };

  // View Results of a Completed Session
  const handleViewResult = async (sessionId) => {
    try {
      setErrorMsg('');
      setCompletingSession(true);
      const result = await interviewService.getInterviewResult(sessionId);
      setSessionResult(result);
      setViewMode('result');
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setCompletingSession(false);
    }
  };

  // Submit Answer to Current Question
  const handleSubmitAnswer = async () => {
    const cleanAnswer = currentAnswerText.trim();
    if (!cleanAnswer) {
      setErrorMsg('Please write an answer before submitting for evaluation.');
      return;
    }

    const currentQuestion = questions[currentQuestionIndex];
    if (!currentQuestion || !activeSession) return;

    try {
      setEvaluatingAnswer(true);
      setErrorMsg('');
      setSuccessMsg('');

      const response = await interviewService.submitAnswer(
        activeSession.id,
        currentQuestion.id,
        { answer_text: cleanAnswer }
      );

      const evaluatedAnswer = response.answer;
      setLastEvaluation(evaluatedAnswer);

      // Update question list in state
      setQuestions((prevQuestions) =>
        prevQuestions.map((q, idx) =>
          idx === currentQuestionIndex ? { ...q, answer: evaluatedAnswer } : q
        )
      );

      setSuccessMsg('Answer evaluated successfully by AI.');
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setEvaluatingAnswer(false);
    }
  };

  // Move to Next Question
  const handleNextQuestion = () => {
    setErrorMsg('');
    setSuccessMsg('');

    if (currentQuestionIndex < questions.length - 1) {
      const nextIdx = currentQuestionIndex + 1;
      setCurrentQuestionIndex(nextIdx);
      const nextQ = questions[nextIdx];
      if (nextQ?.answer) {
        setCurrentAnswerText(nextQ.answer.answer_text || '');
        setLastEvaluation(nextQ.answer);
      } else {
        setCurrentAnswerText('');
        setLastEvaluation(null);
      }
    } else {
      // Reached the end of questions
      handleFinishInterview();
    }
  };

  // Move to Previous Question
  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setErrorMsg('');
      setSuccessMsg('');
      const prevIdx = currentQuestionIndex - 1;
      setCurrentQuestionIndex(prevIdx);
      const prevQ = questions[prevIdx];
      if (prevQ?.answer) {
        setCurrentAnswerText(prevQ.answer.answer_text || '');
        setLastEvaluation(prevQ.answer);
      } else {
        setCurrentAnswerText('');
        setLastEvaluation(null);
      }
    }
  };

  // Complete Interview and Synthesize Results
  const handleFinishInterview = async () => {
    if (!activeSession) return;
    try {
      setCompletingSession(true);
      setErrorMsg('');
      const result = await interviewService.completeInterview(activeSession.id);
      setSessionResult(result);
      setViewMode('result');
      // Refresh history list in background
      interviewService.getInterviews().then((data) => {
        if (Array.isArray(data)) setHistorySessions(data);
      });
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setCompletingSession(false);
    }
  };

  // Helper: Return score badge color
  const getScoreColorClass = (score) => {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-mid';
    return 'score-low';
  };

  // Helper: Word count
  const wordCount = currentAnswerText
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;

  const currentQuestion = questions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === questions.length - 1;
  const allAnswered = questions.length > 0 && questions.every((q) => q.answer);

  return (
    <div className="interview-page">
      {/* Top Header Banner */}
      <section className="welcome-banner interview-header-banner">
        <div className="welcome-content">
          <div className="status-chip">
            <span className="status-dot"></span> Phase 5 — AI Interview Agent
          </div>
          <h1>
            Role-Specific <span className="highlight-text">Interview Practice</span>
          </h1>
          <p>
            Simulate realistic technical and behavioral interviews tailored to your target role.
            Receive instant, rubric-based AI evaluations with concrete strengths and improvement suggestions.
          </p>
        </div>

        {viewMode !== 'setup' && (
          <div className="welcome-actions">
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => {
                setViewMode('setup');
                loadInitialData();
              }}
            >
              ← Back to Setup &amp; History
            </button>
          </div>
        )}
      </section>

      {/* Global Alerts */}
      {errorMsg && (
        <div className="alert alert-danger" role="alert">
          <span className="alert-icon">⚠️</span>
          <span>{errorMsg}</span>
          <button
            type="button"
            className="alert-close"
            onClick={() => setErrorMsg('')}
            aria-label="Dismiss alert"
          >
            ×
          </button>
        </div>
      )}

      {successMsg && (
        <div className="alert alert-success" role="alert">
          <span className="alert-icon">✓</span>
          <span>{successMsg}</span>
        </div>
      )}

      {/* ==================================================================== */}
      {/* VIEW 1: SETUP & CONFIGURATION + HISTORY                              */}
      {/* ==================================================================== */}
      {viewMode === 'setup' && (
        <div className="interview-setup-layout">
          {/* Setup Card */}
          <div className="dashboard-card interview-setup-card">
            <div className="card-header">
              <div className="card-icon">🎙️</div>
              <div>
                <h3>Configure Your Practice Interview</h3>
                <p>Customize role, question focus, and difficulty level</p>
              </div>
            </div>

            <div className="card-body">
              <form onSubmit={handleStartInterview} className="interview-form">
                {/* Target Role Input */}
                <div className="form-group mb-4">
                  <label htmlFor="target-role-input" className="form-label">
                    Target Role / Job Title <span className="text-danger">*</span>
                  </label>
                  <input
                    id="target-role-input"
                    type="text"
                    className="form-control"
                    placeholder="e.g. Python Django Developer, Senior Frontend Engineer"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    required
                  />
                  <small className="form-help text-secondary">
                    Questions will be dynamically adapted to this domain and technology stack.
                  </small>
                </div>

                {/* Interview Type Selector */}
                <div className="form-group mb-4">
                  <label className="form-label">Interview Type</label>
                  <div className="pill-selector-group">
                    {[
                      { id: 'mixed', label: 'Mixed (Recommended)', desc: 'Technical, behavioral & situational scenarios' },
                      { id: 'technical', label: 'Technical Only', desc: 'Architecture, APIs, algorithms & code design' },
                      { id: 'behavioral', label: 'Behavioral Only', desc: 'Teamwork, leadership & STAR scenarios' },
                    ].map((item) => (
                      <button
                        type="button"
                        key={item.id}
                        className={`pill-option ${interviewType === item.id ? 'active' : ''}`}
                        onClick={() => setInterviewType(item.id)}
                      >
                        <span className="pill-title">{item.label}</span>
                        <span className="pill-subtitle">{item.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Difficulty Selector */}
                <div className="form-group mb-4">
                  <label className="form-label">Difficulty Level</label>
                  <div className="difficulty-toggle-group">
                    {[
                      { id: 'beginner', label: 'Beginner', badge: 'Junior / Intern' },
                      { id: 'intermediate', label: 'Intermediate', badge: 'Mid-Level / 2-5 YOE' },
                      { id: 'advanced', label: 'Advanced', badge: 'Senior / Staff / Lead' },
                    ].map((diff) => (
                      <button
                        type="button"
                        key={diff.id}
                        className={`diff-btn ${difficulty === diff.id ? 'active' : ''}`}
                        onClick={() => setDifficulty(diff.id)}
                      >
                        <span className="diff-name">{diff.label}</span>
                        <span className="diff-badge">{diff.badge}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Question Count & Resume Row */}
                <div className="form-row-grid mb-4">
                  {/* Total Questions */}
                  <div className="form-group">
                    <label className="form-label">Number of Questions</label>
                    <div className="questions-count-selector">
                      {[5, 10, 15].map((cnt) => (
                        <button
                          type="button"
                          key={cnt}
                          className={`count-chip ${Number(totalQuestions) === cnt ? 'active' : ''}`}
                          onClick={() => setTotalQuestions(cnt)}
                        >
                          {cnt} Questions
                        </button>
                      ))}
                      <input
                        type="number"
                        min="1"
                        max="20"
                        className="form-control count-custom-input"
                        placeholder="Custom"
                        value={totalQuestions}
                        onChange={(e) => setTotalQuestions(Math.max(1, Math.min(20, Number(e.target.value) || 1)))}
                        title="Enter 1 to 20 questions"
                      />
                    </div>
                  </div>

                  {/* Resume Selector */}
                  <div className="form-group">
                    <label htmlFor="resume-select" className="form-label">
                      Ground in Resume <span className="text-muted">(Optional)</span>
                    </label>
                    {resumes.length > 0 ? (
                      <select
                        id="resume-select"
                        className="form-control"
                        value={selectedResumeId}
                        onChange={(e) => setSelectedResumeId(e.target.value)}
                      >
                        <option value="">-- No Resume (Profile Only) --</option>
                        {resumes.map((res) => (
                          <option key={res.id} value={res.id}>
                            📄 {res.original_filename} ({res.file_type.toUpperCase()})
                          </option>
                        ))}
                      </select>
                    ) : (
                      <div className="resume-notice-box">
                        <span className="text-secondary text-sm">
                          No resumes uploaded yet.
                        </span>{' '}
                        <Link to="/resume-analyzer" className="link-accent text-sm">
                          Upload Resume →
                        </Link>
                      </div>
                    )}
                    <small className="form-help text-secondary">
                      Questions will incorporate projects and experience extracted from your selected document.
                    </small>
                  </div>
                </div>

                {/* Submit CTA */}
                <div className="form-actions-row">
                  <button
                    type="submit"
                    className="btn btn-primary btn-lg"
                    disabled={startingSession}
                  >
                    {startingSession ? (
                      <>
                        <span className="spinner-sm"></span> Generating AI Questions...
                      </>
                    ) : (
                      <>🚀 Start Interview</>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Previous Sessions History Section */}
          <section className="interview-history-section mt-5">
            <div className="section-header-banner mb-3">
              <div>
                <h3>Your Previous Interview Sessions</h3>
                <p className="text-secondary text-sm">
                  Review historical practice rounds, scores, and evaluation notes.
                </p>
              </div>
            </div>

            {loadingInitial ? (
              <div className="loading-container py-5">
                <div className="loading-spinner"></div>
                <p>Loading your interview history...</p>
              </div>
            ) : historySessions.length === 0 ? (
              <div className="empty-state-box">
                <div className="empty-icon">🎯</div>
                <h4>No Practice Sessions Yet</h4>
                <p className="text-secondary">
                  Configure your target role above and start your first simulated AI interview!
                </p>
              </div>
            ) : (
              <div className="interview-history-grid">
                {historySessions.map((sess) => (
                  <div key={sess.id} className="dashboard-card history-card">
                    <div className="history-card-header">
                      <div className="history-title-block">
                        <span className="history-role-title">{sess.target_role}</span>
                        <div className="history-meta-badges">
                          <span className="tag tag-skill text-xs">{sess.interview_type}</span>
                          <span className="tag tag-interest text-xs">{sess.difficulty}</span>
                          <span className={`status-pill status-${sess.status}`}>
                            {sess.status === 'completed' ? '✓ Completed' : 'In Progress'}
                          </span>
                        </div>
                      </div>

                      {sess.overall_score !== null && (
                        <div className={`history-score-badge ${getScoreColorClass(sess.overall_score)}`}>
                          <span className="score-val">{sess.overall_score}</span>
                          <span className="score-denom">/ 100</span>
                        </div>
                      )}
                    </div>

                    <div className="history-card-footer">
                      <span className="history-date text-xs text-muted">
                        {new Date(sess.created_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </span>

                      {sess.status === 'completed' ? (
                        <button
                          type="button"
                          className="btn btn-outline btn-sm"
                          onClick={() => handleViewResult(sess.id)}
                          disabled={completingSession}
                        >
                          View Result →
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          onClick={() => handleResumeSession(sess.id)}
                          disabled={startingSession}
                        >
                          Resume Interview →
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {/* ==================================================================== */}
      {/* VIEW 2: ACTIVE INTERVIEW SCREEN                                      */}
      {/* ==================================================================== */}
      {viewMode === 'interview' && currentQuestion && (
        <div className="active-interview-layout">
          {/* Top Progress & Navigation Bar */}
          <div className="interview-progress-card dashboard-card mb-4">
            <div className="progress-meta-row">
              <div className="progress-info">
                <span className="text-secondary text-sm">Target Role:</span>{' '}
                <strong>{activeSession?.target_role}</strong>
                <span className="meta-divider">•</span>
                <span className="badge-type">{currentQuestion.question_type.toUpperCase()}</span>
                <span className="meta-divider">•</span>
                <span className="text-secondary text-sm">{activeSession?.difficulty} level</span>
              </div>

              <div className="progress-counter">
                Question <strong>{currentQuestionIndex + 1}</strong> of{' '}
                <strong>{questions.length}</strong>
              </div>
            </div>

            {/* Visual Progress Bar */}
            <div className="progress-bar-track">
              <div
                className="progress-bar-fill"
                style={{
                  width: `${((currentQuestionIndex + 1) / questions.length) * 100}%`,
                }}
              ></div>
            </div>

            {/* Question Quick Jump Dots */}
            <div className="question-stepper-dots">
              {questions.map((q, idx) => {
                const isCurrent = idx === currentQuestionIndex;
                const isAnswered = Boolean(q.answer);
                return (
                  <button
                    type="button"
                    key={q.id}
                    className={`stepper-dot ${isCurrent ? 'current' : ''} ${isAnswered ? 'answered' : ''}`}
                    onClick={() => {
                      setCurrentQuestionIndex(idx);
                      if (q.answer) {
                        setCurrentAnswerText(q.answer.answer_text || '');
                        setLastEvaluation(q.answer);
                      } else {
                        setCurrentAnswerText('');
                        setLastEvaluation(null);
                      }
                      setErrorMsg('');
                    }}
                    title={`Question ${idx + 1}${isAnswered ? ' (Answered)' : ''}`}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Main Question Card */}
          <div className="dashboard-card question-card mb-4">
            <div className="card-header">
              <div className="question-num-tag">
                Q{currentQuestion.question_number}
              </div>
              <div className="question-heading-col">
                <span className="question-category-chip">
                  {currentQuestion.question_type === 'technical' && '⚙️ Technical Depth'}
                  {currentQuestion.question_type === 'behavioral' && '🤝 Behavioral & STAR'}
                  {currentQuestion.question_type === 'situational' && '⚡ Situational Problem-Solving'}
                </span>
                <h3 className="question-prompt-text">{currentQuestion.question_text}</h3>
              </div>
            </div>

            {/* Expected Topics Hint Chips */}
            {Array.isArray(currentQuestion.expected_topics) &&
              currentQuestion.expected_topics.length > 0 && (
                <div className="expected-topics-bar">
                  <span className="topics-label">Key Topics to Address:</span>
                  <div className="topics-chips-list">
                    {currentQuestion.expected_topics.map((top, idx) => (
                      <span key={idx} className="tag tag-skill">
                        {top}
                      </span>
                    ))}
                  </div>
                </div>
              )}

            {/* Answer Text Area */}
            <div className="answer-input-container mt-3">
              <div className="textarea-label-row">
                <label htmlFor="answer-textarea" className="form-label">
                  Your Answer
                </label>
                <span className="word-count-badge text-secondary text-xs">
                  {wordCount} words ({currentAnswerText.length} chars)
                </span>
              </div>

              <textarea
                id="answer-textarea"
                rows={7}
                className="form-control answer-textarea"
                placeholder="Structure your answer clearly. For technical questions, mention trade-offs and APIs. For behavioral questions, utilize the STAR framework (Situation, Task, Action, Result)..."
                value={currentAnswerText}
                onChange={(e) => setCurrentAnswerText(e.target.value)}
                disabled={evaluatingAnswer}
              ></textarea>

              <div className="answer-actions-bar mt-3">
                <div className="answering-tip text-secondary text-xs">
                  💡 <em>Tip: Aim for depth, concrete examples, and mentioning key trade-offs.</em>
                </div>

                <div className="action-buttons-group">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleSubmitAnswer}
                    disabled={evaluatingAnswer || !currentAnswerText.trim()}
                  >
                    {evaluatingAnswer ? (
                      <>
                        <span className="spinner-sm"></span> Evaluating with AI...
                      </>
                    ) : lastEvaluation ? (
                      'Update & Re-evaluate'
                    ) : (
                      'Submit Answer'
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Instant AI Evaluation Card (Revealed after submission) */}
          {lastEvaluation && (
            <div className="dashboard-card evaluation-feedback-card mb-4">
              <div className="evaluation-header">
                <div className="eval-score-block">
                  <span className="eval-score-label">AI Score</span>
                  <div className={`eval-score-badge ${getScoreColorClass(lastEvaluation.score)}`}>
                    <span className="score-num">{lastEvaluation.score}</span>
                    <span className="score-total">/ 100</span>
                  </div>
                </div>

                <div className="eval-summary-col">
                  <h4>AI Answer Feedback</h4>
                  <p className="eval-narrative">{lastEvaluation.evaluation}</p>
                </div>
              </div>

              <div className="eval-details-grid mt-4">
                {/* Strengths */}
                <div className="eval-box strengths-box">
                  <div className="box-title">
                    <span className="box-icon">✓</span> Strengths
                  </div>
                  <ul>
                    {(lastEvaluation.strengths || []).map((str, idx) => (
                      <li key={idx}>{str}</li>
                    ))}
                  </ul>
                </div>

                {/* Weaknesses */}
                <div className="eval-box weaknesses-box">
                  <div className="box-title">
                    <span className="box-icon">!</span> Areas for Improvement
                  </div>
                  <ul>
                    {(lastEvaluation.weaknesses || []).map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>

                {/* Missing Points */}
                <div className="eval-box missing-box">
                  <div className="box-title">
                    <span className="box-icon">🔍</span> Missing Important Points
                  </div>
                  <ul>
                    {(lastEvaluation.missing_points || []).map((m, idx) => (
                      <li key={idx}>{m}</li>
                    ))}
                  </ul>
                </div>

                {/* Improvement Suggestions */}
                <div className="eval-box suggestions-box">
                  <div className="box-title">
                    <span className="box-icon">💡</span> How to Level Up
                  </div>
                  <ul>
                    {(lastEvaluation.improvement_suggestions || []).map((s, idx) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Navigation Bar after Evaluation */}
              <div className="post-eval-nav-bar mt-4">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={handlePreviousQuestion}
                  disabled={currentQuestionIndex === 0}
                >
                  ← Previous Question
                </button>

                {isLastQuestion ? (
                  <button
                    type="button"
                    className="btn btn-primary btn-lg"
                    onClick={handleFinishInterview}
                    disabled={completingSession}
                  >
                    {completingSession ? (
                      <>
                        <span className="spinner-sm"></span> Compiling Final Assessment...
                      </>
                    ) : (
                      'Complete Interview & View Results 🏆'
                    )}
                  </button>
                ) : (
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleNextQuestion}
                  >
                    Next Question →
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Bottom Controls if not evaluated yet */}
          {!lastEvaluation && (
            <div className="interview-bottom-nav">
              <button
                type="button"
                className="btn btn-outline"
                onClick={handlePreviousQuestion}
                disabled={currentQuestionIndex === 0}
              >
                ← Previous Question
              </button>

              <div className="bottom-nav-right">
                {allAnswered && (
                  <button
                    type="button"
                    className="btn btn-outline-success"
                    onClick={handleFinishInterview}
                    disabled={completingSession}
                  >
                    Finish Session Now
                  </button>
                )}

                {!isLastQuestion && (
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={handleNextQuestion}
                  >
                    Next Question →
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* VIEW 3: FINAL EVALUATION & RESULTS BREAKDOWN                         */}
      {/* ==================================================================== */}
      {viewMode === 'result' && sessionResult && (
        <div className="interview-result-layout">
          {/* Hero Result Banner */}
          <div className="dashboard-card result-hero-card mb-4">
            <div className="result-hero-content">
              <div className="result-badge-row">
                <span className="status-chip">✓ Practice Session Completed</span>
                <span className="tag tag-skill">{sessionResult.target_role}</span>
                <span className="tag tag-interest">{sessionResult.difficulty}</span>
              </div>

              <h2>Interview Performance Assessment</h2>

              {/* Mandatory AI Disclaimer */}
              <div className="ai-disclaimer-callout">
                <span className="callout-icon">ℹ️</span>
                <span>
                  <strong>AI Evaluation Notice:</strong> AI-generated interview evaluation estimate — not an official hiring assessment.
                </span>
              </div>

              <p className="overall-narrative-text mt-3">
                {sessionResult.overall_feedback}
              </p>
            </div>

            {/* Big Overall Score Badge */}
            <div className="result-score-gauge">
              <div className={`score-circle ${getScoreColorClass(sessionResult.overall_score)}`}>
                <span className="gauge-number">{sessionResult.overall_score}</span>
                <span className="gauge-label">Overall AI Score</span>
              </div>
            </div>
          </div>

          {/* Consolidated Strengths, Weaknesses, Recommendations Grid */}
          <div className="result-breakdown-grid mb-4">
            {/* Strengths */}
            <div className="dashboard-card">
              <div className="card-header">
                <div className="card-icon text-success">⭐</div>
                <div>
                  <h3>Demonstrated Strengths</h3>
                  <p>Key competencies and structured insights</p>
                </div>
              </div>
              <div className="card-body">
                <ul className="bullet-list-check">
                  {(sessionResult.strengths || []).map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Growth Areas */}
            <div className="dashboard-card">
              <div className="card-header">
                <div className="card-icon text-warning">🎯</div>
                <div>
                  <h3>Areas for Growth</h3>
                  <p>Core dimensions that require deeper coverage</p>
                </div>
              </div>
              <div className="card-body">
                <ul className="bullet-list-warn">
                  {(sessionResult.weaknesses || []).map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Recommendations */}
            <div className="dashboard-card">
              <div className="card-header">
                <div className="card-icon text-accent">🚀</div>
                <div>
                  <h3>Strategic Next Steps</h3>
                  <p>Actionable preparation recommendations</p>
                </div>
              </div>
              <div className="card-body">
                <ul className="bullet-list-arrow">
                  {(sessionResult.recommendations || []).map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Question-by-Question Deep Dive */}
          <div className="dashboard-card breakdown-card mb-4">
            <div className="card-header">
              <div className="card-icon">📋</div>
              <div>
                <h3>Question-by-Question Detailed Breakdown</h3>
                <p>Review individual question responses and granular scores</p>
              </div>
            </div>

            <div className="card-body">
              <div className="questions-review-list">
                {(sessionResult.questions || []).map((q) => {
                  const ans = q.answer;
                  return (
                    <div key={q.id} className="question-review-item">
                      <div className="review-item-header">
                        <div className="review-q-meta">
                          <span className="q-badge">Question {q.question_number}</span>
                          <span className="type-badge-sm">{q.question_type}</span>
                        </div>
                        {ans && (
                          <div className={`review-score-chip ${getScoreColorClass(ans.score)}`}>
                            Score: {ans.score} / 100
                          </div>
                        )}
                      </div>

                      <h4 className="review-q-text">{q.question_text}</h4>

                      {ans ? (
                        <div className="review-answer-box">
                          <div className="candidate-answer-section">
                            <span className="label-sm">Your Response:</span>
                            <p className="candidate-answer-text">{ans.answer_text}</p>
                          </div>

                          <div className="eval-notes-section mt-2">
                            <span className="label-sm">Evaluation Notes:</span>
                            <p className="eval-notes-text">{ans.evaluation}</p>
                          </div>

                          {ans.missing_points && ans.missing_points.length > 0 && (
                            <div className="missing-points-row mt-2">
                              <span className="text-secondary text-xs">Missing Points: </span>
                              {ans.missing_points.map((mp, i) => (
                                <span key={i} className="tag tag-interest text-xs">
                                  {mp}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="unanswered-notice text-muted text-sm">
                          <em>This question was not answered.</em>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Result Footer CTA */}
          <div className="result-actions-footer">
            <button
              type="button"
              className="btn btn-primary btn-lg"
              onClick={() => {
                setViewMode('setup');
                loadInitialData();
              }}
            >
              🔄 Start New Interview
            </button>

            <Link to="/dashboard" className="btn btn-outline btn-lg">
              Return to Dashboard
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
