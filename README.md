# AI Debugging Assistant

An enterprise-grade debugging platform with project management, authentication, and a modern SaaS dashboard.

> **Status:** Phase 1C — Authentication, Dashboard, and Project CRUD complete.

---

## Tech Stack

**Frontend** — React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, React Router, Axios, React Hook Form, Zod, Framer Motion

**Backend** — FastAPI, SQLAlchemy, Alembic, PostgreSQL, bcrypt, JWT (python-jose), Pydantic

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

---

## Setup

### 1. Database

Create a PostgreSQL database:

```bash
createdb ai_debugging_assistant
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_debugging_assistant
SECRET_KEY=generate-a-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Run migrations:

```bash
alembic upgrade head
```

Start the server:

```bash
uvicorn app.main:app --reload
```

API is available at `http://localhost:8000/docs` (Swagger UI).

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend.

---

## Project Structure

```
ai-debugging-assistant/
├── backend/
│   ├── alembic/                  # Database migrations
│   ├── app/
│   │   ├── api/                  # Route handlers
│   │   │   ├── auth.py           # POST /login, /register, /logout, GET /me
│   │   │   └── projects.py       # CRUD /projects
│   │   ├── core/
│   │   │   ├── config.py         # Environment config
│   │   │   ├── database.py       # SQLAlchemy engine & session
│   │   │   └── security.py       # JWT encode/decode, bcrypt
│   │   ├── middleware/
│   │   │   └── auth_middleware.py # JWT auth guard
│   │   ├── models/
│   │   │   ├── user.py           # users table
│   │   │   └── project.py        # projects table
│   │   ├── repositories/         # Data access layer
│   │   ├── schemas/              # Pydantic request/response models
│   │   ├── services/             # Business logic layer
│   │   └── main.py               # FastAPI app entry point
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── dashboard/        # StatCard, RecentActivity, DashboardCards
│   │   │   ├── layout/           # Sidebar, TopNavbar, RootLayout, ProtectedRoute
│   │   │   ├── projects/         # CreateProjectDialog, DeleteProjectDialog
│   │   │   └── ui/               # shadcn/ui components (Button, Card, Input, Label)
│   │   ├── lib/
│   │   │   ├── api.ts            # Axios client with JWT interceptor
│   │   │   ├── projects.ts       # Project API calls
│   │   │   └── utils.ts          # cn() utility
│   │   ├── pages/                # Dashboard, Projects, Workspace, Upload,
│   │   │                         # ScanHistory, AI Status, Settings, Profile
│   │   ├── providers/            # AuthProvider (context + useAuth hook)
│   │   ├── types/                # TypeScript interfaces
│   │   ├── App.tsx               # Router configuration
│   │   └── main.tsx              # Entry point
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── index.html
└── README.md
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | No | Create account |
| POST | `/api/auth/login` | No | Sign in |
| GET | `/api/auth/me` | Yes | Current user |
| POST | `/api/auth/logout` | No | (Client-side) |
| POST | `/api/projects` | Yes | Create project |
| GET | `/api/projects` | Yes | List projects (paginated, sortable, searchable) |
| GET | `/api/projects/{id}` | Yes | Get project |
| PUT | `/api/projects/{id}` | Yes | Update project |
| DELETE | `/api/projects/{id}` | Yes | Delete project |

### Query Parameters for `GET /api/projects`

- `page` (default: 1)
- `page_size` (default: 12, max: 100)
- `sort_by` — `created_at`, `project_name`, `language`
- `sort_order` — `asc` or `desc`
- `search` — filters by project name (case-insensitive)

---

## Features

- **Authentication** — JWT-based register/login/logout with protected routes
- **Dashboard** — Statistics cards, quick actions, recent activity, AI status
- **Project Management** — Create, edit, delete projects with search, sort, and pagination
- **Dark Mode** — Full dark theme with glassmorphism design
- **Responsive** — Sidebar collapses to overlay on mobile
