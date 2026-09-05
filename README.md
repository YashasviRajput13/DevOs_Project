# DevOs

<img width="1612" height="712" alt="image" src="https://github.com/user-attachments/assets/ec1f22ba-5931-4531-a7bb-35acf2843d15" />

AI-Powered Developer & Repository Intelligence Platform

Understand your codebase. Search intelligently. Visualize
architecture. Build with AI.

<p>

<a href="https://dev-os-theta.vercel.app">{=html}🌐 Live
Demo</a>{=html} ·
<a href="https://github.com/YashasviRajput13/DevOs_Project">{=html}💻
GitHub</a>{=html} ·
<a href="https://devos-backend-qk4z.onrender.com/docs">{=html}📚 API
Docs</a>{=html}

</p>

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=20&duration=2800&pause=700&color=22D3EE&center=true&vCenter=true&width=700&lines=Understand+your+repository.;Search+your+code+semantically.;Explore+architecture+and+dependencies.;Chat+with+your+codebase.;Build+with+an+AI+Developer+Agent." alt="DevOs animated typing">{=html}
:::

🚀 What is DevOs?

DevOs is an AI-powered developer platform that turns a source-code
repository into an intelligent, searchable knowledge base.

Instead of manually navigating unfamiliar files, tracing dependencies,
and searching through large codebases, developers can connect a
repository, index it, explore its structure, perform semantic code
search, ask repository-aware questions, visualize architecture, and work
through AI-assisted development workflows.

Understand. Build. Ship. With the power of AI.

✨ Core Capabilities

Capability                          Description

🧠 Repository Intelligence          Repository indexing, code chunking,
embeddings, and contextual
understanding

🔎 Semantic Code Search             Find relevant code based on
meaning, not only exact keywords

💬 AI Code Chat                     Ask repository-aware questions
using retrieved project context

🏗️ Architecture Intelligence        Explore repository structure,
dependencies, and architecture

📦 Repository Indexing              Connect repositories, extract
files, chunk code, and generate
embeddings

🤖 Developer Agent                  AI-assisted queries, planning,
testing, branching, commits, and
related workflows

🎬 How DevOs Works

flowchart LR
    A[Developer] --> B[Connect Repository]
    B --> C[Repository Indexing]
    C --> D[Code Chunking]
    D --> E[Embeddings]
    E --> F[(PostgreSQL + pgvector)]
    F --> G[Semantic Retrieval]
    G --> H[Repository Context]
    H --> I[AI Chat]
    H --> J[Developer Agent]
    H --> K[Architecture Intelligence]

🏛️ System Architecture

flowchart TB
    U[Browser] --> FE[Next.js Frontend]
    FE -->|HTTPS API| BE[FastAPI Backend]

    BE --> PM[Projects & Repositories]
    BE --> SS[Semantic Search]
    BE --> RAG[RAG / AI Chat]
    BE --> AG[Developer Agent]
    BE --> AR[Architecture Intelligence]

    PM --> DB[(PostgreSQL + pgvector)]
    SS --> DB
    RAG --> DB

    BE --> GH[GitHub API]
    RAG --> LLM[Groq]
    BE --> EMB[Sentence Transformers]

🔍 Repository Intelligence Pipeline

flowchart LR
    A[GitHub Repository] --> B[File Discovery]
    B --> C[Content Extraction]
    C --> D[Code Chunking]
    D --> E[Embedding Generation]
    E --> F[(pgvector)]
    F --> G[Semantic Retrieval]
    G --> H[LLM Context]
    H --> I[Developer Answer / Action]

🛠️ Tech Stack

Layer                    Technology

Frontend                 Next.js, React, Tailwind CSS
Backend                  Python, FastAPI
ORM                      SQLAlchemy
Database                 PostgreSQL
Vector Search            pgvector
Embeddings               Sentence Transformers --- all-MiniLM-L6-v2
AI / LLM                 Groq
Repository Integration   GitHub
Frontend Hosting         Vercel
Backend Hosting          Render
Production Database      Neon

📁 Project Structure

DevOs_Project/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── app/
│   ├── components/
│   ├── public/
│   └── ...
├── devos/
├── docs/
├── scripts/
├── tests/
├── docker-compose.yml
├── .env.example
└── README.md

🔌 API Surface

The FastAPI backend currently provides API areas for:

Projects

Repositories

Search

AI Chat

Developer Agent

Health

Interactive documentation:

Swagger UI: https://devos-backend-qk4z.onrender.com/docs

Authentication endpoints should only be documented here after they are
actually implemented and registered in the FastAPI application.

⚙️ Local Development

Prerequisites

Python 3.10+

Node.js 18+

npm

PostgreSQL with pgvector support

GitHub token

Groq API key

Clone

git clone https://github.com/YashasviRajput13/DevOs_Project.git
cd DevOs_Project

Backend

cd backend
python -m venv .venv

Windows:

.venv\Scriptsctivate

macOS / Linux:

source .venv/bin/activate

Install and run:

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

Swagger:

http://localhost:8000/docs

Frontend

In another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:3000

🔐 Environment Variables

Never commit real credentials.

Backend

APP_ENV=production
DEBUG=false
DATABASE_URL=your-neon-database-url
GITHUB_TOKEN=your-github-token
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=your-supported-groq-model
JWT_SECRET=your-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60
CORS_ORIGINS=https://dev-os-theta.vercel.app

Frontend

NEXT_PUBLIC_API_URL=https://devos-backend-qk4z.onrender.com

For local development:

NEXT_PUBLIC_API_URL=http://localhost:8000

☁️ Deployment

DevOs uses a separated production architecture:

Developer Browser
       │
       ▼
┌───────────────┐
│    Vercel     │
│ Next.js       │
└───────┬───────┘
        │ HTTPS
        ▼
┌───────────────┐
│    Render     │
│ FastAPI       │
└───┬────┬───┬──┘
    │    │   │
    ▼    ▼   ▼
  Neon GitHub Groq

Component    Platform

Frontend     Vercel
Backend      Render
Database     Neon
Repository   GitHub
AI           Groq

🛡️ Security

Keep API keys in environment variables.

Never commit .env files or production credentials.

Restrict production CORS to trusted frontend origins.

Keep GitHub, database, and AI credentials server-side.

Never expose secrets through NEXT_PUBLIC_* variables.

Keep AI-assisted development operations controlled and reviewable.

🤖 Developer Agent

The Developer Agent follows a structured development workflow:

flowchart LR
    A[Developer Request] --> B[Agent Understanding]
    B --> C[Plan]
    C --> D[Review / Control]
    D --> E[Execute]
    E --> F[Test]
    F --> G[Branch / Commit]
    G --> H[Push]

🗺️ Roadmap

Current

Repository connection

Repository indexing

Code chunking

Embedding generation

Semantic code search

Repository-aware AI chat

Repository overview

Architecture intelligence

Developer Agent workflows

Production frontend deployment

Production backend deployment

Planned

Multi-user workspaces

Project-level data isolation

Role-based access control

Workspace invitations

Multi-LLM provider support

Pull-request intelligence

Issue-aware development

CI/CD integration

Advanced agent workflows

Richer repository analytics

🤝 Contributing

git checkout -b feature/your-feature
# make your changes
# test your changes
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature

Then open a Pull Request.

📄 License

License: Not yet specified.

::: {align="center"}

⚡ Understand. Build. Ship.

DevOs --- an intelligence layer over your codebase.

<a href="https://dev-os-theta.vercel.app">{=html}Live
Demo</a>{=html}  • 
<a href="https://github.com/YashasviRajput13/DevOs_Project">{=html}GitHub</a>{=html}
 •  <a href="https://devos-backend-qk4z.onrender.com/docs">{=html}API
Docs</a>{=html}

<br>{=html}<br>{=html}

<sub>{=html}Built for developers who want to understand, build, and
ship faster.</sub>{=html}
