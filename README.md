# TalentGPT 🚀

> AI-Powered Talent Acquisition Platform — Replace resume-based hiring with evidence-based GitHub analysis.

## Quick Start (3 Steps)

### Step 1: Get API Keys

| Key | Where to get | Cost |
|-----|-------------|------|
| **GEMINI_API_KEY** | [aistudio.google.com](https://aistudio.google.com/app/apikey) | Free |
| **GITHUB_TOKEN** | [github.com/settings/tokens](https://github.com/settings/tokens) | Free |

### Step 2: Setup

```bash
cd backend
copy .env.example .env
# Edit .env and add your keys
```

### Step 3: Run

**Option A — One click:**
```
Double-click start.bat
```

**Option B — Manual:**
```bash
# Terminal 1 (Backend)
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Frontend — just open frontend/index.html in browser
```

## How It Works

1. **Paste a Job Description** → JD Analyzer Agent extracts required skills
2. **Enter GitHub usernames** → GitHub Audit Agent deep-audits all repos
3. **Fraud Detection** → Flags fake repos, commit spam, star farming
4. **Scoring Engine** → 5-dimension evidence-based score (0-100)
5. **Explainability** → Every score linked to specific commits/repos
6. **Interview Questions** → Personalized questions from actual GitHub work

## Scoring Dimensions

| Dimension | Weight | Measured By |
|-----------|--------|-------------|
| Technical Execution | 25% | Non-empty repos, commit volume, language diversity |
| Code Quality | 20% | README, tests, documentation |
| Learning Velocity | 20% | Languages/year, repos/year |
| Collaboration | 15% | Followers, forks received, community impact |
| Skill Alignment | 20% | JD skills vs. candidate languages/repos |

## Project Structure

```
talentgpt/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── database.py          # SQLite models
│   ├── config.py            # Environment config
│   ├── requirements.txt
│   ├── .env.example
│   └── agents/
│       ├── jd_analyzer.py   # Gemini-powered JD parsing
│       ├── github_audit.py  # Deep GitHub analysis
│       ├── fraud_detector.py # 6-signal fraud detection
│       ├── scoring.py       # 5-dimension scoring engine
│       ├── explainability.py # XAI + interview questions
│       └── pipeline.py      # Orchestrator
├── frontend/
│   ├── index.html           # Dashboard
│   ├── style.css            # Dark glassmorphism UI
│   └── app.js               # All frontend logic
└── start.bat                # One-click startup
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/jobs` | Create job + start pipeline |
| GET | `/api/v1/jobs` | List all jobs |
| GET | `/api/v1/jobs/{id}/status` | Check pipeline progress |
| GET | `/api/v1/jobs/{id}/candidates` | Get ranked candidates |
| DELETE | `/api/v1/jobs/{id}` | Delete job |

API Docs: http://localhost:8000/docs

## Demo Usernames to Try

```
torvalds, gvanrossum, karpathy, simonw, yann-lecun
```

## Architecture

```
JD Upload → JD Analyzer (Gemini) → Skill Extraction
                                          ↓
GitHub Usernames → GitHub Audit → Fraud Detection
                                          ↓
                              Scoring Engine (5 dimensions)
                                          ↓
                              Explainability (Gemini)
                                          ↓
                              Interview Questions (Gemini)
                                          ↓
                              Ranked Dashboard
```
