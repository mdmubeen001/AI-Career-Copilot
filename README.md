# AI Multi-Agent Life & Career Copilot

An API-first AI Multi-Agent platform designed to guide engineering students and early-career developers along calibrated career paths. The system benchmarks current competencies against target roles, produces strategic readiness evaluations, and builds personalized roadmaps.

---

## 🚀 Key Features (Phase 1, 2, 3 & 4 Active)

- **JWT Authentication & Profile Engine**: Secure email-based registration, token refresh, and complete academic/personal profile management.
- **Career & Skills Core**: Relational skills repository with proficiency levels (`Beginner`, `Intermediate`, `Advanced`), target roles, and professional bios.
- **Supervisor Agent Orchestration**: Central orchestrator that inspects candidate profile context and routes requests to specialized autonomous agents.
- **Career Analysis Agent**: Analyzes candidate credentials, calculates an objective career readiness score (0–100%), flags strengths, identifies critical knowledge gaps, suggests adjacent paths, and formulates prioritized action steps.
- **AI Resume & ATS Compatibility Analyzer**: Ingests PDF and DOCX resume documents, parses selectable text, and computes an AI-estimated ATS compatibility score, extracting detected skills, missing keywords, section evaluations, and actionable improvements.
- **AI Job Matching & Alignment**: Ingests target job descriptions and benchmarks them against uploaded resumes and career profiles. Computes an AI-estimated match compatibility percentage, verified overlapping competencies, missing job requirements, candidate strengths, alignment gaps, and actionable recommendations.
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
   ↙             ↓              ↘
[ Career Agent ] [ Resume Analyzer ] [ Job Matching Agent ]
         ↓               ↓                    ↓
         └───────────────┼────────────────────┘
                         ↓
             [ LLM Service Provider ]
      (Gemini / OpenAI / Heuristic Fallback)
                         ↓
         [ Structured JSON Validation ]
                         ↓
  [ Relational Models: CareerAnalysis / Resume / JobMatch ]
                         ↓
              JSON Response to Client
                         ↓
           Interactive React Results UI
```

### Upcoming Specialized Agents (Roadmap)
- `skill_gap_agent`: In-depth breakdown of granular competencies and prerequisites.
- `learning_roadmap_agent`: Adaptive weekly learning curriculum and milestones.
- `interview_prep_agent` & `rag_agent`: Mock technical interviews and contextual retrieval over documentation.

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

#### Example Response: `POST /api/v1/jobs/1/match/`
```json
{
  "id": 1,
  "job_description": 1,
  "job_title": "Python Django Developer",
  "company": "Tech Corp",
  "resume": 1,
  "resume_filename": "Developer_Resume.pdf",
  "match_score_estimate": 78,
  "summary": "Candidate profile demonstrates an estimated 78% match compatibility for 'Python Django Developer' at Tech Corp...",
  "matching_skills": ["Python", "Django", "PostgreSQL", "Docker", "REST API", "Git"],
  "missing_skills": ["AWS", "CI/CD", "Redis"],
  "strengths": [
    "Strong direct alignment on core job skills: Python, Django, PostgreSQL, Docker.",
    "High overall technical coverage across the requested stack."
  ],
  "gaps": [
    "Missing high-priority keywords from job description: AWS, CI/CD, Redis."
  ],
  "recommendations": [
    "Tailor your resume summary to directly echo keywords from 'Python Django Developer'.",
    "Bridge priority skill gaps by featuring recent projects using: AWS, CI/CD, Redis.",
    "Use active action verbs and quantify achievements with the Google XYZ formula: Accomplished [X] as measured by [Y], by doing [Z]."
  ],
  "created_at": "2026-09-17T04:15:00Z"
}
```

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
