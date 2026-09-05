# DevOs

<img width="1612" height="712" alt="image" src="https://github.com/user-attachments/assets/ec1f22ba-5931-4531-a7bb-35acf2843d15" />


DevOs is an AI-powered repository intelligence and agentic development platform.

## Overview

DevOs provides a holistic environment for interacting with source code via Large
Language Models (LLMs). It seamlessly connects to your GitHub repositories,
indexes the code, creates embeddings, and provides semantic search, an
interactive AI Chat, architectural visualizations, and a Developer Agent.

### Features

- **Repository Indexing & Search**: Search semantic meaning, not just keywords.
- **RAG Chat**: Context-aware AI answers with exact file lineage citations.
- **Interactive Developer Agent**: Propose code changes, get an interactive
  diff, run secure isolated tests, and seamlessly push changes to a Git branch
  or open a Pull Request.
- **Safety First Architecture**: Changes cannot be committed haphazardly. Strict
  sandboxing and explicit plan approval ensures quality and safety.

## Architecture

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, pgvector
- **Frontend**: Next.js, Tailwind CSS
- **AI Integration**: Groq API + LangChain
- **Git/GitHub**: Seamless execution using local Git CLI wrappers and GitHub
  REST API integration.

## Prerequisites

- Node.js >= 18.x
- Python >= 3.10
- PostgreSQL with `pgvector`
- Git

## Installation & Setup

1. **Clone & Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env and supply actual keys!
   ```

2. **Database Setup** Ensure PostgreSQL is running either natively or via
   Docker.
   ```bash
   cd backend
   pip install -r requirements.txt
   alembic upgrade head
   ```

3. **Backend Startup**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

4. **Frontend Startup**
   ```bash
   cd frontend
   npm ci
   npm run build
   npm run start
   ```

### Docker Deployment

1. Build and run using Docker Compose:
   ```bash
   docker-compose up --build -d
   ```
2. The Database will migrate on startup (make sure you've appropriately run
   migrations).

## Configuration

See `.env.example` to supply variables for:

- Database settings
- `GROQ_API_KEY` and `GROQ_MODEL`
- `GITHUB_TOKEN`
- `NEXT_PUBLIC_API_URL`

## Final Readiness

- **Security Check passed**: Environment variables are redacted in processes,
  `.env` files are ignored, absolute paths blocked.

DEVOS READY FOR DEMO/DEPLOYMENT
