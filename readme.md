<div align="center">
  <h1>⚡ OutreachX</h1>
  <p><strong>AI-powered B2B cold outreach automation</strong></p>
  <p>Discover startups → Find decision-maker emails → Generate personalized cold emails → Track replies → Auto follow-ups</p>
  <br/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Next.js_14-black?style=flat&logo=next.js&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangGraph-4B32C3?style=flat&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Groq-F55036?style=flat&logoColor=white"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white"/>
</div>

---

## What it does

OutreachX runs a full AI outreach pipeline on demand:

```
Your query → AI discovers companies → Scrapes websites → Finds CEO/CTO/HR emails
          → Generates personalized cold emails → You review → Send → Track replies → Auto follow-ups
```

**Three ways to input leads:**
- `"YC India fintech startups after 2020"` — AI discovers companies via SerpAPI + YC directory
- `"email Razorpay, Groww, Sarvam AI"` — direct company name targeting
- Upload CSV / Excel / JSON — your existing database

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| Backend | FastAPI, Python 3.11 |
| AI Orchestration | LangGraph (multi-agent StateGraph) |
| LLM | Groq — Llama 3.3 70B (fast inference, free tier) |
| Lead Discovery | SerpAPI + BeautifulSoup + YC directory scraper |
| Contact Finding | Hunter.io + email pattern guesser + LinkedIn builder |
| Email Sending | SendGrid + SMTP fallback |
| Tracking | Open/click/reply tracking pixel |
| Follow-ups | APScheduler (3-day cadence, 2 max follow-ups) |
| Database | PostgreSQL + SQLAlchemy async |
| Resume Parsing | pdfplumber + Groq extraction |

## Project structure

```
outreachx/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── graph.py              # LangGraph pipeline
│   │   │   ├── state.py              # AgentState TypedDict
│   │   │   └── nodes/
│   │   │       ├── planner.py        # Parses query, detects role/mode
│   │   │       ├── direct_input.py   # "email Razorpay, Groww" → leads
│   │   │       ├── discovery.py      # SerpAPI + YC scraper + CSV upload
│   │   │       ├── researcher.py     # Website scraper + Groq hooks
│   │   │       ├── contact_finder.py # Hunter.io + pattern guesser + LinkedIn
│   │   │       ├── email_generator.py# Groq personalized emails
│   │   │       └── validator.py      # Quality scoring 0–1
│   │   ├── api/routes/
│   │   │   ├── campaigns.py          # Campaign CRUD + send
│   │   │   └── tracking.py           # Open/click/reply tracking
│   │   ├── db/
│   │   │   ├── database.py           # SQLAlchemy async engine
│   │   │   └── crud.py               # All DB operations
│   │   ├── models/
│   │   │   ├── campaign.py
│   │   │   ├── lead.py
│   │   │   └── email.py
│   │   ├── services/
│   │   │   ├── email_sender.py       # SendGrid + SMTP + HTML builder
│   │   │   ├── tracker.py            # Event tracking store
│   │   │   └── followup.py           # APScheduler follow-up queue
│   │   └── main.py                   # FastAPI app
│   ├── requirements.txt
│   ├── render.yaml                   # Render deployment config
│   └── .env.example
└── frontend/
    ├── app/
    │   ├── page.tsx                  # Landing page
    │   └── dashboard/
    │       ├── page.tsx              # Dashboard home + campaign runner
    │       ├── campaigns/page.tsx    # Campaign list
    │       ├── leads/page.tsx        # Leads table
    │       ├── emails/page.tsx       # Email review
    │       ├── analytics/page.tsx    # Funnel charts
    │       └── settings/page.tsx     # API keys + sender config
    ├── lib/api.ts                    # API client (connects to backend)
    └── components/
```

## Quick start (local)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — add your API keys (see below)

uvicorn app.main:app --reload
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
# App running at http://localhost:3000
```

## Required API keys

| Key | Where to get | Free tier |
|-----|-------------|-----------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | ✓ Unlimited |
| `SERPAPI_API_KEY` | [serpapi.com](https://serpapi.com) | 100 searches/month |
| `HUNTER_API_KEY` | [hunter.io](https://hunter.io) | 50 searches/month |
| `SENDGRID_API_KEY` | [sendgrid.com](https://sendgrid.com) | 100 emails/day |
| `DATABASE_URL` | [supabase.com](https://supabase.com) or local PostgreSQL | ✓ Free |

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/agents/run` | Run full AI pipeline (no DB) |
| `POST` | `/campaigns` | Create campaign + save to DB |
| `GET` | `/campaigns` | List all campaigns |
| `GET` | `/campaigns/{id}` | Campaign with leads + emails |
| `POST` | `/campaigns/{id}/send` | Send approved emails |
| `GET` | `/campaigns/{id}/stats` | Open/click/reply rates |
| `POST` | `/emails/send` | Send single email |
| `GET` | `/emails/stats` | Overall stats |
| `GET` | `/track/open/{id}` | Open tracking pixel |
| `POST` | `/track/reply/{id}` | Mark as replied |
| `GET` | `/followups/queue` | View pending follow-ups |
| `POST` | `/resume/parse` | Parse resume PDF/TXT |

## Deploy

### Backend → Render

1. Push to GitHub
2. [render.com](https://render.com) → New Web Service → connect repo
3. Render auto-detects `render.yaml`
4. Add environment variables in Render dashboard
5. Create PostgreSQL on Render → copy URL → set as `DATABASE_URL` (change `postgresql://` → `postgresql+asyncpg://`)
6. Deploy — live at `https://outreachx-backend.onrender.com`

### Frontend → Vercel

```bash
cd frontend
npx vercel
# Follow prompts
# Set NEXT_PUBLIC_API_URL=https://outreachx-backend.onrender.com
```

Or connect GitHub repo at [vercel.com](https://vercel.com) and set the env var in project settings.

## Pipeline flow

```
User input (query / file / company names)
    │
    ▼
Planner node — detects mode + target role (CEO/CTO/HR)
    │
    ├── "email Razorpay, Groww" ──────► Direct Input node
    ├── CSV/Excel/JSON upload ─────────► Discovery node (parse file)
    └── "YC India fintech 2021" ───────► Discovery node (SerpAPI)
                                              │
                                              ▼
                                        Researcher node
                                    (scrapes websites, Groq hooks)
                                              │
                                              ▼
                                       Contact Finder
                                    (Hunter.io → pattern guess)
                                              │
                                              ▼
                                       Email Generator
                                    (Groq, resume-aware, role-aware)
                                              │
                                              ▼
                                          Validator
                                    (scores 0–1, flags weak emails)
                                              │
                                              ▼
                                    Leads + Emails returned
                                    User reviews in dashboard
                                              │
                                              ▼
                                        Send emails
                                    (SendGrid / SMTP + tracking)
                                              │
                                              ▼
                                    Follow-up scheduler
                                    (3 days, max 2 follow-ups)
```

## Environment variables reference

**Backend `.env`:**
```env
GROQ_API_KEY=gsk_...
SERPAPI_API_KEY=...
HUNTER_API_KEY=...
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/outreachx
SENDGRID_API_KEY=SG....
FROM_EMAIL=you@yourdomain.com
APP_ENV=development
```

**Frontend `.env.local`:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

<div align="center">
  Built with LangGraph + Groq &nbsp;·&nbsp; Made by Harshita Yadav
</div>