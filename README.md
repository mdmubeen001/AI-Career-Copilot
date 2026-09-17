# AI Multi-Agent Life & Career Copilot

An API-first AI Multi-Agent platform designed to guide engineering students and early-career developers along calibrated career paths. The system benchmarks current competencies against target roles, produces strategic readiness evaluations, and builds personalized roadmaps.

---

## 🚀 Key Features (Phase 1, 2, 3, 4 & 5 Active)

- **JWT Authentication & Profile Engine**: Secure email-based registration, token refresh, and complete academic/personal profile management.
- **Career & Skills Core**: Relational skills repository with proficiency levels (`Beginner`, `Intermediate`, `Advanced`), target roles, and professional bios.
- **Supervisor Agent Orchestration**: Central orchestrator that inspects candidate profile context and routes requests to specialized autonomous agents.
- **Career Analysis Agent**: Analyzes candidate credentials, calculates an objective career readiness score (0–100%), flags strengths, identifies critical knowledge gaps, suggests adjacent paths, and formulates prioritized action steps.
- **AI Resume & ATS Compatibility Analyzer**: Ingests PDF and DOCX resume documents, parses selectable text, and computes an AI-estimated ATS compatibility score, extracting detected skills, missing keywords, section evaluations, and actionable improvements.
- **AI Job Matching & Alignment**: Ingests target job descriptions and benchmarks them against uploaded resumes and career profiles. Computes an AI-estimated match compatibility percentage, verified overlapping competencies, missing job requirements, candidate strengths, alignment gaps, and actionable recommendations.
- **AI Interview Agent & Mock Simulator**: Simulates role-specific technical, behavioral, and situational interviews. Generates dynamic questions grounded in candidate profile/resume, evaluates submitted answers with score and granular rubric feedback (strengths, weaknesses, missing points, and improvements), and synthesizes comprehensive final session performance.
- **Provider-Independent LLM Abstraction**: Safe server-side AI interface with built-in development fallback and pluggable support for Google Gemini, OpenAI, or custom LLMs.
- **Modern Responsive Web UI**: React + Vite interface with cyberpunk dark-mode aesthetics, glassmorphism, drag-and-drop dropzones, interactive tags, and real-time validation.

---

## 🤖 Multi-Agent Architecture

```
React Frontend / Web Client
              ↓
    [ Django REST API ]
              ↓
  [ Supervisor Agent Orchestrator ]
              ↓
      Select & Dispatch Agent
    ↙         ↓               ↓               ↘
[ Career ] [ Resume ] [ Job Matching ] [ Interview Agent ]
    ↓         ↓               ↓               ↓
    └─────────┴───────┬───────┴───────────────┘
                      ↓
          [ LLM Service Provider ]
   (Gemini / OpenAI / Heuristic Fallback)
                      ↓
      [ Structured JSON Validation ]
                      ↓
  [ Relational Models: Career / Resume / Match / Interview ]
                      ↓
           JSON Response to Client
                      ↓
        Interactive React Results UI
```

### Interview Agent Architecture Flow

```
React
  ↓
Django REST API
  ↓
Interview Agent
  ↓
Profile + CareerProfile + Skills + Resume + ResumeAnalysis
  ↓
LLM
  ↓
Questions
  ↓
User Answers
  ↓
AI Evaluation
  ↓
Final Interview Result
```

### Upcoming Specialized Agents (Roadmap)
- `skill_gap_agent`: In-depth breakdown of granular competencies and prerequisites.
- `learning_roadmap_agent`: Adaptive weekly learning curriculum and milestones.
- `rag_agent`: Contextual retrieval over technical documentation and custom company handbooks.

---

## 📡 API Endpoints

All endpoints are prefixed with `/api/v1/`.

### Authentication & Account
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register/` | Register with email and password | No |
| `POST` | `/api/v1/auth/login/` | Obtain JWT access and refresh tokens | No |
| `POST` | `/api/v1/auth/refresh/` | Refresh access token | No |
| `GET`, `PUT`, `PATCH` | `/api/v1/profile/` | Manage academic profile and user details | Yes (Bearer JWT) |

### Career Module & Skills
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET`, `PUT`, `PATCH` | `/api/v1/career/profile/` | Manage career profile (role, experience, bio) | Yes (Bearer JWT) |
| `GET`, `POST` | `/api/v1/career/skills/` | List or create skills (`?search=` supported) | Yes (Bearer JWT) |
| `GET`, `POST` | `/api/v1/career/user-skills/` | List or assign skills for authenticated user | Yes (Bearer JWT) |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/v1/career/user-skills/<id>/` | View, update level, or delete user skill | Yes (Bearer JWT) |
| `POST` | `/api/v1/career/user-skills/sync/` | Atomic bulk synchronization of user skills | Yes (Bearer JWT) |

### AI Career Analysis (Supervisor Agent)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/career/analyze/` | Generate career readiness analysis for target goal | Yes (Bearer JWT) |
| `GET` | `/api/v1/career/analysis/` | Retrieve user's latest analysis (`?all=true` for history) | Yes (Bearer JWT) |

### Resume & ATS Analyzer
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/resumes/upload/` | Upload `.pdf` or `.docx` resume (multipart, max 5MB) | Yes (Bearer JWT) |
| `GET` | `/api/v1/resumes/` | List all uploaded resumes for authenticated user | Yes (Bearer JWT) |
| `GET`, `DELETE` | `/api/v1/resumes/<id>/` | Retrieve resume details or delete document | Yes (Bearer JWT) |
| `POST` | `/api/v1/resumes/<id>/analyze/` | Execute/re-run AI ATS analysis for target role | Yes (Bearer JWT) |

### Job Matching Module
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/jobs/` | Create a target Job Description | Yes (Bearer JWT) |
| `GET` | `/api/v1/jobs/` | List user's saved Job Descriptions | Yes (Bearer JWT) |
| `GET`, `DELETE` | `/api/v1/jobs/<id>/` | Retrieve or delete a Job Description | Yes (Bearer JWT) |
| `POST` | `/api/v1/jobs/<id>/match/` | Evaluate Job Match against a user's resume | Yes (Bearer JWT) |
| `GET` | `/api/v1/jobs/matches/` | List user's past Job Matches | Yes (Bearer JWT) |
| `GET` | `/api/v1/jobs/matches/<id>/` | Retrieve an individual Job Match evaluation | Yes (Bearer JWT) |

> **Notice**: Job Match scores are strictly AI-generated estimates to benchmark preparation and do not represent official ATS algorithms or guaranteed hiring outcomes.

### Interview Agent Module
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/interviews/` | Create a new interview session | Yes (Bearer JWT) |
| `GET` | `/api/v1/interviews/` | List user's interview sessions | Yes (Bearer JWT) |
| `GET` | `/api/v1/interviews/<id>/` | Retrieve specific session details | Yes (Bearer JWT) |
| `POST` | `/api/v1/interviews/<id>/start/` | Start session & generate questions via AI | Yes (Bearer JWT) |
| `GET` | `/api/v1/interviews/<id>/questions/` | List questions for the session | Yes (Bearer JWT) |
| `POST` | `/api/v1/interviews/<id>/questions/<qid>/answer/` | Submit answer & evaluate with AI rubric | Yes (Bearer JWT) |
| `POST` | `/api/v1/interviews/<id>/complete/` | Complete session & generate final evaluation | Yes (Bearer JWT) |
| `GET` | `/api/v1/interviews/<id>/result/` | Retrieve final evaluation breakdown | Yes (Bearer JWT) |

> **Notice**: Interview scores and feedback are strictly AI-generated estimates to benchmark preparation and do not represent official hiring assessments.

---

## 🗄️ Data Models (Interviews)

- **`InterviewSession`**:
  - `user` (FK to User, user-isolated)
  - `resume` (FK to Resume, optional)
  - `target_role` (CharField)
  - `interview_type` (`technical`, `behavioral`, `mixed`)
  - `difficulty` (`beginner`, `intermediate`, `advanced`)
  - `total_questions` (PositiveIntegerField, 1–20)
  - `current_question` (PositiveIntegerField)
  - `status` (`not_started`, `in_progress`, `completed`)
  - `overall_score` (IntegerField, 0–100)
  - `overall_feedback` (TextField)
  - `strengths`, `weaknesses`, `recommendations` (JSONFields)
- **`InterviewQuestion`**:
  - `session` (FK to InterviewSession)
  - `question_number` (PositiveIntegerField)
  - `question_text` (TextField)
  - `question_type` (`technical`, `behavioral`, `situational`)
  - `expected_topics` (JSONField)
- **`InterviewAnswer`**:
  - `question` (OneToOneField to InterviewQuestion)
  - `answer_text` (TextField)
  - `score` (IntegerField, 0–100)
  - `evaluation` (TextField)
  - `strengths`, `weaknesses`, `missing_points`, `improvement_suggestions` (JSONFields)

---

## ⚙️ Environment Variables

Configure backend settings via environment variables (or `.env` in `backend/`):

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DEBUG` | `True` | Django debug mode |
| `SECRET_KEY` | Development key | Django cryptographic secret |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed HTTP hosts |
| `MAX_UPLOAD_SIZE` | `5242880` (5MB) | Maximum file upload size in bytes |
| `LLM_PROVIDER` | `mock` | AI provider: `mock`, `gemini`, or `openai` |
| `LLM_API_KEY` | *(empty)* | API key for configured provider (or `GEMINI_API_KEY` / `OPENAI_API_KEY`) |

Frontend (`frontend/.env`):
| Variable | Default | Description |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000/api/v1` | Django REST API root URL |

---

## 🛠️ Development Setup & Execution

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 2. Backend Setup & Run
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (Windows)
..\.venv\Scripts\activate

# Apply migrations
python manage.py migrate

# Run system checks and automated tests
python manage.py check
python manage.py test accounts career resumes jobs

# Launch Django development server
python manage.py runserver
```
The backend REST API will be live at `http://127.0.0.1:8000/api/v1/`.

### 3. Frontend Setup & Run
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already installed)
npm install

# Run linter and verify production build
npm run lint
npm run build

# Start Vite development server
npm run dev
```
The React frontend application will be accessible at `http://localhost:5173/`.
