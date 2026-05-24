# ResumeLens

An AI agent that analyzes how well your resume matches a job description and generates a complete application package: rewritten bullets, cover letter, interview prep, and job recommendations.

**Live:** [resumelens.dev](https://resumelens.dev)

---

## Features

- **Match Score**: rates resume to job description alignment from 0–100 with matched and missing skills
- **Resume Bullet Rewriter**: rewrites bullets with ATS optimization; includes a self-critique loop that scores and re-rewrites until quality passes a threshold
- **Cover Letter Generator**: tailored to the specific job description
- **Interview Prep**: technical questions, behavioral questions, and a study topic list based on skill gaps
- **Job Recommendations**: searches real job listings derived from your resume using JSearch (RapidAPI)
- **Follow-up Chat**: ask the agent to refine any part of the analysis. It calls the relevant tool and patches the report in place
- **PDF Export**: download the full report as a formatted PDF

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, Tailwind CSS 4, TypeScript |
| Backend | FastAPI, Python 3.11 |
| AI Agent | LangGraph (ReAct agent), LangChain, OpenAI GPT-4o |
| Resume Parsing | PyMuPDF (PDF), python-docx (DOCX) |
| Job Search | JSearch via RapidAPI |
| Rate Limiting | slowapi |
| Deployment | Vercel (frontend), Fly.io (backend) |

---

## Architecture

The backend runs a **tool-calling ReAct agent** built with LangGraph. On each analysis request, the agent receives the resume and job description, then autonomously decides which tools to call and in what order:

```
analyze_resume_match
  - rewrite_resume_bullets_tool   (includes self-critique loop)
  - write_cover_letter_tool
  - prepare_interview_questions_tool
  - agent writes personalised summary
```

The self-critique loop inside `rewrite_resume_bullets_tool` scores the rewritten bullets and re-rewrites them if the quality score is below the acceptance threshold — without any fixed retry logic in the route handler.

Follow-up chat reuses the same LangGraph thread (via `MemorySaver`), so the agent has full context from the original analysis without re-sending the resume.

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- RapidAPI key (optional — job search is skipped if not set)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

Create `backend/.env`:
```
OPENAI_API_KEY=sk-...
RAPIDAPI_KEY=...              
ALLOWED_ORIGINS=http://localhost:3000
```

Run the backend:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run the frontend:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Health check (JSON) |
| `POST` | `/api/resume/parse` | Upload PDF or DOCX, returns extracted text |
| `POST` | `/api/analyze` | Run the agent, returns full analysis |
| `POST` | `/api/chat` | Follow-up message on an existing analysis thread |
| `POST` | `/api/jobs` | Job recommendations from resume text |

---

## Deployment

| Service | Purpose | Config |
|---------|---------|--------|
| [Fly.io](https://fly.io) | Backend container | `backend/fly.toml` |
| [Vercel](https://vercel.com) | Frontend (Next.js) | Root directory: `frontend` |

**Fly.io secrets required:**
```bash
flyctl secrets set OPENAI_API_KEY=... RAPIDAPI_KEY=... ALLOWED_ORIGINS=https://resumelens.dev -a resume-lens
```

**Vercel environment variable:**
```
NEXT_PUBLIC_API_URL=https://resume-lens.fly.dev
```
