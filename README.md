# AI Multi-Agent Life & Career Copilot

An API-first AI Multi-Agent platform designed to guide engineering students and early-career developers along calibrated career paths. The system benchmarks current competencies against target roles, produces strategic readiness evaluations, and builds personalized roadmaps.

---

## 🚀 Key Features (Phase 1 & Phase 2 Active)

- **JWT Authentication & Profile Engine**: Secure email-based registration, token refresh, and complete academic/personal profile management.
- **Career & Skills Core**: Relational skills repository with proficiency levels (`Beginner`, `Intermediate`, `Advanced`), target roles, and professional bios.
- **Supervisor Agent Orchestration**: Central orchestrator that inspects candidate profile context and routes requests to specialized autonomous agents.
- **Career Analysis Agent**: Analyzes candidate credentials, calculates an objective career readiness score (0–100%), flags strengths, identifies critical knowledge gaps, suggests adjacent paths, and formulates prioritized action steps.
- **Provider-Independent LLM Abstraction**: Safe server-side AI interface with built-in development fallback and pluggable support for Google Gemini, OpenAI, or custom LLMs.
- **Modern Responsive Web UI**: React + Vite interface with cyberpunk dark-mode aesthetics, glassmorphism, interactive tags, and real-time validation.

---

## 🤖 Multi-Agent Architecture

```
User Request / Web / Mobile App
              ↓
  [ Supervisor Agent Orchestrator ]
              ↓
     Select & Dispatch Agent
              ↓
    [ Career Analysis Agent ]
              ↓
    [ LLM Service Provider ]
 (Gemini / OpenAI / Intelligent Fallback)
              ↓
    [ Structured Schema Validation ]
              ↓
   [ Database Persistence ] (CareerAnalysis)
              ↓
   JSON Response to Client
```

### Upcoming Specialized Agents (Roadmap)
- `skill_gap_agent`: In-depth breakdown of granular competencies.
- `learning_roadmap_agent`: Adaptive weekly learning curriculum and milestones.
- `project_recommendation_agent`: Portfolio projects tailored to closing specific gaps.
- `resume_optimization_agent` & `interview_prep_agent`: Resume tailoring and mock interview simulation.

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

#### Example Request: `POST /api/v1/career/analyze/`
```json
{
  "career_goal": "Senior AI Systems Engineer"
}
```

#### Example Response:
```json
{
  "id": 1,
  "career_goal": "Senior AI Systems Engineer",
  "career_readiness": 72,
  "recommended_paths": [
    "Machine Learning Engineer",
    "AI Research Assistant",
    "Data Scientist",
    "LLM Application Engineer"
  ],
  "strengths": [
    "Python",
    "Django",
    "React"
  ],
  "weaknesses": [
    "PyTorch",
    "Deep Learning",
    "TensorFlow"
  ],
  "analysis": "Candidate profile shows promising alignment towards the target role...",
  "next_actions": [
    "Deepen proficiency in priority gap areas: PyTorch, Deep Learning.",
    "Architect a full-scale portfolio project demonstrating production readiness...",
    "Practice architectural system design, data modeling, and performance optimization..."
  ],
  "created_at": "2026-09-15T05:10:00Z",
  "updated_at": "2026-09-15T05:10:00Z"
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
python manage.py test accounts career

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
