<div align="center">

#  DevOs

**AI-Powered Developer & Repository Intelligence Platform**

_DevOs connects to repositories, understands their structure and code, enables
semantic search and repository-aware AI chat, visualizes architecture, and
provides a safe AI Developer Agent._

[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

<br/>

<a href="https://dev-os-theta.vercel.app">
  <img src="https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=24&pause=1000&color=06B6D4&center=true&vCenter=true&width=435&lines=Understand.;Search.;Visualize.;Build.;Ship." alt="Typing SVG" />
</a>

<br/>

[🌍 Live Demo (Vercel)](https://dev-os-theta.vercel.app) •
[⚙️ Backend API (Render)](https://devos-backend-qk4z.onrender.com/docs) •
[🐙 GitHub Repository](https://github.com/YashasviRajput13/DevOs_Project)

<br/>
</div>

---

## 💻 2. PRODUCT PREVIEW

<img width="1561" height="723" alt="image" src="https://github.com/user-attachments/assets/d69116f4-986a-49a3-8815-cc6834d94fb8" />

---

## 🧠 3. WHAT IS DEVOS?

DevOs is an AI-powered repository intelligence platform designed to help
developers understand large codebases faster.

**The core problem:** Developers waste significant time trying to understand:

- Complex repository structures and file dependencies.
- How deeply nested, unfamiliar files interact.
- The high-level architecture mapped to low-level implementation.
- Exactly where and how a piece of functionality is written.

**The solution:** DevOs addresses this by indexing live repositories and
constructing an intelligent semantic layer over the codebase. It parses, chunks,
and vectorizes your code, giving you a Developer Agent that safely finds answers
and executes code-level plans based on deep repository understanding.

---

## ⚡ 4. CORE FEATURES

| Feature Area                    | Capabilities                                                                                                                              |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **AI Repository Understanding** | • Repository indexing<br>• File & code analysis<br>• Code chunking & Embeddings<br>• Dependency mapping                                   |
| **Intelligent Code Search**     | • Semantic vector search<br>• Highly relevant codebase retrieval<br>• RAG-focused context injection                                       |
| **AI Code Chat**                | • Context-aware questioning<br>• Talk directly to your repository<br>• Ask architecture questions<br>• Explanations of complex logic      |
| **Architecture Intelligence**   | • Real-time overview generation<br>• File and folder relationships<br>• Extracted dependencies visualization                              |
| **Data Ingestion**              | • Connects to GitHub API<br>• Secure extraction & chunking<br>• Generates `sentence-transformers` embeddings<br>• Indexes into `pgvector` |
| **AI Developer Agent**          | • Autonomous task analysis & planning<br>• Multi-step reasoning capability<br>• Safety constraints prior to execution                     |

---

## 🔄 5. HOW DEVOS WORKS

```mermaid
flowchart TD
    A[Developer] --> B[Connect GitHub Repository]
    B --> C[Repository Indexing]
    C --> D[File Extraction]
    D --> E[Code Chunking]
    E --> F[Generate Embeddings]
    F --> G[Index to Vector Database]
    A --> H[Ask AI Chat / Search]
    H --> I[Vector / Semantic Search]
    I --> J[Retrieve Repository Context]
    J --> K[AI Developer Agent reasoning]
    K --> L[Developer Action]
```

---

## 🏗️ 6. SYSTEM ARCHITECTURE

```mermaid
flowchart LR
    Browser([Browser]) --> Frontend
    
    subgraph Frontend Subsystem
        Frontend[Next.js Frontend]
    end
    
    Frontend -->|HTTPS API| Backend
    
    subgraph Backend Subsystem
        Backend[FastAPI Application]
        Auth[Auth / JWT]
        Proj[Projects & Repositories]
        Search[Semantic Search]
        Chat[RAG / AI Chat]
        Agent[Developer Agent]
        
        Backend --- Auth
        Backend --- Proj
        Backend --- Search
        Backend --- Chat
        Backend --- Agent
    end
    
    subgraph External Infrastructure
        DB[(PostgreSQL + pgvector)]
        GitHub[GitHub API]
        LLM[Groq / Gemini APIs]
    end
    
    Proj --> GitHub
    Search --> DB
    Chat --> LLM
    Agent --> LLM
```

---

## 🛠️ 7. TECH STACK

**Frontend**

- Next.js (App Router)
- React
- Tailwind CSS

**Backend**

- FastAPI
- Python 3
- SQLAlchemy
- Passlib (bcrypt) & PyJWT

**Machine Learning & AI**

- `sentence-transformers`
- Google Gemini (`gemini-2.0-flash`)
- Groq (`qwen/qwen3.8-27b`)

**Database & Infrastructure**

- PostgreSQL with `pgvector` extension
- Neon (Serverless Postgres)
- Vercel (Frontend Hosting)
- Render (Backend Hosting)

---

## 📁 8. REPOSITORY STRUCTURE

```text
DevOs_Project/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # Route controllers (auth, chat, etc)
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic (Git, LLM, RAG)
│   │   ├── config.py         # Environment configurations
│   │   └── main.py           # FastAPI application entry
│   ├── alembic/              # Database migrations
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Next.js Application
│   ├── src/
│   │   ├── app/              # Next.js 13+ App router pages
│   │   ├── components/       # Reusable React UI components
│   │   ├── context/          # State management (AuthContext)
│   │   └── lib/              # API clients & utilities
│   ├── package.json          # Node dependencies
│   └── tailwind.config.js    # Tailwind layout config
├── docker-compose.yml        # Local development DB setup
└── render.yaml               # Producion backend definitions
```

---

## 🔌 9. API OVERVIEW

The backend exposes a well-structured REST API. Standard endpoints include:

- **Auth** (`/api/auth`): Handles user registration, JWT login, and session
  validation.
- **Projects** (`/api/projects`): Manage organizational workspaces and
  groupings.
- **Repositories** (`/api/projects/{id}/repositories`): Sync your GitHub repos,
  fetch files, build architectural nodes.
- **Search** (`/api/search`): Perform natural language semantic searches against
  your vector-indexed codebase.
- **AI Chat** (`/api/chat`): Conversational RAG endpoints that maintain memory
  and repository context.
- **Developer Agent** (`/api/agent`): High-level endpoints designed for planning
  and executing developer tasks.
- **Health** (`/health`): Startup, readiness, and diagnostics verification.

---

## 💻 10. LOCAL DEVELOPMENT

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL database (or Docker for local DB)

### Clone Repository

```bash
git clone https://github.com/YashasviRajput13/DevOs_Project.git
cd DevOs_Project/devos
```

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:3000`.

---

## 🔐 11. ENVIRONMENT VARIABLES

Ensure your `.env` flags are properly configured in both development and
production. **Never commit actual values.**

**Backend (root `.env` or Render settings):**

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# LLM Providers
GROQ_API_KEY=your_groq_key
GROQ_MODEL=qwen/qwen3.8-27b
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash

# Security 
JWT_SECRET=strong_random_string
APP_SECRET_KEY=strong_random_string
GITHUB_TOKEN=your_personal_access_token

# Deployment
APP_ENV=production
DEBUG=false
CORS_ORIGINS=https://dev-os-theta.vercel.app,http://localhost:3000
```

**Frontend (`frontend/.env.local` or Vercel settings):**

```env
NEXT_PUBLIC_API_URL=https://devos-backend-qk4z.onrender.com
```

---

## 🚀 12. DEPLOYMENT

The production deployment architecture natively splits the workloads for massive
scalability.

```mermaid
flowchart TD
    Browser((Client Browser))
    
    subgraph Vercel
        FE[Next.js Application]
    end
    
    subgraph Render
        BE[FastAPI + Machine Learning]
    end
    
    subgraph Neon
        DB[(PostgreSQL + pgvector)]
    end

    Browser -->|Visits UI| FE
    FE -->|API Requests| BE
    BE -->|SQL / Vectors| DB
```

> **Note:** The frontend application on Vercel is instructed to speak directly
> to the Render backend via the `NEXT_PUBLIC_API_URL` environment variable.

---

## 🛡️ 13. SECURITY

DevOs enforces rigorous platform security measures:

- **Environment Variables:** Credentials are NEVER hardcoded into source code
  mapping.
- **Git Protection:** `.env` and `.env.local` files are safely blacklisted via
  `.gitignore`.
- **API Guarding:** Production CORS policies are strictly enforced.
  Auto-configured Vercel preview branch domains and whitelisted URLs are
  validated dynamically.
- **Authentication:** Users are securely authenticated via `bcrypt` hashing and
  issue standards-compliant JWT validation strategies.
- **GitHub Tokens:** Ingest keys are securely managed within the API runtime
  rather than exposed client-side.

---

## 🤖 14. DEVELOPER AGENT SAFETY

Since DevOs features an underlying Developer Agent that manipulates codebase
functionality, safety constraints are extremely important.

**Agent Execution Workflow:**

1. **User Request:** Initial natural language constraint from the human
   developer.
2. **Understand Intent:** Context retrieved mapped entirely to localized vector
   constraints.
3. **Generate Plan:** A step-by-step non-mutating plan is formalized first.
4. **Review / Approval:** Developer can verify operations before modifying
   origin.

---

## 🗺️ 15. ROADMAP

_Planned Future Features:_

- Multi-user workspaces and organizational teams
- Role-based access control & Invites
- Multi-LLM provider abstraction support (Anthropic / OpenAI toggle)
- CI/CD integration and deployment hooks
- Project-level memory isolation updates
- Issue-aware development (Jira / Linear tracking tie-in)

---

## 🤝 16. CONTRIBUTING

1. **Fork** the repository
2. **Create** your feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

---

## 📄 17. LICENSE

License: Not yet specified.

---

<div align="center">
  <br/>
  <b>Built with ❤️ for developers who want to understand, build, and ship faster.</b><br/>
  <i>DevOs</i>
</div>
